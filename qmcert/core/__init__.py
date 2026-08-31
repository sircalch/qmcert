"""
Core mathematical and physical evaluation algorithms for QMCert.
"""

from qmcert.core.frequencies import (
    classify_stationary_point,
    simulate_ir_spectrum,
    FrequencyAnalysisResult
)
from qmcert.core.scf_opt import (
    evaluate_scf_convergence,
    evaluate_geometry_optimization,
    ConvergenceCriteria
)
from qmcert.core.wavefunction import (
    evaluate_spin_contamination,
    evaluate_orbital_gap,
    SpinAnalysisResult
)
from qmcert.core.thermo import (
    calculate_quasi_rrho_corrections,
    ThermochemistryData
)
from qmcert.core.scoring import assess_qm_quality, QMCertValidationReport

__all__ = [
    "classify_stationary_point",
    "simulate_ir_spectrum",
    "FrequencyAnalysisResult",
    "evaluate_scf_convergence",
    "evaluate_geometry_optimization",
    "ConvergenceCriteria",
    "evaluate_spin_contamination",
    "evaluate_orbital_gap",
    "SpinAnalysisResult",
    "calculate_quasi_rrho_corrections",
    "ThermochemistryData",
    "assess_qm_quality",
    "QMCertValidationReport"
]
