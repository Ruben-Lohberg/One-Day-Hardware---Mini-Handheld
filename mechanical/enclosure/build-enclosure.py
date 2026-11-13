"""Regenerate the case solids and bed-oriented STLs with FreeCAD's Python."""
from pathlib import Path
import os
import FreeCAD as App
import Part
import MeshPart

HERE = Path(__file__).resolve().parent
V = App.Vector
doc = App.newDocument("MiniHandheldEnclosure")
fit = App.openDocument(str(HERE.parent / "display-fit.FCStd"))
pcb = Part.Shape()
pcb.read(str(HERE.parent / "mini_handheld.step"))
display = fit.getObject("Display").Shape.copy()
flex = fit.getObject("FoldedFlex").Shape.copy()

X0, X1, Y0, Y1 = -2.6, 44.6, -5.6, 89.6
OUTER_RADIUS = 2.8
BASE_Z, FLOOR_Z, SEAM_Z, TOP_Z = -4.1, -2.3, 8.9, 10.9
MOUNTS = [(4,4), (38,4), (4,52), (38,52)]
CASE_SCREWS = [(6,-2.55), (36,-2.55), (6,86.55), (36,86.55)]
HEAD_SEAT_Z = -2.50
LID_BOSS_BOTTOM = 5.8
PILOT_END_Z = 9.9
SCREW_D = 2.0
PILOT_D = 1.65
CLEARANCE_D = 2.35
HEAD_D = 3.8     # nominal illustration; use max envelope for checks
HEAD_H = 1.35
HEAD_MAX_D = 4.3
HEAD_MAX_H = 1.55
HEAD_RECESS_D = 4.55
PCB_THICKNESS = 1.595
PCB_SCREW_LENGTH = 5
CASE_SCREW_LENGTH = 12
BUTTONS = [("Up",21,21), ("Down",21,7), ("Left",14,14), ("Right",28,14)]
GUIDE_BOTTOM = 6.1
GUIDE_RADIUS = 3.225
LIP_RADIUS, LIP_TOP = 3.6, 5.93
FOOT_RADIUS = 1.75
ACTUATOR_Z = 3.595
REST_CLEARANCE = .03
CHECK_PRESS = .28
BUTTON_PROTRUSION = 1.5

def box(x0,x1,y0,y1,z0,z1):
    return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))

def cyl(x,y,r,z0,z1):
    return Part.makeCylinder(r,z1-z0,V(x,y,z0))

def rounded(x0,x1,y0,y1,z0,z1,r):
    s = box(x0+r,x1-r,y0,y1,z0,z1).fuse(box(x0,x1,y0+r,y1-r,z0,z1))
    for x in (x0+r,x1-r):
        for y in (y0+r,y1-r):
            s=s.fuse(cyl(x,y,r,z0,z1))
    return s.removeSplitter()

def ramp(inner,wall,y0,y1,z):
    # 45-degree underside, with 0.2 mm buried into the wall for the union.
    p=[V(wall,y0,z-abs(inner-wall)),V(inner,y0,z),V(wall,y0,z)]
    return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,y1-y0,0))

def cleaned(s):
    return s.removeSplitter()

tray = rounded(X0,X1,Y0,Y1,BASE_Z,SEAM_Z,OUTER_RADIUS)
tray = tray.cut(rounded(-.6,42.6,-3.6,87.6,FLOOR_Z,SEAM_Z+.2,1))
for x,y in MOUNTS:
    tray=tray.fuse(cyl(x,y,2.65,FLOOR_Z-.1,0))
    tray=tray.cut(cyl(x,y,PILOT_D/2,-3.75,.1))
