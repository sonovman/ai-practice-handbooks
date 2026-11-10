#!/usr/bin/env python3
"""patent-intelligence 공용 함수 (핸드북 34). 표준 라이브러리만 사용.

- read_table(path): .xlsx / .csv 를 읽어 (머리행, 행 목록) 으로 돌려준다.
  WIPSON 내보내기처럼 맨 위에 제목 줄이 몇 줄 있어도 '알려진 열 이름'이
  3개 이상 있는 첫 줄을 머리행으로 잡는다.
- write_xlsx(path, rows): 시범 자료용 아주 단순한 xlsx 작성기.
- 번호·국가·문헌종류 정규화 도우미.
"""
import csv
import datetime as dt
import io
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def utf8_console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


# ── 열 별칭 ─────────────────────────────────────────────
def load_aliases(path):
    """config/column_aliases.csv: field,alias (한 줄에 하나)."""
    amap = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            field = (row.get("field") or "").strip()
            alias = (row.get("alias") or "").strip()
            if field and alias:
                amap[norm_header(alias)] = field
    return amap


def norm_header(s):
    return re.sub(r"[\s_\-\(\)\[\]/·.:]", "", str(s or "")).lower()


# ── 표 읽기 ─────────────────────────────────────────────
def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _read_xlsx_rows(path, sheet=None):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid2target = {r.get("Id"): r.get("Target") for r in rels.iter(REL_NS + "Relationship")}
        sheets = []
        for s in wb.find("m:sheets", NS).findall("m:sheet", NS):
            rid = s.get("{%s}id" % NS["r"])
            target = rid2target[rid].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            sheets.append((s.get("name"), target))
        if sheet is None:
            name, target = sheets[0]
        else:
            match = [t for t in sheets if t[0] == sheet]
            if not match:
                raise SystemExit("시트 '%s'가 없습니다. 있는 시트: %s" % (sheet, ", ".join(n for n, _ in sheets)))
            name, target = match[0]
        root = ET.fromstring(z.read(target))
    rows = []
    for r in root.iter("{%s}row" % NS["m"]):
        cells = {}
        for c in r.findall("m:c", NS):
            idx = _col_index(c.get("r"))
            t = c.get("t")
            if t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            else:
                v = c.find("m:v", NS)
                val = v.text if v is not None else ""
                if t == "s" and val != "":
                    val = shared[int(val)]
            cells[idx] = val
        if cells:
            width = max(cells) + 1
            rows.append([cells.get(i, "") for i in range(width)])
        else:
            rows.append([])
    return rows


