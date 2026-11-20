# QMCert

**Quality control for quantum-chemistry calculations.**

Before the energies of a calculation are used, a few things should be true: the SCF converged, the geometry optimisation finished, the structure is the kind of stationary point you meant (a minimum or a transition state), an open-shell wavefunction is not badly spin-contaminated, and the thermochemistry is not distorted by low-frequency modes. QMCert reads the output of a calculation and checks exactly those points:

- **SCF convergence** and **geometry optimisation convergence**.
- **Nature of the stationary point** from the harmonic frequencies: local minimum, transition state or higher-order saddle point, compared with what you intended.
- **Spin contamination** \(\langle S^2\rangle\) in unrestricted calculations.
- **HOMO–LUMO gap**, flagging inverted or extremely narrow gaps.
- **Quasi-RRHO thermochemistry** (Grimme) for low-frequency modes, reading whether the program already applied it so that the correction is not counted twice.

Every decision is recorded, and the results are written as a self-contained HTML report, figures (optimisation trajectory and simulated IR spectrum), LaTeX and CSV tables and a draft methods paragraph.

```bash
pip install qmcert
qmcert demo -o my_first_report/
```

Open `my_first_report/report.html` in a browser. The demo uses **synthetic** ORCA-like data, which the report states explicitly; for real calculations see the [worked example](tutorials/worked-example.md).

## Where to go next

- [Installation](installation.md)
- [Checking one calculation](tutorials/single-calculation.md)
- [Worked example: six real ORCA calculations](tutorials/worked-example.md)
- [How the checks work](quality-control.md): what each status means and the thresholds
- [Validation](validation.md): comparison with cclib, GoodVibes and ORCA on 59 calculations
- [API reference](api.md)

## Scope

QMCert reads **ORCA** and **Gaussian** output files. It checks the numerical and structural integrity of a calculation; it does not judge whether the method or basis set is appropriate for your system, and a `PASS` does not replace chemical judgement. Other programs are not supported.

## Getting help

Questions and bug reports are welcome in the [issue tracker](https://github.com/sircalch/qmcert/issues). See [Support and contributing](support.md).
