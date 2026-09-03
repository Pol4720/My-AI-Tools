#!/usr/bin/env python3
"""
Entregables con marca La Subasta Cubana.

Plantillas:
  viabilidad  1 pagina, pre-pago, "tus $X son $Y de puja"
  seleccion   reporte de los 3 vehiculos finalistas
  tarjeta     imagen cuadrada 1080x1080 para WhatsApp

Uso:
  python3 render_pdf.py --plantilla viabilidad --datos d.json --out Diagnostico.pdf
  python3 render_pdf.py --plantilla seleccion  --datos f.json --out Reporte.pdf
  python3 render_pdf.py --plantilla tarjeta    --datos f.json --out tarjetas/
  python3 render_pdf.py --autotest
"""
from __future__ import annotations
import argparse, base64, json, os, subprocess, sys, tempfile
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ASSETS = os.path.join(RAIZ, "assets")

NAVY, NAVY2, RED, REDB, BG = "#02142A", "#0D2440", "#B60000", "#D01019", "#F0F0F0"
PIE = ("ODD Car Investments LLC &nbsp;·&nbsp; 1475 Palm Ave, Hialeah, FL 33010 "
       "&nbsp;·&nbsp; 786-600-2222 &nbsp;·&nbsp; lasubastacubana.com")


def b64(ruta: str) -> str:
    if not ruta or not os.path.exists(ruta):
        return ""
    ext = "png" if ruta.lower().endswith(".png") else "jpeg"
    with open(ruta, "rb") as fh:
        return f"data:image/{ext};base64,{base64.b64encode(fh.read()).decode()}"


def logo() -> str:
    return b64(os.path.join(ASSETS, "logo-lsc.png"))


def img(src: str, clase: str = "", estilo: str = "") -> str:
    """Devuelve un <img> o un marcador gris si no hay imagen (evita el icono roto)."""
    c = f' class="{clase}"' if clase else ""
    e = f' style="{estilo}"' if estilo else ""
    if not src:
        return f'<div{c}{e} style="background:{BG};{estilo}"></div>'
    return f'<img{c}{e} src="{src}">' 


def d(v, dec=2) -> str:
    if v is None or v == "NO APLICA":
        return "—"
    try:
        return f"${float(v):,.{dec}f}"
    except (TypeError, ValueError):
        return str(v)


def odo(v: dict) -> str:
    millas = v.get("odometro")
    return f"{millas:,} mi" if millas else "—"


