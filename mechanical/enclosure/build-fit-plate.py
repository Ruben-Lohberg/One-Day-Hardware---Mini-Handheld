"""Build a one-piece PCB fit gauge and a plate with one case + one gauge."""
import struct
from pathlib import Path
import FreeCAD as App
import Part
import MeshPart

HERE = Path(__file__).resolve().parent
V=App.Vector
pcb=Part.Shape()
pcb.read(str(HERE.parent/"mini_handheld.step"))
solids=pcb.Solids

def near(a,b): return abs(a-b)<.05

def one(predicate):
    result=[s for s in solids if predicate(s.BoundBox,s.Volume)]
    if len(result)!=1:
        raise ValueError(f"Unexpected STEP geometry: {len(result)} matching solids")
    return result[0]

def box(x0,x1,y0,y1,z0,z1):
    return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))

substrate=one(lambda b,v: near(b.XLength,42) and near(b.YLength,56) and near(b.ZMin,0))
usb=one(lambda b,v: b.XMin<-.5 and b.YMin>30 and v>20)
swd=one(lambda b,v: b.XMax>42 and v>20)
top=substrate.BoundBox.ZMax
u=usb.BoundBox
j=swd.BoundBox
if not (near(u.XMin,-1.25) and near(j.XMax,47.64)):
    raise ValueError("Port locations changed; check the gauge envelopes")
# Preserve the actual substrate and holes. Solid tops bridge the small
# solder-mask gap and omit delicate leads. The solid port gauges check
# the openings, rather than reproducing usable electrical contacts.
usb_block=box(u.XMin,u.XMax,u.YMin,u.YMax,top-.05,u.ZMax)
pin_envelope=swd.common(box(42,j.XMax+.1,j.YMin-.1,j.YMax+.1,1.65,j.ZMax+.1)).BoundBox
swd_gauge=box(41.60,j.XMax,j.YMin,j.YMax,pin_envelope.ZMin,pin_envelope.ZMax)
swd_body=box(38.9,41.66,j.YMin,j.YMax,top-.05,j.ZMax)
# Flat-ended gauge approximates the pin row; check its overhang in the slicer.
parts=[usb_block,swd_gauge,swd_body]
for item in solids:
    if any(item.isSame(s) for s in (substrate,usb,swd)):
        continue
    b=item.BoundBox
    if item.Volume<.3 or b.ZMax<=top or b.XMin<0 or b.XMax>42:
        continue
    parts.append(box(b.XMin,b.XMax,b.YMin,b.YMax,top-.05,b.ZMax))
gauge=substrate.multiFuse(parts).removeSplitter()
assert gauge.isValid() and len(gauge.Solids)==1, [(s.Volume,str(s.BoundBox)) for s in gauge.Solids]
doc=App.openDocument(str(HERE/"enclosure.FCStd"))
for name in ("Tray","Bezel"):
    part=doc.getObject(name).Shape
    volume=gauge.common(part).Volume
    print(f"Gauge vs {name}: {volume:.6f} mm3 overlap")
    assert volume<.005
# The gauge is a separate print artifact; keep it out of the assembled view.
gauge.translate(V(-gauge.BoundBox.XMin,-gauge.BoundBox.YMin,-gauge.BoundBox.ZMin))
mesh=MeshPart.meshFromShape(Shape=gauge,LinearDeflection=.035,AngularDeflection=.12,Relative=False)
assert mesh.isSolid()
mesh.write(str(HERE/"pcb-fit-gauge.stl"))

# The tray and bezel retain their validated bed orientations. Leave
# room for brims/supports and keep all pieces away from bed edges.
layout={"tray":[(30,80)],"bezel":[(90,80)],"pcb-fit-gauge":[(150,92)],
        "plunger":[(55+i*18,52) for i in range(4)]}
facet=struct.Struct("<12fH")
data=bytearray()
boxes=[]
for name,positions in layout.items():
    source=(HERE/f"{name}.stl").read_bytes()
    count,=struct.unpack_from("<I",source,80)
    assert len(source)==84+count*facet.size
    for x,y in positions:
        lo=[float("inf")]*3
        hi=[-float("inf")]*3
        for record in facet.iter_unpack(source[84:]):
            p=list(record)
            for k in (3,6,9):
                p[k]+=x
                p[k+1]+=y
                for i in range(3):
                    lo[i]=min(lo[i],p[k+i])
                    hi[i]=max(hi[i],p[k+i])
            data.extend(facet.pack(*p))
        assert abs(lo[2])<.001 and min(lo[:2])>5 and max(hi[:2])<251
        assert all(any(hi[i]+4<a[i] or b[i]+4<lo[i] for i in (0,1))
                   for a,b in boxes)
        boxes.append((lo,hi))
assert len(boxes)==7
header=b"Mini Handheld: 1 tray, 1 bezel, 4 plungers, 1 PCB fit gauge"
(HERE/"case-and-board-plate.stl").write_bytes(header.ljust(80,b" ")+
    struct.pack("<I",len(data)//facet.size)+data)
print("Validated 7 pieces on a 256 x 256 mm bed")
