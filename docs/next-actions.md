# 다음 작업 — `ksure-risk-index-validation`

세션 시작 시 여기와 [`plan.md`](plan.md)부터 본다.

**Last updated:** 2026-08-10  
**Current phase:** repo settings 완료 → **데이터 메타 수집** → lean 파이프라인 구현

## 지금 할 일

1. ~~저장소 골격·README·AGENTS·intake~~ **완료**
2. **사용자:** 외부에서 확인 가능한 데이터 메타 제공
   - RI 파일/시트, 컬럼, grain (국가만인지 국가×업종인지)
   - 타깃 파일/시트, 컬럼, grain (국가×월/연 등)
   - RI 방향 (높을수록 위험?)
   - 국가등급 문자→순서 매핑
   - 파일 확장자 (xlsx/xls/csv) 및 내부 Python 버전
3. **Cursor:** lean `src` + example config + 합성 데이터 + smoke
4. **Cursor:** `run_all.bat` + `requirements.txt` + wheelhouse 안내
5. 합성 테스트 통과 후에만 내부 PC 실행

## 하지 않음

- 실데이터를 이 저장소에 넣기
- 국가×업종 직접 정합성으로 과장 보고
- ML·대시보드·CDN 기반 보고서
- ChatGPT 계획의 스크립트를 그대로 6개 CLI로 쪼개 이관 (lean 우선)

## 내부 이관 최소 세트 (목표)

```text
run_all.bat
requirements.txt
config/*.example.json  (+ 내부에서 채운 *.json)
src/
wheelhouse/            (필요 시)
input/README.txt
```