CSS = f"""
@page {{ size: Letter; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Inter','Helvetica Neue',Arial,sans-serif; color:{NAVY};
        background:#fff; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
.page {{ width:8.5in; min-height:11in; padding:0.55in 0.6in 1.1in; position:relative;
         page-break-after:always; background:#fff; }}
.page:last-child {{ page-break-after:auto; }}
h1,h2,h3,.tit {{ font-family:'Oswald','Archivo Narrow','Arial Narrow',Impact,sans-serif;
                 font-weight:700; letter-spacing:.02em; text-transform:uppercase; }}
.head {{ display:flex; justify-content:space-between; align-items:flex-end;
         border-bottom:3px solid {RED}; padding-bottom:14px; margin-bottom:26px; }}
.head img {{ height:62px; }}
.head .meta {{ text-align:right; font-size:10.5px; color:#5A6673; line-height:1.65; }}
h1 {{ font-size:27px; color:{NAVY}; line-height:1.1; }}
h2 {{ font-size:15px; color:{NAVY}; margin:22px 0 10px;
      border-left:5px solid {RED}; padding-left:10px; }}
.hero {{ background:{NAVY}; color:#fff; border-radius:3px; padding:26px 30px; margin-bottom:22px;
         display:flex; gap:34px; align-items:center; }}
.hero .b {{ flex:1; }}
.hero .lbl {{ font-size:10px; letter-spacing:.13em; color:#93A4B8; text-transform:uppercase; }}
.hero .val {{ font-family:'Oswald','Arial Narrow',Impact,sans-serif; font-size:40px;
              line-height:1.08; margin-top:5px; }}
.hero .val.rojo {{ color:#FF6B6B; }}
.hero .sep {{ width:1px; align-self:stretch; background:rgba(255,255,255,.22); }}
.nota {{ font-size:11px; color:#5A6673; line-height:1.6; margin-top:8px; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; }}
th {{ background:{NAVY}; color:#fff; text-align:left; padding:8px 11px; font-size:10px;
      letter-spacing:.07em; text-transform:uppercase; font-weight:600; }}
td {{ padding:7px 11px; border-bottom:1px solid #E3E7EB; vertical-align:top; }}
tr:nth-child(even) td {{ background:#FAFBFC; }}
td.n {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
tr.tot td {{ background:{NAVY}!important; color:#fff; font-weight:700; font-size:13.5px;
             border:none; padding:11px; }}
.veredicto {{ display:inline-block; padding:8px 20px; border-radius:2px; color:#fff;
              font-family:'Oswald','Arial Narrow',Impact,sans-serif; font-size:16px;
              letter-spacing:.09em; }}
.v-ok {{ background:#0F7B3E; }} .v-mid {{ background:#B8730A; }} .v-no {{ background:{RED}; }}
.cards {{ display:flex; gap:13px; margin-top:14px; }}
.card {{ flex:1; border:1px solid #DCE1E6; border-radius:3px; overflow:hidden; }}
.card img {{ width:100%; height:112px; object-fit:cover; display:block; background:{BG}; }}
.card .c {{ padding:10px 11px; }}
.card .t {{ font-family:'Oswald','Arial Narrow',Impact,sans-serif; font-size:13.5px;
            line-height:1.2; }}
.card .s {{ font-size:10.5px; color:#5A6673; margin-top:5px; line-height:1.55; }}
.card .p {{ font-family:'Oswald','Arial Narrow',Impact,sans-serif; font-size:19px;
            color:{RED}; margin-top:7px; }}
.gal {{ display:grid; grid-template-columns:2fr 1fr 1fr; gap:7px; margin-bottom:16px; }}
.gal img {{ width:100%; height:100%; object-fit:cover; border-radius:3px; background:{BG}; }}
.gal img:first-child {{ grid-row:span 2; height:250px; }}
.gal img:not(:first-child) {{ height:121px; }}
.dos {{ display:flex; gap:22px; }} .dos>div {{ flex:1; }}
ul.p {{ list-style:none; font-size:12px; line-height:1.75; }}
ul.p li {{ padding-left:19px; position:relative; margin-bottom:3px; }}
ul.p li:before {{ position:absolute; left:0; font-weight:700; }}
ul.p.si li:before {{ content:"+"; color:#0F7B3E; }}
ul.p.no li:before {{ content:"!"; color:{RED}; }}
.aviso {{ background:#FFF6F6; border-left:4px solid {RED}; padding:11px 14px; font-size:11px;
          line-height:1.65; margin-top:14px; }}
.valores {{ position:absolute; left:0.6in; right:0.6in; bottom:0.52in;
            border-top:1px solid #DCE1E6; padding-top:11px; display:flex;
            justify-content:space-between; font-size:8.5px; letter-spacing:.11em;
            color:{NAVY}; text-transform:uppercase; font-weight:600; }}
.valores b {{ color:{RED}; }}
.pie {{ position:absolute; left:0; right:0; bottom:0; background:{NAVY}; color:#93A4B8;
        font-size:8.5px; text-align:center; padding:8px; letter-spacing:.05em; }}
"""


def _pagina(cuerpo: str, titulo: str, meta: str) -> str:
    return f"""<div class="page">
  <div class="head"><img src="{logo()}"><div class="meta">{meta}</div></div>
  <h1>{titulo}</h1>{cuerpo}
  <div class="valores"><span>Transparencia <b>en cada paso</b></span>
    <span>Confianza <b>que respalda</b></span><span>Experiencia <b>que garantiza</b></span>
    <span>Resultados <b>que hablan</b></span></div>
  <div class="pie">{PIE}</div></div>"""


def _doc(paginas: str) -> str:
    return (f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
            f'<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&'
            f'family=Inter:wght@400;600&display=swap" rel="stylesheet">'
            f"<style>{CSS}</style></head><body>{paginas}</body></html>")


# ---------------------------------------------------------------- plantillas

