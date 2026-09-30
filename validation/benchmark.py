"""
Compares QMCert with independent references on the ORCA 6.1 benchmark runs.

    python validation/benchmark.py            (needs cclib and GoodVibes: see REF_PYTHON)

References:
    cclib 1.8      final energy, frequencies, IR intensities, HOMO/LUMO, optimisation convergence
    GoodVibes 3    harmonic and quasi-RRHO (Grimme, 100 cm-1) thermochemistry from the same output
    ORCA output    <S^2>, printed thermochemistry, the frequency list itself (number of imaginary modes)
    design         expected saddle-point index and convergence (validation/benchmark_runs/expected.csv)
Output: validation/results/benchmark.csv
"""
import glob
import json
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from qmcert.parsers.orca import parse_orca_output  # noqa: E402
from qmcert.core.scoring import assess_qm_quality  # noqa: E402

RUNS = os.path.join(HERE, "benchmark_runs")
REF_PYTHON = os.environ.get("REF_PYTHON", os.path.join(os.environ.get("TEMP", ""), "claude",
                            "C--Users-Andre-Proyectos-doctorado", "f3e2a386-fde5-4789-b96e-63888bc00667",
                            "scratchpad", "simvenv", "Scripts", "python.exe"))
EH_PER_EV = 1 / 27.211386245988
KCAL = 627.509474

REF_SCRIPT = r'''
import json, sys, cclib
from cclib.parser.utils import convertor
d = cclib.io.ccread(sys.argv[1])
out = {}
# cclib stores energies in eV with its own conversion factor; convert back with the same factor
out["energy_eh"] = convertor(float(d.scfenergies[-1]), "eV", "hartree") if hasattr(d, "scfenergies") else None
out["freqs"] = d.vibfreqs.tolist() if hasattr(d, "vibfreqs") else None
out["irs"] = d.vibirs.tolist() if hasattr(d, "vibirs") else None
if hasattr(d, "moenergies") and hasattr(d, "homos"):
    homo = max(float(d.moenergies[s][d.homos[s]]) for s in range(len(d.homos)))
    lumo = min(float(d.moenergies[s][d.homos[s] + 1]) for s in range(len(d.homos)))
    out["homo_ev"], out["lumo_ev"] = homo, lumo
out["optdone"] = bool(d.optdone) if hasattr(d, "optdone") else None
out["mult"] = int(d.mult) if hasattr(d, "mult") else None
out["natom"] = int(d.natom) if hasattr(d, "natom") else None
print(json.dumps(out))
'''


def cclib_ref(out):
    r = subprocess.run([REF_PYTHON, "-c", REF_SCRIPT, out], capture_output=True, text=True)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return {"error": (r.stderr or r.stdout)[-300:]}


def goodvibes_ref(out):
    d = os.path.dirname(out)
    subprocess.run([REF_PYTHON, "-m", "goodvibes", os.path.basename(out), "-q"], cwd=d, capture_output=True, text=True)
    dat = os.path.join(d, "Goodvibes_output.dat")
    if not os.path.exists(dat):
        return {}
    header = None
    names = {"ZPE": "gv_zpe", "H": "gv_h", "qh-H": "gv_qh", "T.S": "gv_ts", "T.qh-S": "gv_tqs", "G(T)": "gv_g",
             "qh-G(T)": "gv_qg"}
    for line in open(dat, encoding="utf-8", errors="ignore"):
        tok = line.split()
        if tok[:1] == ["Structure"]:
            header = tok[1:]
        elif header and len(tok) == len(header) + 2 and tok[0] == "o" and tok[1] == os.path.basename(out)[:-4]:
            vals = dict(zip(header, map(float, tok[2:])))
            return {names[k]: v for k, v in vals.items() if k in names}
    return {}


def orca_printed(out):
    txt = open(out, encoding="utf-8", errors="ignore").read()
    r = {}
    for key, pat in (("orca_zpe", r"Zero point energy\s+\.\.\.\s+(-?\d+\.\d+) Eh"),
                     ("orca_h", r"Total Enthalpy\s+\.\.\.\s+(-?\d+\.\d+) Eh"),
                     ("orca_ts", r"Final entropy term\s+\.\.\.\s+(-?\d+\.\d+) Eh"),
                     ("orca_g", r"Final Gibbs free energy\s+\.\.\.\s+(-?\d+\.\d+) Eh"),
                     ("orca_svib", r"Vibrational entropy\s+\.\.\.\s+(-?\d+\.\d+) Eh")):
        m = re.findall(pat, txt)
        r[key] = float(m[-1]) if m else np.nan
    s2 = re.findall(r"Expectation value of <S\*\*2>\s*:\s*([\d.]+)", txt)
    r["orca_s2"] = float(s2[-1]) if s2 else np.nan
    r["orca_normal"] = "ORCA TERMINATED NORMALLY" in txt[-3000:]
    r["orca_opt_converged"] = "THE OPTIMIZATION HAS CONVERGED" in txt or "OPTIMIZATION RUN DONE" in txt and "HURRAY" in txt
    return r


