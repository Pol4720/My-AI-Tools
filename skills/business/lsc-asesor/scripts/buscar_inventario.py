#!/usr/bin/env python3
"""
Buscador del inventario de La Subasta Cubana (Copart / IAAI / ACV / Manheim / OpenLane).

El parser trabaja sobre el TEXTO renderizado, no sobre clases CSS, porque las etiquetas
visibles ("Numero de Lote:", "Compra inmediata:", "Oferta Maxima Sugerida:") son mucho mas
estables que el marcado. Si el sitio cambia de diseno, esto sigue funcionando.

Uso:
  python3 buscar_inventario.py --marca toyota --modelo camry --precio-max 8000 --limite 30
  python3 buscar_inventario.py --dano front-end --buy-now --dias-subasta 7
  python3 buscar_inventario.py --vin 4T1BD1FK3HU209003 --fotos
  python3 buscar_inventario.py --descubrir      # mapea los nombres de los filtros del sitio
  python3 buscar_inventario.py --autotest       # verifica el parser sin red
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from datetime import datetime, timedelta

BASE = "https://lasubastacubana.com"
AQUI = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(os.path.dirname(AQUI), "config")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

MESES = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


# ---------------------------------------------------------------- red

def descargar(url: str, intentos: int = 3) -> str:
    import requests
    ultimo = None
    for i in range(intentos):
        try:
            r = requests.get(url, headers={"User-Agent": UA,
                                           "Accept-Language": "es-ES,es;q=0.9"}, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as exc:
            ultimo = exc
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo}")


def a_texto(html: str) -> str:
    """HTML -> texto plano conservando saltos, sin depender de clases."""
    try:
        from bs4 import BeautifulSoup
        sopa = BeautifulSoup(html, "html.parser")
        for t in sopa(["script", "style", "noscript"]):
            t.decompose()
        txt = sopa.get_text("\n")
    except ImportError:
        txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        txt = re.sub(r"<[^>]+>", "\n", txt)
    txt = re.sub(r"&nbsp;?", " ", txt)
    txt = re.sub(r"&amp;", "&", txt)
    return re.sub(r"[ \t]*\n[ \t\n]*", "\n", txt).strip()


# ---------------------------------------------------------------- parseo

def _campo(bloque: str, etiqueta: str) -> str | None:
    """Lee 'Etiqueta: valor' o 'Etiqueta\\nvalor' de forma tolerante."""
    pat = rf"{etiqueta}\s*:?\s*\n?\s*(.+)"
    m = re.search(pat, bloque, re.I)
    if not m:
        return None
    val = m.group(1).strip().strip("*").strip()
    return None if val in ("-", "", "N/A") else val


def _dinero(bloque: str, etiqueta: str) -> float | None:
    pat = rf"{etiqueta}\s*:?\s*\n?\s*\**\s*\$([\d,]+(?:\.\d+)?)"
    m = re.search(pat, bloque, re.I)
    return float(m.group(1).replace(",", "")) if m else None


def _fecha_subasta(bloque: str) -> tuple[str | None, int | None]:
    """'Aug 24, 9:30 am' -> ('2026-08-24 09:30', dias_restantes)."""
    m = re.search(r"Fecha de Subasta\s*:?\s*\n?\s*([A-Z][a-z]{2})\s+(\d{1,2})"
                  r"(?:,\s*(\d{1,2}):(\d{2})\s*([ap]m))?", bloque, re.I)
    if not m:
        m2 = re.search(r"Fecha de (?:Venta|Subasta)\s*:?\s*\n?\s*(\d{4}-\d{2}-\d{2})", bloque, re.I)
        if m2:
            f = datetime.strptime(m2.group(1), "%Y-%m-%d")
            return f.strftime("%Y-%m-%d"), (f - datetime.now()).days
        return None, None
    mes = MESES.get(m.group(1).title())
    if not mes:
        return None, None
    dia, hoy = int(m.group(2)), datetime.now()
    hora = minuto = 0
    if m.group(3):
        hora, minuto = int(m.group(3)), int(m.group(4))
        if m.group(5).lower() == "pm" and hora != 12:
            hora += 12
        elif m.group(5).lower() == "am" and hora == 12:
            hora = 0
    anio = hoy.year
    try:
        f = datetime(anio, mes, dia, hora, minuto)
    except ValueError:
        return None, None
    if (f - hoy).days < -60:                       # cruce de anio
        f = f.replace(year=anio + 1)
    return f.strftime("%Y-%m-%d %H:%M"), (f - hoy).days


def parsear_listado(texto: str) -> list[dict]:
    """Divide por VIN y extrae cada lote. Ignora el panel de facetas."""
    partes = re.split(r"\n(?=VIN\s*\n?[A-HJ-NPR-Z0-9]{17}\b)", texto)
    lotes, vistos = [], set()
    for i, bloque in enumerate(partes):
        mv = re.search(r"VIN\s*\n?\s*([A-HJ-NPR-Z0-9]{17})\b", bloque)
        if not mv:
            continue
        vin = mv.group(1)
        if vin in vistos:
            continue
        vistos.add(vin)

        # El encabezado "2017 Toyota Camry" cae al final del bloque ANTERIOR,
        # porque el corte se hace justo antes de "VIN".
        previo = partes[i - 1][-320:] if i > 0 else ""
        cabecera = (previo + "\n" + bloque[:mv.start()])[-320:]
        mt = re.search(r"((?:19|20)\d{2})\s+([A-Za-z][\w\-]*)\s+([^\n]{1,40}?)\s*\n"
                       r"(?:Compartir|COMPARTIR)", cabecera)
        if not mt:
            mt = re.search(r"((?:19|20)\d{2})\s+([A-Za-z][\w\-]*)\s+([^\n]{1,40})", cabecera)
        anio, marca, modelo = (int(mt.group(1)), mt.group(2), mt.group(3).strip()) if mt \
            else (None, None, None)

        odo = _campo(bloque, "Odómetro") or _campo(bloque, "Odometro") or ""
        odo_n = int(re.sub(r"[^\d]", "", odo)) if re.search(r"\d", odo) else None
        fecha, dias = _fecha_subasta(bloque)
        ubic = _campo(bloque, "Ubicación") or _campo(bloque, "Ubicacion")
        est = None
        if ubic:
            me = re.search(r"\(([A-Z]{2}|[A-Z][A-Za-z ]+)\)", ubic)
            est = me.group(1) if me else None

        casa = None
        for c in ("copart", "iaai", "acv", "manheim", "openlane"):
            if re.search(rf"\b{c}\b", cabecera, re.I) or re.search(rf"\b{c}\b", bloque[:400], re.I):
                casa = c.upper()
                break

        lotes.append({
            "vin": vin,
            "anio": anio, "marca": marca, "modelo": modelo,
            "lote": _campo(bloque, "Número de Lote") or _campo(bloque, "Numero de Lote"),
            "subasta": casa,
            "titulo": _campo(bloque, "Titulo") or _campo(bloque, "Título"),
            "ubicacion": ubic, "estado": est,
            "odometro": odo_n,
            "vendedor": _campo(bloque, "Vendedor"),
            "dano_primario": _campo(bloque, "Daño Primario") or _campo(bloque, "Danos Primarios"),
            "buy_now": _dinero(bloque, "Compra inmediata"),
            "oferta_actual": _dinero(bloque, "Oferta actual"),
            "oferta_max_sugerida": _dinero(bloque, "Oferta Máxima Sugerida")
                                   or _dinero(bloque, "Oferta Maxima Sugerida"),
            "precio_mercado": _dinero(bloque, "Precio de Mercado"),
            "fecha_subasta": fecha, "dias_para_subasta": dias,
            "url": f"{BASE}/inventory-vdp/vin-{vin}",
        })
    return lotes


def parsear_ficha(html: str) -> dict:
    texto = a_texto(html)
    base = parsear_listado(texto)
    d = base[0] if base else {}
    for clave, etiqueta in [("traccion", "Tracción"), ("carroceria", "Tipo"), ("motor", "Motor"),
                            ("transmision", "Transmisión"), ("combustible", "Combustible"),
                            ("color", "Color Exterior"), ("llaves", "Llaves"),
                            ("version", "Versión"), ("dano_secundario", "Daños Secundarios"),
                            ("carril", "Carril/Artículo"),
                            ("actualizado", "Última actualización")]:
        v = _campo(texto, etiqueta)
        if v:
            d[clave] = v
    d["run_and_drive"] = bool(re.search(r"Run\s*&\s*Drive", texto, re.I))
    costo = _dinero(texto, "Costo Estimado de Reparación")
    if costo:
        d["costo_reparacion_estimado"] = costo
    d["fotos"] = extraer_fotos(html)
    return d


def extraer_fotos(html: str) -> list[str]:
    # El CDN de LSC codifica los puntos como _DOT_, asi que hay que aceptar ambas formas.
    urls = re.findall(
        r'https://[^\s"\'<>)]+?(?:_ful|resizer|photo)[^\s"\'<>)]*?(?:\.|_DOT_)jpe?g', html, re.I)
    limpias, vistas = [], set()
    for u in urls:
        u = u.replace("inventory_detail_secondary_filter", "inventory_detail_main_2x_filter") \
             .replace("inventory_list_filter", "inventory_detail_main_2x_filter")
        clave = u.rsplit("/", 1)[-1]
        if clave not in vistas:
            vistas.add(clave)
            limpias.append(u)
    return limpias


# ---------------------------------------------------------------- consulta

def construir_urls(a) -> list[str]:
    filtros = {}
    ruta = os.path.join(CONFIG, "filtros.json")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as fh:
            filtros = json.load(fh)

    segmentos = []
    if a.marca and a.modelo:
        segmentos.append(f"search/{a.marca.lower()}-{a.modelo.lower().replace(' ', '-')}")
    elif a.marca:
        segmentos.append(f"make-{a.marca.lower()}")
    if a.dano:
        segmentos.append(f"damage-{a.dano.lower()}")

    base = f"{BASE}/inventory" + ("/" + "/".join(segmentos) if segmentos else "")
    qs = ["order[default]=asc"]
    for cli, val in [("precio_min", a.precio_min), ("precio_max", a.precio_max),
                     ("anio_min", a.anio_min), ("anio_max", a.anio_max),
                     ("estado", a.estado), ("subasta", a.subasta)]:
        if val is not None and cli in filtros:
            qs.append(f"{filtros[cli]}={val}")
    urls = [f"{base}?{'&'.join(qs)}"]
    for pag in range(2, a.paginas + 1):
        urls.append(f"{base}?{'&'.join(qs)}&page={pag}")
    return urls


def filtrar_local(lotes: list[dict], a) -> list[dict]:
    """Filtrado en cliente: funciona haya o no mapeo de facetas del sitio."""
    out = []
    for l in lotes:
        precio = l.get("buy_now") or l.get("oferta_max_sugerida") or l.get("oferta_actual")
        if a.precio_max and (precio is None or precio > a.precio_max):
            continue
        if a.precio_min and (precio is None or precio < a.precio_min):
            continue
        if a.anio_min and (l.get("anio") is None or l["anio"] < a.anio_min):
            continue
        if a.anio_max and (l.get("anio") is None or l["anio"] > a.anio_max):
            continue
        if a.buy_now and not l.get("buy_now"):
            continue
        if a.dias_subasta is not None:
            d = l.get("dias_para_subasta")
            if d is None or d < 0 or d > a.dias_subasta:
                continue
        if a.estado and (l.get("estado") or "").upper() != a.estado.upper():
            continue
        if a.subasta and (l.get("subasta") or "").upper() != a.subasta.upper():
            continue
        if a.odometro_max and (l.get("odometro") is None or l["odometro"] > a.odometro_max):
            continue
        if a.excluir_rebuild and re.search(r"rebuild|reconstru", l.get("titulo") or "", re.I):
            continue
        out.append(l)
    return out


def descubrir_filtros() -> dict:
    """Mapea los name= de los inputs/selects del panel de filtros. Correr una vez."""
    from bs4 import BeautifulSoup
    html = descargar(f"{BASE}/inventory?order[default]=asc")
    sopa = BeautifulSoup(html, "html.parser")
    hallados = {}
    for el in sopa.find_all(["input", "select"]):
        nombre = el.get("name")
        if not nombre or nombre in hallados:
            continue
        hallados[nombre] = {
            "tipo": el.get("type") or el.name,
            "id": el.get("id"),
            "ejemplo_valor": (el.get("value")
                              or (el.find("option").get("value") if el.name == "select"
                                  and el.find("option") else None)),
        }
    os.makedirs(CONFIG, exist_ok=True)
    ruta = os.path.join(CONFIG, "filtros_descubiertos.json")
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(hallados, fh, indent=2, ensure_ascii=False)
    print(f"{len(hallados)} campos encontrados -> {ruta}")
    print("Revisa el archivo, identifica los que corresponden a precio/anio/estado/subasta,")
    print("y escribe el mapeo final en config/filtros.json con estas claves:")
    print('  {"precio_min": "...", "precio_max": "...", "anio_min": "...",')
    print('   "anio_max": "...", "estado": "...", "subasta": "..."}')
    for n, v in list(hallados.items())[:60]:
        print(f"  {n:<40} {v['tipo']}")
    return hallados


FIXTURE = """
acv
2017 Toyota Camry
Compartir
COMPARTIR
VIN
4T1BD1FK3HU209003
Número de Lote: 79041575
Titulo: Título de Salvamento
Ubicación: Jacksonville North(FL)
Odómetro: 109,619 mi
Vendedor: No especificado
Daño Primario: Parte trasera
Fecha de Subasta: Aug 24, 10:00 am
Compra inmediata:
 **$3,950.00**
