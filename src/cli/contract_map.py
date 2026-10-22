"""Centralized mapping module for CLI contract.

SPEC.md Section 7 states:
'All flag names and JSON output key names MUST reside in ONE centralized mapping module
in the CLI layer (src/cli/contract_map.py) so they can be adapted in minutes if the official
specification differs.'

This module contains ALL flag names, flag aliases, test/mode constants, and output key names.
No other module should hardcode these CLI strings.
"""

from typing import Any, Dict


# ============================================================================
# CLI Flag Names (SPEC.md Section 2: Inputs, Ranges, Defaults, and Units)
# ============================================================================
FLAG_TEST = "--test"
FLAG_MODE = "--mode"
FLAG_EFFECT_SIZE = "--f"
FLAG_ALPHA = "--alpha"
FLAG_POWER = "--power"
FLAG_GROUPS = "--groups"
FLAG_N_TOTAL = "--n-total"

# ============================================================================
# CLI Flag Aliases (SPEC.md Section 2)
# ============================================================================
FLAG_EFFECT_SIZE_ALIAS = "--effect-size"
FLAG_GROUPS_ALIAS = "--k"

# Flag collections for lookup and validation
ALL_CLI_FLAGS = (
    FLAG_TEST,
    FLAG_MODE,
    FLAG_EFFECT_SIZE,
    FLAG_ALPHA,
    FLAG_POWER,
    FLAG_GROUPS,
    FLAG_N_TOTAL,
)

ALL_CLI_ALIASES = (
    FLAG_EFFECT_SIZE_ALIAS,
    FLAG_GROUPS_ALIAS,
)

# ============================================================================
# Test Identifiers & Modes (SPEC.md Section 1: Scope)
# ============================================================================
TEST_ANOVA_ONEWAY = "anova-oneway"
MODE_A_PRIORI = "a-priori"
MODE_POST_HOC = "post-hoc"

VALID_TESTS = (TEST_ANOVA_ONEWAY,)
VALID_MODES = (MODE_A_PRIORI, MODE_POST_HOC)

# ============================================================================
# JSON Output Key Names (SPEC.md Section 5 & Section 7)
# ============================================================================
KEY_N_PER_GROUP = "n_per_group"
KEY_N_TOTAL = "n_total"
KEY_ACTUAL_POWER = "actual_power"
KEY_CRITICAL = "critical"
KEY_DF1 = "df1"
KEY_DF2 = "df2"
KEY_NCP = "ncp"
KEY_ERROR = "error"

# Legacy compatibility keys
KEY_CRITICAL_F_COMPAT = "critical_f"
KEY_DF_NUM_COMPAT = "df_num"
KEY_DF_DENOM_COMPAT = "df_denom"

OUTPUT_KEYS = {
    "n_per_group": KEY_N_PER_GROUP,
    "n_total": KEY_N_TOTAL,
    "actual_power": KEY_ACTUAL_POWER,
    "critical": KEY_CRITICAL,
    "df1": KEY_DF1,
    "df2": KEY_DF2,
    "ncp": KEY_NCP,
    "error": KEY_ERROR,
    # compatibility
    "critical_f": KEY_CRITICAL,
    "df_num": KEY_DF1,
    "df_denom": KEY_DF2,
}

CLI_FLAGS = {
    "test": FLAG_TEST,
    "mode": FLAG_MODE,
    "effect_size": FLAG_EFFECT_SIZE,
    "alpha": FLAG_ALPHA,
    "power": FLAG_POWER,
    "groups": FLAG_GROUPS,
    "n_total": FLAG_N_TOTAL,
}

TEST_NAME = TEST_ANOVA_ONEWAY


# ============================================================================
# Output Formatting Functions (SPEC.md Section 5, 6, 7)
# ============================================================================
def format_success_output(engine_result) -> Dict[str, Any]:
    """Formats engine calculation result into contract single-line JSON dict (SPEC.md Section 5 & 7)."""
    return {
        KEY_N_PER_GROUP: engine_result.n_per_group,
        KEY_N_TOTAL: engine_result.n_total,
        KEY_ACTUAL_POWER: round(engine_result.actual_power, 7),
        KEY_CRITICAL: round(engine_result.critical, 7),
        KEY_DF1: engine_result.df1,
        KEY_DF2: engine_result.df2,
        KEY_NCP: round(engine_result.ncp, 7),
    }


def format_error_output(message: str) -> Dict[str, Any]:
    """Formats error into contract single-line JSON dict (SPEC.md Section 6 & 7)."""
    return {
        KEY_ERROR: str(message),
    }
