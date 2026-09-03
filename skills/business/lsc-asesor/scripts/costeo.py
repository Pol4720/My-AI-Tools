#!/usr/bin/env python3
"""
Motor de costos de La Subasta Cubana.

Reconstruye el modelo del Excel oficial (Costo_Estimado_Total.xlsx) y resuelve
en las dos direcciones:

  directo   oferta  -> costo total
  reverso   presupuesto total -> oferta maxima

Uso:
  python3 costeo.py directo --oferta 5300 --subasta IAAI --titulo Salvage --estado FL
  python3 costeo.py reverso --presupuesto 10000 --estado FL --transporte 700
  python3 costeo.py --autotest
"""
from __future__ import annotations
import argparse, json, os, sys
from dataclasses import dataclass, field, asdict

AQUI = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(os.path.dirname(AQUI), "config")

NO_APLICA = "NO APLICA"

# --------------------------------------------------------------------------
# Tablas oficiales (hoja "Datos" del Excel + lasubastacubana.com/precios-tarifas)
# --------------------------------------------------------------------------

TARIFAS_LSC = [(6000, 599), (11000, 699), (16000, 799), (float("inf"), 899)]

TAX = {"FL": 7.0, "FUERA": 6.0}

TRASPASO_TITULO = 125
ENVIO_DOCS = {"FL": 20, "FUERA": 40}
CERT_TITULO_FL = 210
CERT_TITULO_FUERA_FINANCIADO = 500   # ver nota de discrepancia en references/modelo-costos.md
GESTION_TRANSPORTE = 120

CHAPA = {
    "renovacion": 426,      # Transferencia de Chapa con Renovacion
    "sin-renovacion": 300,  # Transferencia de Chapa sin Renovacion
    "nueva": 350,           # Nueva Chapa (emision de placa)
}

TITULOS_SIN_CIRCULACION = {"salvage", "junk"}
BORDES_ESCALON = [5999, 10999, 15999]


