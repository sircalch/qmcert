"""
QMCert: Automated Quality-Control, Stationary Point Certification, and Reproducibility
Assessment for Quantum-Chemical Calculations.
"""

__version__ = "1.0.0"
__author__ = "Andres Monreal-Hernández"
__license__ = "MIT"

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
    "__version__",
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
