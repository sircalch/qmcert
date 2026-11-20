# Validation

The `validation/` folder of the repository contains the benchmark, the inputs, the ORCA outputs and the result files, so the comparison can be repeated (`python validation/benchmark.py`, which needs cclib and GoodVibes as references).

## The benchmark

59 ORCA 6.1.1 calculations (B3LYP-D3BJ/def2-SVP): minima, radicals and triplets, saddle points, jobs with a truncated optimisation, jobs with an unconverged SCF and UHF single points. The references are:

- **cclib 1.8:** final energy, frequencies, IR intensities, HOMO and LUMO energies, optimisation convergence;
- **ORCA's own output:** \(\langle S^2\rangle\), the printed thermochemistry and the frequency list;
- **the design** of each job (`validation/benchmark_runs/expected.csv`): the expected saddle-point index and whether it should converge.

## Agreement with the references

| Quantity | Reference | Jobs | Largest deviation |
|---|---|---|---|
| Final energy | cclib | 57 | \(5 \times 10^{-10}\) Eh |
| Harmonic frequencies and IR intensities | cclib | 52 | 0 (identical) |
| HOMO and LUMO energies | cclib | 57 | \(6 \times 10^{-5}\) eV |
| Number of imaginary frequencies | cclib | 52 | agrees in all |
| Zero-point energy, enthalpy, Gibbs energy as printed by ORCA | ORCA output | 52 | 0 (identical) |
| \(\langle S^2\rangle\) | ORCA output | 16 | 0 (identical) |

## Verdicts

QMCert gives `PASS` to 48 calculations and `FAIL` to 11. The 11 failures are the intended ones or ones that the design did not foresee:

- 4 jobs whose frequencies show a **different stationary point than designed** (`vinyl`, `methylene_triplet`, `water_linear` and `butane_syn`, for example a structure that was meant to be a minimum with one imaginary frequency). cclib agrees on the number of imaginary frequencies, so QMCert reports what the calculation found rather than what was intended;
- 3 jobs with a **truncated optimisation** and 2 with an **unconverged SCF**;
- 2 **UHF single points with severe spin contamination** (\(\langle S^2\rangle\) = 0.96 and 1.17 for doublets).

## Findings that changed the code

The validation found real defects in earlier versions, which are documented in the [changelog](https://github.com/sircalch/qmcert/blob/master/CHANGELOG.md): frequencies were never read from real ORCA 6 output, HOMO and LUMO were taken from the wrong lines, the SCF convergence was decided by any occurrence instead of the last SCF, and the quasi-RRHO correction could be counted twice because ORCA 6 applies it by default. These are the kinds of errors that a benchmark on real outputs, not on synthetic ones, makes visible.

## Limits

The benchmark covers ORCA 6.1.1 outputs of small and medium molecules with one method. Gaussian outputs are parsed, but they are not part of this benchmark. The thresholds for spin contamination and the HOMO–LUMO gap are conventional defaults, not validated against reference calculations; adjust them to your system.
