"""CLI thin wrapper for gpower-clone.

SPEC.md References:
- Section 2.1: Command line invocation syntax and exit codes (0 for success, 2 for input, 1 for internal).
- Section 2.2: Version query.
- Section 2.3: Inputs and output schemas for anova-oneway.
- Section 3.1 & 3.2: Error JSON format and contract error codes.

Performs parameter parsing, delegates all calculations directly to src.engine,
and outputs single-line JSON on stdout.
Contains NO mathematical or statistical calculation logic.
All flag names, field identifiers, and output key names live exclusively in src.cli.contract_map.
"""

import json
import sys
from typing import Dict, List, Optional

from src.cli.contract_map import (
    FLAG_VERSION,
    FIELD_TEST,
    FIELD_MODE,
    FIELD_F,
    FIELD_ALPHA,
    FIELD_POWER,
    FIELD_GROUPS,
    FIELD_N_TOTAL,
    FIELD_BETA_ALPHA_RATIO,
    VALID_TESTS,
    VALID_MODES,
    MODE_A_PRIORI,
    MODE_POST_HOC,
    MODE_COMPROMISE,
    MODE_CRITERION,
    MODE_SENSITIVITY,
    MODE_REQUIRED_FIELDS,
    ERR_MISSING_PARAM,
    ERR_UNKNOWN_PARAM,
    ERR_INVALID_VALUE,
    ERR_UNSUPPORTED,
    format_version_output,
    format_success_output,
    format_error_output,
)
from src.engine.anova_oneway import (
    compute_a_priori,
    compute_post_hoc,
    compute_compromise,
    compute_criterion,
    compute_sensitivity,
    EngineError,
)


def run(cli_args: Optional[List[str]] = None) -> int:
    """Executes the CLI with the provided arguments or sys.argv[1:]."""
    args = sys.argv[1:] if cli_args is None else list(cli_args)

    # 1. Version Query Check (SPEC.md Section 2.2)
    if FLAG_VERSION in args:
        print(json.dumps(format_version_output(), separators=(",", ":")), file=sys.stdout)
        return 0

    # 2. Argument Syntax Parsing (SPEC.md Section 2.1)
    parsed_flags: Dict[str, str] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if not token.startswith("--"):
            err_dict = format_error_output(
                f"Syntax error: expected parameter starting with '--', got '{token}'",
                ERR_INVALID_VALUE,
            )
            print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
            return 2

        flag_name = token[2:]
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            err_dict = format_error_output(
                f"Parameter '{token}' requires a value",
                ERR_INVALID_VALUE,
                field=flag_name,
            )
            print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
            return 2

        parsed_flags[flag_name] = args[i + 1]
        i += 2

    # 3. Validate Test Identifier (SPEC.md Section 2.3, 3.2 Table, Section 6.1 Scenario 9)
    if FIELD_TEST not in parsed_flags:
        err_dict = format_error_output(
            f"Missing required parameter '--{FIELD_TEST}'",
            ERR_MISSING_PARAM,
            field=FIELD_TEST,
        )
        print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
        return 2

    test_id = parsed_flags[FIELD_TEST]
    if test_id not in VALID_TESTS:
        err_dict = format_error_output(
            f"Unsupported test family '{test_id}'",
            ERR_UNSUPPORTED,
            field=FIELD_TEST,
        )
        print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
        return 2

    # 4. Validate Mode Identifier (SPEC.md Section 2.3, 3.2 Table)
    if FIELD_MODE not in parsed_flags:
        err_dict = format_error_output(
            f"Missing required parameter '--{FIELD_MODE}'",
            ERR_MISSING_PARAM,
            field=FIELD_MODE,
        )
        print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
        return 2

    mode_id = parsed_flags[FIELD_MODE]
    if mode_id not in VALID_MODES:
        err_dict = format_error_output(
            f"Unsupported mode '{mode_id}'",
            ERR_UNSUPPORTED,
            field=FIELD_MODE,
        )
        print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
        return 2

    # 5. Check for Unknown or Mode-Irrelevant Parameters (SPEC.md Section 2.1, 3.2, 6.1 Scenario 3)
    allowed_fields = {FIELD_TEST, FIELD_MODE} | set(MODE_REQUIRED_FIELDS.get(mode_id, ()))
    for flag_name in parsed_flags:
        if flag_name not in allowed_fields:
            err_dict = format_error_output(
                f"Unknown or mode-irrelevant parameter '--{flag_name}'",
                ERR_UNKNOWN_PARAM,
                field=flag_name,
            )
            print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
            return 2

    # 6. Check for Missing Required Parameters (SPEC.md Section 2.1, 3.2, 6.1 Scenario 2)
    for req_field in MODE_REQUIRED_FIELDS[mode_id]:
        if req_field not in parsed_flags:
            err_dict = format_error_output(
                f"Missing required parameter '--{req_field}'",
                ERR_MISSING_PARAM,
                field=req_field,
            )
            print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
            return 2

    # 7. Delegate to Pure Engine for Validation and Calculation (SPEC.md Section 4)
    try:
        if mode_id == MODE_A_PRIORI:
            result = compute_a_priori(
                effect_size_f=parsed_flags[FIELD_F],
                alpha=parsed_flags[FIELD_ALPHA],
                target_power=parsed_flags[FIELD_POWER],
                groups=parsed_flags[FIELD_GROUPS],
            )
        elif mode_id == MODE_POST_HOC:
            result = compute_post_hoc(
                effect_size_f=parsed_flags[FIELD_F],
                alpha=parsed_flags[FIELD_ALPHA],
                n_total=parsed_flags[FIELD_N_TOTAL],
                groups=parsed_flags[FIELD_GROUPS],
            )
        elif mode_id == MODE_COMPROMISE:
            result = compute_compromise(
                effect_size_f=parsed_flags[FIELD_F],
                beta_alpha_ratio=parsed_flags[FIELD_BETA_ALPHA_RATIO],
                n_total=parsed_flags[FIELD_N_TOTAL],
                groups=parsed_flags[FIELD_GROUPS],
            )
        elif mode_id == MODE_CRITERION:
            result = compute_criterion(
                effect_size_f=parsed_flags[FIELD_F],
                target_power=parsed_flags[FIELD_POWER],
                n_total=parsed_flags[FIELD_N_TOTAL],
                groups=parsed_flags[FIELD_GROUPS],
            )
        elif mode_id == MODE_SENSITIVITY:
            result = compute_sensitivity(
                alpha=parsed_flags[FIELD_ALPHA],
                target_power=parsed_flags[FIELD_POWER],
                n_total=parsed_flags[FIELD_N_TOTAL],
                groups=parsed_flags[FIELD_GROUPS],
            )
        else:
            err_dict = format_error_output(
                f"Unsupported mode '{mode_id}'",
                ERR_UNSUPPORTED,
                field=FIELD_MODE,
            )
            print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
            return 2

        out_json = format_success_output(mode_id, result)
        print(json.dumps(out_json, separators=(",", ":")), file=sys.stdout)
        return 0

    except EngineError as ee:
        # SPEC.md Section 2.1 & 3.1: Exit code 2 for input / contract failures
        err_dict = format_error_output(ee.message, ee.code, ee.field)
        print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
        return ee.exit_code
    except Exception as exc:
        # SPEC.md Section 2.1: Exit code 1 for internal calculation errors
        err_dict = format_error_output(f"Internal calculation error: {exc}", "INTERNAL_ERROR")
        print(json.dumps(err_dict, separators=(",", ":")), file=sys.stdout)
        return 1


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
