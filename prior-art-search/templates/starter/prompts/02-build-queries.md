# DB별 검색식 생성

plan.json으로 DB별 검색식과 바로열기 URL을 만들어 줘.
`python tools/build_queries.py plan.json --sheet work/search_sheet.md`
- 신규성용은 cutoff 이전 한정, KR은 확대선출원용(cutoff 없는) 식도 포함.
- 웹 DB는 사람이 실행해야 하니 링크와 식 원문을 함께. 실행 전 호출량은 dry-run으로.
