# stmhome

Placa de control basada en STM32H755ZIT6, diseñada en KiCad 10.

## Contenido principal

- **STM32H755ZITx** (U1), microcontrolador principal
- **ESP32-S3-WROOM-1U** (U6), Wi-Fi / Bluetooth
- **BNO086** (U4), IMU de 9 ejes
- **TJA1051T-3** (U5), transceptor CAN
- Regulador AP7361C-33E (3.3 V), protección de polaridad con P-MOSFET y TVS en +5 V

PCB de 4 capas (100 x 85 mm): F.Cu y B.Cu para señales, In1 = GND, In2 = +3.3 V.

## Estructura

| Archivo / carpeta | Descripción |
|---|---|
| `stmhome.kicad_pro` | Proyecto de KiCad (ábrelo primero) |
| `stmhome.kicad_sch` | Hoja principal (alimentación y conectores) |
| `stm.kicad_sch` | STM32H755 |
| `esp.kicad_sch` | ESP32-S3 |
| `can.kicad_sch` | Bus CAN |
| `bno085.kicad_sch` | IMU BNO086 |
| `stmhome.kicad_pcb` | Layout de la PCB |
| `libsCH340C/` | Símbolos, footprints y modelos 3D propios |
| `scripts/` | Scripts de Python usados para acomodar componentes |

## Abrir el proyecto

1. Instala KiCad 10.
2. Abre `stmhome.kicad_pro`.
3. Si algún símbolo o footprint aparece faltante, agrega las librerías de `libsCH340C/` en
   *Preferencias > Administrar librerías de símbolos / footprints* usando la ruta
   `${KIPRJMOD}/libsCH340C/...`.
