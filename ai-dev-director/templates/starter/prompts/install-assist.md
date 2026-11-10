# AI DEV DIRECTOR 설치 도우미 프롬프트

Claude Code, Codex, Antigravity 중 하나의 대화창에 그대로 붙여 넣습니다.
(`D:/tools`, `D:/work/my_app` 은 내 경로로 바꿉니다.)

---

AI DEV DIRECTOR를 내 PC에 안전하게 설치하려고 한다. 아래 순서대로 하되, 각 단계 결과를 보여 주고 다음으로 넘어가라.
권한 우회 플래그(skip-permissions, yolo, full-access)는 쓰지 말고, 명령은 실행 전에 나에게 보여 줘라.

1. `D:/tools` 에서 공식 저장소만 받는다: `git clone https://github.com/digilogd-cmd/ai-dev-director.git`
   다른 주소·포크·압축 파일은 쓰지 않는다. 받은 뒤 `git log -1 --format="%H %s"` 로 커밋을 보여 줘라.
2. 폴더 안에 가상 환경을 만든다: `python -m venv .venv` → 윈도우는 `.venv\Scripts\activate`, 맥은 `source .venv/bin/activate`
3. `pip install -r requirements.txt requests` (requests는 시험 일부가 쓴다)
4. 이 작업 폴더의 `tools/director_preflight.py --director D:/tools/ai-dev-director --project D:/work/my_app` 를 실행해 결과를 표로 정리하라.
   `[중단]`이 있으면 거기서 멈추고 해결 방법만 알려 줘라.
5. `config.yaml` 에서 다음 두 줄만 바꾼다(다른 줄은 건드리지 마라):
   - `auto_apply: off`
   - `test_command:` 를 내 프로젝트의 실제 테스트 명령으로
6. `python tools/role_matrix.py --available <내가 로그인한 CLI들>` 결과로 HEAD·BUILDER·REVIEWER 배치를 제안하라.
7. 콘솔 켜는 법(윈도우 `.\start-companion.ps1`, 맥 `./start-companion.sh`)과 주소 `http://127.0.0.1:8081` 을 알려 주고, 여기서 멈춰라.
