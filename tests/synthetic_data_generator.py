"""Create synthetic RI monthly files + target workbook matching real layouts."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows


INDUSTRIES = [
    ("금속 광업", "06"),
    ("도매 및 상품 중개업", "46"),
    ("식료품 제조업", "10"),
    ("섬유제품 제조업", "13"),
]


def _write_ri_month(path: Path, year: int, month: int, rows: list[dict]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.merge_cells("A1:E1")
    ws["A1"] = f"{year}년 {month}월 Risk Index 보고서"
    headers = ["국가한글명", "업종한글명", "수입자국가코드", "업종코드", "Risk Index"]
    for c, h in enumerate(headers, start=1):
        ws.cell(2, c, h)

    r = 3
    last_country = None
    for row in rows:
        country = row["country_name"]
        # blank repeated country label like the real file
        ws.cell(r, 1, country if country != last_country else None)
        ws.cell(r, 2, row["industry_name"])
        ws.cell(r, 3, row["country_code"] if country != last_country else None)
        ws.cell(r, 4, row["industry_code"])  # keep as string
        ws.cell(r, 5, f"RI {int(row['ri'])}")
        last_country = country
        r += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def _write_target(path: Path, rows: list[dict]) -> None:
    wb = Workbook()
    # unused left sheet
    ws0 = wb.active
    ws0.title = "04.월별손해율총괄분석"
    ws0["A1"] = "unused"

    ws = wb.create_sheet("단기수출보험")
    # rows 1-2 filler
    ws["F1"] = "검증자료"
    ws["F2"] = ""
    headers = [
        "행 레이블",
        "국가등급",
        "평균 : 사고율(%)",
        "평균 : 손해율(%)",
        "평균 : 실질손해율",
        "미화국별총위험량(단기)",
    ]
    for c, h in enumerate(headers, start=6):
        ws.cell(3, c, h)

    r = 4
    for row in rows:
        ws.cell(r, 6, row["country_name"])
        ws.cell(r, 7, row.get("country_grade"))
        ws.cell(r, 8, row.get("accident_rate"))
        ws.cell(r, 9, row.get("loss_ratio"))
        ws.cell(r, 10, row.get("real_loss_ratio"))
        ws.cell(r, 11, row.get("exposure"))
        r += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def generate_scenario(root: Path, scenario: str, seed: int = 42) -> Path:
    """
    scenario:
      aligned | null | untestable
    """
    rng = np.random.default_rng(seed)
    out = root / scenario
    ri_dir = out / "risk_index"
    tgt_dir = out / "target"
    ri_dir.mkdir(parents=True, exist_ok=True)
    tgt_dir.mkdir(parents=True, exist_ok=True)

    if scenario == "untestable":
        countries = [(f"국가{i}", f"{600 + i}") for i in range(1, 6)]
    else:
        countries = [(f"국가{i}", f"{600 + i}") for i in range(1, 31)]

    # true risk latent 0-1
    latent = {name: rng.random() for name, _ in countries}

    for month in range(1, 13):
        rows = []
        for name, code in countries:
            # some countries missing late months
            if scenario != "untestable" and name in {"국가28", "국가29"} and month > 4:
                continue
            base = latent[name]
            if scenario == "aligned":
                ri = int(np.clip(np.floor(base * 5) + 1, 1, 5))
            elif scenario == "null":
                ri = int(rng.integers(1, 6))
            else:
                ri = int(np.clip(np.floor(base * 5) + 1, 1, 5))

            for j, (ind_name, ind_code) in enumerate(INDUSTRIES):
                ri_row = ri
                # inject industry mix for a few countries
                if name == "국가1" and j == 0:
                    ri_row = min(5, ri + 1) if ri < 5 else ri
                rows.append(
                    {
                        "country_name": name,
                        "country_code": code,
                        "industry_name": ind_name,
                        "industry_code": ind_code,
                        "ri": ri_row,
                    }
                )
        _write_ri_month(
            ri_dir / f"2025년 {month}월 Risk Index 보고서.xlsx",
            2025,
            month,
            rows,
        )

    target_rows = []
    for name, code in countries:
        z = latent[name]
        if scenario == "aligned":
            grade = int(np.clip(np.floor(z * 7) + 1, 1, 7))
            # many zeros; positives increase with risk
            accident = 0.0 if rng.random() > z else float(0.01 + z * rng.random() * 2)
            loss = 0.0 if rng.random() > z else float(0.1 + z * rng.random() * 10)
            real = 0.0 if accident == 0 and loss == 0 else float(loss * (0.5 + rng.random()))
        elif scenario == "null":
            grade = int(rng.integers(1, 8))
            accident = 0.0 if rng.random() > 0.3 else float(rng.random() * 2)
            loss = 0.0 if rng.random() > 0.3 else float(rng.random() * 10)
            real = 0.0 if rng.random() > 0.3 else float(rng.random() * 10)
        else:
            grade = int(np.clip(np.floor(z * 7) + 1, 1, 7))
            accident = 0.0
            loss = 0.0
            real = 0.0

        target_rows.append(
            {
                "country_name": name,
                "country_grade": grade,
                "accident_rate": accident,
                "loss_ratio": loss,
                "real_loss_ratio": real,
                "exposure": float(rng.integers(1_000_000, 90_000_000)),
            }
        )

    # extras: unmatched + excluded labels + NA grade
    if scenario != "untestable":
        target_rows.append(
            {
                "country_name": "미매칭국",
                "country_grade": 3,
                "accident_rate": 0.0,
                "loss_ratio": 0.0,
                "real_loss_ratio": 0.0,
                "exposure": 1_000_000,
            }
        )
        target_rows.append(
            {
                "country_name": "값 없음",
                "country_grade": None,
                "accident_rate": 0.0,
                "loss_ratio": 0.0,
                "real_loss_ratio": 0.0,
                "exposure": None,
            }
        )
        target_rows.append(
            {
                "country_name": "기타",
                "country_grade": None,
                "accident_rate": 0.0,
                "loss_ratio": 0.0,
                "real_loss_ratio": 0.0,
                "exposure": None,
            }
        )

    # Write #N/A as string for a row to emulate Excel error token
    if scenario == "aligned":
        target_rows[2]["country_grade"] = "#N/A"
        target_rows[2]["exposure"] = "#N/A"

    _write_target(
        tgt_dir / "04.월별손해율총괄분석_국별 사고율, 손해율_단기수출보험만.xlsx",
        target_rows,
    )

    # also write a RI-only unmatched country via an extra country in month files already;
    # add one RI country not in target for null/aligned
    if scenario in {"aligned", "null"}:
        # rewrite month 1 to append 추가국 — simpler: add to all months in a second pass
        for month in range(1, 13):
            path = ri_dir / f"2025년 {month}월 Risk Index 보고서.xlsx"
            # reload by regenerating all rows including extra — skip; coverage tested via 미매칭국
            pass

    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="tests/fixtures")
    parser.add_argument(
        "--scenario",
        choices=["aligned", "null", "untestable", "all"],
        default="all",
    )
    args = parser.parse_args(argv)
    root = Path(args.out)
    scenarios = ["aligned", "null", "untestable"] if args.scenario == "all" else [args.scenario]
    for s in scenarios:
        path = generate_scenario(root, s)
        print(f"generated {s} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
