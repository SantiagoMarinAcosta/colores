# Arquitectura de NumeriArte

La aplicación sigue un MVC modular con una capa de servicio y una capa de métodos numéricos aislada.

```text
Vista → controlador → servicio → métodos numéricos → resultado → vista
```

## Flujo de una solicitud

1. **Vista** (`templates/interpolacion.html` + `static/js/interpolacion.js`): el usuario edita los tres
   puntos, la posición objetivo y el método. El JavaScript envía `POST /api/interpolar` con JSON.
2. **Controlador** (`controllers/interpolacion_controller.py`): comprueba que el cuerpo sea un objeto
   JSON, llama a `ColorService.interpolar()` y devuelve el resultado con `jsonify` (200) o los errores
   de validación (400). No contiene fórmulas.
3. **Servicio** (`services/color_service.py`):
   - valida las entradas: exactamente tres puntos, posiciones numéricas, no repetidas y crecientes,
     objetivo dentro de \([x_0, x_2]\), colores `#RRGGBB`, número de muestras entre 121 y 241;
   - construye objetos `PuntoColor`;
   - ejecuta los tres interpoladores (para el procedimiento y la comparación);
   - convierte el resultado decimal a color: redondeo → *clamp* a [0, 255] → hexadecimal;
   - genera las muestras del mural con el método elegido;
   - empaqueta todo en un `ResultadoInterpolacion`.
4. **Métodos numéricos** (`metodos_numericos/`):
   - `base.py`: `InterpoladorBase` con `resolver(puntos, x_objetivo)`, validación de nodos distintos y
     división protegida (un denominador cero lanza `ErrorInterpolacion`, nunca se oculta con un 0);
   - `interpolacion.py`: `InterpoladorLagrange`, `InterpoladorNewton`, `InterpoladorNeville`.
   Cada clase interpola R, G y B por separado y devuelve valores en doble precisión **sin redondear**,
   junto con todos los términos y tablas intermedias.
5. **Resultado** (`models/resultado_interpolacion.py`): dataclass con método, posición, resultado
   decimal, RGB, hexadecimal, procedimiento, comparación, mensaje, indicador `correcto`, datos de
   animación y tiempo de ejecución. `to_dict()` produce la respuesta JSON.
6. **Vista**: el navegador muestra los números con cinco decimales, tipografía las fórmulas con MathJax,
   dibuja la gráfica (Chart.js) y anima el mural. **El JavaScript no interpola**: solo representa los
   colores que llegaron del backend.

## Responsabilidades por capa

| Capa | Archivos | Responsabilidad |
|---|---|---|
| Modelo | `models/punto_color.py`, `models/resultado_interpolacion.py` | Datos y conversión hex ↔ RGB |
| Métodos numéricos | `metodos_numericos/base.py`, `interpolacion.py` | Algoritmos y procedimiento |
| Servicio | `services/color_service.py` | Validación, conversión a color, comparación, muestras |
| Controlador | `controllers/*.py` | HTTP: rutas, códigos de estado, plantillas |
| Vista | `templates/*.html`, `static/` | Presentación, interacción, animación |

## Página principal

- La ruta `GET /` ejecuta el ejemplo predeterminado en el servidor y lo pasa a la plantilla; así la
  explicación académica y las diapositivas muestran valores calculados, no escritos a mano.
- Los mismos datos se incrustan como JSON (`<script type="application/json">`) para que la interfaz
  dibuje el procedimiento y el mural sin una segunda petición.

## Animación

`static/js/animacion_mural.js` define `MuralAnimado`:

- recibe `mural` (metadatos: controles, objetivo, rango) y `muestras_mural` (colores);
- usa `requestAnimationFrame`; el progreso avanza en función del tiempo real × velocidad (0.5×, 1×, 2×);
- se detiene brevemente en cada color de control y en la posición objetivo, que se resalta;
- actualiza la barra de progreso y el RGB de la franja actual;
- `reproducir`, `pausar`, `alternar`, `reiniciar` y `setVelocidad` son sus controles públicos.

La diapositiva 8 usa una segunda instancia del mismo componente.

## Pruebas

`tests/` usa pytest con la aplicación creada por `create_app("testing")`. Las pruebas de algoritmos usan
directamente las clases de `metodos_numericos`; las de servicio, `ColorService`; las de rutas, el
`test_client` de Flask.
