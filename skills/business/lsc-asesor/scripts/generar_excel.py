#!/usr/bin/env python3
"""
Excel comparativo de los 3 vehiculos finalistas.

Replica la logica del "Costo Estimado Total" oficial y le agrega lo que pidio el asesor:
3 danos principales por vehiculo, valor MMR, ahorro y rentabilidad, e imagenes.

Uso:
  python3 generar_excel.py --datos finalistas.json --out Comparativo_Cliente.xlsx
  python3 generar_excel.py --autotest
"""
from __future__ import annotations
import argparse, json, os, sys, tempfile, urllib.request
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from costeo import Escenario, calcular, NO_APLICA          # noqa: E402

NAVY, RED, BG = "FF02142A", "FFB60000", "FFF0F0F0"
VERDE, AMBAR = "FF0F7B3E", "FFB8730A"

F_TIT = Font(name="Arial", size=13, bold=True, color="FFFFFFFF")
F_ENC = Font(name="Arial", size=9, bold=True, color="FFFFFFFF")
F_LBL = Font(name="Arial", size=10, bold=True, color=NAVY)
F_TXT = Font(name="Arial", size=10)
F_TOT = Font(name="Arial", size=11, bold=True, color="FFFFFFFF")
FILL_NAVY = PatternFill("solid", fgColor=NAVY)
FILL_RED = PatternFill("solid", fgColor=RED)
FILL_BG = PatternFill("solid", fgColor=BG)
BORDE = Border(*[Side(style="thin", color="FFDCE1E6")] * 4)
DINERO = '"$"#,##0.00'
PCT = '0.0%'


def _celda(ws, ref, valor, font=F_TXT, fill=None, fmt=None, align=None, wrap=False):
    c = ws[ref]
    c.value = valor
    c.font = font
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    c.alignment = Alignment(horizontal=align or ("right" if fmt == DINERO else "left"),
                            vertical="center", wrap_text=wrap)
    c.border = BORDE
    return c


def _banda(ws, fila, texto, ancho=5):
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ancho)
    _celda(ws, f"A{fila}", texto, F_ENC, FILL_NAVY, align="left")
    ws.row_dimensions[fila].height = 20


