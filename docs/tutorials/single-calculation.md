# Checking one calculation

## Input

Give QMCert the output file of an ORCA or Gaussian job (`.out`, `.log`). The program is detected from the file. The more the job contains, the more can be checked: an optimisation with a frequency calculation allows the stationary point to be classified, and an unrestricted calculation allows the spin contamination to be judged.

The repository includes `sample_orca_calc.out`, a small **synthetic** ORCA-like output for trying the tool (the report says so; it is not a real calculation), and real ORCA 6.1.1 outputs in `tests/data/`.

## Command line

```bash
qmcert assess -i sample_orca_calc.out -o sample_report/
```

```text
 [RESULT] Overall Quantum Chemistry Certification: PASS
 * Stationary Point : LOCAL_MINIMUM (0 imag modes) | Status: PASS
 * SCF Convergence  : Status: PASS
```

Open `sample_report/report.html` for the diagnostic message of each check. A real job whose SCF did not converge shows what a failure looks like:

```bash
qmcert assess -i tests/data/phenol_scf_not_converged.out -o phenol_report/
```

```text
 [RESULT] Overall Quantum Chemistry Certification: FAIL
 * SCF Convergence  : Status: FAIL
```

The overall status is the worst of all checks, so an unconverged SCF makes the whole calculation `FAIL`: its energy cannot be trusted.

## Minimum or transition state

By default QMCert expects a **minimum**. If you are checking a transition state, say so with `--ts`; QMCert then expects exactly one imaginary frequency. The same output can pass or fail depending on what you intended; the [worked example](worked-example.md) shows this with a real transition state.

```bash
qmcert assess -i ts_freq.out --ts -o ts_report/
```

## Python API

```python
from qmcert import assess_qm_quality
from qmcert.parsers.generic_qm import parse_qm_output

data = parse_qm_output("tests/data/h2o_min.out")
meta = data["metadata"]

report = assess_qm_quality(
    metadata=meta,
    scf_converged=data["scf_converged"],
    n_scf_cycles=data["n_scf_cycles"],
    opt_converged=data["opt_converged"],
    n_opt_steps=data["n_opt_steps"],
    frequencies=data["frequencies"],
    intensities=data["intensities"],
    expected_point_type="MINIMUM",
    multiplicity=meta["multiplicity"],
    s2_calculated=data.get("s2_calculated"),
    homo_ev=data.get("homo_ev"),
    lumo_ev=data.get("lumo_ev"),
    thermochemistry=data.get("thermochemistry"),
)
print(report.overall_status)
print(report.frequency_result.point_type, report.frequency_result.n_imaginary)
```

See the [API reference](../api.md) for all arguments and [How the checks work](../quality-control.md) for the meaning of each status.