for x,y in CASE_SCREWS:
    # Back-entry M2 x 12: 1.6 mm head recess, then a clearance bore.
    tray=tray.fuse(cyl(x,y,2.5,FLOOR_Z-.1,SEAM_Z))
    tray=tray.cut(cyl(x,y,HEAD_RECESS_D/2,BASE_Z-.1,HEAD_SEAT_Z))
    tray=tray.cut(cyl(x,y,CLEARANCE_D/2,HEAD_SEAT_Z-.1,SEAM_Z+.2))
    tray=tray.cut(cyl(x,y,2.3,LID_BOSS_BOTTOM-.2,SEAM_Z+.2))

# Snug USB shell opening in the left wall. The exterior counterbore
# brings the plug shoulder close to the recessed connector face.
opening=rounded(33.05,42.95,1.15,5.30,X0-.1,.1,.70)
opening.rotate(V(0,0,0),V(1,1,1),120)
tray=tray.cut(opening)
tray=tray.cut(box(X0-.1,-1.42,30.9,45.1,.05,6.65))

# Side-access SWD clearance, open to the seam to avoid bridging the slot.
tray=tray.cut(box(42.4,X1+.1,12.5,28.35,1.65,SEAM_Z+.1))

# Recessed lettering, read from outside the back of the tray.
font_path = os.environ.get("MINI_HANDHELD_ENGRAVING_FONT")
if not font_path and os.environ.get("WINDIR"):
    font_path = Path(os.environ["WINDIR"]) / "Fonts" / "arialbd.ttf"
if not font_path or not Path(font_path).is_file():
    raise FileNotFoundError("Set MINI_HANDHELD_ENGRAVING_FONT to a TrueType font file.")
font = Path(font_path)
engraving = ("Ruben Lohberg", "Mini Handheld", "Built in one Day", "Nov. 11th 2026")
for i, line in enumerate(engraving):
    glyphs = Part.makeWireString(line, str(font.parent) + os.sep, font.name, 3.0, 0.0)
    faces = Part.makeCompound([Part.makeFace(w, "Part::FaceMakerBullseye")
                               for w in glyphs if w])
    b = faces.BoundBox
    faces.translate(V(-(b.XMin+b.XMax)/2, -(b.YMin+b.YMax)/2, 0))
    faces.rotate(V(0,0,0), V(0,1,0), 180)
    faces.translate(V(21,48.75-4.5*i,BASE_Z-.05))
    cut = faces.extrude(V(0,0,.55))
    assert tray.common(cut).Volume > 0
    tray = tray.cut(cut)

# Backlight rests on four short, printable side ledges. Their seat height
# leaves room for a thin compliant pad; stops sit outside the glass.
for y0,y1 in [(48,54),(75,81)]:
    tray=tray.fuse(ramp(4.35,-.8,y0,y1,6.20))
    tray=tray.fuse(ramp(37.75,42.8,y0,y1,6.20))
    tray=tray.fuse(box(-.8,2.65,y0,y1,6.1,8.5))
    tray=tray.fuse(box(39.45,42.8,y0,y1,6.1,8.5))
lid = rounded(X0,X1,Y0,Y1,SEAM_Z,TOP_Z,OUTER_RADIUS)
lid=lid.cut(rounded(5.35,36.75,37.8,79.4,SEAM_Z-.1,TOP_Z+.1,1.0))
# The lid prints face down, so these stops grow directly from the bed-side
# panel. The lower pair sits outside the center flex exit.
for x0,x1 in [(10,13.1),(28.9,32)]:
    lid=lid.fuse(box(x0,x1,84.32,85.65,7.0,SEAM_Z+.1))
for x0,x1 in [(3.4,6.5),(35.6,38.7)]:
    lid=lid.fuse(box(x0,x1,30.7,31.88,7.0,SEAM_Z+.1))
for x,y in CASE_SCREWS:
    lid=lid.fuse(cyl(x,y,2.05,LID_BOSS_BOTTOM,SEAM_Z+.1))
    lid=lid.cut(cyl(x,y,PILOT_D/2,LID_BOSS_BOTTOM-.1,PILOT_END_Z))
