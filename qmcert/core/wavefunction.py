"""
Wavefunction stability, spin contamination, and frontier orbital gap analysis.
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class SpinAnalysisResult:
    multiplicity: int
    s_exact: float
    s2_exact: float
    s2_calculated: float
    s2_after_annihilation: Optional[float]
    delta_s2: float
    contamination_pct: float
    status: str  # 'PASS', 'WARNING', 'FAIL'
    diagnostic_message: str


def evaluate_spin_contamination(
    multiplicity: int,
    s2_calculated: float,
    s2_annihilated: Optional[float] = None,
    warn_threshold_pct: float = 5.0,
    fail_threshold_pct: float = 10.0
) -> SpinAnalysisResult:
    """
    Evaluates spin contamination <S^2> in unrestricted wavefunctions (UHF/UKS).

    Parameters
    ----------
    multiplicity : int
        Spin multiplicity M = 2S + 1.
    s2_calculated : float
        Calculated expectation value <S^2>.
    s2_annihilated : float, optional
        Expectation value after single annihilation <S^2>_ann.
    warn_threshold_pct : float, default 5.0
        Contamination percentage warning cutoff.
    fail_threshold_pct : float, default 10.0
        Contamination percentage failure cutoff.

    Returns
    -------
    result : SpinAnalysisResult
        Calculated spin metrics, contamination percentage, and validation status.
    """
    s_exact = (multiplicity - 1) / 2.0
    s2_exact = s_exact * (s_exact + 1.0)
    
    delta_s2 = abs(s2_calculated - s2_exact)
    
    # Calculate contamination percentage
    if s2_exact > 0:
        contamination_pct = (delta_s2 / s2_exact) * 100.0
    else:
        # Singlet (S=0, S^2=0): absolute deviation * 100
        contamination_pct = delta_s2 * 100.0
        
    if contamination_pct <= warn_threshold_pct:
        status = "PASS"
        msg = f"Spin contamination is negligible (<S^2> = {s2_calculated:.4f}, exact = {s2_exact:.4f}, error = {contamination_pct:.2f}%)."
    elif contamination_pct <= fail_threshold_pct:
        status = "WARNING"
        msg = f"Moderate spin contamination detected (<S^2> = {s2_calculated:.4f}, exact = {s2_exact:.4f}, error = {contamination_pct:.2f}%). Check if multireference or broken-symmetry treatment is required."
    else:
        status = "FAIL"
        msg = f"Severe spin contamination (<S^2> = {s2_calculated:.4f}, exact = {s2_exact:.4f}, error = {contamination_pct:.2f}% > {fail_threshold_pct}%). Single-reference unrestricted wavefunction is heavily contaminated by higher spin states."

    return SpinAnalysisResult(
        multiplicity=multiplicity,
        s_exact=s_exact,
        s2_exact=s2_exact,
        s2_calculated=s2_calculated,
        s2_after_annihilation=s2_annihilated,
        delta_s2=delta_s2,
        contamination_pct=contamination_pct,
        status=status,
        diagnostic_message=msg
    )


def evaluate_orbital_gap(
    homo_energy: float,
    lumo_energy: float,
    unit: str = "eV"
) -> Dict[str, Any]:
    """
    Computes HOMO-LUMO gap and inspects frontier orbital stability.

    Parameters
    ----------
    homo_energy : float
        Highest Occupied Molecular Orbital energy.
    lumo_energy : float
        Lowest Unoccupied Molecular Orbital energy.
    unit : str, default 'eV'
        Units ('eV' or 'Hartree').

    Returns
    -------
    result : dict
        HOMO, LUMO, gap in eV and Hartree, and small-gap warning.
    """
    hartree_to_ev = 27.211386245988
    
    if unit.lower() in ["hartree", "eh", "au"]:
        homo_eh = homo_energy
        lumo_eh = lumo_energy
        homo_ev = homo_energy * hartree_to_ev
        lumo_ev = lumo_energy * hartree_to_ev
    else:
        homo_ev = homo_energy
        lumo_ev = lumo_energy
        homo_eh = homo_energy / hartree_to_ev
        lumo_eh = lumo_energy / hartree_to_ev
        
    gap_ev = lumo_ev - homo_ev
    gap_eh = lumo_eh - homo_eh
    
    status = "PASS"
    if gap_ev < 0:
        status = "FAIL"
        msg = f"Inverted orbital gap detected (HOMO = {homo_ev:.2f} eV > LUMO = {lumo_ev:.2f} eV). SCF state is unphysical."
    elif gap_ev < 0.5:
        status = "WARNING"
        msg = f"Extremely narrow HOMO-LUMO gap ({gap_ev:.2f} eV). System may exhibit strong multireference/diradicaloid character."
    else:
        msg = f"Standard HOMO-LUMO gap ({gap_ev:.2f} eV / {gap_eh:.4f} Eh)."

    return {
        "status": status,
        "homo_ev": homo_ev,
        "lumo_ev": lumo_ev,
        "gap_ev": gap_ev,
        "gap_eh": gap_eh,
        "diagnostic_message": msg
    }
