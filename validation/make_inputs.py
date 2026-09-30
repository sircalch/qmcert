"""
Writes the ORCA 6.1 inputs of the QMCert v2 benchmark (validation/benchmark_runs/<name>/<name>.inp).

    python validation/make_inputs.py

Level: B3LYP-D3(BJ)/def2-SVP, TightSCF, Opt + analytic Freq (UKS for open shells).
Sets:
    minima     30 closed-shell molecules, starting geometries from RDKit ETKDG + MMFF
    open       12 radicals and triplets (UKS), for <S^2>
    saddles    8 symmetric structures whose gradient keeps the symmetry during optimisation, with a
               known saddle-point index from the literature (1 unless stated)
    truncated  3 optimisations stopped after 2 cycles (MaxIter 2), to test convergence detection
    scf_truncated  2 single points whose SCF is stopped after 4 iterations
    open_restart   vinyl and triplet CH2 restarted from bent geometries (see below)
    open_uhf       UHF/def2-SVP single points of allyl and CN at their optimised B3LYP geometries, written by
                   `python validation/make_inputs.py --uhf` once those optimisations have finished
Expected labels are written to validation/benchmark_runs/expected.csv.
"""
import csv
import os

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "benchmark_runs")
KEYS = "B3LYP D3BJ def2-SVP TightSCF Opt Freq"

MINIMA = {
    "water": "O", "ammonia": "N", "methane": "C", "ethane": "CC", "ethylene": "C=C", "acetylene": "C#C",
    "hcn": "C#N", "co2": "O=C=O", "formaldehyde": "C=O", "methanol": "CO", "ethanol": "CCO",
    "formic_acid": "OC=O", "acetic_acid": "CC(=O)O", "acetone": "CC(C)=O", "acetonitrile": "CC#N",
    "benzene": "c1ccccc1", "toluene": "Cc1ccccc1", "phenol": "Oc1ccccc1", "pyridine": "c1ccncc1",
    "furan": "c1ccoc1", "pyrrole": "c1cc[nH]c1", "imidazole": "c1c[nH]cn1", "urea": "NC(N)=O",
    "formamide": "NC=O", "glycine": "NCC(=O)O", "dimethyl_ether": "COC", "cyclohexane": "C1CCCCC1",
    "cyclopropane": "C1CC1", "propene": "CC=C", "nitromethane": "C[N+](=O)[O-]",
}
OPEN = {  # name: (smiles, multiplicity, exact S(S+1))
    "methyl": ("[CH3]", 2), "hydroxyl": ("[OH]", 2), "amino": ("[NH2]", 2), "cyano": ("[C]#N", 2),
    "nitric_oxide": ("[N]=O", 2), "vinyl": ("[CH]=C", 2), "allyl": ("[CH2]C=C", 2), "methoxy": ("C[O]", 2),
    "hydroperoxyl": ("O[O]", 2), "oxygen_triplet": ("[O][O]", 3), "methylene_triplet": ("[CH2]", 3),
    "imidogen_triplet": ("[NH]", 3),
}


def xyz_from_smiles(smiles, seed=7):
    m = Chem.AddHs(Chem.MolFromSmiles(smiles))
    if m.GetNumAtoms() == 1:
        return [(m.GetAtomWithIdx(0).GetSymbol(), 0.0, 0.0, 0.0)]
    AllChem.EmbedMolecule(m, randomSeed=seed)
    if AllChem.MMFFHasAllMoleculeParams(m):
        AllChem.MMFFOptimizeMolecule(m)
    else:
        AllChem.UFFOptimizeMolecule(m)
    pos = m.GetConformer().GetPositions()
    return [(a.GetSymbol(), *pos[i]) for i, a in enumerate(m.GetAtoms())]


def ring(n, r, z=0.0, phase=0.0):
    return [(r * np.cos(phase + 2 * np.pi * k / n), r * np.sin(phase + 2 * np.pi * k / n), z) for k in range(n)]


def saddles():
    s = {}
    # planar ammonia, D3h: inversion TS (index 1)
    s["ammonia_planar"] = ([("N", 0, 0, 0)] + [("H", *p) for p in ring(3, 1.01)], 1)
    # linear water, D_inf_h: doubly degenerate bend (index 2)
    s["water_linear"] = ([("O", 0, 0, 0), ("H", 0.96, 0, 0), ("H", -0.96, 0, 0)], 2)
    # eclipsed ethane, D3h: internal rotation TS (index 1)
    eth = [("C", 0, 0, 0.765), ("C", 0, 0, -0.765)]
    eth += [("H", *p) for p in ring(3, 1.02, 1.16)] + [("H", *p) for p in ring(3, 1.02, -1.16)]
    s["ethane_eclipsed"] = (eth, 1)
    # planar trans and cis hydrogen peroxide, C2h and C2v: torsional TSs (index 1)
    s["h2o2_trans_planar"] = ([("O", 0.73, 0, 0), ("O", -0.73, 0, 0), ("H", 1.0, 0.92, 0), ("H", -1.0, -0.92, 0)], 1)
    s["h2o2_cis_planar"] = ([("O", 0.73, 0, 0), ("O", -0.73, 0, 0), ("H", 1.0, 0.92, 0), ("H", -1.0, 0.92, 0)], 1)
    # eclipsed methanol (C-H syn to O-H), Cs: methyl rotation TS (index 1)
    s["methanol_eclipsed"] = ([("C", 0, 0, 0), ("O", 1.42, 0, 0), ("H", 1.75, 0.90, 0), ("H", -0.36, 1.03, 0),
                               ("H", -0.36, -0.51, 0.89), ("H", -0.36, -0.51, -0.89)], 1)
    # planar biphenyl, D2h: ring-torsion TS (index 1)
    bp = []
    for sign in (1, -1):
        cx = sign * (0.745 + 1.395)
        for k, (x, y, _) in enumerate(ring(6, 1.395, 0, 0)):
            bp.append(("C", cx + x, y, 0))
    atoms = bp[:]
    for sign in (1, -1):
        cx = sign * (0.745 + 1.395)
        for k, (x, y, _) in enumerate(ring(6, 2.48, 0, 0)):
            if (sign == 1 and k == 3) or (sign == -1 and k == 0):
                continue  # inter-ring bond positions carry no hydrogen
            atoms.append(("H", cx + x, y, 0))
    # the ring carbons at 180 deg (right ring) and 0 deg (left ring) form the 1.49 A inter-ring bond
    s["biphenyl_planar"] = (atoms, 1)
    # syn-periplanar n-butane, C2v: torsional TS (index 1)
    bu = [("C", 0.77, 0, 0), ("C", -0.77, 0, 0), ("C", 1.29, 1.45, 0), ("C", -1.29, 1.45, 0),
          ("H", 1.16, -0.52, 0.88), ("H", 1.16, -0.52, -0.88), ("H", -1.16, -0.52, 0.88), ("H", -1.16, -0.52, -0.88),
          ("H", 2.38, 1.47, 0), ("H", -2.38, 1.47, 0), ("H", 0.93, 1.98, 0.88), ("H", 0.93, 1.98, -0.88),
          ("H", -0.93, 1.98, 0.88), ("H", -0.93, 1.98, -0.88)]
    s["butane_syn"] = (bu, 1)
    return s


