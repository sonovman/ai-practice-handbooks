#!/usr/bin/env python3
"""승인 관문 상태 기록기 (핸드북 34). 대화가 끊겨도 승인 상태가 파일에 남게 한다.

  python tools/pi_gate.py init   --state work/state.json --round 2026-R4
  python tools/pi_gate.py status --state work/state.json
  python tools/pi_gate.py submit ANALYSIS --file work/03_analysis.md
  python tools/pi_gate.py reply  "승인"            # 사용자 답을 그대로 넣으면 해석해 기록
  python tools/pi_gate.py reply  "3번 문헌 빼고 다시"

단계: INPUT_VALIDATION → ANALYSIS(분석결과) → REPORT(보고서 초안) → FINAL(최종본) → CANDIDATES(후보) → HANDOFF
관문은 ANALYSIS · REPORT · CANDIDATES 세 곳. 승인 전에는 다음 단계 submit이 거부된다.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

from pi_common import utf8_console

STAGES = ["INPUT_VALIDATION", "ANALYSIS", "REPORT", "FINAL", "CANDIDATES", "HANDOFF"]
GATED = {"ANALYSIS", "REPORT", "CANDIDATES"}
STATE_NAMES = {"INPUT_VALIDATION": "INPUT_VALIDATION", "ANALYSIS": "ANALYSIS_DRAFTED", "REPORT": "REPORT_DRAFTED",
               "FINAL": "FINAL_REPORT_COMPLETED", "CANDIDATES": "CANDIDATES_PROPOSED", "HANDOFF": "HANDOFF_READY"}
APPROVED_NAMES = {"ANALYSIS": "ANALYSIS_APPROVED", "REPORT": "REPORT_APPROVED", "CANDIDATES": "CANDIDATES_APPROVED"}

APPROVE = re.compile(r"^\s*(승인|승인합니다|승인함|동의|확정|approve[d]?)\s*[.!]?\s*$", re.I)
CONTINUE = re.compile(r"^\s*(계속|계속해|계속 진행|continue)\s*[.!]?\s*$", re.I)
REVISE = re.compile(r"수정|삭제|빼|추가|바꿔|고쳐|변경|다시|보완|넣어|제외")
ADD_DATA = re.compile(r"추가\s*자료|자료\s*추가|공보\s*추가|첨부")


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def interpret(text, accept_continue=True):
    t = (text or "").strip()
    if not t:
        return "wait"
    if APPROVE.match(t):
        return "approve"
    if CONTINUE.match(t):
        return "implicit_approve" if accept_continue else "unclear"
    if ADD_DATA.search(t):
        return "add_data"
    if REVISE.search(t):
        return "revise"
    if re.match(r"^\s*(승인|좋|ok|오케이)", t, re.I):
        return "approve_with_note" if REVISE.search(t) is None and len(t) > 6 else "approve"
    return "unclear"


def load(path):
    p = Path(path)
    if not p.exists():
        raise SystemExit("상태 파일이 없습니다. 먼저 init을 실행하세요: %s" % path)
    return json.loads(p.read_text(encoding="utf-8"))


def save(path, st):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def init(path, round_name, accept_continue=True):
    st = {"round": round_name, "state": "INPUT_VALIDATION", "current": "INPUT_VALIDATION", "approved": [],
          "pending": None, "accept_continue_as_approval": accept_continue, "history": [
              {"at": now(), "event": "init", "state": "INPUT_VALIDATION"}]}
    save(path, st)
    return st


def can_submit(st, stage):
    i = STAGES.index(stage)
    for prev in STAGES[1:i]:
        if prev in GATED and prev not in st["approved"]:
            return False, "%s 관문이 아직 승인되지 않았습니다(%s 제출 불가)." % (prev, stage)
    if st.get("pending") and st["pending"]["stage"] != stage:
        return False, "%s가 승인 대기 중입니다. 먼저 답을 받으세요." % st["pending"]["stage"]
    return True, ""


def submit(st, stage, file=None, note=""):
    ok, why = can_submit(st, stage)
    if not ok:
        raise SystemExit("거부: " + why)
    st["current"] = stage
    st["state"] = STATE_NAMES[stage]
    version = 1 + sum(1 for h in st["history"] if h.get("event") == "submit" and h.get("stage") == stage)
    st["pending"] = {"stage": stage, "file": file, "version": version} if stage in GATED else None
    st["history"].append({"at": now(), "event": "submit", "stage": stage, "file": file, "version": version, "note": note})
    return st


def reply(st, text):
    if not st.get("pending"):
        raise SystemExit("승인 대기 중인 제출물이 없습니다.")
    stage = st["pending"]["stage"]
    kind = interpret(text, st.get("accept_continue_as_approval", True))
    ev = {"at": now(), "event": "reply", "stage": stage, "version": st["pending"]["version"], "text": text, "kind": kind}
    if kind in ("approve", "implicit_approve", "approve_with_note"):
        st["approved"].append(stage)
        st["state"] = APPROVED_NAMES[stage]
        ev["recorded_as"] = {"approve": "명시 승인", "implicit_approve": "묵시 승인('계속')",
                             "approve_with_note": "승인(메모 포함 — 메모가 수정 지시면 되돌릴 것)"}[kind]
        if stage == "ANALYSIS":
            ev["baseline"] = st["pending"]["file"]
            st["baseline"] = {"file": st["pending"]["file"], "version": st["pending"]["version"], "at": ev["at"],
                              "how": ev["recorded_as"]}
        st["pending"] = None
        msg = "%s 관문: %s으로 기록했습니다. 다음 단계로 갈 수 있습니다." % (stage, ev["recorded_as"])
    elif kind in ("revise", "add_data"):
        ev["recorded_as"] = "수정 후 재제출" if kind == "revise" else "추가자료 반영 후 재제출"
        msg = "%s 관문: 승인이 아닙니다(%s). 반영한 뒤 같은 관문에 다시 submit 하세요." % (stage, ev["recorded_as"])
    elif kind == "wait":
        ev["recorded_as"] = "무응답 — 대기"
        msg = "%s 관문: 응답이 없어 대기합니다. 다음 단계로 가지 않습니다." % stage
    else:
        ev["recorded_as"] = "불명확 — 한 가지 질문으로 확인"
        msg = "%s 관문: 승인인지 분명하지 않습니다. '승인'인지, 무엇을 고칠지 한 가지만 물어보세요." % stage
    st["history"].append(ev)
    return st, kind, msg


def status_text(st):
    L = ["회차 %s · 상태 %s" % (st["round"], st["state"]),
         "승인된 관문: " + (", ".join(st["approved"]) or "없음")]
    if st.get("baseline"):
        b = st["baseline"]
        L.append("승인된 분석 기준선: %s (v%s, %s, %s)" % (b["file"], b["version"], b["how"], b["at"]))
    if st.get("pending"):
        L.append("승인 대기: %s v%d (%s)" % (st["pending"]["stage"], st["pending"]["version"], st["pending"]["file"]))
    nxt = None
    for s in STAGES[1:]:
        ok, _ = can_submit(st, s)
        done = s in st["approved"] or any(h.get("event") == "submit" and h.get("stage") == s for h in st["history"])
        if ok and not done:
            nxt = s
            break
    if st.get("pending"):
        L.append("다음 할 일: 사용자 답 받기(승인 / 수정 / 추가자료)")
    elif nxt:
        L.append("다음 할 일: %s 작성 후 submit" % nxt)
    else:
        L.append("다음 할 일: 없음(완료)")
    return "\n".join(L)


def main():
    utf8_console()
    ap = argparse.ArgumentParser(description="승인 관문 상태 기록")
    ap.add_argument("cmd", choices=["init", "status", "submit", "reply"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--state", default="work/state.json")
    ap.add_argument("--round", default="이번 회차")
    ap.add_argument("--file")
    ap.add_argument("--note", default="")
    ap.add_argument("--no-continue", action="store_true", help="'계속'을 승인으로 보지 않음")
    a = ap.parse_args()
    if a.cmd == "init":
        st = init(a.state, a.round, not a.no_continue)
        print(status_text(st))
        return
    st = load(a.state)
    if a.cmd == "status":
        print(status_text(st))
    elif a.cmd == "submit":
        if a.arg not in STAGES[1:]:
            raise SystemExit("단계: " + ", ".join(STAGES[1:]))
        save(a.state, submit(st, a.arg, a.file, a.note))
        print(status_text(st))
    elif a.cmd == "reply":
        st, kind, msg = reply(st, a.arg or "")
        save(a.state, st)
        print(msg)
        print(status_text(st))


if __name__ == "__main__":
    main()
