# Interpolación cromática

## 1. Representación RGB

Un color de pantalla se describe con tres intensidades enteras entre 0 y 255: rojo \(R\), verde \(G\) y
azul \(B\). Si un color depende de la posición \(x\) en el mural, el problema se convierte en interpolar
**tres funciones independientes**: \(R(x)\), \(G(x)\) y \(B(x)\), todas con los mismos nodos.

| Nodo | Posición | Color | \(R\) | \(G\) | \(B\) |
|---|---:|---|---:|---:|---:|
| \(x_0\) | 0 m | Carmesí `#DC143C` | 220 | 20 | 60 |
| \(x_1\) | 3 m | Morado `#800080` | 128 | 0 | 128 |
| \(x_2\) | 6 m | Azul `#1E90FF` | 30 | 144 | 255 |

Posición objetivo: \(x = 4.5\) m.

Con tres nodos distintos existe un único polinomio de grado \(\le 2\) que pasa por ellos. Lagrange,
Newton y Neville llegan a ese mismo polinomio (o a su valor) por caminos distintos.

## 2. Lagrange

\[
P(x)=\sum_{i=0}^{n}y_iL_i(x),\qquad
L_i(x)=\prod_{j\neq i}\frac{x-x_j}{x_i-x_j}
\]

Para \(x = 4.5\):

\[
L_0=\frac{(4.5-3)(4.5-6)}{(0-3)(0-6)}=-0.12500,\quad
L_1=\frac{(4.5-0)(4.5-6)}{(3-0)(3-6)}=0.75000,\quad
L_2=\frac{(4.5-0)(4.5-3)}{(6-0)(6-3)}=0.37500
\]

Verificación: \(L_0+L_1+L_2=1.00000\).

\[
\begin{aligned}
R(4.5)&=220(-0.125)+128(0.75)+30(0.375)=79.75000\\
G(4.5)&=20(-0.125)+0(0.75)+144(0.375)=51.50000\\
B(4.5)&=60(-0.125)+128(0.75)+255(0.375)=184.12500
\end{aligned}
\]

## 3. Newton (diferencias divididas)

\[
P(x)=f[x_0]+f[x_0,x_1](x-x_0)+f[x_0,x_1,x_2](x-x_0)(x-x_1)
\]
\[
f[x_i,\dots,x_j]=\frac{f[x_{i+1},\dots,x_j]-f[x_i,\dots,x_{j-1}]}{x_j-x_i}
\]

| Canal | \(f[x_0]\) | \(f[x_0,x_1]\) | \(f[x_1,x_2]\) | \(f[x_0,x_1,x_2]\) |
|---|---:|---:|---:|---:|
| R | 220 | −30.66667 | −32.66667 | −0.33333 |
| G | 20 | −6.66667 | 48.00000 | 9.11111 |
| B | 60 | 22.66667 | 42.33333 | 3.27778 |

Polinomios:

\[
\begin{aligned}
R(x)&=220-30.66667x-0.33333x(x-3)\\
G(x)&=20-6.66667x+9.11111x(x-3)\\
B(x)&=60+22.66667x+3.27778x(x-3)
\end{aligned}
\]

Evaluados en \(x = 4.5\) dan 79.75000, 51.50000 y 184.12500.

## 4. Neville

\[
P_{i,j}(x)=\frac{(x-x_i)P_{i+1,j}(x)-(x-x_j)P_{i,j-1}(x)}{x_j-x_i}
\]

| Canal | \(P_{0,0}, P_{1,1}, P_{2,2}\) | \(P_{0,1}\) | \(P_{1,2}\) | \(P_{0,2}\) |
|---|---|---:|---:|---:|
| R | 220, 128, 30 | 82.00000 | 79.00000 | **79.75000** |
| G | 20, 0, 144 | −10.00000 | 72.00000 | **51.50000** |
| B | 60, 128, 255 | 162.00000 | 191.50000 | **184.12500** |

Ejemplo (canal rojo):
\(P_{0,1}=\frac{(4.5-0)(128)-(4.5-3)(220)}{3-0}=82\),
\(P_{1,2}=\frac{(4.5-3)(30)-(4.5-6)(128)}{6-3}=79\),
\(P_{0,2}=\frac{(4.5-0)(79)-(4.5-6)(82)}{6-0}=79.75\).

## 5. Ejemplo completo y conversión hexadecimal

Resultado decimal: \((79.75000,\ 51.50000,\ 184.12500)\).

1. **Redondeo** al entero más cercano: \((80, 52, 184)\). (Los empates .5 se redondean hacia arriba.)
2. **Limitación** (*clamp*) a [0, 255]: \(\operatorname{clamp}(v)=\min(255,\max(0,v))\). Aquí no cambia nada.
3. **Hexadecimal**: \(80 = \texttt{0x50}\), \(52 = \texttt{0x34}\), \(184 = \texttt{0xB8}\) → **`#5034B8`**.

Durante el procedimiento no se redondea: los cálculos usan doble precisión y solo la presentación
muestra cinco decimales.

## 6. Comparación

| Método | R | G | B | Hexadecimal | Diferencia máxima |
|---|---:|---:|---:|---|---:|
| Lagrange | 79.75000 | 51.50000 | 184.12500 | `#5034B8` | 0.00000 |
| Newton | 79.75000 | 51.50000 | 184.12500 | `#5034B8` | 0.00000 |
| Neville | 79.75000 | 51.50000 | 184.12500 | `#5034B8` | 0.00000 |

> Los tres métodos producen el mismo resultado porque construyen el mismo polinomio interpolador con
> los mismos puntos. Lo que cambia es el procedimiento de cálculo.

En otras configuraciones puede aparecer una diferencia del orden de \(10^{-14}\) por redondeo de punto
flotante; la aplicación la muestra en notación científica en lugar de ocultarla.

| Método | Ventaja | Limitación | Uso recomendado |
|---|---|---|---|
| Lagrange | Fórmula directa y fácil de explicar. | Debe reconstruirse al agregar puntos. | Ejemplos académicos con pocos colores. |
| Newton | Permite incorporar puntos adicionales. | Requiere tabla de diferencias. | Distribuciones que crecerán con nuevos colores. |
| Neville | Calcula directamente el punto deseado. | No entrega inmediatamente el polinomio completo. | Consultar colores en posiciones concretas. |

## 7. Limitaciones

- **RGB no es perceptualmente uniforme.** Interpolar en RGB es sencillo de explicar, pero pasos iguales
  en RGB no se perciben como cambios de color iguales. Espacios como CIELAB u OKLab dan transiciones
  más naturales.
- **El polinomio puede salir de [0, 255].** Con el ejemplo,
  \(G(x)=9.11111x^2-34x+20\) es negativo entre \(x\approx0.73\) y \(x=3\) (por ejemplo, \(G(1.5)=-10.5\)).
  La aplicación limita cada canal al pintar el mural, informa cuántas muestras se recortaron y muestra
  la curva sin limitar en la gráfica por canal.
- **Grado alto.** Con muchos nodos equiespaciados un único polinomio puede oscilar (fenómeno de Runge);
  para muchos colores conviene interpolar por tramos o con splines.
- **Solo interpolación.** Las posiciones fuera de \([x_0, x_2]\) se rechazan porque serían extrapolación.
