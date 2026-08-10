Place real files on the internal PC only. Never commit them.

Expected layout:

  input/risk_index/2025년 MM월 Risk Index 보고서.xlsx   (12 monthly files)
  input/target/04.월별손해율총괄분석_국별 사고율, 손해율_단기수출보험만.xlsx

Ignore Excel lock files (~$*.xlsx).

Before run_all.bat:
1. Copy config/*.example.json → config/*.json (country_name_map optional empty)
2. Confirm paths in analysis_config.json
3. Confirm ri_higher_means_riskier matches report meta (RI 5 = high risk)
