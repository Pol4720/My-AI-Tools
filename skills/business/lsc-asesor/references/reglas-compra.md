# Reglas de compra y puntuación

Derivadas del checklist oficial de Copart/IAAI, del contrato de compra y de la práctica del negocio.

> **Este archivo está hecho para editarse.** El asesor debe agregar aquí las reglas que aprenda en
> la práctica (marcas o motores a evitar, estados problemáticos, rangos de millaje). Todo lo que
> esté en este archivo, la skill lo aplica.

## A. Bloqueantes absolutos — no se compra

Si aplica alguno, el vehículo sale de la lista. No se le presenta al cliente.

1. **Título pendiente (Pending Title)** o nota de que no se puede emitir duplicado del título.
   Sin título no hay traspaso; el cliente se queda con un carro que no puede poner a su nombre.
2. **Título Rebuild.** Política de la empresa: no se compran.
3. **Lote de Copart que no está en la yarda.** Si no está físicamente ahí, el retiro y el transporte
   se vuelven impredecibles.
4. **Lien activo** (deuda asociada al título).
5. **Depósito de seguridad insuficiente** para la oferta planeada (mínimo 15% del precio total).
6. **El cliente no pagó asesoría.** Si no pagó, el checklist no se llena: compra bajo su propia
   responsabilidad y sin análisis. Es literal en el formulario oficial.

## B. Requieren aceptación escrita del cliente

No se descartan, pero no se compran sin que el cliente acepte el riesgo por escrito. Deja constancia.

1. **Daño en undercarriage (bajos).** Riesgo estructural y mecánico oculto.
2. **Más de 10 años consecutivos en estados con nieve** (según Carfax). Óxido en los bajos.
   Estados de sal: NY, NJ, PA, OH, MI, WI, MN, IL, IN, MA, CT, RI, NH, VT, ME, IA, ND, SD, NE, CO, UT.
3. **Venta privada reciente sin accidentes reportados.** Si un particular lo vendió hace poco y el
   Carfax está limpio, lo más probable es que tenga una falla mecánica o daño oculto. Nadie suelta
   un carro sano recién comprado.
4. **Salvage sin daño visible.** Si la aseguradora lo declaró pérdida total pero no se ve el golpe,
   el daño es mecánico, eléctrico o de agua — lo peor de reparar. Alerta alta aunque el Carfax
   reporte el accidente.
5. **Millas no actuales.** Si la subasta lo declara, el título llegará marcado "Millas No Actuales"
   aunque el Carfax diga otra cosa. El cliente tiene que saberlo y aceptarlo: afecta la reventa.
6. **Copart Buy Now.** El cliente debe confirmar que paga dentro de 24 horas. Si no, Copart relista
   el vehículo y el cliente pierde el depósito.
7. **Daño estructural (chasis)** confirmado.
8. **Sin llaves.** Costo adicional real y posible señal de robo recuperado.

## C. Preferencias — suman o restan puntos

**Suman:**
- Buy Now disponible: compra segura a precio cerrado, sin guerra de pujas ni sobrecosto emocional.
  **Es la opción preferida del negocio.**
- Fecha de subasta dentro de los próximos 7 días.
- Vendedor compañía de seguros con daño visible y coherente con el reporte.
- Run & Drive.
- Título limpio.
- Ubicación cercana al cliente (transporte más barato y más rápido).
- Daño frontal o trasero leve, cosmético, sin bolsas desplegadas.
- Llaves presentes.
- Millaje coherente con el año (~12.000 mi/año).

**Restan:**
- Fecha de subasta a más de 14 días — no cabe en la ventana de 15 días de la asesoría.
- Bolsas de aire desplegadas: reemplazo caro ($1.000-2.500) y sugiere impacto fuerte.
- Gomas desalineadas: sospecha de daño en suspensión o chasis.
- Marcos de puertas deformados: el golpe llegó a la estructura.
- Cristales cuarteados.
- Luces de advertencia en el tablero (Check Engine, ABS, Airbag, batería, aceite).
- Manchas de aceite en el exterior del motor: fugas o problema interno.
- Sonido anormal del motor (si hay audio).
- Ventas anteriores en subasta: el carro ya dio vueltas, alguien lo devolvió o no se pudo reparar.
- Odómetro muy alto para el año.
- Vendedor desconocido.

## D. Rúbrica de puntuación (100 puntos)

| Bloque | Pts | Criterio |
|---|---|---|
| **Encaje presupuestal** | 25 | Costo total ≤ presupuesto: 25. Hasta 5% por encima: 15. Hasta 10%: 5. Más: 0. |
| **Modalidad y timing** | 15 | Buy Now: 15. Subasta ≤7 días: 12. 8-14 días: 7. >14 días: 0. |
| **Título** | 15 | Limpio: 15. Limpio–robo recuperado: 11. Salvage reparable: 8. Salvage no reparable: 0. Rebuild: descalifica. |
| **Daño (fotos)** | 20 | Sin daño o cosmético: 20. Frontal/trasero leve sin bolsas: 15. Moderado con bolsas: 8. Estructural/bajos/agua/fuego: 0. |
| **Historial** | 10 | Carfax limpio y coherente: 10. Un accidente documentado y coherente: 7. Sin Carfax todavía: 5 provisional. Banderas rojas: 0. |
| **Mecánica** | 10 | Run & Drive + llaves + sin luces: 10. Falta uno: 6. Falta más de uno o luces encendidas: 2. |
| **Logística** | 5 | Mismo estado: 5. Vecino: 4. Media distancia: 2. Costa a costa: 0. |

**Lectura:** ≥80 recomendable · 65-79 aceptable con advertencias explícitas · 50-64 solo si el
cliente acepta riesgos concretos · <50 no se presenta.

**Regla de honestidad:** si el bloque de daño se puntuó sin haber mirado las fotos, o el de historial
sin Carfax, dilo en el reporte. Un 82 con la mitad de la evidencia pendiente no es un 82 — repórtalo
como "82 provisional, pendiente Carfax y revisión de fotos".

## E. Estrategia de puja

- El sistema de LSC sugiere una **Oferta Máxima Sugerida** por lote. Úsala como referencia, no como
  orden.
- Los incrementos en Copart son de **$50** sobre la oferta actual.
- La oferta máxima **nunca** debe exceder la que sale de `costeo.py reverso` con el presupuesto real
  del cliente. Ese es el techo duro.
- Si la oferta máxima cae justo encima de un borde de escalón de la tarifa LSC ($5,999 / $10,999 /
  $15,999), evalúa bajar al borde: ahorra $100 de tarifa más el impuesto sobre ella.
- **Buy Now vs pujar:** si el Buy Now está dentro del 8-10% de lo que razonablemente se pagaría
  pujando, recomienda Buy Now. La certeza vale ese margen, especialmente con un cliente que solo
  tiene 15 días y una ventana de 5 videollamadas.
- Recuerda al cliente antes de la subasta: si gana y se echa atrás, **pierde el DS completo**
  (contrato 6.8), y tiene 24 horas para pagar el saldo (6.7).

## F. Espacio para reglas propias del asesor

*(agregar aquí: años mínimos, millaje máximo, marcas o motores a evitar, estados problemáticos,
modelos con historial de transmisión o motor conocido, etc.)*

- Año mínimo: _por definir_
- Millaje máximo aceptable: _por definir_
- Marcas/modelos vetados: _por definir_
- Estados a evitar: _por definir_