def _cargar(nombre, defecto):
    ruta = os.path.join(CONFIG, nombre)
    if os.path.exists(ruta):
        try:
            with open(ruta, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:                                  # pragma: no cover
            print(f"[aviso] no se pudo leer {nombre}: {exc}", file=sys.stderr)
    return defecto


# Tarifas de subasta: LSC compra como dealer, muy por debajo de las publicas.
# Punto de calibracion conocido: $400 sobre $15,200 en IAAI (~2.6%).
# ESTO ES UNA ESTIMACION. Calibrar config/tarifas_subasta.json con facturas reales.
TARIFAS_SUBASTA_DEFECTO = {
    "_nota": "ESTIMADO. Calibrar con facturas reales. Confirmar en la calculadora de LSC.",
    "_modelo": "porcentaje sobre la oferta, con minimo y maximo",
    "COPART": {"pct": 2.8, "min": 150, "max": 700},
    "IAAI":   {"pct": 2.6, "min": 150, "max": 700},
    "ACV":    {"pct": 2.5, "min": 150, "max": 700},
    "MANHEIM": {"pct": 2.5, "min": 150, "max": 700},
    "OPENLANE": {"pct": 2.5, "min": 150, "max": 700},
}

TRANSPORTE_DEFECTO = {
    "_nota": "ESTIMADO por distancia. La cotizacion real sale de SuperDispatch.",
    "tramos": [
        {"hasta_millas": 250,  "precio": 350},
        {"hasta_millas": 500,  "precio": 500},
        {"hasta_millas": 1000, "precio": 700},
        {"hasta_millas": 1800, "precio": 950},
        {"hasta_millas": 99999, "precio": 1300},
    ],
}


def normaliza_estado(estado: str) -> str:
    return "FL" if str(estado).strip().upper() in ("FL", "FLORIDA") else "FUERA"


def tarifa_lsc(oferta: float) -> int:
    for tope, tarifa in TARIFAS_LSC:
        if oferta < tope:
            return tarifa
    return TARIFAS_LSC[-1][1]


def tarifa_subasta(oferta: float, subasta: str) -> tuple[float, bool]:
    """Devuelve (tarifa, es_estimado)."""
    tabla = _cargar("tarifas_subasta.json", TARIFAS_SUBASTA_DEFECTO)
    cfg = tabla.get(str(subasta).strip().upper())
    if cfg is None:
        cfg = TARIFAS_SUBASTA_DEFECTO["COPART"]
    if "fijo" in cfg:
        return float(cfg["fijo"]), bool(cfg.get("estimado", False))
    bruto = oferta * float(cfg.get("pct", 2.6)) / 100.0
    bruto = max(float(cfg.get("min", 0)), min(float(cfg.get("max", 1e9)), bruto))
    return round(bruto, 2), True


def estimar_transporte(millas: float | None) -> tuple[float, bool]:
    if millas is None:
        return 0.0, True
    tabla = _cargar("transporte.json", TRANSPORTE_DEFECTO)
    for tramo in tabla["tramos"]:
        if millas <= tramo["hasta_millas"]:
            return float(tramo["precio"]), True
    return float(tabla["tramos"][-1]["precio"]), True


# --------------------------------------------------------------------------

@dataclass
class Escenario:
    oferta: float
    subasta: str = "COPART"
    titulo: str = "Título Limpio"
    estado: str = "FL"
    financiado: bool = False
    gestiona_chapa: bool = False
    tipo_chapa: str = "renovacion"
    contrata_transporte: bool = True
    pago_transportista: float | None = None
    tarifa_subasta_manual: float | None = None

    @property
    def ubic(self) -> str:
        return normaliza_estado(self.estado)

    @property
    def titulo_sin_circulacion(self) -> bool:
        t = self.titulo.strip().lower()
        return any(k in t for k in TITULOS_SIN_CIRCULACION)


def certificacion_titulo(e: Escenario):
    """Tabla de la hoja Chequeo. Ver nota sobre el bug de Datos!C14."""
    if e.financiado:
        if e.titulo_sin_circulacion:
            return NO_APLICA
        return CERT_TITULO_FL if e.ubic == "FL" else CERT_TITULO_FUERA_FINANCIADO
    return CERT_TITULO_FL if e.ubic == "FL" else NO_APLICA


def transferencia_chapa(e: Escenario):
    if e.titulo_sin_circulacion:
        return NO_APLICA          # no se tramita chapa a un carro que no puede circular
    if e.financiado:
        return CHAPA[e.tipo_chapa]
    if e.ubic == "FUERA" or not e.gestiona_chapa:
        return NO_APLICA
    return CHAPA[e.tipo_chapa]


def _num(v):
    return 0.0 if v == NO_APLICA else float(v)


def calcular(e: Escenario) -> dict:
    t_lsc = tarifa_lsc(e.oferta)
    if e.tarifa_subasta_manual is not None:
        t_sub, sub_estimado = float(e.tarifa_subasta_manual), False
    else:
        t_sub, sub_estimado = tarifa_subasta(e.oferta, e.subasta)

    tasa = TAX["FL"] if e.ubic == "FL" else TAX["FUERA"]
    impuesto = round((e.oferta + t_sub + t_lsc) * tasa / 100.0, 2)

    envio = ENVIO_DOCS[e.ubic]
    cert = certificacion_titulo(e)
    chapa = transferencia_chapa(e)
    titulacion = envio + TRASPASO_TITULO + _num(cert) + _num(chapa)

    if e.contrata_transporte:
        pago = e.pago_transportista if e.pago_transportista is not None else 0.0
        transporte = GESTION_TRANSPORTE + pago
        transporte_detalle = {"coordinacion": GESTION_TRANSPORTE, "transportista": pago}
    else:
        transporte = 0.0
        transporte_detalle = {"coordinacion": NO_APLICA, "transportista": NO_APLICA}

    total = round(e.oferta + t_sub + t_lsc + impuesto + titulacion + transporte, 2)

    return {
        "escenario": asdict(e),
        "subasta": {
            "oferta_maxima": e.oferta,
            "tarifa_subasta": t_sub,
            "tarifa_subasta_estimada": sub_estimado,
            "tarifa_lsc": t_lsc,
        },
        "impuesto": {"tasa_pct": tasa, "monto": impuesto},
        "titulacion": {
            "traspaso_titulo": TRASPASO_TITULO,
            "envio_documentos": envio,
            "certificacion_titulo": cert,
            "transferencia_chapa": chapa,
            "subtotal": round(titulacion, 2),
        },
        "transporte": {**transporte_detalle, "subtotal": round(transporte, 2)},
        "total": total,
        "deposito_seguridad_minimo": round(total * 0.15, 2),
        "avisos": _avisos(e, sub_estimado),
    }


def _avisos(e: Escenario, sub_estimado: bool) -> list[str]:
    av = []
    if sub_estimado:
        av.append("La tarifa de subasta es ESTIMADA. Confirmar en la calculadora de LSC "
                  "antes de dar una cifra final al cliente.")
    if e.contrata_transporte and not e.pago_transportista:
        av.append("Falta el pago al transportista: el total no incluye el traslado. "
                  "Cotizar en SuperDispatch.")
    if e.titulo_sin_circulacion:
        av.append("Titulo salvage/junk: solo se transfiere el titulo. La registracion la "
                  "completa el cliente en la Tag Agency tras pasar inspeccion.")
    if e.ubic == "FUERA" and not e.financiado:
        av.append("Cliente fuera de Florida sin financiamiento: LSC no tramita la chapa ni "
                  "certifica el titulo; el cliente hace ese tramite por su cuenta.")
    av.append("No incluye costos oficiales del DMV, cargos de Tag Agency, verificacion de VIN, "
              "almacenaje en la subasta, reparaciones ni seguro.")
    return av


def resolver_reverso(presupuesto: float, base: Escenario, paso: int = 25) -> dict:
    """Oferta maxima cuyo costo total cabe en el presupuesto."""
    lo, hi = 0, int(presupuesto) + 1000
    mejor = None
    while lo <= hi:
        mid = ((lo + hi) // 2 // paso) * paso
        if mid <= 0:
            break
        e = Escenario(**{**asdict(base), "oferta": float(mid)})
        r = calcular(e)
        if r["total"] <= presupuesto:
            mejor, lo = r, mid + paso
        else:
            hi = mid - paso

    if mejor is None:
        e = Escenario(**{**asdict(base), "oferta": 0.0})
        piso = calcular(e)
        return {
            "viable": False,
            "presupuesto": presupuesto,
            "costo_fijo_minimo": piso["total"],
            "faltante": round(piso["total"] - presupuesto, 2),
            "mensaje": ("El presupuesto no cubre ni las tarifas fijas. Se necesitan al menos "
                        f"${piso['total']:,.2f} antes de poner un solo dolar en el carro."),
            "avisos": piso["avisos"],
        }

    oferta = mejor["subasta"]["oferta_maxima"]
    resultado = {
        "viable": True,
        "presupuesto": presupuesto,
        "oferta_maxima": oferta,
        "detalle": mejor,
        "holgura": round(presupuesto - mejor["total"], 2),
        "avisos": mejor["avisos"],
    }

    # Oportunidad de escalon: bajar al borde puede ahorrar $100 de tarifa + impuesto
    for borde in BORDES_ESCALON:
        if borde < oferta <= borde + 150:
            alt = calcular(Escenario(**{**asdict(base), "oferta": float(borde)}))
            ahorro = round(mejor["total"] - alt["total"] - (oferta - borde), 2)
            if ahorro > 0:
                resultado["oportunidad_escalon"] = {
                    "oferta_alternativa": borde,
                    "ahorro_neto": ahorro,
                    "mensaje": (f"Ofertar ${borde:,} en vez de ${oferta:,.0f} baja la tarifa LSC un "
                                f"escalon. Ahorro neto ~${ahorro:,.2f}."),
                }
            break
    return resultado


# --------------------------------------------------------------------------

def _fmt(v):
    return v if isinstance(v, str) else f"${v:,.2f}"


def imprimir_directo(r: dict) -> None:
    s, t, tr = r["subasta"], r["titulacion"], r["transporte"]
    est = "  [ESTIMADO]" if s["tarifa_subasta_estimada"] else ""
    print("\nCOSTO TOTAL APROXIMADO DE LA OFERTA")
    print("=" * 58)
    print("1- Costos de una compra en subasta")
    print(f"   Oferta maxima a realizar en subasta   {_fmt(s['oferta_maxima']):>16}")
    print(f"   Tarifa de {r['escenario']['subasta']:<27}{_fmt(s['tarifa_subasta']):>16}{est}")
    print(f"   Tarifa de La Subasta Cubana           {_fmt(s['tarifa_lsc']):>16}")
    print(f"2- Impuesto ({r['impuesto']['tasa_pct']:.0f}%)                    "
          f"{_fmt(r['impuesto']['monto']):>16}")
    print("3- Titulacion")
    print(f"   Traspaso del titulo                   {_fmt(t['traspaso_titulo']):>16}")
    print(f"   Envio de documentos                   {_fmt(t['envio_documentos']):>16}")
    print(f"   Certificacion de titulo               {_fmt(t['certificacion_titulo']):>16}")
    print(f"   Transferencia de chapa                {_fmt(t['transferencia_chapa']):>16}")
    print("4- Transporte")
    print(f"   Coordinacion                          {_fmt(tr['coordinacion']):>16}")
    print(f"   Pago estimado al transportista        {_fmt(tr['transportista']):>16}")
    print("-" * 58)
    print(f"5- COSTO TOTAL ESTIMADO                  {_fmt(r['total']):>16}")
    print(f"   Deposito de seguridad minimo (15%)    "
          f"{_fmt(r['deposito_seguridad_minimo']):>16}")
    print("\nAVISOS")
    for a in r["avisos"]:
        print(f"  - {a}")
    print()


def imprimir_reverso(r: dict) -> None:
    if not r["viable"]:
        print(f"\nNO VIABLE\n{r['mensaje']}\n")
        return
    print(f"\nPRESUPUESTO TOTAL DEL CLIENTE   {_fmt(r['presupuesto'])}")
    print(f"OFERTA MAXIMA EN SUBASTA        {_fmt(r['oferta_maxima'])}")
    print(f"Holgura                         {_fmt(r['holgura'])}")
    if "oportunidad_escalon" in r:
        print(f"\n>> {r['oportunidad_escalon']['mensaje']}")
    imprimir_directo(r["detalle"])


def autotest() -> int:
    fallos = []

    def chk(nombre, obtenido, esperado, tol=0.02):
        ok = abs(obtenido - esperado) <= tol if isinstance(esperado, float) else obtenido == esperado
        print(f"  {'ok ' if ok else 'FALLA'} {nombre}: {obtenido} (esperado {esperado})")
        if not ok:
            fallos.append(nombre)

    print("Caso oficial del Excel: IAAI, Salvage, FL, oferta 15200, tarifa subasta 400,")
    print("transportista 770, chapa con renovacion, sin financiamiento, gestiona chapa.")
    e = Escenario(oferta=15200, subasta="IAAI", titulo="Salvage", estado="FL",
                  financiado=False, gestiona_chapa=True, tipo_chapa="renovacion",
                  contrata_transporte=True, pago_transportista=770,
                  tarifa_subasta_manual=400)
    r = calcular(e)
    chk("tarifa LSC", r["subasta"]["tarifa_lsc"], 799)
    chk("impuesto", r["impuesto"]["monto"], 1147.93)
    chk("envio docs", r["titulacion"]["envio_documentos"], 20)
    chk("certificacion", r["titulacion"]["certificacion_titulo"], 210)
    chk("chapa (salvage -> NO APLICA)", r["titulacion"]["transferencia_chapa"], NO_APLICA)
    chk("subtotal titulacion", r["titulacion"]["subtotal"], 355.0)
    chk("subtotal transporte", r["transporte"]["subtotal"], 890.0)
    chk("TOTAL", r["total"], 18791.93)

    print("\nEscalones de la tarifa LSC")
    for oferta, esperado in [(5999, 599), (6000, 699), (10999, 699), (11000, 799),
                             (15999, 799), (16000, 899)]:
        chk(f"oferta {oferta}", tarifa_lsc(oferta), esperado)

    print("\nCoherencia del reverso")
    base = Escenario(oferta=0, subasta="COPART", titulo="Título Limpio", estado="FL",
                     contrata_transporte=True, pago_transportista=700)
    rv = resolver_reverso(10000, base)
    if rv["viable"]:
        chk("total <= presupuesto", rv["detalle"]["total"] <= 10000, True)
        print(f"  -> $10,000 totales = ${rv['oferta_maxima']:,.0f} de puja")
    else:
        fallos.append("reverso no viable con 10000")

    print(f"\n{'TODO OK' if not fallos else 'FALLOS: ' + ', '.join(fallos)}")
    return 0 if not fallos else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Motor de costos de La Subasta Cubana")
    p.add_argument("--autotest", action="store_true", help="verifica el modelo contra el Excel")
    sub = p.add_subparsers(dest="modo")

    def comunes(sp):
        sp.add_argument("--subasta", default="COPART",
                        choices=["COPART", "IAAI", "ACV", "MANHEIM", "OPENLANE"])
        sp.add_argument("--titulo", default="Título Limpio")
        sp.add_argument("--estado", default="FL", help="estado del CLIENTE (FL o cualquier otro)")
        sp.add_argument("--financiado", action="store_true")
        sp.add_argument("--chapa", dest="tipo_chapa", default=None,
                        choices=list(CHAPA), help="si se indica, LSC gestiona la chapa")
        sp.add_argument("--sin-transporte", action="store_true")
        sp.add_argument("--transporte", type=float, default=None,
                        help="pago al transportista en USD")
        sp.add_argument("--millas", type=float, default=None,
                        help="millas hasta el cliente; estima el transporte si no das --transporte")
        sp.add_argument("--tarifa-subasta", type=float, default=None,
                        help="tarifa real de la subasta (evita la estimacion)")
        sp.add_argument("--json", action="store_true")

    d = sub.add_parser("directo"); d.add_argument("--oferta", type=float, required=True); comunes(d)
    v = sub.add_parser("reverso"); v.add_argument("--presupuesto", type=float, required=True); comunes(v)

    a = p.parse_args()
    if a.autotest or a.modo is None:
        return autotest()

    transporte = a.transporte
    if transporte is None and a.millas is not None:
        transporte, _ = estimar_transporte(a.millas)

    base = Escenario(
        oferta=0.0, subasta=a.subasta, titulo=a.titulo, estado=a.estado,
        financiado=a.financiado, gestiona_chapa=a.tipo_chapa is not None,
        tipo_chapa=a.tipo_chapa or "renovacion",
        contrata_transporte=not a.sin_transporte, pago_transportista=transporte,
        tarifa_subasta_manual=a.tarifa_subasta,
    )

    if a.modo == "directo":
        r = calcular(Escenario(**{**asdict(base), "oferta": a.oferta}))
        print(json.dumps(r, indent=2, ensure_ascii=False)) if a.json else imprimir_directo(r)
    else:
        r = resolver_reverso(a.presupuesto, base)
        print(json.dumps(r, indent=2, ensure_ascii=False)) if a.json else imprimir_reverso(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
