# Entregables

## Marca

Extraída del material oficial de LSC.

```css
--lsc-navy:        #02142A   /* azul marino del panel y del isotipo */
--lsc-navy-2:      #0D2440   /* variante para bloques secundarios */
--lsc-red:         #B60000   /* rojo del wordmark SUBASTA CUBANA */
--lsc-red-bright:  #D01019   /* acentos, líneas, etiquetas */
--lsc-bg:          #F0F0F0   /* fondo claro */
--lsc-white:       #FFFFFF
```

Tipografía: sans-serif condensada y de peso alto para titulares (el wordmark es una grotesca
condensada bold), sans normal para texto. En HTML: `Oswald`/`Archivo Narrow` para titulares con
fallback a `Impact, 'Arial Narrow', sans-serif`; `Inter`/`Source Sans` para cuerpo.

Assets en `assets/`: `logo-lsc.png` (marca completa), `logo-lsc-full.png` (con tagline
"TU CONFIANZA, NUESTRA PRIORIDAD"), `isotipo-lsc.png` (mazo + carro, para sellos y marcas de agua).

Elementos de composición del material oficial que conviene mantener: paneles azul marino con
esquinas biseladas, líneas rojas finas como separador bajo los titulares, y la banda inferior de
valores (TRANSPARENCIA · CONFIANZA · EXPERIENCIA · RESULTADOS).

Datos de pie: ODD Car Investments LLC · 1475 Palm Ave, Hialeah, FL 33010 · 786-600-2222 ·
lasubastacubana.com

---

## Para el cliente

Tono: claro, directo, sin jerga. El cliente cubano promedio no conoce la diferencia entre salvage y
rebuilt — explícala en una línea cuando aparezca. Nada de lenguaje interno ("shortlist", "score",
"lote puntuado 82"). Nada de mencionar herramientas de trabajo internas.

### 1. Diagnóstico de Viabilidad (pre-pago, 1 página)

```
[logo]
DIAGNÓSTICO DE VIABILIDAD          [nombre del cliente] · [fecha]

TU PRESUPUESTO                     $10,000
LO QUE PUEDES OFERTAR EN SUBASTA   $7,000
   porque además del carro hay que cubrir:
   tarifa de subasta · tarifa de gestión · impuesto · titulación · transporte

VEREDICTO                          VIABLE
[dos o tres líneas explicando qué alcanza y qué no]

LO QUE HAY HOY EN ESE RANGO
[3 vehículos reales con foto, año/marca/modelo, título, millaje, precio]

[banda de valores]  [pie]
```

Si el veredicto es NO VIABLE, se sustituye el bloque de vehículos por **alternativas concretas**:
con cuánto sí alcanza, qué segmento sí entra hoy, o qué esperar. Nunca dejar al cliente sin salida.

### 2. Reporte de Selección (post-pago, el entregable principal)

Portada + una página por vehículo + página de comparación.

Por vehículo:
- Foto principal grande + 3 secundarias
- Año, marca, modelo, versión, VIN, millaje, ubicación
- Tipo de título, en una línea de español llano
- Daño principal, descrito con lo que se ve en las fotos
- **Costo total desglosado** (la tabla de `modelo-costos.md`)
- **Oferta máxima recomendada** y fecha/hora exacta de la subasta
- Tres razones a favor y las advertencias que correspondan, sin suavizar

Página de comparación: los 3 lado a lado, con costo total, y **una recomendación clara del asesor**.
Un cliente que recibe 3 opciones sin recomendación se paraliza.

### 3. Tarjetas de WhatsApp

Imagen cuadrada 1080×1080 por vehículo: foto, año/marca/modelo, millaje, título, costo total
estimado, fecha de subasta, logo. Es lo que el cliente reenvía a su familia — que se entienda sola.

---

## Para el asesor (interno)

Tono crudo y directo. Aquí sí van los números, las dudas y los riesgos sin filtro.

### 4. Briefing de videollamada

```
CLIENTE      [nombre] · sesión N de 5 · día N de 15
PRESUPUESTO  $X total → $Y de puja
OBJETIVO DE ESTA SESIÓN

LOS 3 QUE VAS A PRESENTAR
  1. [vehículo] — puntuación X/100 — costo total $X — subasta [fecha]
     A FAVOR:     ...
     EN CONTRA:   ...
     PENDIENTE:   Carfax / foto de bajos / ...

OBJECIONES PROBABLES
  "¿Por qué tan caro si el carro sale en $5,000?"  → [respuesta]
  "¿Y si llega con problemas?"                     → [respuesta]
  "¿Puedo recuperar el depósito?"                  → [respuesta: 6.5 vs 6.8]

RIESGOS QUE TIENES QUE DECIR EN VOZ ALTA
  [los que exigen aceptación del cliente]

PRÓXIMO PASO CONCRETO
```

### 5. Checklist llenado

Formato de `references/checklist.md`, con el bloque de resumen de completitud arriba.

### 6. Excel comparativo

`scripts/generar_excel.py`. Estructura: 3 vehículos con sus 3 daños principales, valor MMR,
ahorro y rentabilidad frente al costo total, desglose de impuestos y costos, e imágenes.

---

## Sobre la mención de herramientas

Los entregables al cliente salen con marca LSC y sin referencias a procesos internos, igual que
cualquier documento de trabajo de la empresa. Lo que no se hace nunca es **afirmar una inspección
que no ocurrió**: no se escribe "nuestro equipo revisó el vehículo" si nadie lo revisó
físicamente. La fórmula correcta es "análisis del historial, la ficha de subasta y las imágenes del
lote", que es exactamente lo que la empresa vende en su página de tarifas y es verdad.
