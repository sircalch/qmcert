# QMCert

[![CI](https://github.com/sircalch/qmcert/actions/workflows/test.yml/badge.svg)](https://github.com/sircalch/qmcert/actions)
[![PyPI version](https://img.shields.io/pypi/v/qmcert.svg?color=blue)](https://pypi.org/project/qmcert/)
[![Python versions](https://img.shields.io/pypi/pyversions/qmcert.svg)](https://pypi.org/project/qmcert/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22217572.svg)](https://doi.org/10.5281/zenodo.22217572)

> **Quality checks for quantum-chemical calculations: convergence, stationary points, spin contamination and quasi-RRHO free energies.**

---

## Overview

**QMCert** is an open-source Python package that reads the output of a quantum-chemistry calculation and checks what should be checked before its energies are used: convergence, the nature of the stationary point, spin contamination and the treatment of low-frequency modes in free energies. The ORCA parser was validated on 59 real ORCA 6.1 outputs against cclib, GoodVibes and ORCA's own printout (`validation/`); a Gaussian parser is included but has not been validated on real outputs.

- **Convergence**: outcome of the last SCF in the file; the optimiser's convergence banner.
- **Stationary point**: imaginary frequencies below -10 cm^-1 are counted; a minimum needs none, a transition state exactly one; two or more is a higher-order saddle point. A converged optimisation is not taken as evidence of a minimum.
- **Spin contamination**: deviation of <S^2> from S(S+1), as a percentage of S(S+1) (warning above 5%, failure above 10%).
- **Thermochemistry**: ZPE, H, G and S as printed by the program, and Grimme's quasi-RRHO vibrational entropy (omega_0 = 100 cm^-1). ORCA 6.1 applies quasi-RRHO by default (its output says so); QMCert reads that setting and reports the harmonic and quasi-RRHO free energies explicitly, so the correction is never applied twice.
- **IR spectrum**: Lorentzian broadening of the computed intensities.

> **Version 1.2.0** fixes a reporting defect found by the validation: version 1.1.0 reported a separate quasi-RRHO correction on top of ORCA's free energy, which already contained it (up to 0.73 kcal/mol in the benchmark). See the CHANGELOG.

- **Verdicts**: `PASS` / `WARNING` / `FAIL` for each check; the overall status is the worst of them.
- 📑 **Publication Deliverables**: Interactive self-contained `report.html`, publication vector plots (SVG/PDF/PNG 300 DPI), LaTeX summary tables (`.tex`), and a draft computational-details paragraph that states the results found, including failures.

```
  Quantum Chemical Output (.out, .log)
                    │
                    ▼
  ┌───────────────────────────────────────────────────────────┐
  │                          QMCert                           │
  │  ├── Stationary Point Certification (0 or 1 Imag Freq)    │
  │  ├── Spin Contamination Audit (<S^2> vs S(S+1))           │
  │  ├── SCF & Geometry Optimization Convergence              │
  │  ├── Grimme Quasi-RRHO Thermochemistry Corrections        │
  │  └── Frontier Orbital Gap & Simulated IR Spectrum         │
  └───────────────────────────────────────────────────────────┘
                    │
                    ▼
  ┌───────────────────────────────────────────────────────────┐
  │                   Publication Deliverables                │
  │  ├── report.html (Interactive Dashboard & Badges)         │
  │  ├── qmcert_simulated_ir_spectrum.pdf/svg/png             │
  │  ├── qmcert_summary_table.tex / .csv                      │
  │  ├── methods_snippet.txt (Ready for Manuscript)           │
  │  └── citation.bib (BibTeX Reference)                      │
  └───────────────────────────────────────────────────────────┘
```

---

## Installation

### From PyPI
```bash
pip install qmcert
```

### From Source
```bash
git clone https://github.com/sircalch/qmcert.git
cd qmcert
pip install -e .[dev]
```

---

## Quickstart (CLI)

### 1. Run Demonstration Mode (Instant Benchmark DFT Calculation)
```bash
qmcert demo -o my_qm_validation/
```
Open `my_qm_validation/report.html` in any browser to inspect the report and simulated IR spectrum!

### 2. Assess an ORCA output file
```bash
qmcert assess -i calculation.out -o qm_quality_report/
```

### 3. Check a transition-state calculation
```bash
qmcert assess -i ts_optimization.out --ts -o ts_report/
```

---

## Python API Usage

```python
from qmcert import assess_qm_quality
from qmcert.parsers import parse_qm_output
from qmcert.reporters import generate_qm_figures, generate_qm_manuscript_assets, generate_qm_html_report

# 1. Parse quantum chemistry output (ORCA / Gaussian)
parsed_data = parse_qm_output("my_dft_calc.out")

# 2. Assess calculation quality
report = assess_qm_quality(
    metadata=parsed_data["metadata"],
    scf_converged=parsed_data["scf_converged"],
    frequencies=parsed_data["frequencies"],
    intensities=parsed_data["intensities"],
    expected_point_type="MINIMUM",
    s2_calculated=parsed_data["s2_calculated"],
    thermochemistry=parsed_data["thermochemistry"]
)

print(f"Overall status: {report.overall_status}")
print(f"Stationary Point: {report.frequency_result.point_type}")

# 3. Export all publication assets
generate_qm_figures(report, "output_dir/")
generate_qm_manuscript_assets(report, "output_dir/")
generate_qm_html_report(report, "output_dir/report.html")
```

---

## Citation

If you use QMCert to validate quantum-chemical calculations, certify stationary points, or calculate quasi-RRHO corrections, please cite:

```bibtex
@software{monreal2026qmcert,
  author = {Monreal-Hern{\'a}ndez, Andre},
  title = {{QMCert: Automated Quality-Control, Stationary Point Certification, and Reproducibility Assessment for Quantum-Chemical Calculations}},
  year = {2026},
  version = {1.2.0},
  publisher = {Zenodo},
  url = {https://github.com/sircalch/qmcert}
}
```

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

