# 10편 KIPRIS Plus 클라이언트 연동 (로컬 전용)

28편 `build_queries.py`가 만든 KIPRIS 식(`TL=[…] AB=[…] CL=[…]`)을 10편 `kipris_client.py`로 실제 호출해
결과를 `imports/`에 CSV로 저장하는 다리입니다. **로컬 실행 환경에서만** 됩니다(웹 채팅 앱은 외부 API 차단).

## 준비(한 번만)
1. 10편 템플릿에서 `kipris_client.py`와 `fixtures/`를 받아 `starter/tools/`에 복사합니다.
   (https://sonovman.github.io/ai-practice-handbooks/kipris-plus/templates/)
2. 인증키 등록 후 창을 새로 엽니다: `setx KIPRIS_KEY "본인_REST_AccessKey"`
   (Claude Desktop/Cowork은 앱을 완전히 종료 후 재실행해야 새 키를 읽습니다.)
3. 한글 깨짐 방지: 매 창에서 `chcp 65001` + `set PYTHONUTF8=1`.

## 시험(서버 접속 없음)
- `python tools/test_kipris_client.py`, `python tools/test_kipris_bridge.py` → 둘 다 OK.
  (10편 파일을 복사하지 않았으면 bridge 시험은 자동으로 건너뜁니다.)

## 사용
```
python tools/kipris_bridge.py 사건/plan.json                 # 계획만(호출 0건)
python tools/kipris_bridge.py 사건/plan.json --probe --run   # 첫 1건만, XML 태그 확인
python tools/kipris_bridge.py 사건/plan.json --run --out 사건/imports
python tools/kipris_bridge.py 사건/plan.json --nolimit --run --out 사건/imports  # 확대선출원용
python tools/kipris_client.py usage                           # 이번 달 호출 수
```
- `imports/kipris_Qn.csv`(쿼리별) + `imports/kipris_all.csv`(통합, 여러 쿼리에 걸린 문헌 위로, `cutoff_check` 열).
- `--run` 없으면 호출 안 함 · 호출 상한(`--max-calls`, 기본 30) 초과 시 중단.
- ta(명칭+요약)는 `TL=[…]+AB=[…]`라 필드마다 따로 호출 후 합칩니다(개선 반영).

## 입력값 이름(추정 — 첫 사용 때 --probe로 확인)
| 웹 식 | API 입력값 |
|---|---|
| `TL=[…]` 명칭 | `inventionTitle` |
| `AB=[…]` 요약 | `astrtCont` |
| `CL=[…]` 청구범위 | `claimScope` |
| `IPC=[…]` | `ipcNumber` |

## 첫 사용 때 반드시 확인(--probe 결과로)
1. 입력값 이름이 다르면 `kipris_bridge.py`의 `FIELD_MAP` 수정.
2. `*`(AND)·`+`(OR) 해석: 같은 필드에 `착즙` / `착즙*스크루` / `착즙+스크루`를 넣어 건수 비교(AND는 줄고 OR는 늘어야 정상).
3. 공개일 태그 이름이 다르면 `DATE_COLS` 수정(기준일 전·후 표시 정확도).
4. 근접(^n): 기본은 AND로 바꿔 보냄. API가 근접을 지원하면 `--keep-near`.

## 주의
- 경로 철자 `patUtiModInfoSearchSevice`의 'Sevice'는 공식 주소 철자 — 'Service'로 고치면 실패.
- 명령 프롬프트에서 `^`는 특수문자 — 근접 식은 큰따옴표 안에 넣거나 bridge(방법 A) 사용.
- 무료 이용은 상품별이 아니라 모든 상품 합산 월 1,000건, 매월 1일 초기화.
- 10편 `kipris_client.py`는 CC BY-NC 라이선스라 이 키트에 포함하지 않았습니다 — 사용자가 직접 복사해 씁니다.
