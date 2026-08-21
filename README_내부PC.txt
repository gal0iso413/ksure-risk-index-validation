내부 PC 실행 (USB 반입용)

.bat 파일은 반입하지 않습니다. 실행은 아래 python 한 줄입니다.

1) 이 zip을 풀어 프로젝트 폴더로 씁니다. 이미 같은 폴더가 있으면 src, config, docs 만 덮어쓰면 됩니다.
   input/ 실데이터와 기존 config\analysis_config.json 은 지우지 마세요.

2) 처음이면 명령 프롬프트에서 프로젝트 폴더로 이동한 뒤:
   copy config\analysis_config.example.json config\analysis_config.json
   copy config\country_name_map.example.json config\country_name_map.json
   (이미 json 이 있으면 복사하지 마세요. 경로·제외국가만 확인)

3) 데이터:
   input\risk_index\   ← 2025년 월별 RI xlsx 12개
   input\target\       ← 검증 xlsx 1개
   ~$ 로 시작하는 임시 엑셀은 넣지 마세요.

4) 프로젝트 루트에서:
   python -m src.run_all --config config\analysis_config.json

5) 결과:
   outputs\report\risk_index_validation_report.html
   outputs\report\risk_index_validation_report.md

실패 시 outputs\logs\ 를 확인하세요.
docs\report_template.md 는 보고서 문장 소스입니다. 이 파일이 없으면 HTML이 만들어지지 않습니다.
Python·라이브러리는 내부 PC에 이미 있는 것을 사용합니다.
