"""변동 알림 감시 스크립트 — 바뀌었을 때만 말하는 감시자

어디서 쓰나
  1) Hermes Agent 의 스크립트 예약 작업 (AI 호출 없이 실행 → 토큰 비용 0)
       ~/.hermes/scripts/ 에 넣고
       hermes cron create "every 6h" --no-agent --script watch.py --deliver telegram --name fx-watch
     Hermes 는 이 스크립트가 출력한 글자를 그대로 텔레그램으로 보내고,
     아무것도 출력하지 않으면 보내지 않습니다.
  2) 내 PC 에서 직접 (Hermes 없이)
       python watch.py            ← 확인만, 화면에 출력
       python watch.py --telegram ← 바뀌었으면 텔레그램으로 직접 전송
                                    (환경변수 TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 필요)

무엇을 감시할지는 아래 [설정] 만 고치면 됩니다. Python 표준 라이브러리만 씁니다.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# ───────────────────────── [설정] ─────────────────────────
NAME = "원-달러 환율"                                   # 알림에 표시될 이름
URL = "https://open.er-api.com/v6/latest/USD"         # 확인할 주소 (키 없이 쓰는 공개 환율 API)
JSON_PATH = "rates.KRW"                                # JSON 이면 값 위치 (점으로 구분)
REGEX = None                                           # 웹페이지면 정규식, 예: r"가격\s*([\d,]+)원"
THRESHOLD_PCT = 0.5                                    # 숫자 값이 이 % 이상 움직일 때만 알림 (0 이면 조금만 바뀌어도)
# ─────────────────────────────────────────────────────────

STATE = Path(__file__).with_name(".watch-state-" + re.sub(r"\W+", "_", NAME) + ".json")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "watch.py (personal monitor)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def extract(body):
    if JSON_PATH:
        value = json.loads(body)
        for key in JSON_PATH.split("."):
            value = value[int(key)] if isinstance(value, list) else value[key]
        return value
    if REGEX:
        m = re.search(REGEX, body)
        if not m:
            raise ValueError("정규식에 맞는 내용을 찾지 못했습니다.")
        return m.group(1) if m.groups() else m.group(0)
    raise ValueError("JSON_PATH 나 REGEX 중 하나는 정해야 합니다.")


def as_number(v):
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.stderr.write("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 환경변수가 없어 전송하지 않았습니다.\n")
        return False
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=20) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        sys.stderr.write(f"텔레그램 전송 실패: {e}\n")
        return False


def main():
    try:
        new = extract(fetch(URL))
    except Exception as e:
        sys.stderr.write(f"[{NAME}] 확인 실패: {e}\n")
        return 1  # 0 이 아닌 종료 → Hermes 가 오류 알림을 보냄

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        old = json.loads(STATE.read_text(encoding="utf-8-sig")) if STATE.exists() else None
    except (ValueError, OSError):
        old = None  # 기록 파일이 깨졌으면 새로 시작
    STATE.write_text(json.dumps({"value": new, "checked_at": now}, ensure_ascii=False), encoding="utf-8")

    if old is None:
        message = f"[{NAME}] 감시를 시작합니다. 현재 값: {new}"
    else:
        a, b = as_number(old["value"]), as_number(new)
        if a is not None and b is not None:
            pct = (b - a) / a * 100 if a else 0.0
            if a == b or abs(pct) < THRESHOLD_PCT:
                return 0  # 변화 없음 → 아무것도 출력하지 않음 (= 알림 없음)
            arrow = "▲" if b > a else "▼"
            message = f"[{NAME}] {arrow} {a:,.2f} → {b:,.2f} ({pct:+.2f}%)\n이전 확인: {old['checked_at']} / 이번 확인: {now}"
        else:
            if str(old["value"]) == str(new):
                return 0
            message = f"[{NAME}] 내용이 바뀌었습니다.\n이전: {old['value']}\n현재: {new}"

    print(message)
    if "--telegram" in sys.argv:
        send_telegram(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
