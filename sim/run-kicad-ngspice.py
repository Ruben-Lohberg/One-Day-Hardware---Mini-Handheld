"""Run an ASCII SPICE deck using the ngspice DLL included with Windows KiCad."""

import argparse
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(bin_dir, lines, analog=None):
    # See the ngspice manual's shared library API. KiCad and Python must
    # have the same architecture (normally 64-bit).
    with os.add_dll_directory(str(bin_dir)):
        lib = ctypes.CDLL(str(bin_dir / "ngspice.dll"))
        callback_type = ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p
        )
        messages = []

        @callback_type
        def send_char(message, _ident, _user):
            messages.append(message.decode(errors="replace"))
            return 0

        lib.ngSpice_Init.argtypes = [callback_type] + [ctypes.c_void_p] * 6
        lib.ngSpice_Init.restype = ctypes.c_int
        lib.ngSpice_Circ.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
        lib.ngSpice_Circ.restype = ctypes.c_int
        lib.ngSpice_Command.argtypes = [ctypes.c_char_p]
        lib.ngSpice_Command.restype = ctypes.c_int

        if not lines or any(not line.isascii() or b"\0" in line for line in lines):
            raise ValueError("expected a nonempty ASCII SPICE deck")
        circuit = (ctypes.c_char_p * (len(lines) + 1))(*lines, None)
        status = lib.ngSpice_Init(send_char, None, None, None, None, None, None)
        if analog:
            status = status or lib.ngSpice_Command(f"codemodel {analog.as_posix()}".encode("ascii"))
        status = status or lib.ngSpice_Circ(circuit)
        status = status or lib.ngSpice_Command(b"run")
        print("\n".join(messages))
        errors = ("error:", "fatal", "failed", "timestep too small", "aborted")
        return 1 if status or any(
            word in line.lower() for line in messages for word in errors
        ) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad-bin", type=Path, required=True)
    parser.add_argument("--analog", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("deck", type=Path)
    options = parser.parse_args()
    bin_dir, deck = options.kicad_bin.resolve(), options.deck.resolve()
    lines = deck.read_bytes().splitlines()
    uses_pwl = any(line.lower().startswith(b".model ") and b" pwl(" in line.lower()
                   for line in lines)
    if not uses_pwl or options.analog:
        return run(bin_dir, lines, options.analog)

    # KiCad's generated IBIS circuits need this XSPICE model. ngspice on
    # Windows needs an unquoted absolute path and holds the file open until
    # its process exits; a child process lets us clean up after the run.
    analog = bin_dir.parent / "lib" / "ngspice" / "analog.cm"
    with tempfile.TemporaryDirectory(prefix="spice-cm-") as scratch:
        path = Path(scratch) / analog.name
        if any(c.isspace() for c in str(path)) or not str(path).isascii():
            raise ValueError("Set TEMP to a writable ASCII directory without spaces")
        shutil.copyfile(analog, path)
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--kicad-bin", str(bin_dir),
             "--analog", str(path), str(deck)], check=False,
        ).returncode


if __name__ == "__main__":
    sys.exit(main())
