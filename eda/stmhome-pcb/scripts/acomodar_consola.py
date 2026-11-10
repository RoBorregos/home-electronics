# Correr DENTRO de la consola de Python del editor de PCB de KiCad (con la PCB abierta),
# despues de "Actualizar PCB desde esquematico".
import pcbnew
POS = {"U7": (41.50, 51.00), "C48": (39.00, 57.50), "C49": (44.00, 57.50),
       "Q2": (42.00, 28.50), "D7": (47.80, 27.00), "U8": (129.50, 69.50), "D8": (49.30, 83.00)}
BORRAR = {
    "3f9e1a5b-c4cc-45ba-b603-d433f7a70621", "b95e2a63-af33-4b83-8917-f2c3c3207fe9",
    "def937de-047b-4689-8499-a1b217f37e3e", "026e9938-0499-4697-b211-832fe132e6f8",
    "05a0d43c-b27c-4e2f-b4d6-83aaf1b231a7", "2721e685-1ed7-4522-8bd7-560c41a56cb4",
    "3c9823b3-7606-4885-bbb2-04871e75bfd5", "7b5f98d7-f872-4c31-8394-77e34ff302ea",
    "8cd7b44c-794f-4f52-bda4-5899ec85e1b2", "a4918934-97e2-463f-a19d-8c9d332f5435",
    "abb4bd0a-8b24-459f-846f-b8e585e8ba54", "daefc21e-36b1-484e-9d2a-59860850003d",
    "f00043a0-fdfa-4d02-93df-688ca3ca614f"}
b = pcbnew.GetBoard()
for ref, (x, y) in POS.items():
    fp = b.FindFootprintByReference(ref)
    if fp is None:
        print("NO ESTA:", ref, "-> primero Actualizar PCB desde esquematico")
        continue
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    print(ref, "->", x, y)
for r in ("J2", "D2", "D3"):
    if b.FindFootprintByReference(r):
        print("OJO: sigue", r, "en la PCB (marca 'Eliminar huellas sin simbolo' al actualizar)")
n = 0
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in BORRAR:
        b.Remove(t); n += 1
print("Pistas viejas borradas:", n)
pcbnew.Refresh()
print("Listo. Revisa y guarda con Ctrl+S (Ctrl+Z para deshacer no aplica: si no te gusta, cierra sin guardar).")
