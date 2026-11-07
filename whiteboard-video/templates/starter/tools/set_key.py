#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
set_key.py — Gemini API 키를 운영체제 키체인에 저장/확인/삭제 (화면에 키가 보이지 않게 입력)

  Windows: 자격 증명 관리자 · macOS: 키체인 · Linux: Secret Service(GNOME 키링 등)

준비:   pip install keyring
사용법: python tools/set_key.py          # 저장 (입력 내용은 화면에 표시되지 않음)
        python tools/set_key.py --check  # 저장 여부만 확인(값은 앞 4자리만)
        python tools/set_key.py --delete # 삭제
저장 위치 이름: 서비스 gemini-api / 사용자 default  (wbkit.py가 이 이름으로 읽습니다)
"""
import argparse
import getpass
import sys

SERVICE, USER = "gemini-api", "default"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--delete", action="store_true")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        import keyring
    except ImportError:
        print("keyring이 없습니다: pip install keyring")
        return 2
    if a.check:
        v = keyring.get_password(SERVICE, USER)
        print("저장됨: {}…".format(v[:4]) if v else "저장된 키 없음")
        return 0 if v else 1
    if a.delete:
        try:
            keyring.delete_password(SERVICE, USER)
            print("삭제했습니다.")
        except keyring.errors.PasswordDeleteError:
            print("저장된 키가 없습니다.")
        return 0
    key = getpass.getpass("Gemini API 키를 붙여 넣고 Enter (화면에 표시되지 않음): ").strip()
    if not key.startswith("AIza") or len(key) < 30:
        print("키 형식이 이상합니다(보통 AIza로 시작). 저장하지 않았습니다.")
        return 1
    keyring.set_password(SERVICE, USER, key)
    print("키체인에 저장했습니다: {}… — 이제 .env 파일은 필요 없습니다.".format(key[:4]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
