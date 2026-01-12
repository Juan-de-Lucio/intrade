"""intrade package.

- Preloads commonly used libraries on import (Dec-25 list).
- Re-exports public symbols from intrade.py so users can do:
      from intrade import some_function
"""

from __future__ import annotations

# --- Preload dependencies (robust: warn if missing, don't crash) ---
import importlib
import warnings

_PRELOAD = [
    # stdlib
    "os",
    "glob",
    "zipfile",
    "re",
    "itertools",
    "traceback",

    # third-party
    "pandas",
    "numpy",
    "pyfixest",
    "statsmodels.api",
    "scipy.optimize",
    "natsort",
]

for _mod in _PRELOAD:
    try:
        importlib.import_module(_mod)
    except Exception as _e:
        warnings.warn(
            f"intrade preload: could not import '{_mod}' ({_e}).",
            RuntimeWarning,
        )

# Convenience aliases (only if available)
try:
    import pandas as pd  # noqa: F401
except Exception:
    pd = None  # type: ignore

try:
    import numpy as np  # noqa: F401
except Exception:
    np = None  # type: ignore

try:
    import pyfixest as pf  # noqa: F401
except Exception:
    pf = None  # type: ignore

try:
    import statsmodels.api as sm  # noqa: F401
except Exception:
    sm = None  # type: ignore

try:
    from scipy import optimize  # noqa: F401
except Exception:
    optimize = None  # type: ignore

try:
    from natsort import natsorted  # noqa: F401
except Exception:
    natsorted = None  # type: ignore

try:
    from zipfile import ZipFile  # noqa: F401
except Exception:
    ZipFile = None  # type: ignore


# --- "Nice import" re-export layer ---
from . import intrade as _intrade
from .intrade import *  # noqa: F401,F403

# Respect __all__ if defined in intrade.py, otherwise export all public names
__all__ = getattr(_intrade, "__all__", [n for n in dir(_intrade) if not n.startswith("_")])
