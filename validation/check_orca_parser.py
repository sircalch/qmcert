"""
Compares qmcert.parsers.orca.parse_orca_output with an independent, section-aware reading of real
ORCA 6.1 outputs (validation/orca_runs/*.out).

    python validation/check_orca_parser.py
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from qmcert.parsers.orca import parse_orca_output  # noqa: E402

HERE = os.path.dirname(__file__)


def reference(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    ref = {}
    ref["version"] = re.search(r"Program Version\s+([\d.]+)", txt).group(1)
    ref["final_energy_eh"] = float(re.findall(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)", txt)[-1])
    ref["charge"] = int(re.search(r"Total Charge\s+Charge\s+\.+\s+(-?\d+)", txt).group(1))
    ref["multiplicity"] = int(re.search(r"Multiplicity\s+Mult\s+\.+\s+(\d+)", txt).group(1))
    s2 = re.findall(r"Expectation value of <S\*\*2>\s*:\s*([\d.]+)", txt)
    ref["s2"] = float(s2[-1]) if s2 else None
    # last frequency block: lines "  i:   value cm**-1"
    blocks = re.split(r"VIBRATIONAL FREQUENCIES\s*\n-+\s*\n", txt)
    if len(blocks) > 1:
        body = blocks[-1].split("NORMAL MODES")[0]
        freqs = [float(v) for v in re.findall(r"^\s*\d+:\s+(-?\d+\.\d+)\s+cm\*\*-1", body, re.M)]
        nonzero = [f for f in freqs if abs(f) > 1e-6]
        ref["n_imag"] = sum(1 for f in nonzero if f < 0)
        ref["lowest_freq"] = min(nonzero) if nonzero else None
        ref["n_freqs"] = len(nonzero)
    # last orbital-energy table(s): columns NO OCC E(Eh) E(eV)
    ob = txt.rsplit("ORBITAL ENERGIES", 1)[-1]
    ob = ob.split("MULLIKEN")[0]
    tables = re.split(r"SPIN (?:UP|DOWN) ORBITALS", ob)
    tables = tables[1:] if len(tables) > 1 else [ob]
    homo, lumo = [], []
    for t in tables:
        rows = [(float(o), float(ev)) for o, ev in re.findall(r"^\s*\d+\s+(\d\.\d+)\s+-?\d+\.\d+\s+(-?\d+\.\d+)", t, re.M)]
        occ = [e for o, e in rows if o > 0.5]
        vir = [e for o, e in rows if o < 0.5]
        if occ:
            homo.append(max(occ))
        if vir:
            lumo.append(min(vir))
    ref["homo_ev"] = max(homo) if homo else None
    ref["lumo_ev"] = min(lumo) if lumo else None
    ref["gap_ev"] = ref["lumo_ev"] - ref["homo_ev"] if homo and lumo else None
    z = re.search(r"Zero point energy\s+\.+\s+(-?\d+\.\d+)\s+Eh", txt)
    ref["zpe_eh"] = float(z.group(1)) if z else None
    g = re.search(r"Final Gibbs free energy\s+\.+\s+(-?\d+\.\d+)\s+Eh", txt)
    ref["gibbs_eh"] = float(g.group(1)) if g else None
    ref["opt_converged"] = "OPTIMIZATION RUN DONE" in txt or "HURRAY" in txt
    return ref


def main():
    for path in sorted(glob.glob(os.path.join(HERE, "orca_runs", "*.out"))):
        name = os.path.basename(path)
        ref = reference(path)
        got = parse_orca_output(path)
        print(f"\n=== {name}")
        print("   reference:", {k: (round(v, 6) if isinstance(v, float) else v) for k, v in ref.items()})
        flat = {k: v for k, v in got.items() if not isinstance(v, (list, dict))}
        print("   qmcert   :", {k: (round(v, 6) if isinstance(v, float) else v) for k, v in flat.items()})
        for k, v in got.items():
            if isinstance(v, (list, dict)):
                print(f"   qmcert {k}: {str(v)[:160]}")


if __name__ == "__main__":
    main()
