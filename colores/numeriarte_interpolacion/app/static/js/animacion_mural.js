/* =========================================================================
   MuralAnimado — representa en Canvas los colores YA calculados por el
   backend. Aquí no se interpola nada: solo se pintan franjas verticales.
   ========================================================================= */
(function (global) {
  "use strict";

  var ANCHO = 900, ALTO = 350;
  var MARGEN_X = 40, BANDA_Y = 78, BANDA_ALTO = 180, EJE_Y = BANDA_Y + BANDA_ALTO + 14;
  var DURACION_LLENADO_MS = 4300;   // + 3 pausas en controles + pausa en objetivo ≈ 5 s a 1×
  var PAUSA_CONTROL_MS = 200;
  var PAUSA_OBJETIVO_MS = 300;

  function formatoM(v) { return String(Math.round(v * 1000) / 1000); }
  function luminancia(rgb) { return (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255; }

  function MuralAnimado(canvas, opciones) {
    opciones = opciones || {};
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.barra = opciones.barra || null;
    this.info = opciones.info || null;
    this.alCambiarEstado = opciones.alCambiarEstado || function () {};
    this.velocidad = 1;
    this.datos = null;
    this.progreso = 0;           // número de franjas pintadas (decimal)
    this.estado = "vacio";       // vacio | reproduciendo | pausado | terminado
    this.pausaRestante = 0;
    this.visitados = {};
    this.objetivoAlcanzado = false;
    this.destello = 0;
    this._raf = null;
    this._ultimo = null;
    this._tick = this._tick.bind(this);
    this._ajustarResolucion();
    var self = this;
    global.addEventListener("resize", function () { self._ajustarResolucion(); self.dibujar(); });
    this.dibujar();
  }

  MuralAnimado.prototype._ajustarResolucion = function () {
    var dpr = Math.min(global.devicePixelRatio || 1, 2);
    if (this.canvas.width !== ANCHO * dpr) {
      this.canvas.width = ANCHO * dpr;
      this.canvas.height = ALTO * dpr;
    }
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };

  /** Recibe {mural: {...}, muestras_mural: [...]} tal como responde la API. */
  MuralAnimado.prototype.cargar = function (respuesta) {
    var meta = respuesta.mural || {};
    this.datos = {
      xMin: meta.x_min, xMax: meta.x_max,
      controles: meta.controles || [],
      objetivo: meta.objetivo || null,
      muestras: respuesta.muestras_mural || [],
      metodo: meta.metodo || respuesta.metodo
    };
    this.reiniciar();
  };

  MuralAnimado.prototype._px = function (x) {
    var d = this.datos;
    var t = d.xMax === d.xMin ? 0 : (x - d.xMin) / (d.xMax - d.xMin);
    return MARGEN_X + t * (ANCHO - 2 * MARGEN_X);
  };

  MuralAnimado.prototype.reproducir = function () {
    if (!this.datos || !this.datos.muestras.length) return;
    if (this.estado === "terminado") this.reiniciar();
    if (this.estado === "reproduciendo") return;
    this.estado = "reproduciendo";
    this._ultimo = null;
    this._raf = global.requestAnimationFrame(this._tick);
    this.alCambiarEstado(this.estado);
  };

  MuralAnimado.prototype.pausar = function () {
    if (this.estado !== "reproduciendo") return;
    this.estado = "pausado";
    if (this._raf) global.cancelAnimationFrame(this._raf);
    this._raf = null;
    this.alCambiarEstado(this.estado);
  };

  MuralAnimado.prototype.alternar = function () {
    if (this.estado === "reproduciendo") this.pausar(); else this.reproducir();
  };

  MuralAnimado.prototype.reiniciar = function () {
    if (this._raf) global.cancelAnimationFrame(this._raf);
    this._raf = null;
    this.progreso = 0;
    this.pausaRestante = 0;
    this.visitados = {};
    this.objetivoAlcanzado = false;
    this.destello = 0;
    this.estado = "vacio";
    this.dibujar();
    this._actualizarInfo();
    this.alCambiarEstado(this.estado);
  };

  MuralAnimado.prototype.setVelocidad = function (v) {
    this.velocidad = v > 0 ? v : 1;
  };

  /** Índices donde la animación se detiene brevemente. */
  MuralAnimado.prototype._paradas = function () {
    var paradas = this.datos.controles.map(function (c) {
      return { clave: "c" + c.indice, indice: c.indice, pausa: PAUSA_CONTROL_MS, objetivo: false };
    });
    if (this.datos.objetivo) {
      paradas.push({ clave: "obj", indice: this.datos.objetivo.indice, pausa: PAUSA_OBJETIVO_MS, objetivo: true });
    }
    return paradas.sort(function (a, b) { return a.indice - b.indice; });
  };

  MuralAnimado.prototype._tick = function (ts) {
    if (this.estado !== "reproduciendo") return;
    var dt = this._ultimo === null ? 0 : Math.min(ts - this._ultimo, 64);
    this._ultimo = ts;
    dt *= this.velocidad;
    var n = this.datos.muestras.length;
    if (this.destello > 0) this.destello = Math.max(0, this.destello - dt);

    if (this.pausaRestante > 0) {
      this.pausaRestante -= dt;
    } else {
      var siguiente = this.progreso + dt * n / DURACION_LLENADO_MS;
      var paradas = this._paradas();
      for (var i = 0; i < paradas.length; i++) {
        var p = paradas[i];
        if (!this.visitados[p.clave] && siguiente >= p.indice + 1) {
          this.visitados[p.clave] = true;
          siguiente = p.indice + 1;               // se detiene justo en la franja
          this.pausaRestante = p.pausa;
          this.destello = 600;
          if (p.objetivo) this.objetivoAlcanzado = true;
          break;
        }
      }
      this.progreso = Math.min(n, siguiente);
    }

    this.dibujar();
    this._actualizarInfo();
    if (this.progreso >= n && this.pausaRestante <= 0) {
      this.estado = "terminado";
      this._raf = null;
      this.alCambiarEstado(this.estado);
      return;
    }
    this._raf = global.requestAnimationFrame(this._tick);
  };

  MuralAnimado.prototype._actualizarInfo = function () {
    var n = this.datos ? this.datos.muestras.length : 0;
    var pintadas = Math.floor(this.progreso);
    var pct = n ? (this.progreso / n) * 100 : 0;
    if (this.barra) {
      this.barra.style.width = pct.toFixed(1) + "%";
      if (this.barra.parentElement) this.barra.parentElement.setAttribute("aria-valuenow", pct.toFixed(0));
    }
    if (!this.info) return;
    if (!n || pintadas === 0) {
      this.info.textContent = n ? "Mural vacío · " + n + " franjas listas para pintar." : "Sin datos.";
      return;
    }
    var m = this.datos.muestras[pintadas - 1];
    var html =
      '<span class="muestra" style="background:' + m.hex + '"></span>' +
      "<span>Franja " + pintadas + "/" + n + "</span>" +
      "<span>x = " + Number(m.x).toFixed(3) + " m</span>" +
      "<span>RGB(" + m.rgb.r + ", " + m.rgb.g + ", " + m.rgb.b + ")</span>" +
      "<span>" + m.hex + "</span>";
    if (m.limitado) html += '<span class="text-warning">canal limitado a [0, 255]</span>';
    if (this.objetivoAlcanzado && this.datos.objetivo && pintadas - 1 === this.datos.objetivo.indice) {
      html += '<span class="text-info">★ posición objetivo</span>';
    }
    this.info.innerHTML = html;
  };

  MuralAnimado.prototype.dibujar = function () {
    var ctx = this.ctx;
    ctx.clearRect(0, 0, ANCHO, ALTO);
    ctx.fillStyle = "#070a13";
    ctx.fillRect(0, 0, ANCHO, ALTO);

    var bandaX = MARGEN_X, bandaAncho = ANCHO - 2 * MARGEN_X;
    // Lienzo vacío: patrón tenue
    ctx.fillStyle = "#121829";
    ctx.fillRect(bandaX, BANDA_Y, bandaAncho, BANDA_ALTO);
    ctx.save();
    ctx.beginPath(); ctx.rect(bandaX, BANDA_Y, bandaAncho, BANDA_ALTO); ctx.clip();
    ctx.strokeStyle = "rgba(255,255,255,0.04)";
    ctx.lineWidth = 1;
    for (var gx = bandaX - 40; gx < bandaX + bandaAncho; gx += 18) {
      ctx.beginPath(); ctx.moveTo(gx, BANDA_Y); ctx.lineTo(gx + 40, BANDA_Y + BANDA_ALTO); ctx.stroke();
    }
    ctx.restore();
    if (!this.datos || !this.datos.muestras.length) return;

    var d = this.datos, n = d.muestras.length;
    var anchoFranja = bandaAncho / (n - 1);
    var pintadas = Math.floor(this.progreso);

    // Franjas pintadas (centradas en cada posición de muestra)
    for (var k = 0; k < pintadas; k++) {
      var cx = this._px(d.muestras[k].x);
      var x0 = Math.max(bandaX, cx - anchoFranja / 2);
      var x1 = Math.min(bandaX + bandaAncho, cx + anchoFranja / 2 + 0.6);
      ctx.fillStyle = d.muestras[k].hex;
      ctx.fillRect(x0, BANDA_Y, x1 - x0, BANDA_ALTO);
    }
    if (pintadas === 0) {
      ctx.fillStyle = "rgba(233,237,248,0.35)";
      ctx.font = "500 15px Inter, system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Mural vacío", ANCHO / 2, BANDA_Y + BANDA_ALTO / 2 + 5);
    }

    // Frente de pintura
    if (pintadas > 0 && pintadas < n) {
      var fx = Math.min(bandaX + bandaAncho, this._px(d.muestras[pintadas - 1].x) + anchoFranja / 2);
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.fillRect(fx - 1, BANDA_Y - 4, 2, BANDA_ALTO + 8);
    }
    ctx.strokeStyle = "rgba(255,255,255,0.25)";
    ctx.strokeRect(bandaX + 0.5, BANDA_Y + 0.5, bandaAncho - 1, BANDA_ALTO - 1);

    this._dibujarEscala();
    this._dibujarControles();
    this._dibujarObjetivo();
  };

  MuralAnimado.prototype._dibujarEscala = function () {
    var ctx = this.ctx, d = this.datos;
    ctx.strokeStyle = "rgba(168,178,207,0.7)";
    ctx.fillStyle = "#a8b2cf";
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(MARGEN_X, EJE_Y); ctx.lineTo(ANCHO - MARGEN_X, EJE_Y); ctx.stroke();
    ctx.font = "12px 'JetBrains Mono', ui-monospace, monospace";
    ctx.textAlign = "center";
    var rango = d.xMax - d.xMin;
    var paso = rango <= 8 ? 0.5 : rango <= 20 ? 1 : Math.pow(10, Math.floor(Math.log10(rango / 6)));
    var inicio = Math.ceil(d.xMin / paso) * paso;
    for (var x = inicio; x <= d.xMax + 1e-9; x += paso) {
      var px = this._px(x);
      var entero = Math.abs(x - Math.round(x)) < 1e-9;
      ctx.beginPath(); ctx.moveTo(px, EJE_Y); ctx.lineTo(px, EJE_Y + (entero ? 7 : 4)); ctx.stroke();
      if (entero || rango <= 3) ctx.fillText(formatoM(x), px, EJE_Y + 20);
    }
    ctx.textAlign = "right";
    ctx.fillText("metros", ANCHO - MARGEN_X, EJE_Y + 36);
  };

  MuralAnimado.prototype._dibujarControles = function () {
    var ctx = this.ctx, self = this, d = this.datos;
    d.controles.forEach(function (c, i) {
      var px = self._px(c.x);
      var pintado = Math.floor(self.progreso) > c.indice;
      // Marcador triangular sobre la banda
      ctx.fillStyle = c.hex;
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(px, BANDA_Y - 2); ctx.lineTo(px - 8, BANDA_Y - 16); ctx.lineTo(px + 8, BANDA_Y - 16);
      ctx.closePath(); ctx.fill(); ctx.stroke();
      // Línea guía tenue
      ctx.strokeStyle = pintado ? "rgba(255,255,255,0.55)" : "rgba(255,255,255,0.18)";
      ctx.setLineDash([3, 4]);
      ctx.beginPath(); ctx.moveTo(px, BANDA_Y); ctx.lineTo(px, BANDA_Y + BANDA_ALTO); ctx.stroke();
      ctx.setLineDash([]);
      // Etiquetas
      var alinear = i === 0 ? "left" : i === d.controles.length - 1 ? "right" : "center";
      var tx = alinear === "left" ? px - 8 : alinear === "right" ? px + 8 : px;
      ctx.textAlign = alinear;
      ctx.fillStyle = "#e9edf8";
      ctx.font = "600 13px Inter, system-ui, sans-serif";
      ctx.fillText(c.nombre + "  ·  x = " + formatoM(c.x) + " m", tx, BANDA_Y - 44);
      ctx.fillStyle = "#a8b2cf";
      ctx.font = "12px 'JetBrains Mono', ui-monospace, monospace";
      ctx.fillText(c.hex, tx, BANDA_Y - 26);
    });
  };

  MuralAnimado.prototype._dibujarObjetivo = function () {
    var obj = this.datos.objetivo;
    if (!obj) return;
    var ctx = this.ctx, px = this._px(obj.x);
    var alcanzado = this.objetivoAlcanzado;
    var brillo = alcanzado ? 1 : 0.45;

    if (alcanzado && this.destello > 0) {
      ctx.save();
      ctx.shadowColor = "#ffffff";
      ctx.shadowBlur = 18 * (this.destello / 600);
    } else {
      ctx.save();
    }
    ctx.strokeStyle = "rgba(255,255,255," + brillo + ")";
    ctx.lineWidth = alcanzado ? 2.5 : 1.5;
    if (!alcanzado) ctx.setLineDash([6, 5]);
    ctx.beginPath(); ctx.moveTo(px, BANDA_Y - 6); ctx.lineTo(px, EJE_Y + 6); ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // Recuadro con el color calculado (dentro de la banda, abajo)
    var tam = 30, cy = BANDA_Y + BANDA_ALTO - tam - 10;
    ctx.fillStyle = obj.hex;
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = alcanzado ? 3 : 1.5;
    ctx.fillRect(px - tam / 2, cy, tam, tam);
    ctx.strokeRect(px - tam / 2, cy, tam, tam);

    // Etiqueta inferior
    var texto = (alcanzado ? "★ " : "") + "x = " + formatoM(obj.x) + " m  ·  " + obj.hex +
      "  ·  RGB(" + obj.rgb.r + ", " + obj.rgb.g + ", " + obj.rgb.b + ")";
    ctx.font = (alcanzado ? "700 " : "500 ") + "13px Inter, system-ui, sans-serif";
    var w = ctx.measureText(texto).width + 20;
    var lx = Math.max(MARGEN_X, Math.min(ANCHO - MARGEN_X - w, px - w / 2));
    var ly = ALTO - 30;
    ctx.fillStyle = alcanzado ? obj.hex : "rgba(26,35,64,0.9)";
    ctx.strokeStyle = "rgba(255,255,255," + (alcanzado ? 0.9 : 0.35) + ")";
    ctx.lineWidth = 1;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(lx, ly, w, 24, 12); else ctx.rect(lx, ly, w, 24);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = alcanzado && luminancia(obj.rgb) > 0.6 ? "#000" : "#fff";
    ctx.textAlign = "left";
    ctx.fillText(texto, lx + 10, ly + 16.5);
  };

  global.MuralAnimado = MuralAnimado;
})(window);
