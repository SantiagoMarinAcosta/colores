# NumeriArte: interpolación numérica para la distribución del color

Aplicación web académica (Flask) que muestra cómo la **interpolación polinómica** permite estimar
colores intermedios entre tres colores conocidos de un mural digital, y cómo generar con ella una
distribución cromática continua.

## Objetivo

Un artista define tres colores en tres posiciones del mural. La aplicación:

- calcula el color de una posición intermedia con **Lagrange**, **Newton (diferencias divididas)** o **Neville**;
- muestra el procedimiento matemático completo, canal por canal (\(R(x)\), \(G(x)\), \(B(x)\));
- compara los tres métodos (producen el mismo polinomio);
- genera entre 121 y 241 muestras y **anima el llenado del mural** de izquierda a derecha;
- incluye una **presentación de 10 diapositivas**, una explicación académica y un **glosario** con buscador.

Los algoritmos están implementados a mano, sin SciPy ni SymPy, en
`app/metodos_numericos/interpolacion.py`.

Ejemplo predeterminado: Carmesí `#DC143C` en 0 m, Morado `#800080` en 3 m y Azul `#1E90FF` en 6 m.
En \(x = 4.5\) m los tres métodos dan \((79.75000,\ 51.50000,\ 184.12500)\), es decir, RGB \((80, 52, 184)\) = **`#5034B8`**.

## Instalación

Requisitos: Python 3.10 o superior.

```bash
cd numeriarte_interpolacion
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Ejecución local

```bash
python app.py
```

Abre <http://127.0.0.1:5000>. Rutas disponibles:

| Ruta | Descripción |
|---|---|
| `GET /` | Interpolación cromática, mural, procedimiento, comparación, presentación y explicación |
| `GET /presentacion` | Redirige a `/#presentacion` (la presentación está integrada en la página) |
| `GET /glosario` | Glosario con buscador y filtros |
| `POST /api/interpolar` | Cálculo en JSON |

> Gunicorn no funciona en Windows; en Windows usa `python app.py`. En Linux/macOS también puedes
> probar el modo producción con `gunicorn wsgi:app`.

### Ejemplo de llamada a la API

```bash
curl -X POST http://127.0.0.1:5000/api/interpolar \
  -H "Content-Type: application/json" \
  -d '{"puntos":[{"x":0,"color":"#DC143C"},{"x":3,"color":"#800080"},{"x":6,"color":"#1E90FF"}],
       "x_objetivo":4.5,"metodo":"lagrange","muestras":121}'
```

Respuesta (resumida): `correcto`, `metodo`, `x_objetivo`, `resultado_decimal`, `resultado_rgb`,
`hexadecimal`, `mensaje`, `procedimiento` (método elegido), `procedimientos` (los tres),
`comparacion`, `mural` (metadatos), `muestras_mural` (colores ya calculados) y `tiempo_ms`.
Los errores de validación devuelven HTTP 400 con `correcto: false` y la lista `errores`.

## Pruebas

```bash
python -m pytest -v
```

Las pruebas cubren: reproducción exacta de los nodos con los tres métodos, el resultado en
\(x = 4.5\) con tolerancia \(10^{-9}\), redondeo, hexadecimal, limitación a [0, 255], posiciones
repetidas o desordenadas, objetivo fuera de rango, campos vacíos, colores inválidos, muestras del mural
y todas las rutas.

## Despliegue en Render

1. Sube la carpeta `numeriarte_interpolacion` a un repositorio de GitHub (en la raíz del repositorio).
2. En Render: **New → Blueprint** y selecciona el repositorio; Render lee `render.yaml`.
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn wsgi:app` (Gunicorn usa automáticamente la variable `PORT` de Render).
3. Alternativa manual: **New → Web Service**, runtime Python, con los mismos comandos.

La página carga Bootstrap, MathJax, Chart.js y fuentes desde CDN, por lo que el navegador necesita
conexión a Internet para mostrar estilos, fórmulas y la gráfica.

## Estructura

```text
numeriarte_interpolacion/
├── app.py                     # Servidor de desarrollo
├── wsgi.py                    # Entrada para Gunicorn
├── config.py                  # Configuración por entorno
├── requirements.txt / render.yaml / pytest.ini
├── app/
│   ├── __init__.py            # Fábrica create_app, filtros Jinja, errores
│   ├── controllers/           # Rutas: validan la petición y llaman al servicio
│   ├── models/                # PuntoColor, ResultadoInterpolacion
│   ├── services/              # ColorService: validación, conversión, comparación, mural
│   ├── metodos_numericos/     # Lagrange, Newton, Neville (implementación manual)
│   ├── templates/             # base, interpolacion, _presentacion, glosario, _macros, error
│   └── static/                # styles.css, interpolacion.js, animacion_mural.js, presentacion.js
├── docs/                      # ARQUITECTURA, INTERPOLACION_CROMATICA, GUIA_PRESENTACION
└── tests/                     # pytest
```

Más detalles en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md),
[docs/INTERPOLACION_CROMATICA.md](docs/INTERPOLACION_CROMATICA.md) y
[docs/GUIA_PRESENTACION.md](docs/GUIA_PRESENTACION.md).
