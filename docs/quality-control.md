# How the checks work

Each check returns a status (`PASS`, `WARNING` or `FAIL`) with a short diagnostic. The overall status is the worst of the individual statuses. A `WARNING` asks you to look at a result; a `FAIL` means the calculation should not be used as it is.

## SCF convergence

| Condition | Status |
|---|---|
| SCF converged in 80 % or fewer of the maximum number of cycles (128 by default) | `PASS` |
| SCF converged but needed more than 80 % of the maximum | `WARNING` |
| SCF did not converge | `FAIL` |

An optimisation contains many SCF runs. For ORCA, **the outcome of the last SCF in the file decides**, not the presence of any converged one. Function: [`evaluate_scf_convergence`](api.md).

## Geometry optimisation

`PASS` if the optimisation reached full convergence, `FAIL` otherwise (the structure is then not a stationary point). The energy along the optimisation is plotted in the report. Function: [`evaluate_geometry_optimization`](api.md).

## Stationary point from the frequencies

QMCert counts the **imaginary** harmonic frequencies, those below \(-10\ \mathrm{cm^{-1}}\) (the default `imaginary_cutoff`), and classifies the structure:

| Imaginary frequencies | Classification |
|---|---|
| 0 | `LOCAL_MINIMUM` |
| 1 | `TRANSITION_STATE` |
| 2 or more | `HIGHER_ORDER_SADDLE_POINT` |

The classification is then compared with the expected type, a **minimum** by default or a **transition state** with `--ts` (`expected_point_type="TRANSITION_STATE"` in Python):

| Expected | Found | Status |
|---|---|---|
| minimum | 0 imaginary | `PASS` |
| minimum | 1 or more imaginary | `FAIL` |
| transition state | exactly 1 imaginary | `PASS` |
| transition state | 0, or 2 or more imaginary | `FAIL` |

Function: [`classify_stationary_point`](api.md). The report also simulates the IR spectrum with Lorentzian broadening ([`simulate_ir_spectrum`](api.md)).

## Spin contamination

For unrestricted wavefunctions, \(\langle S^2\rangle\) is compared with the exact value \(S(S+1)\) for the multiplicity \(M = 2S+1\). The contamination is the relative deviation:

\[
\text{contamination} = \frac{\langle S^2\rangle - S(S+1)}{S(S+1)} \times 100\ \%
\]

| Condition (defaults) | Status |
|---|---|
| contamination \(\le 5\) % | `PASS` |
| \(5\) % to \(10\) % | `WARNING` (check whether a multireference or broken-symmetry treatment is needed) |
| above \(10\) % | `FAIL` |

Thresholds: `warn_threshold_pct`, `fail_threshold_pct` of [`evaluate_spin_contamination`](api.md).

## HOMO–LUMO gap

| Gap | Status |
|---|---|
| negative (HOMO above LUMO) | `FAIL`: unphysical SCF state |
| below 0.5 eV | `WARNING`: possible multireference or diradicaloid character |
| otherwise | `PASS` |

Function: [`evaluate_orbital_gap`](api.md).

## Quasi-RRHO thermochemistry

Low-frequency vibrational modes make the harmonic entropy diverge. Grimme's quasi-RRHO treatment (Grimme, *Chem. Eur. J.* **2012**, 18, 9955) damps their contribution with a cutoff of 100 cm\(^{-1}\) by default. QMCert computes the correction ([`calculate_quasi_rrho_corrections`](api.md)) and reports both the harmonic and the quasi-RRHO Gibbs energies.

**It reads whether the program already applied it.** ORCA 6 applies the quasi-RRHO entropy by default, so the Gibbs free energy it prints already contains the correction; adding a separate correction would count it twice (up to 0.73 kcal/mol in the benchmark). QMCert reads the `Quasi RRHO` setting of the output (`ThermochemistryData.quasi_rrho_applied_by_program`) and reports `gibbs_harmonic_hartree` and `gibbs_quasi_rrho_hartree` explicitly. This check does not change the status; it makes the energies you report unambiguous.
