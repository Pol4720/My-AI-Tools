# Modelo de costos LSC

Reconstruido de `Costo_Estimado_Total.xlsx` (hojas `Asesor`, `Chequeo`, `Datos`) y verificado contra
`lasubastacubana.com/precios-tarifas`. Implementado en `scripts/costeo.py`.

## Fórmula maestra

```
TOTAL = oferta
      + tarifa_subasta          (Copart / IAAI / ACV / Manheim)
      + tarifa_LSC              (escalonada)
      + impuesto                (sobre los tres anteriores)
      + costo_titulacion
      + costo_transporte
```

## 1. Tarifa LSC (servicio de compra)

Escalón según el **precio final de compra** (la oferta ganadora, no el total):

| Rango | Tarifa |
|---|---|
| $0 – $5,999 | $599 |
| $6,000 – $10,999 | $699 |
| $11,000 – $15,999 | $799 |
| $16,000 + | $899 |

Comparación estricta: `< 6000 → 599`. Una oferta de $5,999 paga $599; de $6,000 paga $699.

> **Punto de quiebre explotable:** ofertar $5,999 en vez de $6,050 ahorra $100 de tarifa + ~$7 de
> impuesto. Vale la pena avisarle al cliente cuando la puja se acerca a un borde de escalón.

Clientes mayoristas tienen tarifas preferenciales — no están publicadas, pregúntale al asesor.

## 2. Tarifa de la subasta — ESTIMADA, hay que confirmarla

El único número que el modelo no puede derivar. LSC compra como dealer con tarifas muy por debajo
de las públicas: el Excel oficial usa **$400 sobre una compra de $15,200 en IAAI (~2,6%)**, mientras
que un comprador público pagaría más de $1,500 por esa misma compra.

Por eso `costeo.py` lee `config/tarifas_subasta.json`, que el asesor debe ir calibrando con facturas
reales. El resultado **siempre se marca `[ESTIMADO]`**.