def html_viabilidad(x: dict) -> str:
    ver = (x.get("veredicto") or "VIABLE").upper()
    clase = {"VIABLE": "v-ok", "VIABLE CON AJUSTES": "v-mid", "NO VIABLE": "v-no"}.get(ver, "v-mid")
    tarjetas = "".join(f"""<div class="card">{img(b64(v.get('foto_local','')) or v.get('foto',''), 'ph', 'width:100%;height:112px;')}
      <div class="c"><div class="t">{v.get('anio','')} {v.get('marca','')} {v.get('modelo','')}</div>
      <div class="s">{v.get('titulo','—')}<br>{(f"{v['odometro']:,} mi" if v.get('odometro') else '—')}
      &nbsp;·&nbsp; {v.get('ubicacion','—')}</div>
      <div class="p">{d(v.get('buy_now') or v.get('oferta_actual'), 0)}</div></div></div>"""
                      for v in x.get("ejemplos", [])[:3])

    bloque = f'<h2>Lo que hay hoy en ese rango</h2><div class="cards">{tarjetas}</div>' \
        if tarjetas else ""
    alt = ""
    if x.get("alternativas"):
        alt = ('<h2>Tus alternativas</h2><ul class="p si">'
               + "".join(f"<li>{a}</li>" for a in x["alternativas"]) + "</ul>")

    cuerpo = f"""
  <div class="hero">
    <div class="b"><div class="lbl">Tu presupuesto total</div>
      <div class="val">{d(x.get('presupuesto'), 0)}</div></div>
    <div class="sep"></div>
    <div class="b"><div class="lbl">Lo que puedes ofertar en subasta</div>
      <div class="val rojo">{d(x.get('oferta_maxima'), 0)}</div></div>
  </div>
  <p class="nota">La diferencia no se pierde: cubre la tarifa de la subasta, la tarifa de gestión de
  La Subasta Cubana, el impuesto estatal, la titulación y el transporte hasta tu puerta.
  El desglose completo está más abajo.</p>
  <h2>Veredicto</h2>
  <span class="veredicto {clase}">{ver}</span>
  <p class="nota">{x.get('explicacion','')}</p>
  {alt}
  <h2>A dónde va cada dólar</h2>
  {tabla_costos(x.get('desglose', {}))}
  {bloque}
  <div class="aviso"><b>Importante:</b> los vehículos de subasta se venden AS IS, en la condición en
  que se encuentran. Las cifras de tarifa de subasta y transporte son estimados y se confirman antes
  de cualquier compromiso. El depósito de seguridad no es reembolsable si el vehículo se adjudica y
  decides no continuar.</div>"""
    meta = (f"{x.get('cliente','Cliente')}<br>{x.get('fecha', date.today().strftime('%d/%m/%Y'))}"
            f"<br>Asesor: {x.get('asesor','—')}")
    return _doc(_pagina(cuerpo, "Diagnóstico de Viabilidad", meta))


def tabla_costos(g: dict) -> str:
    if not g:
        return ""
    s, t, tr = g.get("subasta", {}), g.get("titulacion", {}), g.get("transporte", {})
    est = ' <span style="color:#8A97A5">(est.)</span>' if s.get("tarifa_subasta_estimada") else ""
    filas = [
        ("Oferta máxima en subasta", s.get("oferta_maxima")),
        (f"Tarifa de la subasta{est}", s.get("tarifa_subasta")),
        ("Tarifa de La Subasta Cubana", s.get("tarifa_lsc")),
        (f"Impuesto ({g.get('impuesto', {}).get('tasa_pct', 0):.0f}%)",
         g.get("impuesto", {}).get("monto")),
        ("Traspaso del título", t.get("traspaso_titulo")),
        ("Envío de documentos", t.get("envio_documentos")),
        ("Certificación de título", t.get("certificacion_titulo")),
        ("Transferencia de chapa", t.get("transferencia_chapa")),
        ("Coordinación de transporte", tr.get("coordinacion")),
        ("Pago estimado al transportista", tr.get("transportista")),
    ]
    cuerpo = "".join(f'<tr><td>{n}</td><td class="n">{d(v)}</td></tr>' for n, v in filas)
    return (f'<table><tr><th>Concepto</th><th style="text-align:right">Monto</th></tr>{cuerpo}'
            f'<tr class="tot"><td>COSTO TOTAL ESTIMADO</td>'
            f'<td class="n">{d(g.get("total"))}</td></tr></table>')