def write(name, atoms, mult=1, keys=KEYS, extra="", ref=None):
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    uks = ref if ref is not None else ("UKS " if mult > 1 else "")
    with open(os.path.join(d, f"{name}.inp"), "w") as fh:
        fh.write(f"! {uks}{keys}\n{extra}* xyz 0 {mult}\n")
        for el, x, y, z in atoms:
            fh.write(f"{el:2s} {x:12.6f} {y:12.6f} {z:12.6f}\n")
        fh.write("*\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for name, smi in MINIMA.items():
        write(name, xyz_from_smiles(smi))
        rows.append({"name": name, "set": "minima", "mult": 1, "expected_index": 0, "expected_converged": 1})
    for name, (smi, mult) in OPEN.items():
        write(name, xyz_from_smiles(smi), mult)
        rows.append({"name": name, "set": "open", "mult": mult, "expected_index": 0, "expected_converged": 1})
    for name, (atoms, index) in saddles().items():
        write(name, atoms)
        rows.append({"name": name, "set": "saddles", "mult": 1, "expected_index": index, "expected_converged": 1})
    for name in ("acetone", "toluene", "glycine"):
        write(f"{name}_truncated", xyz_from_smiles(MINIMA[name], seed=11), keys="B3LYP D3BJ def2-SVP TightSCF Opt",
              extra="%geom MaxIter 2 end\n")
        rows.append({"name": f"{name}_truncated", "set": "truncated", "mult": 1, "expected_index": "",
                     "expected_converged": 0})
    for name in ("phenol", "pyridine"):
        # SCF stopped after 4 iterations in a single-point calculation (ORCA continues after a failed SCF
        # only with an explicit flag, so the job reports the failure)
        write(f"{name}_scf_truncated", xyz_from_smiles(MINIMA[name], seed=13), keys="B3LYP D3BJ def2-SVP",
              extra="%scf MaxIter 4 end\n")
        rows.append({"name": f"{name}_scf_truncated", "set": "scf_truncated", "mult": 1, "expected_index": "",
                     "expected_converged": 0})
    # the RDKit geometries of the vinyl radical and triplet CH2 are linear at the radical carbon and the
    # optimisations keep that symmetry (saddle points); restarts from bent geometries give the minima
    write("vinyl_bent", [("C", 0, 0, 0), ("C", 1.31, 0, 0), ("H", -0.65, 0.90, 0), ("H", 1.88, 0.93, 0),
                         ("H", 1.88, -0.93, 0)], 2)
    write("methylene_triplet_bent", [("C", 0, 0, 0), ("H", 0.99, 0.42, 0), ("H", -0.99, 0.42, 0)], 3)
    for name, mult in (("vinyl_bent", 2), ("methylene_triplet_bent", 3)):
        rows.append({"name": name, "set": "open_restart", "mult": mult, "expected_index": 0, "expected_converged": 1})
    with open(os.path.join(OUT, "expected.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "inputs")


def uhf_inputs():
    rows = list(csv.DictReader(open(os.path.join(OUT, "expected.csv"))))
    for name in ("allyl", "cyano"):
        lines = open(os.path.join(OUT, name, f"{name}.xyz")).read().splitlines()[2:]
        atoms = [(ln.split()[0], *map(float, ln.split()[1:4])) for ln in lines if ln.strip()]
        # the inputs that were run carry the coordinates with 8 decimals, as in the .xyz file
        d = os.path.join(OUT, f"{name}_uhf")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{name}_uhf.inp"), "w") as fh:
            fh.write("! UHF def2-SVP TightSCF\n* xyz 0 2\n")
            for el, x, y, z in atoms:
                fh.write(f"{el:<2s} {x:14.8f} {y:14.8f} {z:14.8f}\n")
            fh.write("*\n")
        if not any(r["name"] == f"{name}_uhf" for r in rows):
            rows.append({"name": f"{name}_uhf", "set": "open_uhf", "mult": 2, "expected_index": "", "expected_converged": 1})
    with open(os.path.join(OUT, "expected.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    import sys
    uhf_inputs() if "--uhf" in sys.argv else main()
