"""Convert ST's PB13 IBIS models with KiCad and build a clock test deck."""

import argparse
import hashlib
import re
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path


COMPONENT = "stm32g070_071_081_lqfp48"
SPEEDS = ("high", "fast", "medium", "low")


def model_name(speed):
    # PB13's io6_i2c_ft selector also lists these push-pull modes.
    return f"io6_ft_3v3_{speed}speed"


def with_voltage_range(ibis):
    # KiCad 10.0.7 uses [Voltage Range] for its generated supply even when
    # ST supplies only individual references. Fill that missing field in the
    # temporary copy from the matching ST pull-up reference; keep all tables.
    chunks = re.split(rb"(?mi)(?=^\[Model\][ \t]+)", ibis)
    for speed in SPEEDS:
        match = re.compile(rb"^\[Model\][ \t]+" + model_name(speed).encode() + rb"[ \t]*\r?\n")
        idx = next(i for i, c in enumerate(chunks) if match.match(c))
        if not re.search(rb"(?mi)^\[Voltage Range\]", chunks[idx]):
            pattern = rb"(?mi)^\[Pullup Reference\][ \t]+([^\r\n]+)(\r?\n)"
            chunks[idx], count = re.subn(
                pattern, rb"[Voltage Range] \1\2[Pullup Reference] \1\2", chunks[idx], count=1
            )
            if count != 1:
                raise ValueError(f"Missing ST supply reference for {speed}")
    return b"".join(chunks)


def schematic(refs):
    root = uuid.uuid4()
    instances = []
    for i, (speed, ref) in enumerate(refs.items()):
        x = 35 + 20 * i
        properties = {
            "Reference": ref,
            "Value": "IBIS_DRIVER",
            "Sim.Device": "IBIS",
            "Sim.Type": "RECTDRIVER",
            "Sim.Pins": "1=GND 2=IN/OUT",
            "Sim.Name": COMPONENT,
            "Sim.Library": COMPONENT + ".ibs",
            "Sim.Ibis.Pin": "25",
            "Sim.Ibis.Model": model_name(speed),
            # Allow the complete IBIS waveforms (low mode tables reach 200 ns).
            "Sim.Params": "ton=250n toff=250n td=2n n=2",
        }
        fields = "\n".join(
            f'(property "{k}" "{v}" (at {x} 50 0) (effects (font (size 1 1))))'
            for k, v in properties.items()
        )
        instances.append(f'''
        (symbol (lib_id "Simulation_SPICE:IBIS_DRIVER") (at {x} 50 0) (unit 1)
          (in_bom yes) (on_board no) (dnp no) (uuid "{uuid.uuid4()}")
          {fields}
          (pin "1" (uuid "{uuid.uuid4()}")) (pin "2" (uuid "{uuid.uuid4()}"))
          (instances (project "driver" (path "/{root}" (reference "{ref}") (unit 1)))))
        ''')
    return f'''(kicad_sch (version 20250114) (generator "handheld_sim") (uuid "{root}") (paper "A4")
      (lib_symbols
        (symbol "Simulation_SPICE:IBIS_DRIVER"
          (in_bom yes) (on_board no)
          (property "Reference" "U" (at 0 0 0) (effects (font (size 1 1))))
          (property "Value" "IBIS_DRIVER" (at 0 0 0) (effects (font (size 1 1))))
          (symbol "IBIS_DRIVER_1_1"
            (pin power_in line (at 0 -5.08 90) (length 2.54)
              (name "GND" (effects (font (size 1 1)))) (number "1" (effects (font (size 1 1)))))
            (pin output line (at 5.08 0 180) (length 2.54)
              (name "IN/OUT" (effects (font (size 1 1)))) (number "2" (effects (font (size 1 1))))))))
      {"".join(instances)}
    )
    '''


def convert(cli, archive):
    refs = {speed: f"U{uuid.uuid4().int % 1000000000}" for speed in SPEEDS}
    with tempfile.TemporaryDirectory(prefix="handheld-ibis-") as td:
        folder = Path(td)
        with zipfile.ZipFile(archive) as package:
            ibis = package.read(COMPONENT + ".ibs")
        if not re.search(rb"(?m)^25\s+PB13\s+io6_i2c_ft\s", ibis):
            raise ValueError("IBIS archive does not map PB13 to the expected pin selector")
        (folder / (COMPONENT + ".ibs")).write_bytes(with_voltage_range(ibis))
        (folder / "driver.kicad_sch").write_text(schematic(refs), encoding="ascii")
        subprocess.run(
            [str(cli), "sch", "export", "netlist", "--format", "spice",
             "-o", "driver.cir", "driver.kicad_sch"],
            cwd=folder, check=True,
        )
        export = (folder / "driver.cir").read_text(encoding="utf-8")
        includes = [Path(p) for p in re.findall(r'(?mi)^\.include\s+"([^"]+)"', export)]
        result = {}
        for speed, ref in refs.items():
            matches = [p for p in includes if p.stem == ref]
            if len(matches) != 1:
                raise RuntimeError(f"KiCad did not generate the IBIS subcircuit for {speed}")
            path = folder / matches[0]
            model = path.read_text(encoding="ascii")
            if "*Pin number: 25" not in model or f"*Model: {model_name(speed)}" not in model:
                raise RuntimeError(f"Unexpected IBIS conversion for {speed}")
            if re.search(r"(?i)\bpwl\s*\(\s*\)", model):
                raise RuntimeError(f"KiCad generated an empty switching waveform for {speed}")
            name = re.search(r"(?mi)^\.subckt\s+(\S+)\s+GND\s+PIN\b", model)
            if not name:
                raise RuntimeError(f"Unexpected SPICE port order for {speed}")
            result[speed] = model.replace(name[1], f"pb13_{speed}")
        return result, hashlib.sha256(ibis).hexdigest()


def build(cli, archive, output):
    models, digest = convert(cli, archive)
    layout = Path(__file__).with_name("lcd-sck-layout.cir").read_text(encoding="ascii")
    interconnect = layout[layout.index(".subckt section"):layout.index("\nVfast")]
    lines = [
        "Mini Handheld - ST IBIS PB13 driver with estimated PCB and flex",
        f"* ST {COMPONENT}.ibs SHA256 {digest}",
        "* Driver/package from ST IBIS. Receiver/flex/vias/PCB RLC are estimates.",
        "* Ideal 3.3 V nominal driver supply. No receiver clamp or return-path extraction.",
        interconnect,
        *models.values(),
        ".tran 10p 500n 0 10p",
    ]
    cases = [(speed, speed, "") for speed in SPEEDS] + [
        ("high33", "high", "rseries=33"),
        ("high_light", "high", "zpcb=140 zflex=100 cload=3p"),
        ("high_heavy", "high", "zpcb=65 zflex=55 cload=12p"),
    ]
    for name, speed, params in cases:
        lines += [
            f"Xgpio_{name} 0 src_{name} pb13_{speed}",
            f"Xpath_{name} src_{name} rx_{name} clock rout=1m {params}",
            f".meas tran peak_{name} MAX v(rx_{name}) FROM=2n TO=250n",
            f".meas tran low_{name} MIN v(rx_{name}) FROM=252n TO=499n",
            f".meas tran rise_{name} TRIG v(rx_{name}) VAL=0.33 RISE=1 "
            f"TARG v(rx_{name}) VAL=2.97 RISE=1",
        ]
    output.write_text("\n".join(lines + [".end", ""]), encoding="ascii")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad-cli", required=True, type=Path)
    parser.add_argument("--st-archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.kicad_cli.resolve(), args.st_archive.resolve(), args.output.resolve())
