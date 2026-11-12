"""Arrange two complete sets on a 256 mm square print bed."""
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
LAYOUT = {
    "tray": [(20, 72), (74, 72)],
    "bezel": [(128, 72), (182, 72)],
    "plunger": [(x, y) for x in (144, 158, 172, 186) for y in (36, 51)],
}
FACET = struct.Struct("<12fH")
facets = bytearray()
boxes = []
for name, positions in LAYOUT.items():
    data = (HERE / f"{name}.stl").read_bytes()
    count, = struct.unpack_from("<I", data, 80)
    assert len(data) == 84 + count * FACET.size, f"Expected binary STL: {name}"
    for x, y in positions:
        lo = [float("inf")] * 3
        hi = [-float("inf")] * 3
        for record in FACET.iter_unpack(data[84:]):
            v = list(record)
            for i in (3, 6, 9):
                v[i] += x
                v[i + 1] += y
                for j in range(3):
                    lo[j] = min(lo[j], v[i + j])
                    hi[j] = max(hi[j], v[i + j])
            facets.extend(FACET.pack(*v))
        assert min(lo) >= -1e-5 and max(hi) < 256, (name, lo, hi)
        assert all(any(hi[i] + 2 < a[i] or b[i] + 2 < lo[i] for i in (0, 1))
                   for a, b in boxes), f"Insufficient plate clearance: {name}"
        boxes.append((lo, hi))

assert len(boxes) == 12
header = b"Mini Handheld: 2 trays, 2 bezels, 8 plungers".ljust(80, b" ")
(HERE / "two-cases-plate.stl").write_bytes(
    header + struct.pack("<I", len(facets) // FACET.size) + facets
)
