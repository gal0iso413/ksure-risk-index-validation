# 다음 작업 — `ksure-risk-index-validation`

**Last updated:** 2026-08-10  
**Current phase:** 확정 스키마 반영 구현 + 합성 테스트

## 지금

1. ~~데이터 메타·파이프라인·합성 테스트~~
2. ~~requirements 패키지: 내부 PC에 이미 있음 → wheelhouse 불필요~~
3. ~~RI 방향: 1–5, RI5=고위험 확정~~
4. **다음: 내부 PC 실행** (최소 코드 반입 → input 배치 → config → `run_all.bat`)
5. 첫 실행 후 `unmatched_countries.xlsx` 보고 필요 시 `country_name_map.json`만 보강

## 하지 않음

- 실데이터 git 반입
- 국가×업종 직접 정합성 주장
- 퍼지 국가매칭, 비율 재스케일, 수식 재계산
- ML/대시보드
- wheelhouse (현재 환경에서는 불필요)
