# QMCert

[![CI](https://github.com/amonreal/qmcert/actions/workflows/test.yml/badge.svg)](https://github.com/amonreal/qmcert/actions)
[![PyPI version](https://img.shields.io/pypi/v/qmcert.svg?color=blue)](https://pypi.org/project/qmcert/)
[![Python versions](https://img.shields.io/pypi/pyversions/qmcert.svg)](https://pypi.org/project/qmcert/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1234569.svg)](https://doi.org/10.5281/zenodo.1234569)

> **Automated Quality-Control, Stationary Point Certification, and Reproducibility Assessment for Quantum-Chemical Calculations.**

---

## Overview

**QMCert** is an open-source scientific toolkit designed to systematically audit, validate, and certify electronic structure calculations (**DFT, HF, post-HF, semiempirical**) from **ORCA**, **Gaussian**, **Q-Chem**, and **NWChem**.

Instead of manually inspecting log files to ensure calculations are publication-ready, `qmcert` performs a comprehensive automated audit with a single command:

- 🎯 **Stationary Point Certification**:
  - Automatically identifies imaginary frequencies ($\nu < 0\text{ cm}^{-1}$).
  - Validates **Local Minima** (0 imaginary modes) vs **Transition States** (exactly 1 imaginary mode).
  - Flags unphysical saddle points with clear diagnostic messages.
- 🔄 **Wavefunction & Spin Contamination ($\langle S^2 \rangle$)**:
  - Audits expectation values $\langle S^2 \rangle_{\text{calc}}$ vs exact theoretical $S(S+1)$.
  - Calculates spin contamination percentage and triggers alerts if $> 5.0\%$.
- ⚡ **SCF & Geometry Convergence Verification**:
  - Checks 4 standard convergence thresholds (Energy change, Max/RMS gradients, Max/RMS displacements).
- 🌡️ **Advanced Thermochemistry & Quasi-Harmonic Corrections**:
  - Extracts ZPVE, thermal enthalpy $H(T)$, Gibbs free energy $G(T)$, and entropy $S(T)$.
  - Applies **Grimme's quasi-RRHO harmonic entropy correction** to prevent rotational/vibrational divergence for low-frequency modes ($\nu < 100\text{ cm}^{-1}$).
- 🌈 **Simulated IR Vibrational Spectra**:
  - Lorentzian line-broadening with peak identification.
- 🚦 **Quantum Chemistry Validation Score (`PASS` / `WARNING` / `FAIL`)**.
- 📑 **Publication Deliverables**: Interactive self-contained `report.html`, publication vector plots (SVG/PDF/PNG 300 DPI), LaTeX summary tables (`.tex`), and a draft **Computational Details** Methods paragraph with automated **BibTeX citations**.

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
git clone https://github.com/amonreal/qmcert.git
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

### 2. Assess ORCA / Gaussian Output File
```bash
qmcert assess -i calculation.out -o qm_quality_report/
```

### 3. Certify a Transition State (TS) Calculation
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

print(f"Overall Certification: {report.overall_status}")
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
  version = {1.0.0},
  publisher = {Zenodo},
  url = {https://github.com/amonreal/qmcert}
}
```

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
