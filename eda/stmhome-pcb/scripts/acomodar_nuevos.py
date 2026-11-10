"""
Acomoda en la PCB SOLO los componentes nuevos (U7, C48, C49, Q2, D7, U8, D8)
y borra las pistas que quedaron colgando de J2, D2 y D3.
No toca nada del acomodo que ya tienes.

Antes de correrlo:
  1. En el editor de PCB: Herramientas -> Actualizar PCB desde esquematico,
     con "Eliminar huellas sin simbolo" marcado (para que se vayan J2, D2 y D3).
  2. Guarda y CIERRA el editor de PCB.
Uso (en la carpeta del proyecto):
  python acomodar_nuevos.py
"""
import re, shutil, sys, os

PCB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stmhome.kicad_pcb")

# Referencia: (x, y) en mm, coordenadas de la PCB
POSICIONES = {
    # Regulador 3.3 V donde estaba J2, capacitores abajo de sus pines
    "U7":  (41.50, 51.00),
    "C48": (39.00, 57.50),   # entrada (lado VI, pin 1 del LDO)
    "C49": (44.00, 57.50),   # salida (lado VO, pin 3 del LDO)
    # Proteccion de polaridad donde estaba D3, TVS de 5 V a su derecha
    "Q2":  (42.00, 28.50),
    "D7":  (47.80, 27.00),
    # TVS del SWD entre los test points y J1
    "U8":  (129.50, 69.50),
    # TVS del paro, junto a J4
    "D8":  (49.30, 83.00),
}

# Pistas de las redes viejas de J2/D2/D3 (quedan sueltas al quitar esas piezas)
PISTAS_A_BORRAR = {
    "3f9e1a5b-c4cc-45ba-b603-d433f7a70621", "b95e2a63-af33-4b83-8917-f2c3c3207fe9",
    "def937de-047b-4689-8499-a1b217f37e3e", "026e9938-0499-4697-b211-832fe132e6f8",
    "05a0d43c-b27c-4e2f-b4d6-83aaf1b231a7", "2721e685-1ed7-4522-8bd7-560c41a56cb4",
    "3c9823b3-7606-4885-bbb2-04871e75bfd5", "7b5f98d7-f872-4c31-8394-77e34ff302ea",
    "8cd7b44c-794f-4f52-bda4-5899ec85e1b2", "a4918934-97e2-463f-a19d-8c9d332f5435",
    "abb4bd0a-8b24-459f-846f-b8e585e8ba54", "daefc21e-36b1-484e-9d2a-59860850003d",
    "f00043a0-fdfa-4d02-93df-688ca3ca614f",
}

def bloques(s, cabeza):
    """Devuelve (inicio, fin) de cada bloque '(cabeza' de primer nivel."""
    res, pos = [], 0
    pat = re.compile(r"\n\t\(" + cabeza + r"[\s\"]")
    while True:
        m = pat.search(s, pos)
        if not m:
            return res
        i = m.start() + 1
        d, j, comillas = 0, i, False
        while True:
            c = s[j]
            if comillas:
                if c == "\\": j += 1
                elif c == '"': comillas = False
            elif c == '"': comillas = True
            elif c == "(": d += 1
            elif c == ")":
                d -= 1
                if d == 0: break
            j += 1
        res.append((i, j + 1))
        pos = j + 1

def main():
    if os.path.exists(os.path.join(os.path.dirname(PCB), "~stmhome.kicad_pcb.lck")):
        print("Parece que el editor de PCB sigue abierto. Cierralo y vuelve a correr esto.")
        sys.exit(1)
    with open(PCB, encoding="utf-8", newline="") as f:
        s = f.read()

    fps = bloques(s, "footprint")
    refs = {}
    for a, b in fps:
        m = re.search(r'\(property "Reference" "([^"]+)"', s[a:b])
        if m: refs[m.group(1)] = (a, b)

    faltan = [r for r in POSICIONES if r not in refs]
    if faltan:
        print("No encuentro en la PCB:", ", ".join(faltan))
        print("Primero haz 'Actualizar PCB desde esquematico', guarda y cierra.")
        sys.exit(1)
    viejos = [r for r in ("J2", "D2", "D3") if r in refs]
    if viejos:
        print("Siguen en la PCB:", ", ".join(viejos),
              "-> repite la actualizacion con 'Eliminar huellas sin simbolo' marcado.")
        sys.exit(1)

    shutil.copy2(PCB, PCB + ".antes_script")

    # 1) mover huellas nuevas (solo su (at ...) principal; pads y textos son relativos)
    cambios = []
    for ref, (x, y) in POSICIONES.items():
        a, b = refs[ref]
        blk = s[a:b]
        m = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)((?: [-\d.]+)?)\)", blk)
        nuevo = blk[:m.start()] + f"\n\t\t(at {x} {y}{m.group(3)})" + blk[m.end():]
        cambios.append((a, b, nuevo))
        print(f"{ref:4s} -> ({x}, {y})")

    # 2) borrar pistas viejas
    borradas = 0
    for a, b in bloques(s, "segment") + bloques(s, "via") + bloques(s, "arc"):
        m = re.search(r'\(uuid "([^"]+)"\)', s[a:b])
        if m and m.group(1) in PISTAS_A_BORRAR:
            fin = b
            while fin < len(s) and s[fin] in "\r\n": fin += 1
            cambios.append((a - 1 if s[a - 1] == "\t" else a, fin, ""))
            borradas += 1

    for a, b, txt in sorted(cambios, reverse=True):
        s = s[:a] + txt + s[b:]

    with open(PCB, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    print(f"Pistas viejas borradas: {borradas}")
    print("Listo. Respaldo en stmhome.kicad_pcb.antes_script")
    print("Abre la PCB, revisa, rellena zonas (B) y rutea lo nuevo.")

if __name__ == "__main__":
    main()