for _,x,y in BUTTONS:
    # Printed as part of the bezel, with no separate guide plate.
    # Chamfer the lower outside rim to clear the nearby folded display flex.
    rim=Part.makeCone(3.75,4.1,.65,V(x,y,GUIDE_BOTTOM))
    lid=lid.fuse(rim.fuse(cyl(x,y,4.1,GUIDE_BOTTOM+.65,SEAM_Z+.1)))
    lid=lid.cut(cyl(x,y,GUIDE_RADIUS,GUIDE_BOTTOM-.1,TOP_Z+.1))

def plunger(x,y):
    # The complete button goes into the guide from inside the bezel.
    # The flare behind the flat face prints without a horizontal overhang.
    foot_z=ACTUATOR_Z+REST_CLEARANCE
    tip=cyl(x,y,FOOT_RADIUS,foot_z,3.75)
    flare=Part.makeCone(FOOT_RADIUS,LIP_RADIUS,1.85,V(x,y,3.74))
    lip=cyl(x,y,LIP_RADIUS,5.59,LIP_TOP)
    stem=cyl(x,y,3.0,5.58,TOP_Z+BUTTON_PROTRUSION)
    return cleaned(tip.fuse(flare).fuse(lip).fuse(stem))

tray,lid=map(cleaned,(tray,lid))
plungers = [(name,plunger(x,y)) for name,x,y in BUTTONS]

def feature(name,label,shape):
    o=doc.addObject("Part::Feature",name)
    o.Label=label
    o.Shape=shape
    return o

hardware=doc.addObject("App::DocumentObjectGroup","Reference")
hardware.Label="Reference assembly (do not print)"
for n,label,s in [("PCB","Populated PCB",pcb),("LCD","LCD",display),("Flex","Folded FPC",flex)]:
    hardware.addObject(feature(n,label,s))

def stl(name, shape, flip=False):
    s=shape.copy()
    if flip:
        s.rotate(V(0,0,0), V(1,0,0), 180)
    b=s.BoundBox
    s.translate(V(-b.XMin,-b.YMin,-b.ZMin))
    mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.035,AngularDeflection=.12,Relative=False)
    assert mesh.isSolid(), name
    mesh.write(str(HERE/(name+".stl")))

for n,label,s,flip in [("tray","Lower tray",tray,False),("bezel","Top bezel",lid,True),
                        ("plunger","One-piece plunger",plungers[0][1],False)]:
    if n in ("tray","bezel"):
        feature(n.title(),label,s)
    assert s.isValid() and len(s.Solids)==1, n
    stl(n,s,flip)
for n,shape in plungers:
    feature(n,n+" plunger",shape)

# Reject unwanted solid interference. Intended surface contact is zero volume.
def overlap(a,b):
    return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0
for n,shape in [("tray",tray),("bezel",lid)]+plungers:
    for label,ref in [("PCB",pcb),("LCD",display),("flex",flex)]:
        v=overlap(shape,ref)
        print(n,label,round(v,6))
        assert v<.005, (n,label,v)
        if n=="bezel" and label=="flex":
            assert v<.00001, (n,label,v)
for a,b in [(tray,lid)]+[(s,t) for _,s in plungers for t in (lid,tray)]:
    assert overlap(a,b)<.005, ("Case part interference", a.common(b).BoundBox, overlap(a,b))
for n,s in plungers:
    pressed=s.copy()
    pressed.translate(V(0,0,-CHECK_PRESS))
    assert overlap(pressed,lid)<.005, n
    for other in (tray,display,flex):
        assert overlap(pressed,other)<.005, n
# The lip blocks outward motion. The installed PCB and switch block
# inward escape before the stem can leave the guide.
for n,shape in plungers:
    moved=shape.copy()
    moved.translate(V(0,0,GUIDE_BOTTOM-LIP_TOP))
    assert overlap(moved,lid)<.005, n
    moved.translate(V(0,0,.05))
    assert overlap(moved,lid)>.005, n
    inward=shape.copy()
    inward.translate(V(0,0,-1))
    assert inward.BoundBox.ZMax>TOP_Z and overlap(inward,pcb)>.005, n
