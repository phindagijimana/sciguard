"""Honest public comparators for SciGuard (Paper 2).

B0 is the BIDS Validator filename/sidecar contract. B1 is the CWL/Nipype
File-type contract. Neither is SciGuard. Neither emits a scientific-correctness
certificate. Unsafe-acceptance vs these arms is not computed here.
"""

from baselines.bids_b0 import check_b0
from baselines.cwl_types_b1 import check_b1

__all__ = ["check_b0", "check_b1"]
