"""
Worked example: checking real ORCA 6.1.1 calculations.

Uses six real ORCA outputs bundled in tests/data (B3LYP-D3BJ/def2-SVP): two closed-shell minima,
a methyl radical, triplet O2, the planar-NH3 transition state and a phenol job whose SCF did not
converge.

Run from the repository root:

    python examples/orca_outputs_to_report.py
"""

import os

from qmcert import assess_qm_quality
from qmcert.parsers.generic_qm import parse_qm_output
from qmcert.reporters import (
    generate_qm_figures,
    generate_qm_html_report,
    generate_qm_manuscript_assets,
)

DATA_DIR = os.path.join("tests", "data")
OUTPUT_DIR = "orca_example_output"

# (file, what the calculation was meant to be)
JOBS = [
    ("h2o_min", "MINIMUM"),
    ("acetone_min", "MINIMUM"),
    ("ch3_radical", "MINIMUM"),
    ("o2_triplet", "MINIMUM"),
    ("nh3_planar_ts", "TRANSITION_STATE"),
    ("phenol_scf_not_converged", "MINIMUM"),
]


def assess(name, expected):
    data = parse_qm_output(os.path.join(DATA_DIR, name + ".out"))
    meta = data.get("metadata", {})
    report = assess_qm_quality(
        metadata=meta,
        scf_converged=data.get("scf_converged", True),
        n_scf_cycles=data.get("n_scf_cycles", 15),
        opt_converged=data.get("opt_converged"),
        n_opt_steps=data.get("n_opt_steps"),
        frequencies=data.get("frequencies"),
        intensities=data.get("intensities"),
        expected_point_type=expected,
        multiplicity=meta.get("multiplicity", 1),
        s2_calculated=data.get("s2_calculated"),
        homo_ev=data.get("homo_ev"),
        lumo_ev=data.get("lumo_ev"),
        thermochemistry=data.get("thermochemistry"),
        energies_trajectory=data.get("energies_trajectory"),
    )
    return data, report


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"{'calculation':26} {'expected':17} {'SCF':5} {'stationary point':20} {'<S^2>':>7}  overall")
    for name, expected in JOBS:
        data, report = assess(name, expected)
        freq = report.frequency_result
        point = f"{freq.point_type} ({freq.n_imaginary} imag)" if freq else "-"
        s2 = f"{data['s2_calculated']:.3f}" if data.get("s2_calculated") is not None else "-"
        print(f"{name:26} {expected:17} {report.scf_result['status']:5} {point:20} {s2:>7}  {report.overall_status}")

    # Full report for the transition state, checked against the right expectation.
    data, report = assess("nh3_planar_ts", "TRANSITION_STATE")
    generate_qm_figures(report, OUTPUT_DIR)
    assets = generate_qm_manuscript_assets(report, OUTPUT_DIR)
    with open(assets["methods_text"], "r", encoding="utf-8") as f:
        methods_text = f.read()
    with open(assets["citation_bib"], "r", encoding="utf-8") as f:
        citation_bib = f.read()
    html_path = os.path.join(OUTPUT_DIR, "report.html")
    generate_qm_html_report(report, html_path, methods_text=methods_text, citation_bib=citation_bib)
    print(f"\nReport for nh3_planar_ts written to {html_path}")


if __name__ == "__main__":
    main()
