#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kipris_client.py — KIPRIS Plus·공공데이터포털 지식재산 Open API를 공식 주소로 직접 호출하는 작은 클라이언트

특징
  - 표준 라이브러리만 사용 (추가 설치 없음, Python 3.8+)
  - 인증키는 코드에 쓰지 않고 환경변수에서 읽음 (KIPRIS_KEY, DATA_GO_KR_KEY)
  - 화면·파일에 남는 주소에서는 인증키를 가림
  - 응답 XML의 <item>을 열 이름 그대로 표로 바꿈 (열 이름을 미리 가정하지 않음)
  - 결과가 1건이어도 항상 목록으로 처리
  - 오류 응답(인증키 오류·한도 초과 등)을 찾아 알려 줌
  - 초당 호출 수를 제한하고(기본 초당 5건), 이번 달 호출 수를 내 컴퓨터에 기록해 무료 한도(월 1,000건)에 다가가면 경고

사용 예 (Windows 명령 프롬프트)
  set KIPRIS_KEY=발급받은_REST_AccessKey
  python kipris_client.py biblio 1020050050026
  python kipris_client.py search --title 자율주행 --rows 10 --csv result.csv
  python kipris_client.py raw /kipo-api/kipi/patUtiModInfoSearchSevice/getBibliographySumryInfoSearch applicationNumber=1020050050026 --show-xml
  python kipris_client.py usage

공공데이터포털(data.go.kr) API — 예: 특허기술거래 국유판매기술정보
  set DATA_GO_KR_KEY=공공데이터포털_인증키(Decoding)
  python kipris_client.py datagokr https://apis.data.go.kr/1431000/StaownTradePatentInfoService/<상세기능_오퍼레이션> pageNo=1 numOfRows=10
  (<상세기능_오퍼레이션>은 공공데이터포털 해당 API 페이지의 '상세기능'·Swagger에서 확인)
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

KIPRIS_BASE = "http://plus.kipris.or.kr"   # 공식 매뉴얼·샘플의 주소. 상품 명세서에 https 주소가 있으면 그것을 쓰세요.
PATH_BIBLIO = "/kipo-api/kipi/patUtiModInfoSearchSevice/getBibliographySumryInfoSearch"  # 'Sevice' 철자는 공식 주소 그대로
PATH_SEARCH = "/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
FREE_MONTHLY = 1000
USAGE_FILE = Path.home() / ".kipris_usage.json"
KEY_PARAMS = ("ServiceKey", "serviceKey", "accessKey")


class ApiError(Exception):
    pass


# ── 인증키 가리기 ──────────────────────────────────────────────
def mask(url_or_text):
    return re.sub(r"((?:ServiceKey|serviceKey|accessKey)=)[^&\s]+", r"\1****", str(url_or_text))


# ── 호출량 관리 ────────────────────────────────────────────────
class Usage:
    def __init__(self, path=USAGE_FILE, today=None):
        self.path = Path(path)
        self.month = (today or dt.date.today()).strftime("%Y-%m")
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        self.count = data.get(self.month, 0)
        self.data = data

    def add(self, n=1):
        self.count += n
        self.data[self.month] = self.count
        try:
            self.path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
        return self.count

    def warn_text(self):
        if self.count >= FREE_MONTHLY:
            return "이번 달 기록상 {}건 — 무료 한도(월 {}건, 상품 합산)를 넘었을 수 있습니다.".format(self.count, FREE_MONTHLY)
        if self.count >= FREE_MONTHLY * 0.8:
            return "이번 달 기록상 {}건 — 무료 한도(월 {}건)의 80%를 넘었습니다.".format(self.count, FREE_MONTHLY)
        return ""


# ── 호출 ───────────────────────────────────────────────────────
class Client:
    def __init__(self, key, base=KIPRIS_BASE, key_param="ServiceKey", per_second=5.0, timeout=30,
                 usage=None, opener=None):
        if not key:
            raise ApiError("인증키가 없습니다. 환경변수(KIPRIS_KEY 또는 DATA_GO_KR_KEY)를 설정하세요.")
        if per_second > 40:
            raise ApiError("초당 40건 이하로 설정하세요(계정별 초당 50건 이상이면 이용이 제한됩니다).")
        self.key, self.base, self.key_param = key, base, key_param
        self.min_gap = 1.0 / per_second
        self.timeout = timeout
        self.usage = usage
        self.opener = opener or urllib.request.urlopen
        self._last = 0.0

    def build_url(self, path, params):
        q = dict(params)
        q[self.key_param] = self.key
        base = path if path.startswith("http") else self.base + path
        return base + ("&" if "?" in base else "?") + urllib.parse.urlencode(q)

    def get(self, path, params):
        wait = self.min_gap - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        url = self.build_url(path, params)
        self._last = time.monotonic()
        try:
            with self.opener(url, timeout=self.timeout) as r:
                body = r.read()
        except urllib.error.HTTPError as e:
            raise ApiError("HTTP {} — {}".format(e.code, mask(url)))
        except urllib.error.URLError as e:
            raise ApiError("접속 실패({}) — 인터넷·사내 방화벽에서 plus.kipris.or.kr 접속이 허용되는지 확인하세요. {}".format(e.reason, mask(url)))
        if self.usage:
            self.usage.add()
        return body


# ── 응답 해석 ──────────────────────────────────────────────────
def _text(el):
    return (el.text or "").strip() if el is not None else ""


def _local(tag):
    return tag.split("}", 1)[-1]