Oferta actual:
 **-**
Oferta Máxima Sugerida:
 **$3,950.00**
Precio de Mercado (Estimado):
 **-**
copart
2022 Toyota Tacoma
Compartir
COMPARTIR
VIN
3TYAX5GN9NT035952
Número de Lote: 45556503
Titulo: Certificado de Título Limpio
Ubicación: Fort Myers(FL)
Odómetro: 89,249 mi
Vendedor: Progressive Casualty Insurance
Daño Primario: Sin daños reportados
Fecha de Subasta: Aug 25, 9:30 am
Compra inmediata:
 **$11,975.00**
Oferta actual:
 **$1,050.00**
Oferta Máxima Sugerida:
 **-**
"""


def autotest() -> int:
    lotes = parsear_listado(FIXTURE.strip())
    fallos = []

    def chk(n, o, e):
        ok = o == e
        print(f"  {'ok   ' if ok else 'FALLA'} {n}: {o!r}")
        if not ok:
            fallos.append(f"{n} (esperado {e!r})")

    chk("cantidad de lotes", len(lotes), 2)
    if len(lotes) == 2:
        a, b = lotes
        chk("vin[0]", a["vin"], "4T1BD1FK3HU209003")
        chk("anio[0]", a["anio"], 2017)
        chk("marca[0]", a["marca"], "Toyota")
        chk("modelo[0]", a["modelo"], "Camry")
        chk("lote[0]", a["lote"], "79041575")
        chk("titulo[0]", a["titulo"], "Título de Salvamento")
        chk("estado[0]", a["estado"], "FL")
        chk("odometro[0]", a["odometro"], 109619)
        chk("buy_now[0]", a["buy_now"], 3950.0)
        chk("oferta_actual[0] vacia", a["oferta_actual"], None)
        chk("sugerida[0]", a["oferta_max_sugerida"], 3950.0)
        chk("dano[0]", a["dano_primario"], "Parte trasera")
        chk("vin[1]", b["vin"], "3TYAX5GN9NT035952")
        chk("vendedor[1]", b["vendedor"], "Progressive Casualty Insurance")
        chk("oferta_actual[1]", b["oferta_actual"], 1050.0)
        chk("sugerida[1] vacia", b["oferta_max_sugerida"], None)
        chk("fecha[0] parseada", a["fecha_subasta"] is not None, True)

    fotos = extraer_fotos(
        '<img src="https://x.com/media/cache/inventory_list_filter/a_ful_dcd32d83_DOT_jpg">'
        '<img src="https://x.com/media/cache/inventory_detail_secondary_filter/b_resizer_ec3.jpg">')
    chk("fotos extraidas", len(fotos), 2)
    chk("foto normalizada a alta resolucion",
        "inventory_detail_main_2x_filter" in fotos[0], True)

    print(f"\n{'PARSER OK' if not fallos else 'FALLOS: ' + '; '.join(fallos)}")
    print("\nNota: esto valida el parser sin red. Antes de usar en produccion corre una")
    print("busqueda real y confirma que los datos coinciden con la web.")
    return 0 if not fallos else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Buscador del inventario de La Subasta Cubana")
    p.add_argument("--marca"); p.add_argument("--modelo"); p.add_argument("--dano")
    p.add_argument("--precio-min", type=float); p.add_argument("--precio-max", type=float)
    p.add_argument("--anio-min", type=int); p.add_argument("--anio-max", type=int)
    p.add_argument("--estado", help="estado del LOTE, ej. FL")
    p.add_argument("--subasta", choices=["COPART", "IAAI", "ACV", "MANHEIM", "OPENLANE"])
    p.add_argument("--odometro-max", type=int)
    p.add_argument("--buy-now", action="store_true", help="solo lotes con Compra Inmediata")
    p.add_argument("--dias-subasta", type=int, help="maximo de dias hasta la subasta")
    p.add_argument("--excluir-rebuild", action="store_true", default=True)
    p.add_argument("--paginas", type=int, default=3)
    p.add_argument("--limite", type=int, default=25)
    p.add_argument("--vin", help="ficha completa de un VIN")
    p.add_argument("--lote", help="ficha completa de un numero de lote")
    p.add_argument("--fotos", action="store_true", help="incluir URLs de fotos")
    p.add_argument("--out", help="guardar JSON en un archivo")
    p.add_argument("--descubrir", action="store_true")
    p.add_argument("--autotest", action="store_true")
    a = p.parse_args()

    if a.autotest:
        return autotest()
    if a.descubrir:
        descubrir_filtros(); return 0

    if a.vin or a.lote:
        url = f"{BASE}/inventory-vdp/" + (f"vin-{a.vin}" if a.vin else f"lot-{a.lote}")
        d = parsear_ficha(descargar(url))
        d["url"] = url
        if not a.fotos:
            d.pop("fotos", None)
        salida = d
    else:
        lotes = []
        for url in construir_urls(a):
            try:
                lotes.extend(parsear_listado(a_texto(descargar(url))))
            except Exception as exc:
                print(f"[aviso] fallo {url}: {exc}", file=sys.stderr)
                break
            time.sleep(0.8)
        vistos, unicos = set(), []
        for l in lotes:
            if l["vin"] not in vistos:
                vistos.add(l["vin"]); unicos.append(l)
        salida = filtrar_local(unicos, a)[:a.limite]
        print(f"[info] {len(unicos)} lotes descargados, {len(salida)} tras filtrar",
              file=sys.stderr)

    texto = json.dumps(salida, indent=2, ensure_ascii=False)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(texto)
        print(f"-> {a.out}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