def _descargar_foto(url: str, destino: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r, open(destino, "wb") as fh:
            fh.write(r.read())
        return destino
    except Exception:
        return None


def _foto_local(v: dict, tmp: str, idx: int) -> str | None:
    fotos = v.get("fotos") or []
    if not fotos:
        return None
    f = str(fotos[0])
    if os.path.exists(f):
        return f
    if f.startswith("http"):
        return _descargar_foto(f, os.path.join(tmp, f"v{idx}.jpg"))
    return None


def _costeo(v: dict, cli: dict) -> dict:
    if v.get("desglose"):
        return v["desglose"]
    e = Escenario(
        oferta=float(v.get("oferta_recomendada") or v.get("buy_now")
                     or v.get("oferta_max_sugerida") or 0),
        subasta=(v.get("subasta") or "COPART").upper(),
        titulo=v.get("titulo", "Título Limpio"),
        estado=cli.get("estado", "FL"),
        financiado=bool(cli.get("financiado")),
        gestiona_chapa=bool(cli.get("gestiona_chapa")),
        tipo_chapa=cli.get("tipo_chapa", "renovacion"),
        contrata_transporte=cli.get("contrata_transporte", True),
        pago_transportista=v.get("pago_transportista", cli.get("pago_transportista")),
        tarifa_subasta_manual=v.get("tarifa_subasta"),
    )
    return calcular(e)


def hoja_comparativo(wb, vs, cli, cost):
    ws = wb.active
    ws.title = "Comparativo"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 34
    for i in range(len(vs)):
        ws.column_dimensions[get_column_letter(2 + i)].width = 26

    ncols = 1 + len(vs)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    _celda(ws, "A1", "COMPARATIVO DE VEHÍCULOS  ·  LA SUBASTA CUBANA", F_TIT, FILL_NAVY)
    ws.row_dimensions[1].height = 28
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    _celda(ws, "A2", f"Cliente: {cli.get('nombre','—')}    ·    Asesor: {cli.get('asesor','—')}"
                     f"    ·    {date.today().strftime('%d/%m/%Y')}", F_TXT, FILL_BG)

    f = 4
    _banda(ws, f, "IDENTIFICACIÓN", ncols); f += 1
    for etq, clave in [("Año / Marca / Modelo", "_titulo"), ("VIN", "vin"), ("Lote", "lote"),
                       ("Subasta", "subasta"), ("Tipo de título", "titulo"),
                       ("Ubicación", "ubicacion"), ("Odómetro (mi)", "odometro"),
                       ("Vendedor", "vendedor"), ("Llaves", "llaves"),
                       ("Fecha de subasta", "fecha_subasta"), ("Run & Drive", "run_and_drive")]:
        _celda(ws, f"A{f}", etq, F_LBL, FILL_BG)
        for i, v in enumerate(vs):
            val = (f"{v.get('anio','')} {v.get('marca','')} {v.get('modelo','')}".strip()
                   if clave == "_titulo" else v.get(clave, "—"))
            if isinstance(val, bool):
                val = "Sí" if val else "No"
            _celda(ws, f"{get_column_letter(2+i)}{f}", val if val not in (None, "") else "—",
                   fmt="#,##0" if clave == "odometro" else None, wrap=True)
        f += 1

    f += 1
    _banda(ws, f, "DAÑOS PRINCIPALES", ncols); f += 1
    for k in range(3):
        _celda(ws, f"A{f}", f"Daño {k+1}", F_LBL, FILL_BG)
        for i, v in enumerate(vs):
            danos = v.get("danos") or [x for x in (v.get("dano_primario"),
                                                   v.get("dano_secundario")) if x]
            _celda(ws, f"{get_column_letter(2+i)}{f}",
                   danos[k] if k < len(danos) else "—", wrap=True)
        f += 1

    f += 1
    _banda(ws, f, "COSTOS", ncols); f += 1
    filas = [
        ("Oferta máxima en subasta", lambda g: g["subasta"]["oferta_maxima"]),
        ("Tarifa de la subasta", lambda g: g["subasta"]["tarifa_subasta"]),
        ("Tarifa de La Subasta Cubana", lambda g: g["subasta"]["tarifa_lsc"]),
        ("Impuesto", lambda g: g["impuesto"]["monto"]),
        ("Traspaso del título", lambda g: g["titulacion"]["traspaso_titulo"]),
        ("Envío de documentos", lambda g: g["titulacion"]["envio_documentos"]),
        ("Certificación de título", lambda g: g["titulacion"]["certificacion_titulo"]),
        ("Transferencia de chapa", lambda g: g["titulacion"]["transferencia_chapa"]),
        ("Coordinación de transporte", lambda g: g["transporte"]["coordinacion"]),
        ("Pago al transportista", lambda g: g["transporte"]["transportista"]),
    ]
    for etq, fn in filas:
        _celda(ws, f"A{f}", etq, F_LBL, FILL_BG)
        for i, g in enumerate(cost):
            val = fn(g)
            es_num = not isinstance(val, str)
            _celda(ws, f"{get_column_letter(2+i)}{f}", val if es_num else NO_APLICA,
                   fmt=DINERO if es_num else None, align=None if es_num else "right")
        f += 1

    fila_total = f
    _celda(ws, f"A{f}", "COSTO TOTAL ESTIMADO", F_TOT, FILL_NAVY)
    for i, g in enumerate(cost):
        _celda(ws, f"{get_column_letter(2+i)}{f}", g["total"], F_TOT, FILL_NAVY, DINERO)
    ws.row_dimensions[f].height = 22
    f += 2

    _banda(ws, f, "VALOR DE MERCADO Y RENTABILIDAD", ncols); f += 1
    fila_mmr = f
    _celda(ws, f"A{f}", "Valor MMR (Manheim Market Report)", F_LBL, FILL_BG)
    for i, v in enumerate(vs):
        col = get_column_letter(2 + i)
        mmr = v.get("mmr")
        _celda(ws, f"{col}{f}", mmr if mmr else "—", fmt=DINERO if mmr else None)
    f += 1
    _celda(ws, f"A{f}", "Ahorro frente al mercado", F_LBL, FILL_BG)
    for i in range(len(vs)):
        col = get_column_letter(2 + i)
        c = _celda(ws, f"{col}{f}",
                   f"=IF(ISNUMBER({col}{fila_mmr}),{col}{fila_mmr}-{col}{fila_total},\"—\")",
                   fmt=DINERO)
        c.font = Font(name="Arial", size=10, bold=True, color=VERDE)
    fila_ahorro = f
    f += 1
    _celda(ws, f"A{f}", "Rentabilidad sobre el costo", F_LBL, FILL_BG)
    for i in range(len(vs)):
        col = get_column_letter(2 + i)
        c = _celda(ws, f"{col}{f}",
                   f"=IF(ISNUMBER({col}{fila_mmr}),{col}{fila_ahorro}/{col}{fila_total},\"—\")",
                   fmt=PCT)
        c.font = Font(name="Arial", size=10, bold=True, color=VERDE)
    f += 1
    _celda(ws, f"A{f}", "Depósito de seguridad mínimo (15%)", F_LBL, FILL_BG)
    for i, g in enumerate(cost):
        _celda(ws, f"{get_column_letter(2+i)}{f}", g["deposito_seguridad_minimo"], fmt=DINERO)
    f += 2

    _banda(ws, f, "PUNTUACIÓN Y VEREDICTO", ncols); f += 1
    _celda(ws, f"A{f}", "Puntuación (0-100)", F_LBL, FILL_BG)
    for i, v in enumerate(vs):
        _celda(ws, f"{get_column_letter(2+i)}{f}", v.get("puntuacion", "—"), align="right")
    f += 1
    _celda(ws, f"A{f}", "Recomendación", F_LBL, FILL_BG)
    for i, v in enumerate(vs):
        _celda(ws, f"{get_column_letter(2+i)}{f}", v.get("veredicto", "—"), wrap=True)
    ws.row_dimensions[f].height = 34
    f += 1
    _celda(ws, f"A{f}", "Pendientes de verificar", F_LBL, FILL_BG)
    for i, v in enumerate(vs):
        _celda(ws, f"{get_column_letter(2+i)}{f}",
               "; ".join(v.get("pendientes", [])) or "—", wrap=True)
    ws.row_dimensions[f].height = 42
    f += 2

    aviso = ("La tarifa de la subasta y el pago al transportista son ESTIMADOS: confirmar en la "
             "calculadora de LSC y en SuperDispatch. No incluye costos oficiales del DMV, Tag "
             "Agency, verificación de VIN, almacenaje, reparaciones ni seguro. Los vehículos se "
             "compran AS IS.")
    ws.merge_cells(start_row=f, start_column=1, end_row=f + 1, end_column=ncols)
    _celda(ws, f"A{f}", aviso, Font(name="Arial", size=8, italic=True, color="FF5A6673"),
           FILL_BG, wrap=True)
    return ws


def hoja_vehiculo(wb, v, g, idx, tmp):
    ws = wb.create_sheet(f"Vehículo {idx}")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 36
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 3
    ws.column_dimensions["E"].width = 40

    ws.merge_cells("B1:E1")
    _celda(ws, "B1", f"{v.get('anio','')} {v.get('marca','')} {v.get('modelo','')}  ·  "
                     f"{v.get('vin','')}", F_TIT, FILL_NAVY)
    ws.row_dimensions[1].height = 28

    f = 3
    _celda(ws, f"B{f}", "COSTO TOTAL APROXIMADO DE LA OFERTA", F_ENC, FILL_NAVY)
    _celda(ws, f"C{f}", "", F_ENC, FILL_NAVY)
    f += 1
    secciones = [
        ("1- Costos de una compra en subasta", [
            ("Oferta máxima a realizar en subasta", g["subasta"]["oferta_maxima"]),
            (f"Tarifa de {v.get('subasta','la subasta')}", g["subasta"]["tarifa_subasta"]),
            ("Tarifa de La Subasta Cubana", g["subasta"]["tarifa_lsc"])]),
        (f"2- Impuesto ({g['impuesto']['tasa_pct']:.0f}%)", [
            ("Impuesto sobre compra de vehículo", g["impuesto"]["monto"])]),
        ("3- Titulación", [
            ("Tarifa de traspaso del título", g["titulacion"]["traspaso_titulo"]),
            ("Envío de documentos", g["titulacion"]["envio_documentos"]),
            ("Certificación de título", g["titulacion"]["certificacion_titulo"]),
            ("Transferencia de chapa", g["titulacion"]["transferencia_chapa"])]),
        ("4- Costos de transporte", [
            ("Coordinación de transporte", g["transporte"]["coordinacion"]),
            ("Pago estimado al transportista", g["transporte"]["transportista"])]),
    ]
    for titulo, filas in secciones:
        _celda(ws, f"B{f}", titulo, F_LBL, FILL_BG)
        _celda(ws, f"C{f}", "", F_TXT, FILL_BG)
        f += 1
        for etq, val in filas:
            _celda(ws, f"B{f}", f"    {etq}")
            es_num = not isinstance(val, str)
            _celda(ws, f"C{f}", val, fmt=DINERO if es_num else None,
                   align=None if es_num else "right")
            f += 1
    _celda(ws, f"B{f}", "5- COSTO TOTAL ESTIMADO", F_TOT, FILL_NAVY)
    _celda(ws, f"C{f}", g["total"], F_TOT, FILL_NAVY, DINERO)
    ws.row_dimensions[f].height = 22
    f += 2

    _celda(ws, f"B{f}", "Depósito de seguridad mínimo (15%)", F_LBL, FILL_BG)
    _celda(ws, f"C{f}", g["deposito_seguridad_minimo"], fmt=DINERO)
    f += 2

    _celda(ws, f"B{f}", "AVISOS", F_ENC, FILL_RED)
    _celda(ws, f"C{f}", "", F_ENC, FILL_RED)
    f += 1
    for a in g.get("avisos", []):
        ws.merge_cells(f"B{f}:C{f}")
        _celda(ws, f"B{f}", f"· {a}", Font(name="Arial", size=8.5, color="FF5A6673"), wrap=True)
        ws.row_dimensions[f].height = 26
        f += 1

    foto = _foto_local(v, tmp, idx)
    if foto:
        try:
            from PIL import Image as PILImage
            im = PILImage.open(foto).convert("RGB")
            im.thumbnail((520, 390))
            red = os.path.join(tmp, f"thumb{idx}.png")
            im.save(red)
            xi = XLImage(red)
            ws.add_image(xi, "E3")
        except Exception as exc:                                   # pragma: no cover
            print(f"[aviso] no se pudo insertar la foto: {exc}", file=sys.stderr)
    return ws


def construir(datos: dict, salida: str) -> str:
    vs = datos.get("vehiculos", [])[:3]
    if not vs:
        raise ValueError("El JSON no trae 'vehiculos'.")
    cli = datos.get("cliente_config", datos.get("cliente", {}))
    if isinstance(cli, str):
        cli = {"nombre": cli}
    cost = [_costeo(v, cli) for v in vs]

    tmp = tempfile.mkdtemp()
    wb = Workbook()
    hoja_comparativo(wb, vs, cli, cost)
    for i, (v, g) in enumerate(zip(vs, cost), 1):
        hoja_vehiculo(wb, v, g, i, tmp)
    wb.save(salida)
    return salida


DEMO = {
    "cliente": {"nombre": "Cliente de prueba", "asesor": "Asesor LSC", "estado": "FL",
                "contrata_transporte": True, "pago_transportista": 700, "gestiona_chapa": True},
    "vehiculos": [
        {"anio": 2017, "marca": "Toyota", "modelo": "Camry", "vin": "4T1BD1FK3HU209003",
         "lote": "79041575", "subasta": "COPART", "titulo": "Título de Salvamento",
         "ubicacion": "Jacksonville North(FL)", "odometro": 109619, "llaves": "YES",
         "vendedor": "No especificado", "fecha_subasta": "24 ago, 10:00 am",
         "run_and_drive": True, "oferta_recomendada": 3950, "mmr": 9800, "puntuacion": 78,
         "danos": ["Parte trasera", "Abolladuras menores laterales"],
         "veredicto": "Aceptable con advertencias",
         "pendientes": ["Carfax", "foto de bajos"]},
        {"anio": 2018, "marca": "Honda", "modelo": "Accord", "vin": "1HGCV1F96JA074224",
         "lote": "15771357", "subasta": "ACV", "titulo": "Certificado de Título Limpio",
         "ubicacion": "Johnston(RI)", "odometro": 89493, "llaves": "YES",
         "vendedor": "ACV_CERTIFIED_INDEPENDENT", "fecha_subasta": "—",
         "run_and_drive": True, "oferta_recomendada": 6400, "mmr": 12500, "puntuacion": 84,
         "danos": ["Sin daños reportados"], "veredicto": "Recomendable",
         "pendientes": ["Carfax"]},
        {"anio": 2016, "marca": "Nissan", "modelo": "Rogue", "vin": "JN8AS5MT2DW540313",
         "lote": "15820307", "subasta": "IAAI", "titulo": "Título de Salvamento",
         "ubicacion": "Fairborn(OH)", "odometro": 132717, "llaves": "NO",
         "vendedor": "Geico Insurance", "fecha_subasta": "26 ago, 9:30 am",
         "run_and_drive": False, "oferta_recomendada": 2900, "mmr": 7200, "puntuacion": 58,
         "danos": ["Parte delantera", "Bolsas desplegadas", "Gomas desalineadas"],
         "veredicto": "Solo si acepta riesgos", "pendientes": ["Carfax", "sin llaves"]},
    ],
}


def autotest() -> int:
    out = os.path.join(tempfile.mkdtemp(), "Comparativo_demo.xlsx")
    construir(DEMO, out)
    from openpyxl import load_workbook
    wb = load_workbook(out)
    fallos = []

    def chk(n, o, e):
        ok = o == e
        print(f"  {'ok   ' if ok else 'FALLA'} {n}: {o!r}")
        if not ok:
            fallos.append(n)

    chk("hojas", wb.sheetnames,
        ["Comparativo", "Vehículo 1", "Vehículo 2", "Vehículo 3"])
    ws = wb["Comparativo"]
    chk("titulo", "COMPARATIVO" in str(ws["A1"].value), True)
    hay_total = any(ws.cell(r, 1).value == "COSTO TOTAL ESTIMADO"
                    for r in range(1, ws.max_row + 1))
    chk("fila de total presente", hay_total, True)
    chk("tres columnas de vehiculo", ws["D5"].value, "2016 Nissan Rogue")
    print(f"  ok    archivo: {out} ({os.path.getsize(out):,} bytes)")
    print(f"\n{'EXCEL OK' if not fallos else 'FALLOS: ' + ', '.join(fallos)}")
    return 0 if not fallos else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Excel comparativo de 3 vehículos")
    p.add_argument("--datos"); p.add_argument("--out", default="Comparativo.xlsx")
    p.add_argument("--autotest", action="store_true")
    a = p.parse_args()
    if a.autotest or not a.datos:
        return autotest()
    with open(a.datos, encoding="utf-8") as fh:
        print(f"-> {construir(json.load(fh), a.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
