---
name: whiteboard-video
description: 주제나 원고를 받아 대본 → Gemini TTS 내레이션 → 실제 음성 길이로 자막·장면 길이 → 손그림 선화 → 그리기 순서 주석 → 화이트보드 애니메이션 렌더 → 음성·자막 조립까지 한국어 화이트보드 설명 영상을 만든다. 화이트보드 영상, 손그림 애니메이션, SRT로 그리는 영상 요청에 사용.
---

# 화이트보드 설명 영상 만들기

이 프로젝트의 도구: `tools/wbkit.py`(음성·자막·조립·키 점검), `.agents/skills/srt-whiteboard-animation/`(그리기 렌더러), 선택으로 HyperFrames(`npx hyperframes`).
**단계마다 결과를 보여 주고 사용자의 확인을 받은 뒤 다음 단계로 갑니다.**

## 0. 준비 확인
1. `python tools/wbkit.py keycheck` — 실패가 있으면 멈추고 핸드북 3장 방법으로 키를 넣으라고 안내합니다. 키 값을 묻거나 받지 않습니다.
2. `.agents/skills/srt-whiteboard-animation/`이 없으면 `python tools/setup_skills.py`를 제안합니다.
3. 그리기 렌더러 환경: `python .agents/skills/srt-whiteboard-animation/scripts/prepare_env.py --check` → 마지막 줄 `ENV_PY=<경로>`를 기억합니다. 없으면 같은 스크립트를 `--check` 없이 실행.

## 1. 대본 (`script.md`)
- 형식: `## scene-01 제목` 아래 한 줄에 한 문장. 장면 하나는 한 가지 생각만, 20~35초 분량(한국어 약 90~150자).
- 한 문장 30자 안팎, 괄호·기호·이모지 없음(그대로 읽힘). 숫자는 읽는 방식으로(3% → 3퍼센트).
- 장면마다 그릴 대상 2~4개를 대본 아래 `<!-- 그림: … -->` 주석으로 적어 둡니다.

## 2. 음성
- `python tools/wbkit.py tts script.md --out assets/audio --voice Kore --style "차분하고 친절한 강의 톤"`
- 처음에는 `--dry-run`으로 요청 내용을 보여 줍니다. 장면별 길이(초)를 표로 보고합니다.

## 3. 자막·장면 길이
- `python tools/wbkit.py srt script.md --audio assets/audio --out narration.srt --scenes scenes.json`
- 장면 길이 = 실제 음성 길이 + 0.5초. 이 값이 그리기 시간의 기준입니다.

## 4. 선화(그림)
- 장면마다 16:9 PNG 한 장, 파일 이름 `assets/whiteboard/<프로젝트>/scene-01-<이름>.png`.
- 그림 규칙: 미색 종이 배경 `#F5EBD7`, 진회색 선, 빨강·주황·파랑은 아주 조금만. 단순한 손그림, 여백 넉넉히, 대상끼리 겹치지 않게.
- **그림 안에 글자·숫자·로고를 넣지 않습니다**(자막으로 넣음). 실존 인물·다른 작품의 캐릭터를 그리지 않습니다.
- 이미지 생성 도구를 쓸 수 없으면 사용자에게 장면별 프롬프트를 주고 PNG를 받아 넣게 합니다.

## 5. 그리기 순서 주석 (`<그림이름>.annotation.json`)
- 그림을 실제로 보고, 대본의 사건 순서대로 영역을 정합니다: 배경 깔기 → 주인공·대상 → 동작·변화 → 반응·결과.
- `canvas`는 그림의 실제 픽셀 크기, `region`은 정수 픽셀. 겹치는 대상은 앞 요소의 `protectedRegions`로 보호.
- `label`·`narrativeRole`은 한국어로.
- 그다음 `python tools/wbkit.py sync --annotations assets/whiteboard/<프로젝트>` — 장면 길이와 요소별 시작·길이를 자막에 맞춰 자동으로 채웁니다.
- `.agents/skills/srt-whiteboard-animation/assets/preview.html`을 Chrome이나 Edge로 열어 사용자가 영역·순서·시간을 확인·수정하게 합니다(화면 글자는 중국어 — 핸드북의 버튼 대조표 참고).

## 6. 렌더
```
<ENV_PY> .agents/skills/srt-whiteboard-animation/scripts/render_stream_whiteboard.py \
  <그림.png> <그림.annotation.json> assets/whiteboard/<프로젝트>/scene-01-whiteboard.mp4 \
  --bare-tip --cap-long-edge 1920
```
- 손 그림(`drawing-hand.png`) 펜대에는 원작자 표식이 있으므로 기본은 `--bare-tip`(펜 끝만). 손을 보이려면 사용자가 만든 손 PNG를 네 번째 인자로 넣습니다.
- 결과 파일 이름은 `scenes.json`의 `video` 값(`scene-01-whiteboard.mp4`)과 같게 합니다.
- 첫 장면 렌더 후 시작·중간·끝 화면을 확인받고 나머지를 렌더합니다.

## 7. 조립
- 기본: `python tools/wbkit.py assemble --video-dir assets/whiteboard/<프로젝트> --srt narration.srt --out final.mp4` (자막은 켜고 끄는 내장 자막)
- 화면에 자막을 새기려면 `--burn`, 배경음악은 `--bgm 파일 --bgm-volume 0.1`.
- 제목 카드·움직이는 자막이 필요하면: `python tools/wbkit.py hyperframes --srt narration.srt` → `hf-video/media/`에 장면 영상·음성 복사 → `npx hyperframes lint hf-video` → `npx hyperframes render hf-video`.

## 8. 마무리 점검
- 첫 화면에 선이 미리 보이지 않는지, 자막과 그리는 대상이 맞는지, 장면 끝에 완성 그림이 0.5초 이상 머무는지 확인합니다.
- 유튜브에 올릴 때 사실적인 합성 인물·음성이 없으면 합성 콘텐츠 공개 대상이 아니지만, AI 음성 사용은 설명란에 밝히기를 권합니다.
