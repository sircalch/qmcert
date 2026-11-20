# Worked example: six real ORCA calculations

This example checks six real ORCA 6.1.1 outputs (B3LYP-D3BJ/def2-SVP), bundled with the repository in `tests/data/`. Run it from the repository root:

```bash
python examples/orca_outputs_to_report.py
```

```text
calculation                expected          SCF   stationary point       <S^2>  overall
h2o_min                    MINIMUM           PASS  LOCAL_MINIMUM (0 imag)       -  PASS
acetone_min                MINIMUM           PASS  LOCAL_MINIMUM (0 imag)       -  PASS
ch3_radical                MINIMUM           PASS  LOCAL_MINIMUM (0 imag)   0.754  PASS
o2_triplet                 MINIMUM           PASS  -                      2.007  PASS
nh3_planar_ts              TRANSITION_STATE  PASS  TRANSITION_STATE (1 imag)       -  PASS
phenol_scf_not_converged   MINIMUM           FAIL  -                          -  FAIL
```

## What each calculation shows

- **`h2o_min`, `acetone_min`:** closed-shell optimisations with a frequency calculation. All frequencies are real, so the structures are certified as local minima.
- **`ch3_radical`:** a doublet methyl radical (UKS). \(\langle S^2\rangle = 0.754\) against the exact value \(S(S+1) = 0.75\), a contamination of 0.5 %, well below the 5 % warning limit.
- **`o2_triplet`:** a triplet \(\mathrm{O_2}\) single-point calculation, with no optimisation or frequencies, so there is no stationary point to classify and only the SCF and the spin are checked. \(\langle S^2\rangle = 2.007\) against the exact 2.0 (0.3 % contamination).
angle = 2.007\) against the exact 2.0 (0.3 % contamination).
- **`nh3_planar_ts`:** the planar ammonia inversion saddle point. It has one imaginary frequency. It is certified as a transition state **because it was declared as one**.
- **`phenol_scf_not_converged`:** a job whose SCF did not converge. It is a `FAIL`: with an unconverged wavefunction, nothing else in the output can be trusted.

## The same output, two intentions

The planar-NH\(_3\) result depends on what you meant to compute. Checked as a minimum (the default), the same file fails:

```bash
qmcert assess -i tests/data/nh3_planar_ts.out -o nh3_as_minimum/
```

```text
 [RESULT] Overall Quantum Chemistry Certification: FAIL
 * Stationary Point : TRANSITION_STATE (1 imag modes) | Status: FAIL
```

and with `--ts` it passes:

```bash
qmcert assess -i tests/data/nh3_planar_ts.out --ts -o nh3_as_ts/
```

```text
 [RESULT] Overall Quantum Chemistry Certification: PASS
 * Stationary Point : TRANSITION_STATE (1 imag modes) | Status: PASS
```

An optimisation that was meant to find a minimum but ended on a saddle point is one of the most common undetected errors in computational studies, and it is what the expected type is for.

## The report

The script writes a full report for the transition state: `report.html` with the diagnostic message of each check, the optimisation trajectory and simulated IR spectrum figures, the summary table, and `methods_snippet.txt`, a draft methods paragraph that states each result (including the number of imaginary frequencies). Edit the paragraph so that it describes your study; see [Outputs](../outputs.md).
