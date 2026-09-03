# Búsqueda en el inventario

## Por qué el inventario de LSC y no Copart directo

lasubastacubana.com agrega **Copart, IAAI, ACV, Manheim y OpenLane** en un solo índice, se renderiza
en el servidor (no necesita JavaScript), no pide credenciales y expone más datos que la propia ficha
pública de Copart. Volumen típico: ~14.000 lotes Copart, ~3.900 ACV, ~230 IAAI, ~10 Manheim, con
~8.350 marcados **Cómpralo Ahora**.

Copart e IAAI directos exigen login y bloquean automatización. bid.cars es historial de ventas
pasadas, útil para calibrar precios pero no para inventario vivo. Manheim y ACV como subastas
privadas aparecen aquí con datos pobres (Manheim casi sin precios) — para esas, el asesor tiene que
pegar los datos desde su portal de dealer.

## Qué devuelve cada lote

**Listado:** VIN · nº de lote · tipo de título · ubicación (ciudad+estado) · odómetro · vendedor y
tipo de vendedor · daño primario · **Compra Inmediata** · oferta actual · **Oferta Máxima Sugerida** ·
**fecha y hora de subasta** · tiempo restante · logo de la subasta · foto principal.

**Ficha del lote** (`/inventory-vdp/vin-{VIN}` o `/inventory-vdp/lot-{LOTE}`), añade:
daño secundario · costo estimado de reparación · precio de mercado estimado · tracción · tipo de
carrocería · motor · transmisión · combustible · color · **llaves (YES/NO/EXM)** · versión/trim ·
carril y artículo · subasta específica · última actualización · designación **Run & Drive** ·
**y las URLs de todas las fotos del lote en alta resolución**.

Las fotos son lo más valioso: se descargan sin autenticación y se pueden mirar para evaluar daño
real, bolsas desplegadas, tablero, gomas, bajos y cristales.

## Sintaxis de URL

**Confirmadas por prueba directa:**

```
/inventory?order[default]=asc          listado base
/inventory/make-toyota                 por marca (slug en minúscula, guiones)
/inventory/search/toyota-camry         marca+modelo
/inventory/damage-front-end            por daño primario
/inventory-vdp/vin-{VIN}               ficha por VIN
/inventory-vdp/lot-{LOTE}              ficha por lote
/dealer/inventory                      inventario propio de LSC
```

Slugs de daño verificados: `front-end`, `rear-end`, `side`, `minor-dent-scratches`, `mechanical`,
`normal-wear`, `water-flood`, `all-over`, `rollover`, `hail`.

**Facetas presentes en el panel de filtros pero cuyos nombres de parámetro no están confirmados:**
subasta, fecha de subasta desde/hasta, año desde/hasta, rango de precio (distinguiendo Compra
Inmediata de Oferta Actual), tipo de título, estado, odómetro, cilindros, tipo de vehículo, tipo de
vendedor, y el flag Cómpralo Ahora.

Para resolverlos de una vez:
```bash
python3 scripts/buscar_inventario.py --descubrir
```
Descarga el HTML crudo, extrae los `name=` de todos los inputs y selects del panel de filtros, y
escribe el mapeo en `config/filtros.json`. Corre esto **una vez** al instalar la skill y otra vez
cada vez que el parser empiece a fallar. Mientras `config/filtros.json` no exista, el script filtra
por ruta y hace el resto del filtrado en local sobre los resultados descargados — más lento pero
funciona igual.

## Cómo construir un barrido

**Nunca una sola búsqueda.** Un asesor mira 3 carros; la skill debe mirar 200. Arma de 4 a 8
consultas que crucen el espacio de solución:

1. **Por marca del segmento** — si el cliente quiere un SUV mediano confiable: RAV4, CR-V, Rogue,
   Equinox, Escape, Tucson. Una consulta por marca.
2. **Con y sin Buy Now** — el Buy Now es la compra segura (precio cerrado, sin guerra de pujas),
   pero el subastado sale más barato. Trae ambos y deja que la puntuación decida.
3. **Salvage y título limpio por separado** — el salvage con daño frontal leve suele ser la mejor
   relación precio/valor; el título limpio da tranquilidad. Son dos conversaciones distintas.
4. **Cercano y lejano** — un lote en Florida ahorra $500-800 de transporte respecto a uno en
   California. Un carro $600 más barato en Oregón no es más barato.

Consolida, deduplica por VIN, y sigue con el filtro duro de `reglas-compra.md`.

## Interpretación de campos

**Oferta Máxima Sugerida** — la sugerencia del propio sistema de LSC. Buen punto de partida, no
evangelio. Cuando existe y es igual al Buy Now, significa que el sistema recomienda cerrar directo.

**Precio de Mercado (Estimado)** — casi siempre viene vacío (`-`). No lo cites al cliente si no
tiene valor. Para valor de mercado real usa MMR de Manheim, que el asesor consulta aparte.

**Vendedor / Tipo Vendedor** — señal fuerte:
- `Compañía de Seguros` (Geico, Progressive, State Farm) → pérdida total por siniestro. El daño está
  documentado y suele ser lo que se ve. Predecible.
- `FRANCHISE` / `ACV_CERTIFIED_INDEPENDENT` → trade-in de concesionario. Normalmente título limpio,
  sin siniestro, pero puede traer problema mecánico que hizo al dealer soltarlo.
- `Compañía de Alquiler` → uso intensivo, mantenimiento al día, kilometraje alto.
- `Desconocido` / `No especificado` → menos información, más riesgo. Exige más peso a las fotos.

**Llaves** — `YES` bien, `NO` es un costo extra real (llave con transponder son $200-400) y a veces
señal de robo recuperado. `EXM` significa que hay que examinarlo.

**Fecha de Subasta** vacía → normalmente ACV o Manheim, que operan distinto. Verifica en la ficha.

**Título "Limpio - Recuperación de Robo"** — es título limpio pero el carro fue robado y apareció.
Riesgo: piezas faltantes, daño de encendido forzado. Mirar fotos del interior con lupa.

## Buenas prácticas de la herramienta

- El HTML trae el panel de facetas completo (cientos de marcas y modelos) en cada página. Usa
  `text_content_token_limit` al hacer `web_fetch` manual, o el script, que ya lo recorta.
- El listado pagina de ~10 en 10. Para barridos grandes usa el script, no `web_fetch` a mano.
- Los precios y fechas cambian a diario. **Nunca reutilices lotes de una sesión anterior** como si
  fueran vigentes; revalida antes de presentárselos al cliente.
- Si un lote desaparece del inventario entre la búsqueda y la videollamada, se vendió o se retiró.
  Ten siempre un cuarto candidato de reserva.
