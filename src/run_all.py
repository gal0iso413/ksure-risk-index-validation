"""Pipeline entrypoint. Implementation comes after data meta is locked."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="국가 Risk Index 정합성 검증 파이프라인"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="path to analysis_config.json",
    )
    args = parser.parse_args(argv)

    print(
        f"[ksure-risk-index-validation] stub: config={args.config}\n"
        "Pipeline modules are not implemented yet. "
        "Provide data meta, then implement lean src steps.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
