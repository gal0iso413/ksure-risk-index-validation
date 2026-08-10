@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "config\analysis_config.json" (
  echo [ERROR] config\analysis_config.json 이 없습니다.
  echo         config\analysis_config.example.json 을 복사해 경로·컬럼맵을 채우세요.
  exit /b 1
)

python -m src.run_all --config config\analysis_config.json
if errorlevel 1 (
  echo [ERROR] 파이프라인 실패. outputs\logs\ 를 확인하세요.
  exit /b 1
)

echo [OK] 완료. 보고서: outputs\report\risk_index_validation_report.html
endlocal