**Regla operativa:** antes de dar una cifra final al cliente, confirma en la calculadora de
lasubastacubana.com/estimar-precios. Es lo que el propio Excel indica ("Tomar valor desde la
calculadora de LSC"). No presentes una tarifa de subasta estimada como si fuera definitiva.

## 3. Impuesto

```
impuesto = (oferta + tarifa_subasta + tarifa_LSC) × tasa
tasa = 7% si el cliente vive en Florida, 6% si vive fuera
```

Ojo: el impuesto se aplica **sobre las tarifas también**, no solo sobre la oferta. Se olvida fácil y
son cientos de dólares.

## 4. Titulación

```
costo_titulacion = envío_docs + traspaso_título + certificación + transferencia_chapa
```

**Traspaso de título:** $125 siempre. Cubre preparación, revisión, notarización y trámite. El título
queda electrónico en el DMV; la copia impresa la pide el cliente en una Tag Agency.

**Envío de documentos:** $20 si el cliente está en Florida (a la Agencia de Chapas), $40 si está
fuera (FedEx).

**Certificación de título en el DMV:**

| Ubicación | Financiado | Título | Certificación |
|---|---|---|---|
| Florida | cualquiera | TL / Rebuilt | $210 |
| Florida | No | Salvage / Junk | $210 |
| Florida | Sí | Salvage / Junk | NO APLICA |
| Fuera FL | Sí | TL / Rebuilt | $500 |
| Fuera FL | Sí | Salvage / Junk | NO APLICA |
| Fuera FL | No | cualquiera | NO APLICA |

> ⚠️ **Bug conocido en el Excel oficial.** La celda `Asesor!A19` referencia
> `CertificaciónTítuloNoFl = Datos!C14`, que contiene el texto `"NO APLICA"`. Pero la hoja `Chequeo`
> (columna R, que es la tabla de resultados esperados) dice que Fuera-de-Florida + Financiado debe
> costar **$500**. La fórmula nunca devolverá 500. `costeo.py` implementa la intención de `Chequeo`
> ($500) porque es la tabla de casos de prueba. **Confírmalo con la oficina** y, si el $500 es
> correcto, hay que arreglar `Datos!C14` en el Excel de la empresa.

**Transferencia de chapa** (solo si aplica):

| Tipo | Costo |
|---|---|
| Transferencia con renovación | $426 |
| Transferencia sin renovación | $300 |
| Nueva chapa (emisión de placa) | $350 |

Aplica cuando:
- **Financiado:** siempre, salvo título Salvage o Junk.
- **No financiado:** solo si el cliente está en Florida, pidió que LSC le gestione la chapa, y el
  título no es Salvage ni Junk.

Razón de las exclusiones: no se puede tramitar chapa para un vehículo que todavía no puede circular
(un salvage necesita pasar inspección primero), y fuera de Florida sin financiamiento el cliente
hace el trámite por su cuenta.

## 5. Transporte

Si el cliente contrata el servicio:
```
costo_transporte = $120 (coordinación LSC) + pago directo al transportista
```

El pago al transportista **no pasa por LSC** — el cliente le paga directo al chofer cuando recibe el
carro. LSC solo coordina: cotiza con varias compañías con seguro activo, negocia, y envía datos del
transportista y póliza.

**De dónde sale la cifra del transportista:** SuperDispatch. Ver `scripts/costeo.py --ayuda-transporte`.
- Si LSC tiene la **Pricing Insights API** activada, exporta `SUPERDISPATCH_API_KEY` y el script
  consulta el precio real de mercado de la ruta.
- Si no, el script estima por distancia con la tabla de `config/transporte.json`, marcada
  `[ESTIMADO]`. La cotización real la saca el asesor del TMS de SuperDispatch.

**Aviso obligatorio al cliente** (`precios-tarifas`): si la subasta cobra almacenaje al retirar, el
transportista lo paga por adelantado y el cliente lo reembolsa al recibir el vehículo.

## 6. Depósito de seguridad (DS)

Mínimo **15% del precio total** de la operación (contrato 6.6). Puede ser mayor si hay riesgo
elevado: transporte largo, tarifas de subasta altas, almacenaje, particularidades de título.

**El DS no es reembolsable** si el vehículo se adjudica y el cliente decide no proceder (6.8). Si el
vehículo *no* se adjudica y no hay saldo pendiente, se reembolsa menos fees de procesamiento y
costos de preparación ya incurridos (6.5).

Formas de pago del DS y de la asesoría: efectivo, Zelle, cashier's check, wire transfer, money order,
y link de tarjeta de crédito.

> **Zelle — instrucción al cliente (de `Lin_vía_transferencias.docx`):**
> Teléfono (786) 258-7334, nombre **ODD CAR INVESTMENTS LLC**.
> Guardar el contacto solo con ese nombre. No llamar al número.
> **Nunca escribir "Cuba", "Remesa", "Envío" ni similares** en el contacto o en la descripción del
> pago — hace que el banco congele la transferencia.

## 7. Costos que NO cubre LSC

Decirlos siempre, es el valor "transparencia" de la empresa y evita reclamos:
- Costos oficiales del DMV (titulación y registración)
- Cargos de la Agencia de Chapas
- Impuestos estatales adicionales
- Costos administrativos del DMV
- Envíos FedEx u otro servicio
- Verificación de VIN
- **Almacenaje en la subasta** — 100% del cliente, siempre, aunque LSC coordine transporte
- Reparaciones, inspección de salvage, seguro

## 8. Solución inversa (presupuesto → oferta máxima)

El cliente casi siempre dice un presupuesto **total**. Hay que convertirlo a oferta máxima, y no es
una resta simple: la tarifa LSC es escalonada y el impuesto se aplica sobre ella.

`costeo.py reverso` busca la oferta más alta cuyo total quepa en el presupuesto, respetando los
escalones. Redondea hacia abajo al múltiplo de $25 y, si la oferta cae dentro de $150 por encima de
un borde de escalón ($5,999 / $10,999 / $15,999), reporta también la opción de bajar al borde y
señala el ahorro.

### Ejemplo trabajado

Cliente en Florida, $10,000 totales, quiere transporte (~$700), título limpio, sin financiamiento,
sin gestión de chapa:

```
oferta máxima            $7,000
tarifa subasta (est.)      $260
tarifa LSC                 $699
impuesto 7%                $558
titulación (125+20+210)    $355
transporte (120+700)       $820
─────────────────────────────────
total                    $9,692     ✓ cabe en $10,000
```

La conversación con el cliente es: *"tus $10,000 son $7,000 de puja."* Ese es el número que hay que
darle temprano, porque define todo lo demás y evita 15 días de expectativas rotas.