def _read_csv_rows(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit("CSV 인코딩을 읽지 못했습니다(UTF-8 또는 CP949로 저장해 주세요).")
    return [row for row in csv.reader(io.StringIO(text))]


def read_table(path, aliases, sheet=None):
    p = str(path).lower()
    if p.endswith(".xlsx") or p.endswith(".xlsm"):
        rows = _read_xlsx_rows(path, sheet)
    elif p.endswith(".csv"):
        rows = _read_csv_rows(path)
    elif p.endswith(".xls"):
        raise SystemExit("옛 .xls 형식입니다. 엑셀에서 '다른 이름으로 저장 → .xlsx' 후 다시 실행하세요.")
    else:
        raise SystemExit("지원 형식: .xlsx, .csv")
    header_idx = None
    for i, row in enumerate(rows[:30]):
        hits = sum(1 for c in row if norm_header(c) in aliases)
        if hits >= 3:
            header_idx = i
            break
    if header_idx is None:
        raise SystemExit("머리행을 찾지 못했습니다. config/column_aliases.csv에 실제 열 이름을 추가하세요.")
    header = rows[header_idx]
    fields = [aliases.get(norm_header(h)) for h in header]
    unknown = [h for h, f in zip(header, fields) if h and not f]
    out = []
    for n, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        if not any(str(c).strip() for c in row):
            continue
        rec = {"_row": n}
        for f, v in zip(fields, row):
            if f and str(v).strip() != "":
                rec[f] = str(v).strip()
        out.append(rec)
    return header, fields, unknown, out


# ── 값 정규화 ───────────────────────────────────────────
def parse_date(s):
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", s) and 20000 < float(s) < 80000:  # 엑셀 일련번호
        return (dt.date(1899, 12, 30) + dt.timedelta(days=int(float(s)))).isoformat()
    m = re.match(r"(\d{4})[.\-/년 ]*(\d{1,2})[.\-/월 ]*(\d{1,2})", s)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return dt.date(y, mo, d).isoformat()
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", s)
    if m:
        try:
            return dt.date(*map(int, m.groups())).isoformat()
        except ValueError:
            return None
    return None


def compact(num):
    """번호 비교용: 영숫자만 대문자로."""
    return re.sub(r"[^0-9A-Za-z]", "", str(num or "")).upper()


COUNTRY_WORDS = {"한국": "KR", "대한민국": "KR", "미국": "US", "일본": "JP", "중국": "CN",
                 "유럽": "EP", "EPO": "EP", "PCT": "WO", "WIPO": "WO"}


def norm_country(val, *numbers):
    v = str(val or "").strip().upper()
    if v in ("KR", "US", "JP", "CN", "EP", "WO"):
        return v
    for k, c in COUNTRY_WORDS.items():
        if k.upper() in v:
            return c
    for num in numbers:
        m = re.match(r"\s*(KR|US|JP|CN|EP|WO)", str(num or "").upper())
        if m:
            return m.group(1)
    return v or "?"


KIND_RE = re.compile(r"(A\d?|B\d?|U\d?|Y\d?|S\d?)\s*$")


def kind_code(num):
    m = KIND_RE.search(str(num or "").upper().replace(" ", ""))
    return m.group(1) if m else ""


def doc_type(country, kind_text, app_no, pub_no, reg_no):
    """invention / utility / design 판정. 문헌종류 열 → 번호 규칙 순."""
    t = str(kind_text or "")
    if any(w in t for w in ("실용", "Utility", "UTILITY", "实用")):
        return "utility"
    if any(w in t for w in ("디자인", "Design", "外观")):
        return "design"
    codes = [kind_code(pub_no), kind_code(reg_no)]
    if country in ("CN", "JP", "KR") and any(c.startswith(("U", "Y")) for c in codes if c):
        return "utility"
    if country == "US" and any(c.startswith("S") for c in codes if c):
        return "design"
    a = compact(app_no)
    if country == "KR":
        m = re.search(r"(10|20|30)(\d{4})\d{7}", a)
        if m:
            return {"10": "invention", "20": "utility", "30": "design"}[m.group(1)]
    if country == "CN":
        m = re.search(r"(\d{4})([123])\d{7}", a)
        if m:
            return {"1": "invention", "2": "utility", "3": "design"}[m.group(2)]
    return "invention"


def year_of(date_iso):
    return int(date_iso[:4]) if date_iso else None


def months_between(d1, d2):
    a = dt.date.fromisoformat(d1)
    b = dt.date.fromisoformat(d2)
    return (b.year - a.year) * 12 + (b.month - a.month) + (b.day - a.day) / 31.0


def tokens(text):
    t = re.sub(r"[^0-9A-Za-z가-힣ぁ-んァ-ン一-龥]", " ", str(text or "").lower())
    out = set()
    for w in t.split():
        if re.fullmatch(r"[가-힣ぁ-んァ-ン一-龥]+", w) and len(w) > 2:
            out.update(w[i:i + 2] for i in range(len(w) - 1))  # 한중일 2글자 조각
        elif len(w) > 1:
            out.add(w)
    return out


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ── 시범용 xlsx 작성기 ─────────────────────────────────
def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _col_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def write_xlsx(path, rows, sheet_name="검색결과"):
    sheet_rows = []
    for ri, row in enumerate(rows, start=1):
        cells = "".join(
            '<c r="%s%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (_col_name(ci), ri, _esc(v))
            for ci, v in enumerate(row) if str(v) != "")
        sheet_rows.append('<row r="%d">%s</row>' % (ri, cells))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="%s"><sheetData>%s</sheetData></worksheet>' % (NS["m"], "".join(sheet_rows)))
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="%s" xmlns:r="%s"><sheets><sheet name="%s" sheetId="1" r:id="rId1"/></sheets></workbook>'
          % (NS["m"], NS["r"], _esc(sheet_name)))
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>')
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                 '</Relationships>')
    ctypes = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
              '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
              '</Types>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
