"""Run with FreeCAD's Python. Regenerates a separate enclosure fit study."""
from pathlib import Path
from math import pi, sin, cos, ceil
import FreeCAD as App
import Part
import Import

here = Path(__file__).resolve().parent
V = App.Vector
doc = App.newDocument("DisplayFit")
Import.insert(str(here / "mini_handheld.step"), doc.Name)
board = Part.Shape()
board.read(str(here / "mini_handheld.step"))
if not any(abs(s.BoundBox.XLength - 42) < .05 and abs(s.BoundBox.YLength - 56) < .05
           and abs(s.BoundBox.XMin) < .05 and abs(s.BoundBox.YMin) < .05 for s in board.Solids):
    raise ValueError("Board size or STEP origin changed; recheck the fit study datums.")
raw = Part.Shape()
raw.read(str(here / "HS20HS072RX-flat.step"))

# Datums in the STEP frame, not the KiCad screen coordinates.
exit_y, mouth_y = 32.2, 32.6
x_center, slot_z = 21.0, 2.505
radius, insertion, length = 2.5, 2.95, 20.7
tip_y = mouth_y + insertion
upper = (length - pi * radius - (tip_y - exit_y)) / 2
tangent_y = exit_y - upper
bottom = tip_y - tangent_y
assert upper > 0 and bottom > 5.0  # keep the terminal stiffener out of the bend
exit_z = slot_z + 2 * radius

def feature(name, label, shape, color):
    if shape.isNull() or not shape.isValid():
        raise RuntimeError(f"Invalid solid: {label}")
    f = doc.addObject("Part::Feature", name)
    f.Label, f.Shape = label, shape
    if f.ViewObject:
        f.ViewObject.ShapeColor = color
    return f

# Keep the supplier CAD above the glass edge; replace its straight exposed tail.
glass_edge = -26.4
x_shift = x_center + .05  # supplier STEP tail center is -0.05 mm
body = raw.common(Part.makeBox(50, 60, 20, V(-25, glass_edge, -10)))
body.translate(V(x_shift, exit_y - glass_edge, exit_z + .53))
feature("Display", "HS20HS072RX display (supplier geometry)", body, (.12, .18, .25))

# Approximate taper measured from the flat STEP, with the 6.5 mm mating
# end and 5 mm stiffener from the drawing. Develop along the neutral line.
profile = [(0, -11.1, 10.0), (4.5, -11.1, 11.1),
           (11.0, -11.1, 11.1), (12.0, -4.0, 3.9),
           (13.1, -3.3, 3.2), (length, -3.3, 3.2)]
def widths(d):
    for (u, l, r), (v, ll, rr) in zip(profile, profile[1:]):
        if d <= v + 1e-7:
            t = (d-u)/(v-u)
            return x_shift+l+(ll-l)*t, x_shift+r+(rr-r)*t
    raise ValueError(d)

def section(d):
    if d <= upper:
        y, z, ny, nz = exit_y-d, exit_z, 0, 1
    elif d <= upper + pi*radius:
        t = (d-upper)/radius
        y, z, ny, nz = tangent_y-radius*sin(t), slot_z+radius*(1+cos(t)), -sin(t), cos(t)
    else:
        y, z, ny, nz = tangent_y+d-upper-pi*radius, slot_z, 0, -1
    x1, x2 = widths(d)
    # Use the 0.30 mm stiffened tip thickness as a clearance envelope.
    h = .15
    verts = [V(x,y+k*h*ny,z+k*h*nz) for x,k in [(x1,1),(x2,1),(x2,-1),(x1,-1)]]
    return Part.makePolygon(verts + verts[:1])

stations = sorted(set([0,upper,upper+pi*radius,length-5,length] + [p[0] for p in profile] +
                      [upper+pi*radius*i/36 for i in range(1,36)]))
tail = Part.makeLoft([section(d) for d in stations], True, True)
feature("FoldedFlex", "FPC fit envelope — R2.5, 2.95 mm inserted", tail, (.83, .49, .12))
doc.recompute()

# Check geometry against the populated STEP. Connector mating is modeled
# within the closed slot, with a small nominal clearance above the slot floor.
for label, solid in [("Display",body), ("FPC",tail)]:
    overlaps = []
    for i, item in enumerate(board.Solids):
        if solid.BoundBox.intersect(item.BoundBox):
            vol = solid.common(item).Volume
            if vol > 1e-5:
                overlaps.append((i, round(vol,5), str(item.BoundBox)))
    print(label, "intersection(s):", overlaps)
print("Fold radius", radius, "insertion", insertion, "tail outside Y", tail.BoundBox.YMin)
print("Display bounds:", body.BoundBox)
doc.saveAs(str(here / "display-fit.FCStd"))