def html_seleccion(x: dict) -> str:
    vs = x.get("vehiculos", [])[:3]
    meta = (f"{x.get('cliente','Cliente')}<br>{x.get('fecha', date.today().strftime('%d/%m/%Y'))}"
            f"<br>Asesor: {x.get('asesor','—')}")
    paginas = []

    filas = "".join(
        f"<tr><td><b>{v.get('anio','')} {v.get('marca','')} {v.get('modelo','')}</b><br>"
        f'<span style="font-size:10.5px;color:#5A6673">{v.get("titulo","—")} · '
        f'{v.get("ubicacion","—")}</span></td>'
        f'<td class="n">{odo(v)}</td>'
        f'<td class="n">{d(v.get("oferta_recomendada"), 0)}</td>'
        f'<td class="n"><b>{d(v.get("costo_total"))}</b></td>'
        f'<td>{v.get("fecha_subasta","—")}</td></tr>' for v in vs)
    resumen = f"""
  <p class="nota">Estas son las tres mejores opciones que encontramos para tu presupuesto y tus
  necesidades. En las páginas siguientes está el detalle de cada una.</p>
  <h2>Comparación</h2>
  <table><tr><th>Vehículo</th><th style="text-align:right">Millaje</th>
  <th style="text-align:right">Oferta sugerida</th><th style="text-align:right">Costo total</th>
  <th>Subasta</th></tr>{filas}</table>
  <h2>Nuestra recomendación</h2>
  <p class="nota">{x.get('recomendacion','')}</p>
  <div class="aviso"><b>Antes de decidir:</b> los vehículos se compran AS IS. El análisis se basa en
  el historial del vehículo, la ficha de la subasta y las imágenes del lote; no incluye una prueba
  mecánica en carretera. Las fechas de subasta son firmes y los precios cambian a diario.</div>"""
    paginas.append(_pagina(resumen, "Reporte de Selección", meta))

    for i, v in enumerate(vs, 1):
        fotos = [b64(f) if os.path.exists(str(f)) else f for f in (v.get("fotos") or [])][:3]
        while len(fotos) < 3:
            fotos.append("")
        gal = ('<div class="gal">' + "".join(
            img(f, "", f"width:100%;height:{'250px' if k == 0 else '121px'};"
                      f"{'grid-row:span 2;' if k == 0 else ''}border-radius:3px;")
            for k, f in enumerate(fotos)) + "</div>")
        favor = "".join(f"<li>{s}</li>" for s in v.get("a_favor", []))
        contra = "".join(f"<li>{s}</li>" for s in v.get("advertencias", []))
        ficha = "".join(
            f'<tr><td>{k}</td><td class="n">{val}</td></tr>' for k, val in [
                ("VIN", v.get("vin", "—")), ("Lote", v.get("lote", "—")),
                ("Subasta", v.get("subasta", "—")), ("Título", v.get("titulo", "—")),
                ("Millaje", f"{v['odometro']:,} mi" if v.get("odometro") else "—"),
                ("Ubicación", v.get("ubicacion", "—")),
                ("Daño principal", v.get("dano_primario", "—")),
                ("Llaves", v.get("llaves", "—")), ("Transmisión", v.get("transmision", "—")),
                ("Motor", v.get("motor", "—")),
            ])
        cuerpo = f"""{gal}
  <div class="hero"><div class="b"><div class="lbl">Oferta máxima recomendada</div>
    <div class="val">{d(v.get('oferta_recomendada'), 0)}</div></div><div class="sep"></div>
    <div class="b"><div class="lbl">Costo total estimado</div>
    <div class="val rojo">{d(v.get('costo_total'), 0)}</div></div><div class="sep"></div>
    <div class="b"><div class="lbl">Fecha de subasta</div>
    <div class="val" style="font-size:23px">{v.get('fecha_subasta','—')}</div></div></div>
  <div class="dos"><div><h2>Ficha</h2><table>{ficha}</table></div>
    <div><h2>A favor</h2><ul class="p si">{favor}</ul>
    {'<h2>A tener en cuenta</h2><ul class="p no">' + contra + '</ul>' if contra else ''}</div></div>
  <h2>Costo desglosado</h2>{tabla_costos(v.get('desglose', {}))}"""
        paginas.append(_pagina(
            cuerpo, f"Opción {i} — {v.get('anio','')} {v.get('marca','')} {v.get('modelo','')}",
            meta))
    return _doc("".join(paginas))


