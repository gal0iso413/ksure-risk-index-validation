# Plan — `ksure-risk-index-validation`

국가 RI 정합성 검증 PoC. 상세 방법론은 초기 ChatGPT 계획을 참고하되, **국가 단위·lean 이관**으로 재구성한다.

## 1. 과업 성격

모델 개발이 아니다. RI(1~5)와 실제 위험지표의 관계가 기대 방향과 맞는지 검증한다.

핵심 타깃: 손해율, 실질손해율, 사고율, 국가등급.  
참고만: 국별총위험량(규모·포트폴리오 효과 주의).

## 2. 분석 단위 (고정)

| 데이터 | 기대 grain | 처리 |
|--------|------------|------|
| RI | 국가 (업종이 있어도 **국가 요약**) | 중앙값·평균·고위험 비율 등 |
| Target | 국가×기간 (월/연) | 국가 요약 후 조인; 월행을 독립표본으로 쓰지 않음 |

의사반복 금지. 국가×업종 직접 정합성을 검증했다고 쓰지 않는다.

## 3. 파이프라인 (lean)

단일 진입점 `python -m src.run_all` / `run_all.bat`가 아래를 순서 실행:

1. Inspect inputs (프로필)
2. Validate schema / quality issues
3. Join coverage
4. Build analysis table (국가 grain)
5. Statistical validation (Spearman + bootstrap CI, Kruskal–Wallis, 단조 여부)
6. Figures (정적 PNG)
7. Offline HTML report

모듈은 `src/` 아래 소수 파일로 유지. 내부 PC에는 **디렉터리 통째 최소 세트**만 옮긴다.

## 4. 판정

지표별: Supported / Partially supported / Not supported / Untestable.  
p-value만으로 결론 내지 않음. 방향·효과·CI·표본·민감도를 함께 보고.

## 5. 환경

- Home: 합성 데이터로 개발·테스트
- Internal: 오프라인 pip + wheelhouse, 실데이터 `input/`
- 원본 읽기 전용, 시드 고정, 민감 로그 금지

## 6. 완료 기준

- [ ] 합성 정합·무관·오류 시나리오 smoke 통과
- [ ] 매칭률·분석 단위·한계가 보고서에 명시
- [ ] 정합성 없음/검증 불가 결론도 정상 생성
- [ ] 내부 이관 파일 수 최소화 문서화
