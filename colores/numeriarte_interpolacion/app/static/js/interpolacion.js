/* =========================================================================
   Interfaz principal: formulario → POST /api/interpolar → vista.
   Todos los números vienen del backend; aquí solo se formatean (5 decimales)
   y se representan. No se recalcula ninguna interpolación en el navegador.
   ========================================================================= */
(function () {
  "use strict";

  var CANALES = ["r", "g", "b"];
  var LETRA = { r: "R", g: "G", b: "B" };
  var NOMBRE_CANAL = { r: "Canal rojo", g: "Canal verde", b: "Canal azul" };
  var PATRON_HEX = /^#?[0-9a-fA-F]{6}$/;

  var $ = function (id) { return document.getElementById(id); };
  var form = $("form-interpolacion");
  var entradaInicial = JSON.parse($("entrada-inicial").textContent);
  var ultimo = JSON.parse($("datos-iniciales").textContent);
  var pestanaActiva = "lagrange";
  var idSolicitud = 0;
  var grafica = null;

  // ---------------------------------------------------------------- formato
  function f5(v) {
    v = Number(v);
    if (Math.abs(v) < 5e-6) v = 0;
    return v.toFixed(5);
  }
  function fm(v) { return String(Math.round(Number(v) * 1e6) / 1e6); }
  function par(v) { return Number(v) < 0 ? "(" + fm(v) + ")" : fm(v); }
  function parF(v) { return Number(v) < 0 ? "(" + f5(v) + ")" : f5(v); }
  function dato(v) { return Number.isInteger(Number(v)) ? fm(v) : f5(v); }
  function datoPar(v) { return Number(v) < 0 ? "(" + dato(v) + ")" : dato(v); }
  function resta(a, b) { return "(" + fm(a) + "-" + par(b) + ")"; }
  function sumaFirmada(valores) {
    return valores.map(function (v, i) {
      var s = f5(Math.abs(v));
      var neg = Number(v) < 0 && f5(v) !== "0.00000";
      if (i === 0) return (neg ? "-" : "") + s;
      return (neg ? " - " : " + ") + s;
    }).join("");
  }
  function factorX(xm) {
    xm = Number(xm);
    if (xm === 0) return "x";
    return xm < 0 ? "(x+" + fm(-xm) + ")" : "(x-" + fm(xm) + ")";
  }
  function escapar(t) {
    return String(t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function luminancia(rgb) { return (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255; }
  function chip(hex, texto) {
    return '<span class="chip-color"><i style="background:' + hex + '"></i>' + escapar(texto || hex) + "</span>";
  }
  function bloque(titulo, contenido) {
    return '<div class="bloque-formula">' + (titulo ? "<h5>" + titulo + "</h5>" : "") + contenido + "</div>";
  }
  function eq(tex) { return "\\[" + tex + "\\]"; }

  // ---------------------------------------------------------------- MathJax
  function tipografiar(el, intentos) {
    var mj = window.MathJax;
    if (mj && typeof mj.typesetPromise === "function" && mj.startup && mj.startup.promise) {
      mj.startup.promise = mj.startup.promise
        .then(function () { return mj.typesetPromise([el]); })
        .catch(function (e) { console.error("MathJax:", e); });
    } else if ((intentos || 0) < 40) {
      setTimeout(function () { tipografiar(el, (intentos || 0) + 1); }, 250);
    }
  }
  function limpiarMath(el) {
    var mj = window.MathJax;
    if (mj && typeof mj.typesetClear === "function") mj.typesetClear([el]);
  }

  // ---------------------------------------------------------------- mural
  function textoBoton(estado) {
    return { vacio: "▶ Reproducir", reproduciendo: "⏸ Pausar", pausado: "▶ Continuar", terminado: "↻ Repetir" }[estado] || "▶ Reproducir";
  }
  var mural = new window.MuralAnimado($("canvas-mural"), {
    barra: $("barra-mural"), info: $("info-mural"),
    alCambiarEstado: function (estado) { $("btn-mural-play").textContent = textoBoton(estado); }
  });
  var muralDiapo = $("canvas-diapositiva") ? new window.MuralAnimado($("canvas-diapositiva"), {
    barra: $("barra-diapositiva"), info: $("info-diapositiva"),
    alCambiarEstado: function (estado) { $("btn-diapo-play").textContent = textoBoton(estado); }
  }) : null;

  $("btn-mural-play").addEventListener("click", function () { mural.alternar(); });
  $("btn-mural-reiniciar").addEventListener("click", function () { mural.reiniciar(); });
  document.querySelectorAll("#grupo-velocidad [data-velocidad]").forEach(function (b) {
    b.addEventListener("click", function () {
      mural.setVelocidad(parseFloat(b.dataset.velocidad));
      document.querySelectorAll("#grupo-velocidad [data-velocidad]").forEach(function (o) {
        o.classList.toggle("active", o === b);
      });
    });
  });
  if (muralDiapo) {
    $("btn-diapo-play").addEventListener("click", function () { muralDiapo.alternar(); });
    $("btn-diapo-reiniciar").addEventListener("click", function () { muralDiapo.reiniciar(); });
    document.addEventListener("presentacion:cambio", function (e) {
      if (e.detail.indice === 7) { muralDiapo.reiniciar(); muralDiapo.reproducir(); }
      else muralDiapo.pausar();
    });
  }

  // ---------------------------------------------------------------- formulario
  var bloquesPunto = Array.prototype.slice.call(document.querySelectorAll(".punto-control"));

  function actualizarMuestraPunto(bloquePunto) {
    var hex = bloquePunto.querySelector(".campo-hex").value.trim();
    var etiqueta = bloquePunto.querySelector(".rgb-punto");
    if (PATRON_HEX.test(hex)) {
      var h = hex.replace("#", "");
      var r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16);
      bloquePunto.style.setProperty("--color-punto", "#" + h);
      etiqueta.textContent = "RGB(" + r + ", " + g + ", " + b + ")";
    } else {
      etiqueta.textContent = "hex inválido";
    }
  }

  bloquesPunto.forEach(function (bp) {
    var selector = bp.querySelector(".campo-selector");
    var texto = bp.querySelector(".campo-hex");
    selector.addEventListener("input", function () {
      texto.value = selector.value.toUpperCase();
      texto.classList.remove("is-invalid");
      actualizarMuestraPunto(bp);
    });
    texto.addEventListener("input", function () {
      var v = texto.value.trim();
      if (PATRON_HEX.test(v)) {
        selector.value = ("#" + v.replace("#", "")).toLowerCase();
        texto.classList.remove("is-invalid");
      }
      actualizarMuestraPunto(bp);
    });
    actualizarMuestraPunto(bp);
  });

  function leerFormulario() {
    return {
      puntos: bloquesPunto.map(function (bp) {
        return {
          x: bp.querySelector(".campo-x").value,
          color: bp.querySelector(".campo-hex").value.trim(),
          nombre: bp.querySelector(".campo-nombre").value.trim()
        };
      }),
      x_objetivo: $("x-objetivo").value,
      metodo: $("metodo").value,
      muestras: parseInt($("muestras").value, 10)
    };
  }

  function marcarVacios() {
    form.querySelectorAll(".campo-x, .campo-hex, #x-objetivo").forEach(function (el) {
      el.classList.toggle("is-invalid", el.value.trim() === "");
    });
  }

  function mostrarErrores(errores) {
    var caja = $("errores");
    if (!errores || !errores.length) { caja.classList.add("oculto"); caja.innerHTML = ""; return; }
    caja.innerHTML = "<strong>No se pudo calcular el color:</strong><ul>" +
      errores.map(function (e) { return "<li>" + escapar(e) + "</li>"; }).join("") + "</ul>";
    caja.classList.remove("oculto");
  }

  function calcular() {
    var id = ++idSolicitud;
    marcarVacios();
    $("panel-resultado").classList.add("cargando");
    return fetch("/api/interpolar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(leerFormulario())
    })
      .then(function (resp) {
        return resp.json().catch(function () { return { correcto: false, errores: ["Respuesta inválida del servidor (" + resp.status + ")."] }; });
      })
      .then(function (datos) {
        if (id !== idSolicitud) return null;               // respuesta obsoleta
        if (!datos.correcto) {
          mostrarErrores(datos.errores || [datos.mensaje || "Error desconocido."]);
          return null;
        }
        mostrarErrores(null);
        ultimo = datos;
        pestanaActiva = datos.clave_metodo;
        renderizarTodo(datos);
        return datos;
      })
      .catch(function (err) {
        if (id === idSolicitud) mostrarErrores(["No hay conexión con el servidor: " + err.message]);
        return null;
      })
      .finally(function () {
        if (id === idSolicitud) $("panel-resultado").classList.remove("cargando");
      });
  }

  form.addEventListener("submit", function (e) { e.preventDefault(); calcular(); });
  $("metodo").addEventListener("change", function () { calcular(); });
  $("muestras").addEventListener("change", function () { calcular(); });

  $("btn-animar").addEventListener("click", function () {
    calcular().then(function (datos) {
      if (!datos) return;
      $("mural").scrollIntoView({ behavior: "smooth", block: "start" });
      mural.reiniciar();
      mural.reproducir();
    });
  });

  $("btn-reiniciar").addEventListener("click", function () {
    entradaInicial.puntos.forEach(function (p, i) {
      var bp = bloquesPunto[i];
      bp.querySelector(".campo-x").value = p.x;
      bp.querySelector(".campo-hex").value = p.color;
      bp.querySelector(".campo-selector").value = p.color.toLowerCase();
      bp.querySelector(".campo-nombre").value = p.nombre;
      actualizarMuestraPunto(bp);
    });
    $("x-objetivo").value = entradaInicial.x_objetivo;
    $("metodo").value = entradaInicial.metodo;
    $("muestras").value = String(entradaInicial.muestras);
    form.querySelectorAll(".is-invalid").forEach(function (el) { el.classList.remove("is-invalid"); });
    mostrarErrores(null);
    calcular();
  });

  // ---------------------------------------------------------------- resultados
  function renderizarResultado(d) {
    var tarjeta = $("tarjeta-color");
    tarjeta.style.backgroundColor = d.hexadecimal;
    $("hex-grande").textContent = d.hexadecimal;
    $("hex-grande").style.color = luminancia(d.resultado_rgb) > 0.62 ? "#111" : "#fff";
    $("chip-metodo").textContent = d.metodo;
    $("chip-posicion").textContent = "x = " + fm(d.x_objetivo) + " m";
    var dec = d.resultado_decimal, rgb = d.resultado_rgb;
    $("res-decimal").textContent = "(" + f5(dec.r) + ", " + f5(dec.g) + ", " + f5(dec.b) + ")";
    $("res-rgb").textContent = "(" + rgb.r + ", " + rgb.g + ", " + rgb.b + ")";
    $("res-hex").textContent = d.hexadecimal;
    $("res-r").textContent = f5(dec.r);
    $("res-g").textContent = f5(dec.g);
    $("res-b").textContent = f5(dec.b);
    var msj = $("mensaje-estado");
    msj.textContent = d.mensaje;
    msj.classList.toggle("advertencia", d.canales_limitados && d.canales_limitados.length > 0);
    $("tiempo-ms").textContent = Number(d.tiempo_ms).toFixed(3);
  }

  // --- Lagrange
  function procLagrange(p) {
    var x = p.x, n = p.nodos.length, html = "";
    html += bloque("Fórmula general",
      eq("P(x)=\\sum_{i=0}^{" + (n - 1) + "} y_i L_i(x),\\qquad L_i(x)=\\prod_{\\substack{j=0\\\\ j\\neq i}}^{" + (n - 1) + "}\\frac{x-x_j}{x_i-x_j}"));
    var bases = p.bases.map(function (b) {
      var simb = b.factores.map(function (f) { return "(x-x_" + f.j + ")"; }).join("");
      var simbDen = b.factores.map(function (f) { return "(x_" + b.i + "-x_" + f.j + ")"; }).join("");
      var num = b.factores.map(function (f) { return resta(x, f.xj); }).join("");
      var den = b.factores.map(function (f) { return resta(b.xi, f.xj); }).join("");
      return eq("L_" + b.i + "(" + fm(x) + ")=\\frac{" + simb + "}{" + simbDen + "}=\\frac{" + num + "}{" + den +
        "}=\\frac{" + f5(b.numerador) + "}{" + f5(b.denominador) + "}=" + f5(b.valor));
    }).join("");
    var suma = p.bases.map(function (b) { return "L_" + b.i; }).join("+");
    html += bloque("Polinomios base en x = " + fm(x), bases +
      eq(suma + "=" + f5(p.suma_bases) + (Math.abs(p.suma_bases - 1) < 1e-9 ? "\\quad\\checkmark" : "")));
    CANALES.forEach(function (c) {
      var datos = p.canales[c], L = LETRA[c];
      var sust = datos.terminos.map(function (t, i) {
        return (i ? "+" : "") + dato(t.y) + "\\left(" + f5(t.L) + "\\right)";
      }).join("");
      var prods = sumaFirmada(datos.terminos.map(function (t) { return t.producto; }));
      html += tarjetaCanal(c,
        eq(L + "(" + fm(x) + ")=" + datos.terminos.map(function (t) { return "y_" + t.i + "L_" + t.i; }).join("+")) +
        eq(L + "(" + fm(x) + ")=" + sust) +
        eq(L + "(" + fm(x) + ")=" + prods + "=" + f5(datos.resultado)), datos.resultado);
    });
    return html;
  }

  // --- Newton
  function tablaNewton(datos, nodos) {
    var n = nodos.length, filas = "";
    for (var i = 0; i < n; i++) {
      filas += "<tr><td>" + i + '</td><td class="num">' + fm(nodos[i]) + "</td>";
      for (var k = 0; k < n; k++) {
        filas += i < datos.columnas[k].length
          ? '<td class="num' + (i === 0 ? " resaltada" : "") + '">' + f5(datos.columnas[k][i]) + "</td>"
          : '<td class="vacia">—</td>';
      }
      filas += "</tr>";
    }
    var cab = '<th class="num">f[x<sub>i</sub>]</th>';
    for (var o = 1; o < n; o++) {
      var arg = [];
      for (var m = 0; m <= o; m++) arg.push("x<sub>i" + (m ? "+" + m : "") + "</sub>");
      cab += '<th class="num">f[' + arg.join(", ") + "]</th>";
    }
    return '<div class="table-responsive"><table class="table table-sm tabla-numeriarte align-middle"><thead><tr><th>i</th>' +
      '<th class="num">x<sub>i</sub></th>' + cab + "</tr></thead><tbody>" + filas + "</tbody></table></div>" +
      '<p class="small text-tenue mt-1">Fila resaltada: coeficientes del polinomio de Newton.</p>';
  }

  function procNewton(p) {
    var x = p.x, html = "";
    html += bloque("Fórmula general",
      eq("P(x)=f[x_0]+f[x_0,x_1](x-x_0)+f[x_0,x_1,x_2](x-x_0)(x-x_1)") +
      eq("f[x_i,\\ldots,x_j]=\\frac{f[x_{i+1},\\ldots,x_j]-f[x_i,\\ldots,x_{j-1}]}{x_j-x_i}"));
    CANALES.forEach(function (c) {
      var d = p.canales[c], L = LETRA[c], cuerpo = "";
      cuerpo += eq(d.valores_y.map(function (y, i) { return L + "_" + i + "=" + dato(y); }).join(",\\quad "));
      for (var orden = 1; orden < d.detalles.length; orden++) {
        cuerpo += d.detalles[orden].map(function (e) {
          var args = [];
          for (var m = e.i; m <= e.j; m++) args.push("x_" + m);
          return eq(L + "[" + args.join(",") + "]=\\frac{" + dato(e.superior) + "-" + datoPar(e.inferior) + "}{" +
            fm(e.x_superior) + "-" + par(e.x_inferior) + "}=" + f5(e.valor));
        }).join("");
      }
      cuerpo += tablaNewton(d, p.nodos);
      // Polinomio
      var poli = "", producto = "";
      d.coeficientes.forEach(function (a, k) {
        if (k > 0) producto += factorX(p.nodos[k - 1]);
        var neg = a < 0 && f5(a) !== "0.00000";
        var mag = k === 0 ? dato(Math.abs(a)) : f5(Math.abs(a));
        poli += (k === 0 ? (neg ? "-" : "") : (neg ? "-" : "+")) + mag + producto;
      });
      cuerpo += eq(L + "(x)=" + poli);
      // Evaluación
      var sust = d.terminos.map(function (t, k) {
        if (k === 0) return dato(t.coeficiente);
        return "+\\left(" + f5(t.coeficiente) + "\\right)\\left(" + f5(t.producto_nodos) + "\\right)";
      }).join("");
      cuerpo += eq(L + "(" + fm(x) + ")=" + sust) +
        eq(L + "(" + fm(x) + ")=" + sumaFirmada(d.terminos.map(function (t) { return t.termino; })) + "=" + f5(d.resultado));
      html += tarjetaCanal(c, cuerpo, d.resultado);
    });
    return html;
  }

  // --- Neville
  function tablaNeville(d, nodos) {
    var n = nodos.length, filas = "", cab = "";
    for (var k = 0; k < n; k++) cab += '<th class="num">Nivel ' + k + ": P<sub>i,i+" + k + "</sub></th>";
    for (var i = 0; i < n; i++) {
      filas += "<tr><td>" + i + '</td><td class="num">' + fm(nodos[i]) + "</td>";
      for (var j = 0; j < n; j++) {
        filas += i < d.niveles[j].length
          ? '<td class="num' + (j === n - 1 ? " resaltada" : "") + '">' + f5(d.niveles[j][i].valor) + "</td>"
          : '<td class="vacia">—</td>';
      }
      filas += "</tr>";
    }
    return '<div class="table-responsive"><table class="table table-sm tabla-numeriarte align-middle"><thead><tr><th>i</th>' +
      '<th class="num">x<sub>i</sub></th>' + cab + "</tr></thead><tbody>" + filas + "</tbody></table></div>";
  }

  function procNeville(p) {
    var x = p.x, html = "";
    html += bloque("Fórmula general",
      eq("P_{i,j}(x)=\\frac{(x-x_i)\\,P_{i+1,j}(x)-(x-x_j)\\,P_{i,j-1}(x)}{x_j-x_i}"));
    CANALES.forEach(function (c) {
      var d = p.canales[c], cuerpo = "";
      cuerpo += "<p class=\"small text-suave mb-1\">Valores iniciales (nivel 0):</p>" +
        eq(d.niveles[0].map(function (e) { return "P_{" + e.i + "," + e.i + "}=" + dato(e.valor); }).join(",\\quad "));
      for (var k = 1; k < d.niveles.length; k++) {
        cuerpo += '<p class="small text-suave mb-1">Nivel ' + k + ":</p>";
        cuerpo += d.niveles[k].map(function (e) {
          return eq("P_{" + e.i + "," + e.j + "}=\\frac{" + resta(x, e.xi) + "\\left(" + dato(e.p_superior) + "\\right)-" +
            resta(x, e.xj) + "\\left(" + dato(e.p_inferior) + "\\right)}{" + fm(e.xj) + "-" + par(e.xi) + "}=" + f5(e.valor));
        }).join("");
      }
      cuerpo += tablaNeville(d, p.nodos);
      var ult = d.niveles.length - 1;
      cuerpo += eq(LETRA[c] + "(" + fm(x) + ")=P_{0," + ult + "}=" + f5(d.resultado));
      html += tarjetaCanal(c, cuerpo, d.resultado);
    });
    return html;
  }

  function tarjetaCanal(c, cuerpo, resultado) {
    return '<div class="tarjeta-canal ' + c + '"><div class="cabecera"><span><span class="punto-canal ' + c + '"></span>' +
      NOMBRE_CANAL[c] + " " + LETRA[c] + "(x)</span><span class=\"mono\">" + f5(resultado) + "</span></div>" +
      '<div class="cuerpo">' + cuerpo + "</div></div>";
  }

  function renderizarProcedimiento(d) {
    var cont = $("contenedor-procedimiento");
    var p = d.procedimientos[pestanaActiva];
    var html = { lagrange: procLagrange, newton: procNewton, neville: procNeville }[pestanaActiva](p);
    var dec = d.comparacion.metodos.filter(function (m) { return m.clave === pestanaActiva; })[0];
    html += bloque("Conversión a color",
      eq("(" + f5(dec.decimal.r) + ",\\ " + f5(dec.decimal.g) + ",\\ " + f5(dec.decimal.b) + ")" +
        "\\xrightarrow{\\text{redondeo y } [0,255]}\\boxed{RGB=(" + dec.rgb.r + "," + dec.rgb.g + "," + dec.rgb.b + ")}" +
        "\\longrightarrow\\boxed{\\texttt{\\" + dec.hexadecimal + "}}"));
    limpiarMath(cont);
    cont.innerHTML = html;
    tipografiar(cont);
    document.querySelectorAll("#pestanas-metodo [data-metodo]").forEach(function (b) {
      b.classList.toggle("active", b.dataset.metodo === pestanaActiva);
      b.innerHTML = escapar(b.textContent.replace(/\s*seleccionado$/, "")) +
        (b.dataset.metodo === d.clave_metodo ? ' <span class="badge text-bg-primary">seleccionado</span>' : "");
    });
  }

  document.querySelectorAll("#pestanas-metodo [data-metodo]").forEach(function (b) {
    b.addEventListener("click", function () {
      pestanaActiva = b.dataset.metodo;
      renderizarProcedimiento(ultimo);
    });
  });

  // --- Comparación
  function renderizarComparacion(d) {
    var filas = d.comparacion.metodos.map(function (m) {
      var dif = f5(m.diferencia_maxima);
      if (m.diferencia_maxima > 0) dif += ' <span class="text-tenue small">(' + m.diferencia_maxima.toExponential(2) + ")</span>";
      return "<tr" + (m.clave === d.clave_metodo ? ' class="table-active"' : "") + '><td class="fw-semibold">' + m.metodo + "</td>" +
        '<td class="num">' + f5(m.decimal.r) + '</td><td class="num">' + f5(m.decimal.g) + '</td><td class="num">' + f5(m.decimal.b) + "</td>" +
        "<td>" + chip(m.hexadecimal) + '</td><td class="num">' + dif + "</td></tr>";
    }).join("");
    $("tabla-comparacion").innerHTML =
      '<div class="table-responsive"><table class="table table-sm tabla-numeriarte align-middle"><thead><tr>' +
      '<th>Método</th><th class="num">R</th><th class="num">G</th><th class="num">B</th><th>Hexadecimal</th>' +
      '<th class="num">Diferencia máxima</th></tr></thead><tbody>' + filas + "</tbody></table></div>" +
      '<p class="small text-tenue mt-2 mb-0">Diferencia máxima respecto de Lagrange en cualquier canal. ' +
      (d.comparacion.coinciden ? "Los tres métodos coinciden (diferencia < 10<sup>−9</sup>)." : "Atención: los métodos no coinciden.") + "</p>";
    $("explicacion-comparacion").textContent = d.comparacion.explicacion;
  }

  // --- Gráfica
  function renderizarGrafica(d) {
    var lienzo = $("grafica-canales");
    if (typeof window.Chart === "undefined") {
      lienzo.parentElement.innerHTML = '<p class="small text-tenue">La gráfica requiere conexión para cargar Chart.js.</p>';
      return;
    }
    function serie(c) { return d.muestras_mural.map(function (m) { return { x: m.x, y: m.decimal[c] }; }); }
    var xs = [d.mural.x_min, d.mural.x_max];
    var limites = function (y) { return xs.map(function (x) { return { x: x, y: y }; }); };
    var conjuntos = [
      { label: "R(x)", data: serie("r"), borderColor: "#ff4d6d", pointRadius: 0, borderWidth: 2 },
      { label: "G(x)", data: serie("g"), borderColor: "#2ecc71", pointRadius: 0, borderWidth: 2 },
      { label: "B(x)", data: serie("b"), borderColor: "#3b9dff", pointRadius: 0, borderWidth: 2 },
      { label: "Límites 0 y 255", data: limites(0), borderColor: "rgba(255,181,71,.8)", borderDash: [5, 5], pointRadius: 0, borderWidth: 1 },
      { label: "_255", data: limites(255), borderColor: "rgba(255,181,71,.8)", borderDash: [5, 5], pointRadius: 0, borderWidth: 1 }
    ];
    var opciones = {
      responsive: true, maintainAspectRatio: false, animation: false, parsing: true,
      interaction: { mode: "nearest", intersect: false, axis: "x" },
      scales: {
        x: { type: "linear", min: d.mural.x_min, max: d.mural.x_max, title: { display: true, text: "x (m)", color: "#a8b2cf" },
             ticks: { color: "#a8b2cf" }, grid: { color: "rgba(255,255,255,.06)" } },
        y: { title: { display: true, text: "Intensidad", color: "#a8b2cf" }, ticks: { color: "#a8b2cf" }, grid: { color: "rgba(255,255,255,.06)" } }
      },
      plugins: {
        legend: { labels: { color: "#e9edf8", filter: function (it) { return it.text.charAt(0) !== "_"; } } },
        tooltip: { callbacks: { label: function (ctx) { return ctx.dataset.label + ": " + f5(ctx.parsed.y); },
                                title: function (items) { return "x = " + Number(items[0].parsed.x).toFixed(3) + " m"; } },
                   filter: function (it) { return it.datasetIndex < 3; } }
      }
    };
    if (grafica) { grafica.data.datasets = conjuntos; grafica.options = opciones; grafica.update(); }
    else grafica = new window.Chart(lienzo, { type: "line", data: { datasets: conjuntos }, options: opciones });
  }

  function renderizarMural(d) {
    mural.cargar(d);
    if (muralDiapo) muralDiapo.cargar(d);
    $("txt-muestras").textContent = d.mural.total_muestras;
    var nota = $("nota-limitacion");
    nota.textContent = d.mural.muestras_limitadas > 0
      ? d.mural.muestras_limitadas + " de " + d.mural.total_muestras + " muestras tenían algún canal fuera de [0, 255] " +
        "y se limitaron (clamp). Es una limitación del polinomio, no un error: revisa la gráfica de curvas."
      : "Ninguna muestra salió del intervalo [0, 255].";
  }

  function renderizarTodo(d) {
    renderizarResultado(d);
    renderizarProcedimiento(d);
    renderizarComparacion(d);
    renderizarGrafica(d);
    renderizarMural(d);
  }

  renderizarTodo(ultimo);
})();
