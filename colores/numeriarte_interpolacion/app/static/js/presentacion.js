/* =========================================================================
   Presentación integrada: navegación, puntos, teclado, pantalla completa,
   nombre del expositor y gesto de deslizar en móvil.
   ========================================================================= */
(function () {
  "use strict";

  var contenedor = document.getElementById("contenedor-presentacion");
  if (!contenedor) return;

  var diapositivas = Array.prototype.slice.call(contenedor.querySelectorAll(".diapositiva"));
  var btnAnterior = document.getElementById("btn-anterior");
  var btnSiguiente = document.getElementById("btn-siguiente");
  var btnPantalla = document.getElementById("btn-pantalla");
  var contador = document.getElementById("contador-diapositivas");
  var puntos = document.getElementById("puntos-diapositivas");
  var campoExpositor = document.getElementById("campo-expositor");
  var seccion = document.getElementById("presentacion");
  var actual = 0;
  var visible = false;
  var CLAVE_EXPOSITOR = "numeriarte.expositor";

  // ---- Puntos de navegación ----
  diapositivas.forEach(function (_d, i) {
    var b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "tab");
    b.setAttribute("aria-label", "Ir a la diapositiva " + (i + 1));
    b.addEventListener("click", function () { ir(i); });
    puntos.appendChild(b);
  });

  function ir(indice) {
    if (indice < 0 || indice >= diapositivas.length || indice === actual && diapositivas[actual].classList.contains("activa")) return;
    var atras = indice < actual;
    diapositivas[actual].classList.remove("activa", "atras");
    actual = indice;
    var d = diapositivas[actual];
    d.classList.toggle("atras", atras);
    d.classList.add("activa");
    d.scrollTop = 0;
    actualizarControles();
    document.dispatchEvent(new CustomEvent("presentacion:cambio", { detail: { indice: actual, total: diapositivas.length } }));
  }

  function actualizarControles() {
    contador.textContent = (actual + 1) + " / " + diapositivas.length;
    btnAnterior.disabled = actual === 0;
    btnSiguiente.disabled = actual === diapositivas.length - 1;
    Array.prototype.forEach.call(puntos.children, function (p, i) {
      p.classList.toggle("activo", i === actual);
      p.setAttribute("aria-selected", i === actual ? "true" : "false");
    });
  }

  btnAnterior.addEventListener("click", function () { ir(actual - 1); });
  btnSiguiente.addEventListener("click", function () { ir(actual + 1); });

  // ---- Pantalla completa ----
  function enPantallaCompleta() {
    return document.fullscreenElement === contenedor || document.webkitFullscreenElement === contenedor;
  }
  function alternarPantallaCompleta() {
    if (enPantallaCompleta()) {
      (document.exitFullscreen || document.webkitExitFullscreen).call(document);
    } else {
      var pedir = contenedor.requestFullscreen || contenedor.webkitRequestFullscreen;
      if (pedir) {
        var r = pedir.call(contenedor);
        if (r && r.catch) r.catch(function () {});
      }
    }
  }
  btnPantalla.addEventListener("click", alternarPantallaCompleta);
  ["fullscreenchange", "webkitfullscreenchange"].forEach(function (ev) {
    document.addEventListener(ev, function () {
      btnPantalla.textContent = enPantallaCompleta() ? "✕" : "⛶";
      btnPantalla.setAttribute("aria-label", enPantallaCompleta() ? "Salir de pantalla completa" : "Pantalla completa");
      if (enPantallaCompleta()) contenedor.focus({ preventScroll: true });
    });
  });

  // ---- Teclado: solo si la presentación está visible o en pantalla completa ----
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entradas) {
      visible = entradas[0].isIntersecting;
      var enlace = document.querySelector('.menu-enlace[data-menu="presentacion"]');
      var principal = document.querySelector('.menu-enlace[data-menu="interpolacion"]');
      if (enlace && principal) {
        enlace.classList.toggle("activo", visible);
        principal.classList.toggle("activo", !visible);
      }
    }, { threshold: 0.35 }).observe(contenedor);
  } else {
    visible = true;
  }

  document.addEventListener("keydown", function (e) {
    var t = e.target;
    var escribiendo = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable);
    if (escribiendo || e.altKey || e.ctrlKey || e.metaKey) return;
    if (!visible && !enPantallaCompleta()) return;
    switch (e.key) {
      case "ArrowRight": case "PageDown": ir(actual + 1); e.preventDefault(); break;
      case "ArrowLeft": case "PageUp": ir(actual - 1); e.preventDefault(); break;
      case "Home": ir(0); e.preventDefault(); break;
      case "End": ir(diapositivas.length - 1); e.preventDefault(); break;
      case "f": case "F": alternarPantallaCompleta(); e.preventDefault(); break;
    }
  });

  // ---- Deslizar en pantallas táctiles ----
  var toqueX = null, toqueY = null;
  contenedor.addEventListener("touchstart", function (e) {
    toqueX = e.touches[0].clientX; toqueY = e.touches[0].clientY;
  }, { passive: true });
  contenedor.addEventListener("touchend", function (e) {
    if (toqueX === null) return;
    var dx = e.changedTouches[0].clientX - toqueX, dy = e.changedTouches[0].clientY - toqueY;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) ir(actual + (dx < 0 ? 1 : -1));
    toqueX = toqueY = null;
  }, { passive: true });

  // ---- Nombre del expositor ----
  function mostrarExpositor() {
    var nombre = campoExpositor.value.trim();
    document.querySelectorAll(".nombre-expositor-texto").forEach(function (el) {
      el.textContent = nombre ? "Expositor(a): " + nombre : "";
    });
  }
  try { campoExpositor.value = window.localStorage.getItem(CLAVE_EXPOSITOR) || ""; } catch (err) { /* sin almacenamiento */ }
  campoExpositor.addEventListener("input", function () {
    mostrarExpositor();
    try { window.localStorage.setItem(CLAVE_EXPOSITOR, campoExpositor.value); } catch (err) { /* ignorar */ }
  });
  mostrarExpositor();

  actualizarControles();
  window.Presentacion = { ir: ir, actual: function () { return actual; }, total: diapositivas.length };
  if (seccion && window.location.hash === "#presentacion") contenedor.focus({ preventScroll: true });
})();