# Verify the only interference during a press is with the intended actuator.
for (_,x,y),(n,s) in zip(BUTTONS,plungers):
    s=s.copy()
    s.translate(V(0,0,-CHECK_PRESS))
    actuator=cyl(x,y,FOOT_RADIUS+.01,ACTUATOR_Z-.28,ACTUATOR_Z+.04)
    assert overlap(s,pcb.cut(actuator))<.005, n
    assert overlap(s,pcb)>0, n
# Simplified, separate reference screws. The shanks show the nominal
# thread envelope, which intentionally bites into the printed pilot walls.
def screw_shape(x,y,bearing_z,length,points_up):
    shank = cyl(x,y,SCREW_D/2,0,length-.65).fuse(
        Part.makeCone(SCREW_D/2,.19,.65,V(x,y,length-.65)))
    head = cyl(x,y,HEAD_D/2,-HEAD_H+.4,0).fuse(
        Part.makeCone(HEAD_D/2-.33,HEAD_D/2,.41,V(x,y,-HEAD_H)))
    recess = box(x-.95,x+.95,y-.24,y+.24,-HEAD_H-.05,-HEAD_H+.55).fuse(
        box(x-.24,x+.24,y-.95,y+.95,-HEAD_H-.05,-HEAD_H+.55))
    result=cleaned(shank.fuse(head.cut(recess)))
    if not points_up:
        result.rotate(V(x,y,0),V(1,0,0),180)
    result.translate(V(0,0,bearing_z))
    assert result.isValid() and len(result.Solids)==1
    return result

screws=doc.addObject("App::DocumentObjectGroup","Screws")
screws.Label="M2 screws (reference only)"
for i,(x,y) in enumerate(CASE_SCREWS,1):
    head=cyl(x,y,HEAD_MAX_D/2,HEAD_SEAT_Z-HEAD_MAX_H,HEAD_SEAT_Z)
    tip=HEAD_SEAT_Z+CASE_SCREW_LENGTH
    shank=cyl(x,y,SCREW_D/2,HEAD_SEAT_Z,tip)
    assert overlap(head,tray)<.005 and overlap(shank,tray)<.005
    assert not any(overlap(shank,part)>.005 for part in (pcb,display,flex))
    assert tip-LID_BOSS_BOTTOM >= 3.5
    assert PILOT_END_Z-tip >= .35
    assert TOP_Z-PILOT_END_Z >= .9
    screws.addObject(feature("CaseScrew"+str(i),f"M2 x 12 case screw {i}",
                            screw_shape(x,y,HEAD_SEAT_Z,CASE_SCREW_LENGTH,True)))
for i,(x,y) in enumerate(MOUNTS,1):
    tip=PCB_THICKNESS-PCB_SCREW_LENGTH
    head=cyl(x,y,HEAD_MAX_D/2,PCB_THICKNESS,PCB_THICKNESS+HEAD_MAX_H)
    shank=cyl(x,y,SCREW_D/2,tip,PCB_THICKNESS)
    assert overlap(head,pcb)<.005 and overlap(shank,pcb)<.005
    for part in (lid,display,flex):
        assert overlap(head,part)<.005 and overlap(shank,part)<.005
    assert tip-(-3.75) >= .30
    assert 2.7 < 3.5 <= HEAD_D  # PCB hole and minimum head bearing diameter
    screws.addObject(feature("MountScrew"+str(i),f"M2 x 5 PCB screw {i}",
                            screw_shape(x,y,PCB_THICKNESS,PCB_SCREW_LENGTH,False)))
doc.recompute()
doc.saveAs(str(HERE/"enclosure.FCStd"))
