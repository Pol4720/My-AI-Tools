# Instalación y primer arranque

## 1. Poner la skill donde Claude Code la vea

```bash
mkdir -p ~/.claude/skills
cp -r lsc-asesor ~/.claude/skills/
```

O descomprime el `.skill` que viene con este paquete.

## 2. Dependencias

```bash
pip install requests beautifulsoup4 openpyxl pillow playwright
python -m playwright install chromium     # para generar los PDF y las tarjetas
```

`playwright` es opcional: si no está, el generador cae a `wkhtmltopdf`, y si tampoco está,
deja el HTML listo para imprimir a PDF desde el navegador.

## 3. Verificar que todo funciona

```bash
cd ~/.claude/skills/lsc-asesor
python3 scripts/costeo.py --autotest             # debe dar TODO OK y cuadrar $18,791.93
python3 scripts/buscar_inventario.py --autotest  # debe dar PARSER OK
python3 scripts/generar_excel.py --autotest      # debe dar EXCEL OK
python3 scripts/render_pdf.py --autotest         # debe dar RENDER OK
```

## 4. Prueba de humo contra la web real

**Este paso importa.** Los autotests validan la lógica sin red; esto valida que el parser sigue
alineado con el sitio.

```bash
python3 scripts/buscar_inventario.py --marca toyota --modelo camry --limite 5
```

Abre lasubastacubana.com/inventory/search/toyota-camry en el navegador y compara: los VIN, los
precios y las fechas tienen que coincidir. Si no coinciden, avísame y ajusto el parser.

Después:
```bash
python3 scripts/buscar_inventario.py --descubrir
```
Escribe `config/filtros_descubiertos.json`. Identifica ahí los campos de precio, año, estado y
subasta, y cópialos a `config/filtros.json`. Con eso el filtrado pasa a hacerse en el servidor y
las búsquedas se vuelven mucho más rápidas.

## 5. Calibrar

Dos archivos de `config/` mejoran con el uso y valen oro:

- **`tarifas_subasta.json`** — cada factura real de Copart o IAAI que le metas hace más exactos
  todos los presupuestos. Hoy está calibrado con un solo punto ($400 sobre $15,200 en IAAI).
- **`transporte.json`** — cada transporte cerrado ajusta el tramo correspondiente.

Y un tercero que define cómo la skill juzga los vehículos:

- **`references/reglas-compra.md`**, sección F. Ahí van tus reglas propias: año mínimo, millaje
  máximo, marcas o motores que evitas, estados problemáticos. Todo lo que escribas ahí, la skill
  lo aplica en la puntuación.

## 6. SuperDispatch (opcional)

Si LSC activa la Pricing Insights API:
```bash
export SUPERDISPATCH_API_KEY="..."
```
El estimado por distancia se reemplaza por precio real de mercado de la ruta. Sin la clave, la
cotización real la sigues sacando del TMS de SuperDispatch y se la pasas al script con
`--transporte`.
