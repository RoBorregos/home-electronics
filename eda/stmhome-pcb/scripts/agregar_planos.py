# Correr en la consola de scripting del editor de PCB (con la PCB abierta).
# Agrega plano GND en In1.Cu y plano +3.3V en In2.Cu, del tamano de la placa.
import pcbnew
b = pcbnew.GetBoard()
caja = b.GetBoardEdgesBoundingBox()
m = pcbnew.FromMM(0.5)
x1, y1 = caja.GetLeft() + m, caja.GetTop() + m
x2, y2 = caja.GetRight() - m, caja.GetBottom() - m
def plano(nombre_red, capa):
    net = b.FindNet(nombre_red)
    if net is None:
        print("No existe la red", nombre_red); return
    for z in b.Zones():
        if z.GetLayer() == capa and z.GetNetname() == nombre_red:
            print("Ya hay plano", nombre_red, "en", b.GetLayerName(capa)); return
    z = pcbnew.ZONE(b)
    z.SetLayer(capa)
    z.SetNet(net)
    z.SetZoneName(nombre_red + "_plano")
    z.SetLocalClearance(pcbnew.FromMM(0.3))
    z.SetMinThickness(pcbnew.FromMM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(pcbnew.FromMM(0.4))
    z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        o.Append(x, y)
    b.Add(z)
    print("Plano", nombre_red, "en", b.GetLayerName(capa))
plano("GND", pcbnew.In1_Cu)
plano("+3.3V", pcbnew.In2_Cu)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.Refresh()
print("Listo. Guarda con Ctrl+S.")
