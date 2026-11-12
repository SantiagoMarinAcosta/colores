# Guía de presentación

Duración sugerida: 10–12 minutos. Navegación: flechas ← →, puntos inferiores o botones; **F** activa la
pantalla completa. Escribe tu nombre en la portada: aparece en el pie de las diapositivas.

## Guion por diapositiva

1. **Portada.** «Vamos a mostrar cómo un método numérico permite que una computadora calcule los colores
   de un mural a partir de solo tres colores elegidos por el artista».
2. **Problema real.** «El artista fija carmesí en 0 m, morado en 3 m y azul en 6 m. Lo que falta son todos
   los tonos intermedios; necesitamos una regla matemática para calcularlos».
3. **Color como dato.** «Cada color es una terna (R, G, B). Por eso el problema se convierte en tres
   problemas de interpolación: uno por canal».
4. **Qué es interpolar.** «Interpolar es estimar valores entre puntos conocidos. Con tres puntos hay un único
   polinomio de grado 2 que pasa por ellos».
5. **Lagrange.** «Cada base \(L_i\) vale 1 en su nodo y 0 en los demás. En \(x = 4.5\): −0.125, 0.75 y
   0.375. Suman 1, lo que sirve como verificación».
6. **Cálculo RGB.** «Multiplicamos cada canal por las bases: R = 79.75, G = 51.5, B = 184.125. Redondeamos,
   limitamos y convertimos: RGB (80, 52, 184), es decir #5034B8».
7. **Comparación.** «Newton usa diferencias divididas y Neville una tabla triangular. Los tres dan lo mismo
   porque el polinomio interpolador es único». *(Mostrar la sección de procedimiento si hay tiempo).*
8. **Animación.** «El servidor evalúa el polinomio en 121 posiciones; el navegador solo pinta. Observen las
   pausas en los tres colores conocidos y el resaltado en 4.5 m».
9. **Importancia informática.** «Este mismo principio aparece en degradados, escalado de imágenes,
   fotogramas intermedios de animación y mapas de color científicos».
10. **Conclusión.** Leer la frase final y mencionar la limitación de RGB y del *clamp*.

Demostración en vivo sugerida (1–2 minutos): cambiar el color del centro o la posición objetivo, pulsar
**Calcular color**, cambiar a Newton o Neville y pulsar **Animar mural**.

## Posibles preguntas del profesor

**¿Por qué los tres métodos dan exactamente el mismo resultado?**
Porque el polinomio de grado \(\le n\) que pasa por \(n+1\) puntos con abscisas distintas es único. Los
métodos solo cambian la forma de construirlo o evaluarlo. Puede haber diferencias de \(10^{-14}\) por
aritmética de punto flotante.

**¿Por qué interpolar cada canal por separado?**
R, G y B son coordenadas independientes del color. Interpolar cada una con los mismos nodos equivale a
interpolar el vector (R, G, B).

**¿Qué pasa si el polinomio da un valor negativo o mayor que 255?**
Ocurre: en el ejemplo, \(G(1.5) = -10.5\). Se limita (*clamp*) a [0, 255] para obtener un color válido, y la
aplicación lo informa en lugar de ocultarlo. La gráfica por canal muestra la curva sin limitar.

**¿Por qué no se redondea durante el cálculo?**
Redondear en pasos intermedios acumula error. Se trabaja en doble precisión y solo se redondea al
presentar (cinco decimales) y al convertir a entero para el color.

**¿Qué ventaja tiene Newton sobre Lagrange?**
Si se agrega un cuarto color, Newton solo añade una fila y una columna a la tabla y un término al
polinomio; Lagrange debe recalcular todas las bases.

**¿Para qué sirve Neville si no da el polinomio?**
Cuando solo interesa el valor en un punto, Neville lo obtiene directamente y la tabla permite ver cómo
mejora la estimación al combinar más nodos.

**¿Por qué no se permite \(x\) fuera de [0, 6]?**
Eso sería extrapolación: el polinomio no está respaldado por datos fuera del intervalo y sus valores
pueden crecer rápidamente.

**¿Es RGB la mejor opción?**
Para explicar el método sí, por su sencillez. Para resultados visualmente más uniformes se usan espacios
perceptuales como CIELAB u OKLab; el algoritmo de interpolación sería el mismo.

**¿Qué pasa si dos colores tienen la misma posición?**
Un denominador \(x_i - x_j\) sería cero. La aplicación lo rechaza con un mensaje explicativo.

**¿Por qué el navegador no calcula los colores?**
Para separar responsabilidades: el backend contiene los métodos numéricos probados con pytest y el
frontend solo representa los resultados. Así la animación siempre muestra exactamente lo calculado.
