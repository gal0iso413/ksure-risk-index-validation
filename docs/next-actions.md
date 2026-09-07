# 다음 작업 — `ksure-risk-index-validation`

**Last updated:** 2026-09-07  
**Current phase:** 5지표 주분석 기록 완료. 2026-09-07 미팅 후 **위험국 축소 + 선행 사례(데이터 대기) + 업종 접기(후속)** 로 전환.

미팅 원문 정리: [`meeting-2026-09-07.md`](meeting-2026-09-07.md).

## 지금

1. ~~데이터 메타·파이프라인·합성 테스트~~
2. ~~requirements 패키지: 내부 PC에 이미 있음 → wheelhouse 불필요~~
3. ~~RI 방향: 1–5, RI5=고위험 확정~~
4. ~~내부 PC 1차 실행 (DRM 해제 후 HTML 산출)~~
5. ~~1차 고객 설명 (4지표)~~
6. ~~내부 PC에서 코드 반영 후 재실행 (총위험량 핵심 타깃 + 상세 HTML/MD)~~
7. ~~5지표 HTML 캡처 → 집계만 [`results-guide-second.md`](results-guide-second.md)에 저장~~
8. 필요 시 `unmatched_countries.xlsx` 보고 `country_name_map.json` 보강 후 재실행
9. **데이터 대기 (리스크 부서):** 심층감시국 이력, 국가등급 변동 이력, 과거 월별 RI(저장된 값), 국가×업종 인수 금액. 레이아웃 확정 전 코드 확장 최소화.
10. **과업 A (기존 2025 파일로 가능한 것부터):** 주분석을 국가등급 5·6·7 부분집합에서 재실행할 설계. 혼재 월 집계 대안(최빈/빈도)은 설정 스위치로. 선행·심층감시는 9번 수신 후.
11. **과업 B (9번 인수 금액 수신 후):** 업종으로 접은 RI 표. 정합성 검증이 아니라 신규 요약. 국가 타깃에 업종 RI를 붙여 검증한다고 쓰지 않음.
12. 거시 유가·환율 등(과업 C)은 이 레포에 넣지 않음.

문장 수정은 [`report_template.md`](report_template.md). 읽기: [`results-guide.md`](results-guide.md).  
5지표 집계: [`results-guide-second.md`](results-guide-second.md). 1차 4지표 기록: [`results-guide-first.md`](results-guide-first.md).

## 일정

- 9월: 행안부 평가 증빙 (이 레포 산출과 별개로 진행 중일 수 있음)
- **10월:** 과업 A 결과 (가능하면 B 초안)
- **11월 중순 전:** 리스크 부서 사업계획 결과 보고에 넣을 문장

## 하지 않음

- 실데이터 git 반입
- 국가×업종 행에 연간 국가 타깃을 반복해 정합성을 주장
- 퍼지 국가매칭, 비율 재스케일, 수식 재계산
- ML 재학습·대시보드
- 과거 RI 재추정(코드 없는 구간을 새로 만들기)
- 거시 원자재 수집
- wheelhouse (현재 환경에서는 불필요)
