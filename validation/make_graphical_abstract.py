"""
Graphical abstract for the QMCert v2 manuscript (Elsevier: 531 x 1328 px minimum, readable at
5 x 13 cm). Built only from validation/results/benchmark.csv.
"""
import os

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
INK, INK2 = "#0b0b0b", "#52514e"
NEW, OLD, REF = "#2a78d6", "#e87ba4", "#1baf7a"
KCAL = 627.509474


def main():
    d = pd.read_csv(os.path.join(HERE, "results", "benchmark.csv"))
    matplotlib.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                                "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                                "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig = plt.figure(figsize=(13 / 2.54, 5 / 2.54))
    a = fig.add_axes([0.03, 0.08, 0.40, 0.70])
    b = fig.add_axes([0.58, 0.22, 0.39, 0.53])

    a.axis("off")
    a.set_title("Converged, but not a minimum", fontsize=8, color=INK)
    rows = [("vinyl radical", "1 imaginary mode", "706i"), ("triplet CH$_2$", "2 imaginary modes", "932i"),
            ("both, restarted bent", "0 imaginary modes", "")]
    for k, (m, n, v) in enumerate(rows):
        y = 0.78 - 0.30 * k
        col = OLD if k < 2 else REF
        a.text(0.02, y, m, fontsize=7.5, color=INK, transform=a.transAxes, va="center")
        a.text(0.52, y, n, fontsize=7, color=col, transform=a.transAxes, va="center", fontweight="bold")
        a.text(0.52, y - 0.11, v + (" cm$^{-1}$" if k < 2 else ""), fontsize=6.5, color=INK2, transform=a.transAxes,
               va="center")
    a.text(0.02, -0.06, "RDKit geometries, UKS B3LYP; optimiser kept the linear symmetry", fontsize=5.5, color=INK2,
           transform=a.transAxes)

    t = d[d.gv_g.notna()]
    dg = t.qm_qrrho_dg * KCAL
    once = (t.orca_g - t.gv_g) * KCAL
    b.scatter(dg, once, s=8, color=REF, lw=0, label="ORCA G (already corrected)")
    b.scatter(dg, once + dg, s=8, marker="^", color=OLD, lw=0, label="corrected again")
    b.plot([0, 0.75], [0, 0.75], color=INK2, lw=0.5, ls="--")
    b.set_xlim(-0.03, 0.78)
    b.set_ylim(-0.05, 1.6)
    b.set_xticks([0, 0.25, 0.5, 0.75], ["0", "0.25", "0.5", "0.75"], fontsize=7)
    b.set_yticks([0, 0.5, 1.0, 1.5], ["0", "0.5", "1.0", "1.5"], fontsize=7)
    b.set_xlabel("quasi-RRHO correction (kcal/mol)", fontsize=7)
    b.set_ylabel("G - harmonic G (kcal/mol)", fontsize=7)
    b.set_title("Quasi-RRHO: apply it once", fontsize=8, color=INK)
    b.legend(fontsize=5.5, frameon=False, loc="upper left", borderaxespad=0.1)
    fig.text(0.5, 0.975, "QMCert: 59 ORCA calculations checked against cclib, GoodVibes and ORCA",
             ha="center", va="top", fontsize=9, fontweight="bold", color=INK)
    out = os.path.join(HERE, "figures", "graphical_abstract")
    fig.savefig(out + ".png", dpi=400)
    fig.savefig(out + ".pdf")
    from PIL import Image
    im = Image.open(out + ".png").convert("RGB")
    im.save(out + ".tif", compression="tiff_lzw", dpi=(400, 400))
    print("graphical abstract", im.size[0], "x", im.size[1], "px")


if __name__ == "__main__":
    main()
