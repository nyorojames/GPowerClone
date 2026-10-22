"""CLI thin wrapper for gpower-clone.

SPEC.md Section 7:
Performs parameter parsing, delegates calculations directly to src.engine,
and outputs single-line JSON on stdout.
Contains NO mathematical or statistical calculation logic.
All flag names, aliases, and output key names live in src.cli.contract_map.
"""

import argparse
import json
import sys
from typing import List, Optional

from src.cli.contract_map import (
    FLAG_TEST,
    FLAG_MODE,
    FLAG_EFFECT_SIZE,
    FLAG_EFFECT_SIZE_ALIAS,
    FLAG_ALPHA,
    FLAG_POWER,
    FLAG_GROUPS,
    FLAG_GROUPS_ALIAS,
    FLAG_N_TOTAL,
    TEST_ANOVA_ONEWAY,
    MODE_A_PRIORI,
    MODE_POST_HOC,
    VALID_TESTS,
    VALID_MODES,
    format_success_output,
    format_error_output,
)
from src.engine.anova_oneway import (
    compute_a_priori,
    compute_post_hoc,
    CalculationError,
)


class ContractArgumentParser(argparse.ArgumentParser):
    """Custom parser ensuring all CLI syntax errors conform to the JSON contract."""
    def error(self, message: str):
        print(json.dumps(format_error_output(message), separators=(",", ":")), file=sys.stdout)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Builds the argument parser using centralized contract flags."""
    parser = ContractArgumentParser(
        prog="gpower-clone",
        add_help=False,
    )
    parser.add_argument(FLAG_TEST, dest="test", type=str, required=False)
    parser.add_argument(FLAG_MODE, dest="mode", type=str, required=False)
    parser.add_argument(FLAG_EFFECT_SIZE, FLAG_EFFECT_SIZE_ALIAS, dest="effect_size", type=str, required=False)
    parser.add_argument(FLAG_ALPHA, dest="alpha", type=str, required=False)
    parser.add_argument(FLAG_POWER, dest="power", type=str, required=False)
    parser.add_argument(FLAG_GROUPS, FLAG_GROUPS_ALIAS, dest="groups", type=str, required=False)
    parser.add_argument(FLAG_N_TOTAL, dest="n_total", type=str, required=False)
    return parser


def run(cli_args: Optional[List[str]] = None) -> int:
    """Executes the CLI with the provided arguments or sys.argv."""
    parser = build_parser()
    try:
        args, unknown = parser.parse_known_args(args=cli_args)
    except SystemExit as se:
        return se.code
    except Exception as e:
        print(json.dumps(format_error_output(f"Argument parsing failed: {e}"), separators=(",", ":")), file=sys.stdout)
        return 1

    if unknown:
        print(json.dumps(format_error_output(f"Unrecognized arguments: {unknown}"), separators=(",", ":")), file=sys.stdout)
        return 1

    # Validate test
    if args.test is None:
        print(json.dumps(format_error_output(f"Missing required argument: {FLAG_TEST}"), separators=(",", ":")), file=sys.stdout)
        return 1
    if args.test not in VALID_TESTS:
        print(json.dumps(format_error_output(f"Unsupported test '{args.test}'. Expected '{TEST_ANOVA_ONEWAY}'"), separators=(",", ":")), file=sys.stdout)
        return 1

    # Validate mode
    if args.mode is None:
        print(json.dumps(format_error_output(f"Missing required argument: {FLAG_MODE}"), separators=(",", ":")), file=sys.stdout)
        return 1
    if args.mode not in VALID_MODES:
        print(json.dumps(format_error_output(f"Invalid mode '{args.mode}'. Must be '{MODE_A_PRIORI}' or '{MODE_POST_HOC}'"), separators=(",", ":")), file=sys.stdout)
        return 1

    # Check common required flags
    if args.effect_size is None:
        print(json.dumps(format_error_output(f"Missing required argument: {FLAG_EFFECT_SIZE}"), separators=(",", ":")), file=sys.stdout)
        return 1
    if args.alpha is None:
        print(json.dumps(format_error_output(f"Missing required argument: {FLAG_ALPHA}"), separators=(",", ":")), file=sys.stdout)
        return 1
    if args.groups is None:
        print(json.dumps(format_error_output(f"Missing required argument: {FLAG_GROUPS}"), separators=(",", ":")), file=sys.stdout)
        return 1

    try:
        if args.mode == MODE_A_PRIORI:
            if args.power is None:
                print(json.dumps(format_error_output(f"Missing required argument: {FLAG_POWER}"), separators=(",", ":")), file=sys.stdout)
                return 1
            result = compute_a_priori(
                effect_size_f=args.effect_size,
                alpha=args.alpha,
                target_power=args.power,
                groups=args.groups,
            )
        else:  # MODE_POST_HOC
            if args.n_total is None:
                print(json.dumps(format_error_output(f"Missing required argument: {FLAG_N_TOTAL}"), separators=(",", ":")), file=sys.stdout)
                return 1
            result = compute_post_hoc(
                effect_size_f=args.effect_size,
                alpha=args.alpha,
                n_total=args.n_total,
                groups=args.groups,
            )

        output_json = format_success_output(result)
        # SPEC.md Section 7: Strict single-line JSON on success
        print(json.dumps(output_json, separators=(",", ":")), file=sys.stdout)
        return 0

    except CalculationError as ce:
        # SPEC.md Section 6: Single-line JSON {"error": "<description>"} and non-zero exit code
        print(json.dumps(format_error_output(ce.error), separators=(",", ":")), file=sys.stdout)
        return 1
    except Exception as exc:
        print(json.dumps(format_error_output(str(exc)), separators=(",", ":")), file=sys.stdout)
        return 1


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
