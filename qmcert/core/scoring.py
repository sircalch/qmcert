"""
Quantum Chemistry Validation Matrix, Quality Scoring Engine, and Report Structure.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from qmcert.core.frequencies import FrequencyAnalysisResult, classify_stationary_point
from qmcert.core.scf_opt import evaluate_scf_convergence, evaluate_geometry_optimization
from qmcert.core.wavefunction import SpinAnalysisResult, evaluate_spin_contamination, evaluate_orbital_gap
from qmcert.core.thermo import ThermochemistryData, calculate_quasi_rrho_corrections


@dataclass
class QMCertValidationReport:
    overall_status: str  # 'PASS', 'WARNING', 'FAIL'
    validation_score: str
    metadata: Dict[str, Any]
    scf_result: Optional[Dict[str, Any]]
    geometry_result: Optional[Dict[str, Any]]
    frequency_result: Optional[FrequencyAnalysisResult]
    spin_result: Optional[SpinAnalysisResult]
    orbital_result: Optional[Dict[str, Any]]
    thermochemistry: Optional[ThermochemistryData]
    quasi_rrho_correction: Optional[Dict[str, Any]]
    recommendations: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assess_qm_quality(
    metadata: Dict[str, Any],
    scf_converged: bool = True,
    n_scf_cycles: int = 15,
    opt_converged: Optional[bool] = None,
    n_opt_steps: Optional[int] = None,
    frequencies: Optional[List[float]] = None,
    intensities: Optional[List[float]] = None,
    expected_point_type: str = "MINIMUM",
    multiplicity: int = 1,
    s2_calculated: Optional[float] = None,
    homo_ev: Optional[float] = None,
    lumo_ev: Optional[float] = None,
    thermochemistry: Optional[ThermochemistryData] = None,
    energies_trajectory: Optional[List[float]] = None
) -> QMCertValidationReport:
    """
    Evaluates quantum chemical calculation quality against established computational chemistry standards.

    Parameters
    ----------
    metadata : dict
        Engine metadata (functional, basis set, dispersion, solvent, engine).
    scf_converged : bool
        Whether SCF converged.
    n_scf_cycles : int
        Number of SCF iterations.
    opt_converged : bool, optional
        Whether geometry optimization converged.
    n_opt_steps : int, optional
        Number of optimization steps.
    frequencies : list of float, optional
        Harmonic vibrational frequencies.
    intensities : list of float, optional
        Harmonic IR intensities.
    expected_point_type : str
        'MINIMUM' or 'TRANSITION_STATE'.
    multiplicity : int
        Spin multiplicity.
    s2_calculated : float, optional
        <S^2> expectation value.
    homo_ev : float, optional
        HOMO orbital energy in eV.
    lumo_ev : float, optional
        LUMO orbital energy in eV.
    thermochemistry : ThermochemistryData, optional
        Parsed thermochemistry.
    energies_trajectory : list of float, optional
        Trajectory of electronic energies during optimization.

    Returns
    -------
    report : QMCertValidationReport
        Comprehensive certification report.
    """
    statuses = []
    recommendations = []
    
    # 1. SCF Convergence Check
    scf_res = evaluate_scf_convergence(scf_converged, n_scf_cycles)
    statuses.append(scf_res["status"])
    if scf_res["status"] != "PASS":
        recommendations.append(scf_res["diagnostic_message"])

    # 2. Geometry Optimization Check (if applicable)
    geom_res = None
    if opt_converged is not None and n_opt_steps is not None:
        geom_res = evaluate_geometry_optimization(
            opt_converged, n_opt_steps, energies_trajectory=energies_trajectory
        )
        statuses.append(geom_res["status"])
        if geom_res["status"] != "PASS":
            recommendations.append(geom_res["diagnostic_message"])

    # 3. Vibrational Frequencies & Stationary Point Certification
    freq_res = None
    qrrho_res = None
    if frequencies is not None and len(frequencies) > 0:
        freq_res = classify_stationary_point(
            frequencies, intensities=intensities, expected_type=expected_point_type
        )
        statuses.append(freq_res.status)
        if freq_res.status != "PASS":
            recommendations.append(freq_res.diagnostic_message)
            
        # Quasi-RRHO thermochemistry check
        qrrho_res = calculate_quasi_rrho_corrections(frequencies)

    # 4. Spin Contamination Check (if open-shell / unrestricted)
    spin_res = None
    if s2_calculated is not None:
        spin_res = evaluate_spin_contamination(multiplicity, s2_calculated)
        statuses.append(spin_res.status)
        if spin_res.status != "PASS":
            recommendations.append(spin_res.diagnostic_message)

    # 5. Frontier Orbital Gap Check
    orb_res = None
    if homo_ev is not None and lumo_ev is not None:
        orb_res = evaluate_orbital_gap(homo_ev, lumo_ev, unit="eV")
        statuses.append(orb_res["status"])
        if orb_res["status"] != "PASS":
            recommendations.append(orb_res["diagnostic_message"])

    # Overall Scoring Decision
    if "FAIL" in statuses:
        overall_status = "FAIL"
        validation_score = "QUANTUM CHEMISTRY CERTIFICATION = REJECTED / INVALID"
    elif "WARNING" in statuses:
        overall_status = "WARNING"
        validation_score = "QUANTUM CHEMISTRY CERTIFICATION = ACCEPTABLE WITH WARNINGS"
    else:
        overall_status = "PASS"
        validation_score = "QUANTUM CHEMISTRY CERTIFICATION = FULLY CERTIFIED"

    return QMCertValidationReport(
        overall_status=overall_status,
        validation_score=validation_score,
        metadata=metadata,
        scf_result=scf_res,
        geometry_result=geom_res,
        frequency_result=freq_res,
        spin_result=spin_res,
        orbital_result=orb_res,
        thermochemistry=thermochemistry,
        quasi_rrho_correction=qrrho_res,
        recommendations=recommendations,
        provenance={
            "tool": "QMCert",
            "version": "1.0.0",
            "citation": "Monreal-Hernández, A. (2026). QMCert: Automated Quality-Control, Stationary Point Certification, and Reproducibility Assessment for Quantum-Chemical Calculations."
        }
    )