def one(name, exp):
    out = os.path.join(RUNS, name, name + ".out")
    row = {"name": name, "set": exp["set"], "mult": int(exp["mult"]),
           "expected_index": exp["expected_index"], "expected_converged": int(exp["expected_converged"])}
    q = parse_orca_output(out)
    th = q.get("thermochemistry")
    idx = exp["expected_index"]
    ptype = "TRANSITION_STATE" if (pd.notna(idx) and int(float(idx)) == 1) else "MINIMUM"
    rep = assess_qm_quality(q["metadata"], scf_converged=q["scf_converged"], n_scf_cycles=q["n_scf_cycles"],
                            opt_converged=q["opt_converged"], n_opt_steps=q["n_opt_steps"],
                            frequencies=q["frequencies"], intensities=q["intensities"], expected_point_type=ptype,
                            multiplicity=q["metadata"]["multiplicity"], s2_calculated=q["s2_calculated"],
                            homo_ev=q["homo_ev"], lumo_ev=q["lumo_ev"], thermochemistry=th,
                            energies_trajectory=q["energies_trajectory"])
    fr = rep.frequency_result
    row.update(qm_energy=q["final_energy_hartree"], qm_nfreq=len(q["frequencies"] or []),
               qm_nimag=fr.n_imaginary if fr else np.nan, qm_point=fr.point_type if fr else "",
               qm_freq_status=fr.status if fr else "", qm_opt_converged=q["opt_converged"],
               qm_opt_status=rep.geometry_result["status"] if rep.geometry_result else "",
               qm_scf_status=rep.scf_result["status"], qm_s2=q["s2_calculated"],
               qm_spin_status=rep.spin_result.status if rep.spin_result else "",
               qm_homo=q["homo_ev"], qm_lumo=q["lumo_ev"], qm_natoms=q["metadata"].get("n_atoms"),
               qm_mult=q["metadata"].get("multiplicity"), qm_overall=rep.overall_status)
    if th is not None:
        row.update(qm_zpe=th.zpve_hartree, qm_h=th.enthalpy_hartree, qm_g=th.gibbs_free_energy_hartree)
    if rep.quasi_rrho_correction:
        row["qm_qrrho_dg"] = rep.quasi_rrho_correction["delta_g_quasi_rrho_hartree"]
        row["qm_n_low"] = rep.quasi_rrho_correction["n_low_freq_modes"]

    c = cclib_ref(out)
    row["cc_error"] = c.get("error", "")
    if "energy_eh" in c:
        row["dev_energy"] = (abs(q["final_energy_hartree"] - c["energy_eh"])
                             if c["energy_eh"] is not None and q["final_energy_hartree"] is not None else np.nan)
        cf = np.array(c.get("freqs") or [])
        qf = np.array(q["frequencies"] or [])
        row["cc_nfreq"] = len(cf)
        row["cc_nimag"] = int(np.sum(cf < 0))
        if len(cf) and len(cf) == len(qf):
            row["dev_freq"] = float(np.max(np.abs(np.sort(cf) - np.sort(qf))))
            ci, qi = np.array(c.get("irs") or []), np.array(q["intensities"] or [])
            if len(ci) == len(qi) and len(qi):
                row["dev_ir"] = float(np.max(np.abs(ci[np.argsort(cf)] - qi[np.argsort(qf)])))
        if c.get("homo_ev") is not None and q["homo_ev"] is not None:
            row["dev_homo"] = abs(q["homo_ev"] - c["homo_ev"])
            row["dev_lumo"] = abs(q["lumo_ev"] - c["lumo_ev"])
        row["cc_optdone"] = c.get("optdone")
        row["cc_natom"] = c.get("natom")
    row.update(orca_printed(out))
    row.update(goodvibes_ref(out))
    return row


def main():
    exp = pd.read_csv(os.path.join(RUNS, "expected.csv"))
    rows = []
    for _, e in exp.iterrows():
        out = os.path.join(RUNS, e["name"], e["name"] + ".out")
        if not os.path.exists(out):
            print("missing", e["name"])
            continue
        rows.append(one(e["name"], e))
        print(e["name"], "done", flush=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    pd.DataFrame(rows).to_csv(os.path.join(HERE, "results", "benchmark.csv"), index=False)
    print(len(rows), "runs")


if __name__ == "__main__":
    main()
