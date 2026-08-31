"""
Tests for ORCA and Gaussian calculation log parsers.
"""

import os
import tempfile
import pytest
from qmcert.parsers.orca import parse_orca_output
from qmcert.parsers.gaussian import parse_gaussian_output
from qmcert.parsers.generic_qm import parse_qm_output


def test_orca_parser():
    orca_text = """
  ************************************************************
  *                        * O   R   C   A *                  *
  *                   Program Version 5.0.4                   *
  ************************************************************

| 1> ! B3LYP def2-TZVP D3BJ Opt Freq

Total Charge           Charge          ....    0
Multiplicity           Mult            ....    1

                     *** SUCCESSFUL RUN ***
                     SCF CONVERGED AFTER 14 CYCLES

FINAL SINGLE POINT ENERGY      -154.23456789

-----------------------
VIBRATIONAL FREQUENCIES
-----------------------
   0:         0.00 cm**-1
   1:         0.00 cm**-1
   2:         0.00 cm**-1
   3:         0.00 cm**-1
   4:         0.00 cm**-1
   5:         0.00 cm**-1
   6:       150.25 cm**-1
   7:       450.80 cm**-1
   8:      1200.40 cm**-1
   9:      3050.10 cm**-1

-----------
IR SPECTRUM
-----------
   6:      150.25 cm**-1     12.50 km/mol
   7:      450.80 cm**-1     45.20 km/mol
   8:     1200.40 cm**-1     85.00 km/mol
   9:     3050.10 cm**-1    120.40 km/mol

Zero point energy                ...      0.08500000 Eh
Final Gibbs free energy          ...   -154.18000000 Eh
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".out", delete=False) as f:
        f.write(orca_text)
        f_path = f.name
        
    try:
        data = parse_orca_output(f_path)
        assert data["metadata"]["engine"] == "ORCA"
        assert data["metadata"]["functional"] == "B3LYP"
        assert data["metadata"]["dispersion"] == "D3BJ"
        assert data["scf_converged"] is True
        assert len(data["frequencies"]) == 10
        assert data["thermochemistry"] is not None
        assert data["thermochemistry"].zpve_hartree == 0.085
        
        # Test generic dispatcher
        data_gen = parse_qm_output(f_path)
        assert data_gen["metadata"]["engine"] == "ORCA"
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)


def test_gaussian_parser():
    gau_text = """
 Entering Gaussian System, Inc.
 # opt freq b3lyp/6-31g(d)

 Charge =  0 Multiplicity = 1

 SCF Done:  E(RB3LYP) =  -154.12345678     A.U. after   11 cycles
 
 Stationary point found.
 
 Frequencies --   150.25   450.80  1200.40
 IR Inten    --    12.50    45.20    85.00
 
 Zero-point correction=                           0.084000
 Sum of electronic and thermal Free Energies=  -154.070000
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write(gau_text)
        f_path = f.name
        
    try:
        data = parse_gaussian_output(f_path)
        assert data["metadata"]["engine"] == "Gaussian"
        assert data["metadata"]["functional"] == "B3LYP"
        assert data["scf_converged"] is True
        assert data["opt_converged"] is True
        assert len(data["frequencies"]) == 3
        assert data["thermochemistry"] is not None
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)
