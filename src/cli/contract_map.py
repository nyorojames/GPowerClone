"""Centralized mapping module for CLI contract.

SPEC.md References:
- Section 2.1: Command line invocation syntax and exit codes.
- Section 2.2: Version query structure.
- Section 2.3: Input and output field definitions for anova-oneway.
- Section 3.1: Standard error JSON structure.
- Section 3.2: The seven contract error codes.

All flag names, field names, valid test/mode constants, output keys, and error codes
live exclusively in this module.
"""

from typing import Any, Dict, Optional, Tuple


# ============================================================================
# CLI Flag Names (SPEC.md Section 2.1, 2.2, 2.3)
# ============================================================================
FLAG_TEST = "--test"
FLAG_MODE = "--mode"
FLAG_F = "--f"
FLAG_ALPHA = "--alpha"
FLAG_POWER = "--power"
FLAG_GROUPS = "--groups"
FLAG_N_TOTAL = "--n_total"
FLAG_BETA_ALPHA_RATIO = "--beta_alpha_ratio"
FLAG_VERSION = "--version"


# ============================================================================
# Contract Field Identifiers (SPEC.md Section 2.3, 3.1, 3.2)
# ============================================================================
FIELD_TEST = "test"
FIELD_MODE = "mode"
FIELD_F = "f"
FIELD_ALPHA = "alpha"
FIELD_POWER = "power"
FIELD_GROUPS = "groups"
FIELD_N_TOTAL = "n_total"
FIELD_BETA_ALPHA_RATIO = "beta_alpha_ratio"


# ============================================================================
# Test Identifiers & Modes (SPEC.md Section 1.1, 2.3)
# ============================================================================
TEST_ANOVA_ONEWAY = "anova-oneway"
VALID_TESTS = (TEST_ANOVA_ONEWAY,)

MODE_A_PRIORI = "a-priori"
MODE_POST_HOC = "post-hoc"
MODE_COMPROMISE = "compromise"
MODE_CRITERION = "criterion"
MODE_SENSITIVITY = "sensitivity"

VALID_MODES = (
    MODE_A_PRIORI,
    MODE_POST_HOC,
    MODE_COMPROMISE,
    MODE_CRITERION,
    MODE_SENSITIVITY,
)

# Mapping from mode to required parameter fields (SPEC.md Section 2.3, 6.2)
MODE_REQUIRED_FIELDS: Dict[str, Tuple[str, ...]] = {
    MODE_A_PRIORI: (FIELD_F, FIELD_ALPHA, FIELD_POWER, FIELD_GROUPS),
    MODE_POST_HOC: (FIELD_F, FIELD_ALPHA, FIELD_N_TOTAL, FIELD_GROUPS),
    MODE_COMPROMISE: (FIELD_F, FIELD_BETA_ALPHA_RATIO, FIELD_N_TOTAL, FIELD_GROUPS),
    MODE_CRITERION: (FIELD_F, FIELD_POWER, FIELD_N_TOTAL, FIELD_GROUPS),
    MODE_SENSITIVITY: (FIELD_ALPHA, FIELD_POWER, FIELD_N_TOTAL, FIELD_GROUPS),
}


# ============================================================================
# JSON Output Key Names (SPEC.md Section 2.2, 2.3, 3.1, 6.2)
# ============================================================================
KEY_NCP = "ncp"
KEY_CRITICAL_F = "critical_f"
KEY_DF1 = "df1"
KEY_DF2 = "df2"
KEY_N_TOTAL = "n_total"
KEY_ACTUAL_POWER = "actual_power"
KEY_POWER = "power"
KEY_N_PER_GROUP = "n_per_group"
KEY_ALPHA = "alpha"
KEY_BETA = "beta"
KEY_F = "f"

KEY_ERROR = "error"
KEY_CODE = "code"
KEY_FIELD = "field"

KEY_CONTRACT_VERSION = "contract_version"
KEY_NAME = "name"
KEY_ENGINE = "engine"


