#!/usr/bin/env python3
"""역공학 적법 범위 사전 점검 (핸드북 21). 표준 라이브러리만 사용.

REA로 무언가를 분석하기 전에, 그 대상·목적·방법이 '해도 되는 범위'인지 먼저 따집니다.
분석 자체가 적법해도 결과물의 사용이 위법일 수 있으므로, 분석 단계와 사용 단계를 나눠 묻습니다.
이 도구는 법률 자문이 아니라 체크리스트입니다. 애매하면 전문가(변호사·변리사)에게 확인하세요.

  python tools/scope_check.py                      # 대화형으로 질문
  python tools/scope_check.py --answers ans.json   # 미리 적은 답으로
  python tools/scope_check.py --print-questions     # 질문지만 출력(ans.json 양식)

판정  RED 하지 말 것 · AMBER 전문가 확인 전 보류 · GREEN 진행하되 기록
종료 코드 0(GREEN) / 1(AMBER) / 2(RED)
"""
import argparse
import json
import sys
from pathlib import Path

# 각 질문: key, 물음, (답이 위험을 뜻하면) 위험 신호
QUESTIONS = [
    ("own", "분석 대상이 내가 직접 만든 프로그램입니까?", None),
    ("oss_license", "오픈소스라면 라이선스가 역공학·개작을 허용합니까? (아니오/모름이면 주의)", None),
    ("authorized", "내가 만든 것이 아니라면, 소유자의 서면 허락이나 계약상 권한이 있습니까?", None),
    ("lawful_copy", "그 프로그램을 정당한 권한으로 보유·이용 중입니까? (구매·라이선스 등)", None),
    ("purpose", "주 목적은 무엇입니까? [호환성/보안연구/내데이터이전/교육·학습/상호운용/기타]", None),
    ("tpm", "복사 방지·DRM·라이선스 인증 같은 기술적 보호조치를 우회해야 합니까?", "yes"),
    ("server", "분석이 내 소유가 아닌 원격 서버·계정의 보호를 우회하거나 그 서버에 요청을 보냅니까?", "yes"),
    ("info_easy", "호환에 필요한 정보를 공개 문서·API 등 다른 방법으로 쉽게 얻을 수 있습니까? (예이면 역분석 보충성 요건에 어긋남)", "yes"),
    ("scope_limited", "분석을 '목적에 필요한 부분'으로 한정합니까?", None),
    ("redistribute", "분석 결과로 원본과 표현이 실질적으로 유사한 프로그램을 만들어 배포·판매할 계획입니까?", "yes"),
    ("resell_code", "추출한 코드·리소스·데이터를 제3자에게 제공하거나 상업적으로 재사용할 계획입니까?", "yes"),
    ("eula", "대상의 이용약관(EULA)이 역공학을 금지하고 있습니까? (예/모름이면 주의)", None),
]
YES = {"y", "yes", "예", "네", "true", "1", "o"}
NO = {"n", "no", "아니오", "아니요", "false", "0", "x"}


def norm(v):
    s = str(v).strip().lower()
    if s in YES:
        return "yes"
    if s in NO:
        return "no"
    return s


