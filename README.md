# ksure-risk-index-validation

**국가 Risk Index 정합성 검증** — K-SURE가 제공하는 국가 RI(1~5등급)가 손해율·실질손해율·사고율·국가등급 등 실제 위험지표와 기대 방향의 관계를 보이는지 검증하는 단기 분석 PoC.

자매 프로젝트: [`ksure-overseas-biz-analysis`](../ksure-overseas-biz-analysis), [`ksure-similar-claim-search`](../ksure-similar-claim-search)

**계획:** [`docs/plan.md`](docs/plan.md)  
**세션 시작:** [`docs/next-actions.md`](docs/next-actions.md)  
**Intake:** [`docs/intake.md`](docs/intake.md)

**데이터 경계:** 실 RI·타깃 원자료는 내부 PC에만 존재한다. 이 저장소에는 코드·config 예시·합성 데이터만 둔다. `input/` 실파일은 git에 올리지 않는다.

## 범위

| | |
|--|--|
| **In** | 국가 RI ↔ 국가 위험지표 정합성 (Spearman·등급별 분포·민감도·오프라인 HTML 보고서) |
| **Out** | ML/예측, 대시보드, 국가×업종 직접 정합성 주장, 국별총위험량의 핵심 타깃화 |

분석 결과가 RI의 유용성을 지지해야 한다는 전제는 없다. Supported / Partially supported / Not supported / Untestable을 **지표별로** 판정한다.

## 구조

```text
config/     analysis·column·국가등급 맵 (example → 내부에서 실명 복사)
src/        lean 파이프라인 (단일 진입점 + 소수 모듈)
tests/      합성 데이터 · smoke
input/      실데이터 위치 (gitignore)
outputs/    tables · figures · logs · report
wheelhouse/ 오프라인 wheel
docs/       plan · intake · next-actions
```

내부 이관 파일 수를 최소화한다. ChatGPT 계획의 6-스크립트 분리는 참고만 하고, 배포 형태는 `run_all.bat` 한 번이다.

## 실행 (Home PC — 합성 데이터)

```bash
cd /home/tom/projects/ksure-risk-index-validation
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 합성 데이터 + smoke (구현 후)
.venv/bin/python -m tests.synthetic_data_generator
.venv/bin/python -m pytest tests/test_smoke.py -v

# 전체 파이프라인 (config는 example 복사본)
cp config/analysis_config.example.json config/analysis_config.json
cp config/column_map.example.json config/column_map.json
cp config/country_grade_map.example.json config/country_grade_map.json
.venv/bin/python -m src.run_all --config config/analysis_config.json
```

## 실행 (내부 PC — Windows, 오프라인)

```bat
REM 1) (최초 1회) 오프라인 패키지 설치
python -m pip install --no-index --find-links wheelhouse -r requirements.txt

REM 2) input\ 에 RI·타깃 파일 배치, config\*.json 컬럼맵 확정

REM 3) 원클릭
run_all.bat
```

산출물: `outputs/tables/`, `outputs/figures/`, `outputs/report/risk_index_validation_report.html`, `outputs/logs/run_summary.log`

## 제약

- 원본 파일 읽기 전용 · 수정 금지
- 인터넷·CDN·외부 API·클라우드 없음
- 로그에 기업명·민감 행 데이터 출력 금지
- 난수 시드 고정
- 의사반복 금지: 타깃이 국가 단위면 RI를 국가로 집계한 뒤 조인
