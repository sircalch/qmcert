"""
Figures and tables for the QMCert v2 manuscript, built only from validation/results/benchmark.csv.

    python validation/make_figures.py
"""
import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(HERE, "figures")
TAB = os.path.join(HERE, "tables")
MM = 1 / 25.4
DOUBLE = 190 * MM
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
NEW, OLD, REF, AUX = "#2a78d6", "#e87ba4", "#1baf7a", "#eda100"
KCAL = 627.509474
SETNAME = {"minima": "closed-shell minima", "open": "radicals and triplets", "open_restart": "restarts (bent)",
           "saddles": "symmetric saddle points", "truncated": "optimisation stopped", "scf_truncated": "SCF stopped",
           "open_uhf": "UHF single points"}


def setup():
    matplotlib.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "legend.fontsize": 6.5, "axes.edgecolor": INK2, "axes.labelcolor": INK,
        "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 0.6, "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
        "axes.axisbelow": True, "legend.frameon": False, "lines.linewidth": 1.2, "lines.markersize": 4,
        "savefig.dpi": 600, "pdf.fonttype": 42, "ps.fonttype": 42})


def panel(ax, letter, x=-0.16):
    ax.text(x, 1.03, f"({letter})", transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", color=INK)


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig_thermo(d):
    t = d[d.gv_g.notna()].copy()
    t["qm_dg"] = t.qm_qrrho_dg * KCAL
    t["gv_dg"] = (t.gv_ts - t.gv_tqs) * KCAL
    t["orca_minus_harm"] = (t.orca_g - t.gv_g) * KCAL
    fig, (a, b) = plt.subplots(1, 2, figsize=(DOUBLE, 70 * MM))
    lim = (-0.05, 0.75)
    a.scatter(t.gv_dg, t.qm_dg, s=12, color=NEW, lw=0, zorder=3)
    a.plot(lim, lim, color=INK2, lw=0.6, ls="--")
    a.set(xlim=lim, ylim=lim, xlabel="GoodVibes: $T(S_{\\mathrm{harm}} - S_{\\mathrm{qRRHO}})$ (kcal mol$^{-1}$)",
          ylabel="QMCert: $\\Delta G_{\\mathrm{qRRHO}}$ (kcal mol$^{-1}$)")
    dev = (t.qm_dg - t.gv_dg).abs().max()
    a.text(0.97, 0.05, f"max. difference {dev:.4f} kcal mol$^{{-1}}$\n(GoodVibes prints 6 decimals in $E_h$)",
           transform=a.transAxes, ha="right", fontsize=6.5, color=INK2)
    panel(a, "a")

    b.scatter(t.qm_dg, t.orca_minus_harm, s=12, color=REF, lw=0, zorder=3, label="$G_{\\mathrm{ORCA}}$ (printed)")
    b.scatter(t.qm_dg, t.orca_minus_harm + t.qm_dg, s=12, marker="^", color=OLD, lw=0, zorder=3,
              label="$G_{\\mathrm{ORCA}} + \\Delta G_{\\mathrm{qRRHO}}$ (correction applied twice)")
    b.plot(lim, lim, color=INK2, lw=0.6, ls="--")
    b.plot(lim, [2 * v for v in lim], color=INK2, lw=0.5, ls=":")
    b.set(xlim=lim, ylim=(-0.05, 1.6), xlabel="QMCert $\\Delta G_{\\mathrm{qRRHO}}$ (kcal mol$^{-1}$)",
          ylabel="$G$ minus harmonic $G$ (kcal mol$^{-1}$)")
    b.legend(loc="upper left")
    panel(b, "b")
    fig.tight_layout(w_pad=2.5)
    save(fig, "fig2_thermo")


def table_agreement(d):
    rows = [("Final energy", "dev_energy", "$E_h$", "cclib"),
            ("Frequencies", "dev_freq", "cm$^{-1}$", "cclib"),
            ("IR intensities", "dev_ir", "km mol$^{-1}$", "cclib"),
            ("HOMO energy", "dev_homo", "eV", "cclib (from $E_h$)"),
            ("LUMO energy", "dev_lumo", "eV", "cclib (from $E_h$)")]
    lines = [r"\begin{tabular}{llrrl}", r"\toprule", r"Quantity & unit & outputs & max.\ abs.\ difference & reference \\", r"\midrule"]
    for name, col, unit, ref in rows:
        v = d[col].dropna()
        lines.append(f"{name} & {unit} & {len(v)} & {v.max():.1e} & {ref} " + r"\\")
    th = d[d.orca_g.notna()]
    for name, a, b in (("Zero-point energy", "qm_zpe", "orca_zpe"), ("Enthalpy", "qm_h", "orca_h"),
                       ("Gibbs free energy", "qm_g", "orca_g")):
        v = (th[a] - th[b]).abs()
        lines.append(f"{name} & $E_h$ & {len(v)} & {v.max():.1e} & ORCA output " + r"\\")
    s2 = d[d.orca_s2.notna()]
    lines.append(f"$\\langle S^2\\rangle$ & -- & {len(s2)} & {(s2.qm_s2 - s2.orca_s2).abs().max():.1e} & ORCA output " + r"\\")
    q = d[d.gv_g.notna()]
    v = (q.qm_qrrho_dg - (q.gv_ts - q.gv_tqs)).abs() * KCAL
    lines.append(f"$\\Delta G_{{\\mathrm{{qRRHO}}}}$ & kcal mol$^{{-1}}$ & {len(v)} & {v.max():.1e} & GoodVibes " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(TAB, "table_agreement.tex"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def table_verdicts(d):
    lines = [r"\begin{tabular}{lllll}", r"\toprule",
             r"Calculation & intended & imaginary modes (cclib) & QMCert & QMCert verdict \\", r"\midrule"]
    special = d[d.set.isin(["saddles", "open_restart", "truncated", "scf_truncated", "open_uhf"]) |
                ((d.set.isin(["minima", "open"])) & (d.cc_nimag.fillna(0) > 0))]
    for r in special.itertuples():
        name = r.name.replace("_", " ")
        if r.set in ("truncated", "scf_truncated"):
            intended = "not converged"
            found = "--"
            qm = "SCF not converged" if r.set == "scf_truncated" else "optimisation not converged"
            verdict = r.qm_scf_status if r.set == "scf_truncated" else r.qm_opt_status
        elif r.set == "open_uhf":
            intended, found = "UHF doublet", "--"
            qm, verdict = r"$\langle S^2\rangle$ = " + f"{r.qm_s2:.3f}", r.qm_spin_status
        elif pd.isna(r.qm_nimag):
            continue  # calculation without a frequency section (still running when the table was made)
        else:
            ei = int(float(r.expected_index))
            intended = "minimum" if ei == 0 else ("transition state" if ei == 1 else f"saddle, index {ei}")
            found = str(int(r.cc_nimag))
            qm = f"{int(r.qm_nimag)} ({r.qm_point.replace('_', ' ').lower()})"
            verdict = r.qm_freq_status
        lines.append(f"{name} & {intended} & {found} & {qm} & {verdict} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(TAB, "table_verdicts.tex"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def table_s_all(d):
    lines = [r"\begin{tabular}{llrrrrl}", r"\toprule",
             r"Calculation & set & atoms & imag.\ & $\langle S^2\rangle$ & $\Delta G_{\mathrm{qRRHO}}$ & overall \\", r"\midrule"]
    for r in d.itertuples():
        s2 = f"{r.qm_s2:.4f}" if pd.notna(r.qm_s2) else "--"
        dg = f"{r.qm_qrrho_dg * KCAL:.3f}" if pd.notna(r.qm_qrrho_dg) else "--"
        ni = f"{int(r.qm_nimag)}" if pd.notna(r.qm_nimag) else "--"
        lines.append(f"{r.name.replace('_', ' ')} & {SETNAME[r.set]} & {int(r.qm_natoms)} & {ni} & {s2} & {dg} & {r.qm_overall} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(TAB, "table_s_all.tex"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    for p in (FIG, TAB):
        os.makedirs(p, exist_ok=True)
    setup()
    d = pd.read_csv(os.path.join(RES, "benchmark.csv"))
    fig_thermo(d)
    table_agreement(d)
    table_verdicts(d)
    table_s_all(d)
    print("figures written")


if __name__ == "__main__":
    main()