def evaluate(a):
    reds, ambers, notes = [], [], []

    def g(k):
        return norm(a.get(k, ""))

    # RED: 명백히 선을 넘는 경우
    if g("tpm") == "yes":
        reds.append("기술적 보호조치(DRM·복사방지·라이선스 인증) 우회는 이 핸드북의 범위를 벗어납니다. 저작권법 보호조치 무력화 금지·각국 법(미국 DMCA §1201 등) 위반 소지가 큽니다.")
    if g("server") == "yes":
        reds.append("내 소유가 아닌 원격 서버·계정의 보호를 우회하거나 무단 요청을 보내는 것은 정보통신망법 등 위반이 될 수 있습니다. 서버 측 로직은 역공학 대상이 아닙니다.")
    if g("redistribute") == "yes":
        reds.append("원본과 표현이 실질적으로 유사한 프로그램을 개발·배포·판매하는 것은 저작권법 제101조의4 제2항이 금지합니다(역분석 정보의 목적 외 이용).")
    if g("resell_code") == "yes":
        reds.append("추출한 코드·리소스를 제3자 제공·상업 재사용하는 것은 저작권 침해가 될 수 있습니다. 아이디어·원리의 학습과 표현의 복제는 다릅니다.")

    owned = g("own") == "yes"
    authorized = g("authorized") == "yes"
    oss_ok = g("oss_license") == "yes"

    # 권한 축: 내 것도, 허락도, 허용 라이선스도 아니면 보류
    if not (owned or authorized or oss_ok):
        ambers.append("내가 만든 것도, 소유자 허락도, 역공학을 허용하는 오픈소스 라이선스도 확인되지 않았습니다. 권한을 먼저 확보하세요.")
    if not owned and g("lawful_copy") != "yes":
        ambers.append("정당한 권한으로 보유·이용 중인 프로그램이 아니면 역분석 허용 요건(저작권법 제101조의3 제1항 제6호)에 해당하기 어렵습니다.")

    purpose = g("purpose")
    legit_purposes = {"호환성", "보안연구", "내데이터이전", "교육", "교육·학습", "상호운용"}
    if purpose and purpose not in legit_purposes and purpose != "기타":
        notes.append("목적('{}')이 전형적 정당 목적과 달라 보입니다. 호환성·보안연구·내 데이터 이전·교육·상호운용 중 무엇에 해당하는지 분명히 하세요.".format(purpose))
    if purpose == "기타":
        ambers.append("목적이 '기타'입니다. 역분석의 정당 목적(호환성 확보 등)에 해당하는지 확인 전에는 보류하세요.")

    if purpose == "호환성":
        if g("info_easy") == "yes":
            ambers.append("호환 정보를 다른 방법으로 쉽게 얻을 수 있다면, 역분석의 보충성 요건(제101조의4)에 어긋납니다. 공개 API·문서를 먼저 확인하세요.")
        if g("scope_limited") != "yes":
            ambers.append("호환 목적 역분석은 '호환에 필요한 부분'으로 한정해야 합니다(상당성 요건).")

    if g("eula") in ("yes", "모름", ""):
        notes.append("이용약관(EULA)이 역공학을 금지하는지 확인하세요. 법상 허용되는 범위와 계약상 제한은 별개로 다퉈질 수 있습니다.")
    if oss_ok and not owned:
        notes.append("오픈소스라도 라이선스의 고지·동일조건 배포 의무를 지키세요.")

    status = "RED" if reds else "AMBER" if ambers else "GREEN"
    return status, reds, ambers, notes


def report(status, reds, ambers, notes):
    mark = {"GREEN": "진행 가능(기록 남기기)", "AMBER": "보류 — 전문가 확인", "RED": "하지 말 것"}
    out = ["적법 범위 점검 결과: [{}] {}".format(status, mark[status]), ""]
    if reds:
        out.append("■ 하지 말 것")
        out += ["  - " + r for r in reds]
    if ambers:
        out.append("■ 확인 전 보류")
        out += ["  - " + r for r in ambers]
    if notes:
        out.append("■ 참고")
        out += ["  - " + r for r in notes]
    if status == "GREEN":
        out.append("분석 대상·목적·방법·권한 근거를 work/ 에 기록으로 남기고 진행하세요. 결과물의 사용 단계도 같은 기준으로 다시 점검합니다.")
    out.append("")
    out.append("※ 이 도구는 체크리스트이며 법률 자문이 아닙니다. 구체적 사안은 변호사·변리사에게 확인하세요.")
    return "\n".join(out)


def ask_interactive():
    a = {}
    sys.stderr.write("각 물음에 답하세요(예/아니오, purpose는 보기 중 하나). 모르면 '모름'.\n\n")
    for k, q, _ in QUESTIONS:
        try:
            a[k] = input(q + " > ").strip()
        except EOFError:
            a[k] = ""
    return a


def main(argv=None):
    ap = argparse.ArgumentParser(description="역공학 적법 범위 사전 점검")
    ap.add_argument("--answers", help="답을 담은 JSON 파일")
    ap.add_argument("--print-questions", action="store_true")
    ap.add_argument("--report", help="결과를 저장할 파일")
    a = ap.parse_args(argv)
    if a.print_questions:
        tmpl = {k: "" for k, _, _ in QUESTIONS}
        sys.stdout.write(json.dumps(tmpl, ensure_ascii=False, indent=2) + "\n")
        for k, q, _ in QUESTIONS:
            sys.stdout.write("# {}: {}\n".format(k, q))
        return 0
    answers = json.loads(Path(a.answers).read_text(encoding="utf-8")) if a.answers else ask_interactive()
    status, reds, ambers, notes = evaluate(answers)
    text = report(status, reds, ambers, notes)
    sys.stdout.write(text + "\n")
    if a.report:
        Path(a.report).write_text(text + "\n", encoding="utf-8")
    return {"GREEN": 0, "AMBER": 1, "RED": 2}[status]


if __name__ == "__main__":
    sys.exit(main())
