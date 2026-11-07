# 검증 질문 단계

```
방금 브리핑의 사실 주장(숫자, 날짜, 사건번호, 이름, 인과, 인용)을 모두 뽑아 줘.
주장마다 확인 질문을 만들고, 브리핑을 보지 말고 원문만 보고 다시 답해.
| 주장 | 확인 질문 | 원문에서 찾은 답(구절·위치) | 일치/불일치/원문에 없음 |
불일치·원문에 없음은 고치거나 지운 최종본을 다시 써 줘.
```

그다음 PC에서 기계 대조:
```
python tools/evidence_check.py 원문.txt 브리핑.md
python tools/term_check.py 브리핑.md --glossary glossary/*.csv --source 원문.txt
python tools/cite_check.py 브리핑.md --source 판결문.txt        # 판례일 때
```