# ============================================================================
# The Seven Contract Error Codes (SPEC.md Section 3.2)
# ============================================================================
ERR_MISSING_PARAM = "MISSING_PARAM"
ERR_UNKNOWN_PARAM = "UNKNOWN_PARAM"
ERR_INVALID_VALUE = "INVALID_VALUE"
ERR_OUT_OF_RANGE = "OUT_OF_RANGE"
ERR_INCONSISTENT = "INCONSISTENT"
ERR_UNSUPPORTED = "UNSUPPORTED"
ERR_NO_SOLUTION = "NO_SOLUTION"


# ============================================================================
# Version Payload (SPEC.md Section 2.2)
# ============================================================================
VERSION_PAYLOAD: Dict[str, str] = {
    KEY_CONTRACT_VERSION: "1.0.0",
    KEY_NAME: "K3-solo",
    KEY_ENGINE: "Python 3.12",
}


# ============================================================================
# Output Formatting Functions (SPEC.md Section 2.1, 2.2, 2.3, 2.4, 3.1)
# ============================================================================
def format_version_output() -> Dict[str, str]:
    """Returns single-line JSON dictionary for version query (SPEC.md Section 2.2)."""
    return VERSION_PAYLOAD


def format_success_output(mode: str, engine_result: Any) -> Dict[str, Any]:
    """Formats calculation result into single-line JSON dict with raw double precision numbers.

    SPEC.md Section 2.3 & 2.4:
    - Floating-point outputs are formatted with full double precision (no rounding).
    - Integer fields (n_total, df1, df2, n_per_group) are exact JSON integers.
    """
    if mode == MODE_A_PRIORI:
        out = {
            KEY_NCP: float(engine_result.ncp),
            KEY_CRITICAL_F: float(engine_result.critical_f),
            KEY_DF1: int(engine_result.df1),
            KEY_DF2: int(engine_result.df2),
            KEY_N_TOTAL: int(engine_result.n_total),
            KEY_ACTUAL_POWER: float(engine_result.actual_power),
        }
        if getattr(engine_result, "n_per_group", None) is not None:
            out[KEY_N_PER_GROUP] = int(engine_result.n_per_group)
        return out

    elif mode == MODE_POST_HOC:
        out = {
            KEY_NCP: float(engine_result.ncp),
            KEY_CRITICAL_F: float(engine_result.critical_f),
            KEY_DF1: int(engine_result.df1),
            KEY_DF2: int(engine_result.df2),
            KEY_POWER: float(engine_result.power),
        }
        if getattr(engine_result, "n_per_group", None) is not None:
            out[KEY_N_PER_GROUP] = int(engine_result.n_per_group)
        return out

    elif mode == MODE_COMPROMISE:
        return {
            KEY_DF1: int(engine_result.df1),
            KEY_DF2: int(engine_result.df2),
            KEY_NCP: float(engine_result.ncp),
            KEY_CRITICAL_F: float(engine_result.critical_f),
            KEY_ALPHA: float(engine_result.alpha),
            KEY_BETA: float(engine_result.beta),
            KEY_POWER: float(engine_result.power),
        }

    elif mode == MODE_CRITERION:
        return {
            KEY_DF1: int(engine_result.df1),
            KEY_DF2: int(engine_result.df2),
            KEY_NCP: float(engine_result.ncp),
            KEY_CRITICAL_F: float(engine_result.critical_f),
            KEY_ALPHA: float(engine_result.alpha),
        }

    elif mode == MODE_SENSITIVITY:
        return {
            KEY_DF1: int(engine_result.df1),
            KEY_DF2: int(engine_result.df2),
            KEY_NCP: float(engine_result.ncp),
            KEY_CRITICAL_F: float(engine_result.critical_f),
            KEY_F: float(engine_result.f),
        }

    raise ValueError(f"Unrecognized mode '{mode}'")


def format_error_output(message: str, code: str, field: Optional[str] = None) -> Dict[str, Any]:
    """Formats error into single-line JSON dict conforming to contract (SPEC.md Section 3.1)."""
    out: Dict[str, Any] = {
        KEY_ERROR: str(message),
        KEY_CODE: str(code),
    }
    if field is not None:
        out[KEY_FIELD] = str(field)
    return out
