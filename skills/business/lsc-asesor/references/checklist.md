# Checklist Copart / IAAI

Los 30 puntos del formulario oficial, cada uno con su **fuente de verdad**. Llena todo lo que la
fuente permita. Lo que no, se marca `[PENDIENTE — falta X]`. Nunca se rellena a ojo.

Leyenda:
`[FICHA]` deducible de la ficha del lote · `[FOTO]` requiere mirar las imágenes ·
`[CARFAX]` requiere el reporte · `[ASESOR]` requiere juicio o confirmación humana ·
`[CLIENTE]` requiere respuesta del cliente

## Puerta de entrada

| # | Punto | Fuente |
|---|---|---|
| 0 | **¿El cliente pagó asesoría?** Si NO → no se continúa el checklist. El cliente compra bajo su propia responsabilidad. | `[ASESOR]` |

## Bloqueantes

| # | Punto | Fuente |
|---|---|---|
| 1 | ¿Título pendiente o sin duplicado posible? → no se compra | `[FICHA]` + `[ASESOR]` |
| 2 | ¿El DS es adecuado para la oferta? (≥15% del total) | calculado |
| 3 | Si es Copart, ¿el vehículo está en la yarda? | `[FICHA]` + `[ASESOR]` |
| 4 | Si es Buy Now en Copart, ¿el cliente confirma pago en 24h? | `[CLIENTE]` |
| 5 | ¿Tiene fecha de venta? | `[FICHA]` |
| 6 | ¿Tiene llaves? | `[FICHA]` (campo Llaves: YES/NO/EXM) |
| 7 | VIN | `[FICHA]` |

## Riesgo del título y las millas

| # | Punto | Fuente |
|---|---|---|
| 8 | ¿Accidente visible y significativo, suficiente para justificar pérdida total? **Si es salvage y NO se ve daño → alto riesgo de daño mecánico oculto**, aunque el Carfax reporte accidente | `[FOTO]` |
| 9 | Millas no actuales declaradas por la subasta → el título llegará marcado así; el cliente debe aceptarlo | `[FICHA]` + `[CLIENTE]` |
| 10 | ¿Las millas son actuales? Si no, valorar | `[CARFAX]` |
| 11 | Tipo de título (no se compran rebuild) | `[FICHA]` |
| 12 | Con qué tipo de título quedará el vehículo una vez registrado a nombre del cliente | `[ASESOR]` (depende del estado) |
| 13 | ¿Tiene lien? | `[CARFAX]` |

## Historial

| # | Punto | Fuente |
|---|---|---|
| 14 | Si hay View Condition Report en Copart, revisarlo completo y dejar valoración | `[ASESOR]` |
| 15 | Fecha de adquisición del último propietario. Venta privada reciente sin accidentes → posible falla mecánica o daño oculto. Solo bajo responsabilidad del cliente | `[CARFAX]` |
| 16 | Motivo de la venta en subasta (accidente, reposición bancaria, fin de leasing…) | `[FICHA]` (tipo de vendedor) + `[CARFAX]` |
| 17 | ¿Más de 10 años consecutivos en estados con nieve? → solo con aceptación del riesgo de óxido | `[CARFAX]` |
| 18 | ¿Registra ventas anteriores en subasta? Argumentar | `[CARFAX]` |
| 19 | Verificar que año, marca, modelo y versión coincidan con el Carfax | `[FICHA]` + `[CARFAX]` |
| 20 | ¿Se evaluó cada aspecto del accidente reportado en Carfax? | `[CARFAX]` |
| 21 | Notas de la publicación del vehículo | `[FICHA]` |

## Ficha técnica

| # | Punto | Fuente |
|---|---|---|
| 22 | Tipo de motor (ej. V6 – 3.5L) | `[FICHA]` |
| 23 | Tracción (delantera, trasera, 4x4, AWD) | `[FICHA]` |
| 24 | Combustible (gasolina, diésel, híbrido, eléctrico, flex, gas) | `[FICHA]` |
| 25 | Transmisión (automática, manual) | `[FICHA]` |

## Condición mecánica

| # | Punto | Fuente |
|---|---|---|
| 26 | ¿Run & Drive? | `[FICHA]` |
| 27 | Luces de advertencia en el tablero. **Obligatorio ver el tablero completo y legible** | `[FOTO]` |
| 28 | ¿Sonido inusual del motor? (si hay audio) | `[ASESOR]` |
| 29 | ¿Manchas de aceite en el exterior del motor? (fugas o problema interno) | `[FOTO]` |

## Daños

| # | Punto | Fuente |
|---|---|---|
| 30 | ¿Daños en el chasis? Valorar | `[FOTO]` |
| 31 | ¿Daños en undercarriage? → solo bajo responsabilidad exclusiva del cliente | `[FOTO]` |
| 32 | ¿Gomas desalineadas? Valorar | `[FOTO]` |
| 33 | ¿Daños en los marcos de las puertas? Valorar | `[FOTO]` |
| 34 | ¿Bolsas de aire desplegadas? Valorar | `[FOTO]` |
| 35 | Cristales: parabrisas y ventanillas, cuarteaduras o grietas | `[FOTO]` |

---

## Cómo mirar las fotos

Las URLs salen de la ficha del lote. Ábrelas y míralas de verdad, una por una. Un lote de Copart
trae típicamente 8-12 fotos. Qué buscar en cada tipo de toma:

- **Frontal y trasera** — severidad real del golpe, alineación de faros y parrilla, si el capó cierra.
- **Laterales** — líneas de puerta, separaciones irregulares entre paneles (señal de estructura
  torcida), diferencias de tono de pintura (reparación previa).
- **Interior** — bolsas desplegadas (volante y tablero rotos), tapicería (agua deja manchas y moho),
  columna de dirección forzada (robo).
- **Tablero encendido** — la foto clave. Lee cada testigo. Si el tablero no está encendido en
  ninguna foto, **dilo**: no se puede afirmar que no hay luces.
- **Motor** — manchas de aceite, correas, radiador desplazado, mangueras sueltas.
- **Bajos** — óxido, chasis doblado, escape golpeado. Muchas veces no hay foto de bajos; entonces
  el punto 31 queda `[PENDIENTE]`.
- **Ruedas** — camber anormal (rueda inclinada) indica suspensión o chasis dañado.
- **Odómetro** — comparar con el declarado.

## Formato de salida

Genera el checklist como tabla con tres columnas: **Punto · Respuesta · Fuente**. Al final, un
bloque de resumen:

```
COMPLETADO:  22/35 puntos
PENDIENTE CARFAX:  8 puntos  (#10, #13, #15, #17, #18, #19, #20, ...)
PENDIENTE FOTO:    3 puntos  (no hay foto de bajos ni de tablero encendido)
BLOQUEANTES:       ninguno
ACEPTACIONES REQUERIDAS DEL CLIENTE:  millas no actuales (#9)
```

Ese bloque de resumen es lo primero que lee el asesor. Que sea honesto es todo el valor.
