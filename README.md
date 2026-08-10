# ksure-risk-index-validation

**국가 Risk Index 정합성 검증** — 2025년 국가 RI(1~5)와 단기수출보험 국별 사고율·손해율·실질손해율·국가등급의 **정합성**을 검토하는 단기 분석 PoC.

자매 프로젝트: `ksure-overseas-biz-analysis`, `ksure-similar-claim-search`

**계획:** [`docs/plan.md`](docs/plan.md) · **세션 시작:** [`docs/next-actions.md`](docs/next-actions.md) · **Intake:** [`docs/intake.md`](docs/intake.md)

실데이터는 내부 PC에만 둔다. 저장소에는 코드·example config·합성 fixture만 포함한다.

## 범위

| | |
|--|--|
| **In** | 2025 국가 RI ↔ 2025 위험지표 정합성 (비모수·발생여부·민감도·오프라인 HTML) |
| **Out** | ML/예측, 대시보드, 국가×업종 직접 검증, 국별총위험량 핵심 판정, “독립 예측력” 주장 |

표현: **현재 RI와 2025년 위험지표 간 정합성 검토** (독립 예측력 검증 아님). RI 유용성 결론을 강제하지 않는다.

## 데이터 (확정)

| 구분 | 내용 |
|------|------|
| RI | `input/risk_index/2025년*월*Risk*Index*보고서*.xlsx` ×12, `Sheet1`, 헤더 Excel 2행, A:E, 값 `RI 1`–`RI 5` |
| 검증 | `input/target/…단기수출보험만.xlsx`, 시트 `단기수출보험`, 헤더 Excel 3행, **F:K만** |
| 조인 | 국가한글명 (코드 없음). 퍼지매칭 금지. 수동맵 `config/country_name_map.json` |
| 집계 | 국가×업종×월 → 국가×월 → **국가×연도 1행**. 주 RI = 월별 중앙값. 주 코호트 ≥6개월 |

`RI 5`=고위험, 국가등급 1–7(클수록 고위험). 비율은 cached 숫자 그대로, 헤더 `%`로 재스케일하지 않음.

## 구조

```text
config/     analysis_config · country_name_map (example)
src/        load_ri · load_target · aggregate · matching · stats · figures · report · run_all
tests/      synthetic_data_generator · test_smoke
input/      risk_index/ · target/   (gitignore)
outputs/    tables · figures · logs · report
wheelhouse/ 오프라인 wheel
```

## 실행 (Home — 합성)

```bash
cd /home/tom/projects/ksure-risk-index-validation
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

.venv/bin/python -m tests.synthetic_data_generator --out tests/fixtures --scenario all
.venv/bin/python -m pytest tests/test_smoke.py -v

# 예시 파이프라인 (aligned fixture 경로를 config에 넣거나 아래처럼)
cp config/analysis_config.example.json config/analysis_config.json
# paths를 tests/fixtures/aligned/... 로 수정 후
.venv/bin/python -m src.run_all --config config/analysis_config.json
```

## 실행 (내부 PC — Windows 오프라인)

```bat
python -m pip install --no-index --find-links wheelhouse -r requirements.txt
REM input\risk_index\ 에 월별 12개, input\target\ 에 검증 xlsx
REM config\*.example.json → *.json 복사·경로 확인
run_all.bat
```

산출: `outputs/tables/country_analysis_table.xlsx`, `figures/*.png`, `report/risk_index_validation_report.html`
