"""
Applies QMCert 1.1.0 (commit 6c076b2) to the benchmark outputs for comparison.

    git worktree add ../qm110 6c076b2
    python validation/legacy_v110_run.py validation/benchmark_runs validation/results/legacy_v110.csv ../qm110
"""
import sys, os, json, glob
sys.path.insert(0, sys.argv[3])  # checkout of QMCert 1.1.0 (git worktree add <dir> 6c076b2)
from qmcert.parsers.orca import parse_orca_output
from qmcert.core.scoring import assess_qm_quality
import csv
root = sys.argv[1]
rows = []
for e in csv.DictReader(open(os.path.join(root, "expected.csv"))):
    out = os.path.join(root, e["name"], e["name"] + ".out")
    q = parse_orca_output(out)
    idx = e["expected_index"]
    ptype = "TRANSITION_STATE" if idx not in ("", None) and int(float(idx)) == 1 else "MINIMUM"
    r = assess_qm_quality(q["metadata"], scf_converged=q["scf_converged"], n_scf_cycles=q["n_scf_cycles"],
                          opt_converged=q["opt_converged"], n_opt_steps=q["n_opt_steps"], frequencies=q["frequencies"],
                          intensities=q["intensities"], expected_point_type=ptype, multiplicity=q["metadata"]["multiplicity"],
                          s2_calculated=q["s2_calculated"], homo_ev=q["homo_ev"], lumo_ev=q["lumo_ev"],
                          thermochemistry=q["thermochemistry"], energies_trajectory=q["energies_trajectory"])
    rows.append({"name": e["name"], "v110_overall": r.overall_status,
                 "v110_freq": r.frequency_result.status if r.frequency_result else "",
                 "v110_nimag": r.frequency_result.n_imaginary if r.frequency_result else "",
                 "v110_scf": r.scf_result["status"], "v110_opt": r.geometry_result["status"] if r.geometry_result else "",
                 "v110_spin": r.spin_result.status if r.spin_result else "", "v110_natoms": q["metadata"]["n_atoms"],
                 "v110_score": r.validation_score})
w = csv.DictWriter(open(sys.argv[2], "w", newline=""), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows))