def html_tarjeta(v: dict) -> str:
    foto = b64(str(v.get("fotos", [""])[0])) if v.get("fotos") and \
        os.path.exists(str(v["fotos"][0])) else (v.get("fotos") or [""])[0]
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;font-family:'Inter',Arial,sans-serif;background:{NAVY};
 color:#fff;-webkit-print-color-adjust:exact}}
.f{{width:1080px;height:560px;object-fit:cover;display:block;background:{BG}}}
.c{{padding:40px 52px}}
.t{{font-family:'Oswald',Impact,sans-serif;font-size:60px;line-height:1.02;text-transform:uppercase}}
.s{{font-size:25px;color:#93A4B8;margin-top:16px;line-height:1.5}}
.g{{display:flex;gap:56px;margin-top:34px;align-items:flex-end}}
.lbl{{font-size:16px;letter-spacing:.14em;color:#93A4B8;text-transform:uppercase}}
.val{{font-family:'Oswald',Impact,sans-serif;font-size:56px;line-height:1.05;margin-top:6px}}
.val.r{{color:#FF6B6B}} .val.sm{{font-size:34px}}
.b{{position:absolute;bottom:0;left:0;right:0;background:{RED};height:12px}}
.lg{{position:absolute;bottom:36px;right:52px;height:62px;background:#fff;padding:7px 13px;
 border-radius:3px}}</style></head><body>
{img(foto, "f")}
<div class="c"><div class="t">{v.get('anio','')} {v.get('marca','')} {v.get('modelo','')}</div>
<div class="s">{v.get('titulo','—')} &nbsp;·&nbsp;
{(f"{v['odometro']:,} millas" if v.get('odometro') else '—')} &nbsp;·&nbsp;
{v.get('ubicacion','—')}</div>
<div class="g"><div><div class="lbl">Costo total estimado</div>
<div class="val r">{d(v.get('costo_total'), 0)}</div></div>
<div><div class="lbl">Subasta</div>
<div class="val sm">{v.get('fecha_subasta','—')}</div></div></div></div>
<img class="lg" src="{logo()}"><div class="b"></div></body></html>"""


# ---------------------------------------------------------------- salida

def a_pdf(html: str, salida: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
        fh.write(html)
        tmp = fh.name
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = nav.new_page()
            pg.goto("file://" + tmp, wait_until="networkidle")
            pg.pdf(path=salida, format="Letter", print_background=True,
                   margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            nav.close()
        return salida
    except Exception as exc:
        print(f"[aviso] playwright no disponible ({exc}); pruebo wkhtmltopdf", file=sys.stderr)
    try:
        subprocess.run(["wkhtmltopdf", "--enable-local-file-access", "-q",
                        "--page-size", "Letter", "-B", "0", "-T", "0", "-L", "0", "-R", "0",
                        tmp, salida], check=True)
        return salida
    except Exception as exc:
        alt = os.path.splitext(salida)[0] + ".html"
        with open(alt, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"[aviso] no hay motor de PDF ({exc}). HTML guardado en {alt}; "
              f"abrelo e imprime a PDF.", file=sys.stderr)
        return alt
    finally:
        os.unlink(tmp)


def a_png(html: str, salida: str, ancho=1080, alto=1080) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
        fh.write(html)
        tmp = fh.name
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = nav.new_page(viewport={"width": ancho, "height": alto})
            pg.goto("file://" + tmp, wait_until="networkidle")
            pg.screenshot(path=salida)
            nav.close()
        return salida
    finally:
        os.unlink(tmp)


DEMO = {
    "cliente": "Cliente de prueba", "asesor": "Asesor LSC", "presupuesto": 10000,
    "oferta_maxima": 7325, "veredicto": "VIABLE",
    "explicacion": "Con ese presupuesto alcanzas un sedán 2016-2019 con título limpio y millaje "
                   "moderado, o un SUV mediano salvage con daño frontal reparable.",
    "desglose": {"subasta": {"oferta_maxima": 7325, "tarifa_subasta": 205.1,
                             "tarifa_subasta_estimada": True, "tarifa_lsc": 699},
                 "impuesto": {"tasa_pct": 7, "monto": 575.09},
                 "titulacion": {"traspaso_titulo": 125, "envio_documentos": 20,
                                "certificacion_titulo": 210, "transferencia_chapa": "NO APLICA",
                                "subtotal": 355},
                 "transporte": {"coordinacion": 120, "transportista": 700, "subtotal": 820},
                 "total": 9979.19},
    "ejemplos": [{"anio": 2017, "marca": "Toyota", "modelo": "Camry",
                  "titulo": "Título Limpio", "odometro": 109619,
                  "ubicacion": "Jacksonville North(FL)", "buy_now": 3950}],
    "vehiculos": [{"anio": 2017, "marca": "Toyota", "modelo": "Camry",
                   "vin": "4T1BD1FK3HU209003", "lote": "79041575", "subasta": "COPART",
                   "titulo": "Título de Salvamento", "odometro": 109619,
                   "ubicacion": "Jacksonville North(FL)", "dano_primario": "Parte trasera",
                   "llaves": "YES", "transmision": "AUTOMATIC",
                   "oferta_recomendada": 3950, "costo_total": 6120.5,
                   "fecha_subasta": "24 ago, 10:00 am",
                   "a_favor": ["Compra inmediata disponible: precio cerrado, sin guerra de pujas",
                               "Daño trasero limitado y llaves presentes",
                               "Está en Florida: transporte más barato y rápido"],
                   "advertencias": ["Título de salvamento: requiere inspección antes de circular",
                                    "Pendiente revisar el Carfax"],
                   "fotos": []}],
    "recomendacion": "La opción 1 por relación precio-riesgo: está en Florida, tiene Buy Now y el "
                     "daño es visible y acotado.",
}


def autotest() -> int:
    out = tempfile.mkdtemp()
    ok = True
    for nombre, fn in [("viabilidad", html_viabilidad), ("seleccion", html_seleccion)]:
        try:
            h = fn(DEMO)
            assert "<html" in h and "Subasta" in h and len(h) > 2000
            r = a_pdf(h, os.path.join(out, f"{nombre}.pdf"))
            tam = os.path.getsize(r)
            print(f"  ok    {nombre}: {r} ({tam:,} bytes)")
            ok &= tam > 5000
        except Exception as exc:
            print(f"  FALLA {nombre}: {exc}")
            ok = False
    try:
        r = a_png(html_tarjeta(DEMO["vehiculos"][0]), os.path.join(out, "tarjeta.png"))
        print(f"  ok    tarjeta: {r} ({os.path.getsize(r):,} bytes)")
    except Exception as exc:
        print(f"  FALLA tarjeta: {exc}")
        ok = False
    print("\n" + ("RENDER OK" if ok else "HAY FALLOS"))
    print(f"Salidas de prueba en {out}")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Entregables con marca La Subasta Cubana")
    p.add_argument("--plantilla", choices=["viabilidad", "seleccion", "tarjeta"])
    p.add_argument("--datos", help="JSON de entrada")
    p.add_argument("--out", help="archivo .pdf, o carpeta si la plantilla es 'tarjeta'")
    p.add_argument("--autotest", action="store_true")
    a = p.parse_args()
    if a.autotest or not a.plantilla:
        return autotest()

    with open(a.datos, encoding="utf-8") as fh:
        x = json.load(fh)

    if a.plantilla == "tarjeta":
        carpeta = a.out or "tarjetas"
        os.makedirs(carpeta, exist_ok=True)
        vs = x.get("vehiculos", x if isinstance(x, list) else [x])
        for i, v in enumerate(vs, 1):
            slug = f"{v.get('anio','')}_{v.get('marca','')}_{v.get('modelo','')}".replace(" ", "-")
            r = a_png(html_tarjeta(v), os.path.join(carpeta, f"{i:02d}_{slug}.png"))
            print(f"-> {r}")
    else:
        h = html_viabilidad(x) if a.plantilla == "viabilidad" else html_seleccion(x)
        print(f"-> {a_pdf(h, a.out or f'{a.plantilla}.pdf')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