def check_error(root):
    """오류로 보이는 응답이면 ApiError. 응답 형식이 서비스마다 조금씩 달라 여러 표시를 함께 본다."""
    tags = {_local(e.tag): _text(e) for e in root.iter()}
    if _local(root.tag) == "OpenAPI_ServiceResponse" or "returnReasonCode" in tags:      # 공공데이터포털 게이트웨이 오류
        raise ApiError("게이트웨이 오류 {}: {}".format(tags.get("returnReasonCode", "?"), tags.get("returnAuthMsg") or tags.get("errMsg", "")))
    if tags.get("successYN", "").upper() == "N":
        raise ApiError("요청 실패 {}: {}".format(tags.get("resultCode", "?"), tags.get("resultMsg", "")))
    code = tags.get("resultCode")
    if code not in (None, "", "0", "00", "000"):
        raise ApiError("요청 실패 {}: {}".format(code, tags.get("resultMsg", "")))


def parse_items(xml_bytes):
    """XML에서 <item>마다 하위 태그를 {태그: 값}으로. 하위의 하위 태그는 '부모.자식'으로 펼친다."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        snippet = xml_bytes[:200].decode("utf-8", "replace")
        raise ApiError("XML이 아닌 응답입니다({}): {}".format(e, snippet))
    check_error(root)
    rows = []
    for item in root.iter():
        if _local(item.tag) != "item":
            continue
        row = {}
        for child in item:
            kids = list(child)
            if kids:
                for g in kids:
                    row["{}.{}".format(_local(child.tag), _local(g.tag))] = _text(g)
            else:
                row[_local(child.tag)] = _text(child)
        rows.append(row)
    total = next((_text(e) for e in root.iter() if _local(e.tag) in ("totalCount", "TotalSearchCount")), "")
    return rows, total


def write_csv(rows, path):
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return cols


def show(rows, total, limit_cols=6):
    print("결과 {}건{}".format(len(rows), " (전체 {}건)".format(total) if total else ""))
    if not rows:
        return
    cols = list(rows[0].keys())
    print("받은 열 {}개: {}".format(len(cols), ", ".join(cols)))
    for i, r in enumerate(rows, 1):
        brief = " | ".join("{}={}".format(c, r.get(c, ""))[:60] for c in cols[:limit_cols])
        print("{:>3}. {}".format(i, brief))


# ── 명령 ───────────────────────────────────────────────────────
def kv_pairs(items):
    out = {}
    for s in items:
        if "=" not in s:
            raise ApiError("'이름=값' 형식이어야 합니다: {}".format(s))
        k, v = s.split("=", 1)
        if k in KEY_PARAMS:
            raise ApiError("인증키는 인자로 넣지 말고 환경변수로 설정하세요.")
        out[k] = v
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="KIPRIS Plus·공공데이터포털 지식재산 Open API 클라이언트")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("biblio", help="출원번호로 서지요약정보")
    b.add_argument("application_number")
    s = sub.add_parser("search", help="발명의 명칭 등으로 항목별 검색")
    s.add_argument("--title", help="발명의 명칭(inventionTitle)")
    s.add_argument("--rows", type=int, default=10, help="한 번에 받을 건수(numOfRows)")
    s.add_argument("--page", type=int, default=1, help="페이지(pageNo)")
    # 입력값 이름은 KIPRIS Plus 상품 명세서로 확인하세요. 다르면 raw 명령으로 명세서 이름 그대로 넣습니다.
    r = sub.add_parser("raw", help="KIPRIS Plus 임의 기능 호출 (명세서의 경로와 입력값 그대로)")
    r.add_argument("path")
    r.add_argument("params", nargs="*")
    d = sub.add_parser("datagokr", help="공공데이터포털 API 호출 (예: 특허기술거래 정보)")
    d.add_argument("url", help="End Point + /오퍼레이션")
    d.add_argument("params", nargs="*")
    sub.add_parser("usage", help="이번 달 기록된 호출 수")
    for p in (b, s, r, d):
        p.add_argument("--csv", help="결과를 CSV로 저장")
        p.add_argument("--show-xml", action="store_true", help="받은 XML 원문도 출력 (태그 이름 확인용)")
        p.add_argument("--per-second", type=float, default=5.0)
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    usage = Usage()
    if a.cmd == "usage":
        print("{} 기록: {}건 / 무료 {}건".format(usage.month, usage.count, FREE_MONTHLY))
        print("이 숫자는 이 컴퓨터에서 이 스크립트로 부른 횟수입니다. 정확한 사용량은 KIPRIS Plus 마이페이지에서 확인하세요.")
        return 0
    try:
        if a.cmd == "datagokr":
            c = Client(os.environ.get("DATA_GO_KR_KEY", ""), key_param="serviceKey", per_second=a.per_second)
            path, params = a.url, kv_pairs(a.params)
        else:
            c = Client(os.environ.get("KIPRIS_KEY", ""), per_second=a.per_second, usage=usage)
            if a.cmd == "biblio":
                path, params = PATH_BIBLIO, {"applicationNumber": re.sub(r"\D", "", a.application_number)}
            elif a.cmd == "search":
                params = {"numOfRows": a.rows, "pageNo": a.page}
                if not a.title:
                    raise ApiError("--title 을 넣으세요. 다른 조건은 raw 명령으로 명세서의 입력값 이름 그대로 넣습니다.")
                params["inventionTitle"] = a.title
                path = PATH_SEARCH
            else:
                path, params = a.path, kv_pairs(a.params)
        body = c.get(path, params)
        if a.show_xml:
            print(body.decode("utf-8", "replace"))
        rows, total = parse_items(body)
        show(rows, total)
        if a.csv:
            cols = write_csv(rows, a.csv)
            print("저장: {} ({}건, 열 {}개)".format(a.csv, len(rows), len(cols)))
        w = usage.warn_text()
        if w and a.cmd != "datagokr":
            print("※ " + w)
        return 0
    except ApiError as e:
        print("오류: " + mask(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
