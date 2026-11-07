#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wbkit.py — 화이트보드 애니메이션 영상의 '음성·자막·조립·키 점검' 도구 (핸드북 17편)

srt-whiteboard-animation이 만든 '소리 없는 장면 영상'에 Gemini TTS 내레이션과 자막을 붙여
한 편의 MP4로 만듭니다. 순서는 [대본 → 음성 → 실제 길이로 자막·장면 길이 → 화이트보드 렌더 → 조립]입니다.

명령
  keycheck   API 키가 안전하게 놓였는지 점검(값은 가려서 표시), .gitignore·권한·코드 속 키 노출 검사
  tts        대본(script.md)의 장면마다 Gemini TTS로 WAV 생성
  srt        음성 파일의 실제 길이로 자막(narration.srt)과 장면 길이표(scenes.json) 생성
  sync       annotation.json의 장면 길이·요소별 그리기 시작/길이를 자막에 맞춰 자동 수정
  assemble   장면 영상 + 음성 (+ 배경음악, 자막)을 ffmpeg로 이어 붙여 최종 MP4
  hyperframes  같은 재료로 HyperFrames 구성 파일(index.html) 생성 — 제목·움직이는 자막이 필요할 때

대본 형식 (script.md)
  ## scene-01 장면 제목
  내레이션 문장. 한 줄에 한 문장을 권장합니다.
  ## scene-02 …

API 키를 찾는 순서: 환경 변수 GOOGLE_API_KEY → GEMINI_API_KEY → 운영체제 키체인(keyring 설치 시)
→ 프로젝트의 .env 파일. 키 값은 화면·로그·파일에 절대 쓰지 않습니다.

필요한 것: Python 3.9+ (tts·srt·keycheck는 추가 설치 없음), assemble은 ffmpeg/ffprobe
"""
import argparse
import base64
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3.8-flash-tts"
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_\-]{35}")
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "renders", "out"}


def out(s=""):
    print(s, flush=True)


# ---------------------------------------------------------------- API 키
def read_dotenv(path):
    vals = {}
    p = Path(path)
    if not p.exists():
        return vals
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().removeprefix("export ").strip()
        vals[k] = v.strip().strip("'\"")
    return vals


def find_key(project="."):
    """(키, 출처) — 키 값은 호출한 쪽에서도 출력하지 않습니다."""
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(name):
            return os.environ[name], "환경 변수 " + name
    try:
        import keyring  # 선택 설치: pip install keyring
        v = keyring.get_password("gemini-api", "default")
        if v:
            return v, "운영체제 키체인(keyring: gemini-api)"
    except Exception:
        pass
    env = read_dotenv(Path(project) / ".env")
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        if env.get(name):
            return env[name], "프로젝트 .env의 " + name
    return None, None


def mask(key):
    return key[:4] + "…" + key[-2:] if key and len(key) > 8 else "(짧음)"


def text_files(root):
    for p in Path(root).rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts[:-1]) & SKIP_DIRS) and p.name != ".env":
            if p.suffix.lower() in {".py", ".js", ".ts", ".json", ".md", ".txt", ".html", ".yaml", ".yml", ".toml", ".sh", ".ps1", ".cfg", ".ini", ""}:
                if p.stat().st_size < 2_000_000:
                    yield p


def keycheck(project="."):
    rows = []
    add = lambda level, detail: rows.append((level, detail))
    root = Path(project)
    key, src = find_key(project)
    if key:
        add("통과", "키 찾음 — {} ({})".format(mask(key), src))
        if not KEY_PATTERN.fullmatch(key):
            add("주의", "형식이 일반적인 Gemini API 키(AIza로 시작, 39자)와 다릅니다. 복사가 잘렸는지 확인하세요.")
    else:
        add("실패", "키를 찾지 못했습니다. 환경 변수 GEMINI_API_KEY, 키체인, 또는 .env 중 하나에 넣으세요.")
    env = root / ".env"
    gi = root / ".gitignore"
    ignored = gi.exists() and any(l.strip() in (".env", ".env*", "*.env", "/.env") for l in gi.read_text(encoding="utf-8").splitlines())
    if env.exists():
        add("통과" if ignored else "실패", ".env가 .gitignore에 {}".format("있습니다" if ignored else "없습니다 — 저장소에 올라갈 수 있습니다"))
        if os.name == "posix":
            mode = stat.S_IMODE(env.stat().st_mode)
            add("통과" if mode & 0o077 == 0 else "주의", ".env 권한 {} {}".format(oct(mode), "" if mode & 0o077 == 0 else "→ chmod 600 .env 로 나만 읽게"))
        if shutil.which("git") and (root / ".git").exists():
            r = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", ".env"], capture_output=True)
            if r.returncode == 0:
                add("실패", ".env가 이미 git에 기록되어 있습니다. git rm --cached .env 후 키를 새로 발급하세요.")
    leaks = []
    for p in text_files(root):
        try:
            if KEY_PATTERN.search(p.read_text(encoding="utf-8", errors="ignore")):
                leaks.append(str(p.relative_to(root)))
        except OSError:
            pass
    if leaks:
        add("실패", "키처럼 보이는 문자열이 파일에 있습니다: " + ", ".join(leaks[:5]) + " — 지우고 키를 다시 발급하세요.")
    else:
        add("통과", "코드·문서 파일에 키 형태 문자열 없음")
    return rows


# ---------------------------------------------------------------- 대본
def read_script(path):
    scenes, cur = [], None
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r"^##\s*(scene-\d+)\s*(.*)$", line.strip())
        if m:
            cur = {"id": m.group(1), "title": m.group(2).strip(), "lines": []}
            scenes.append(cur)
        elif cur is not None and line.strip() and not line.strip().startswith("<!--"):
            cur["lines"].append(line.strip())
    if not scenes:
        raise ValueError("'## scene-01 제목' 형식의 장면을 찾지 못했습니다.")
    for s in scenes:
        if not s["lines"]:
            raise ValueError("{}에 내레이션이 없습니다.".format(s["id"]))
    return scenes


# ---------------------------------------------------------------- TTS
def request_body(model, text, voice, style=None):
    if uses_interactions(model):
        content = {"type": "text", "text": text}
        if style:
            content["annotations"] = [{"type": "speech_metadata", "style": style}]
        return f"{API}/interactions", {
            "model": model,
            "input": [{"type": "user_input", "content": [content]}],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice}]},
        }
    prompt = ("Say in a {}: ".format(style) + text) if style else text
    return f"{API}/models/{model}:generateContent", {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }


def uses_interactions(model):
    """3.8 세대 TTS는 Interactions API, 이전 미리보기 모델은 generateContent."""
    return not ("preview-tts" in model or model.endswith("-tts-preview") or "2.5" in model)


def find_audio(obj):
    """응답 JSON 어디에 있든 base64 오디오를 찾는다(API 형태가 바뀌어도 견디도록)."""
    if isinstance(obj, dict):
        mime = str(obj.get("mimeType") or obj.get("mime_type") or "")
        if isinstance(obj.get("data"), str) and (mime.startswith("audio") or len(obj["data"]) > 200):
            return obj["data"], mime
        for k in ("output_audio", "outputAudio", "inlineData", "inline_data"):
            if k in obj:
                r = find_audio(obj[k])
                if r:
                    return r
        for v in obj.values():
            r = find_audio(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_audio(v)
            if r:
                return r
    return None


def save_audio(raw, path, rate=24000):
    """WAV(RIFF)면 그대로, 머리 없는 PCM(L16)이면 24kHz·모노·16비트 WAV로 감싸 저장."""
    if raw[:4] == b"RIFF":
        Path(path).write_bytes(raw)
        return
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(raw)


def wav_seconds(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def call_api(url, body, key, tries=4):
    data = json.dumps(body).encode("utf-8")
    for i in range(tries):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "ignore")[:300].replace(key, "***")
            if e.code in (429, 500, 503) and i < tries - 1:
                wait = 2 ** i * 5
                out("  {} — {}초 뒤 다시 시도".format(e.code, wait))
                time.sleep(wait)
                continue
            raise RuntimeError("HTTP {}: {}".format(e.code, msg))


def tts(script, outdir, model=DEFAULT_MODEL, voice="Kore", style=None, dry=False, project="."):
    scenes = read_script(script)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    key = None
    if not dry:
        key, src = find_key(project)
        if not key:
            raise RuntimeError("API 키가 없습니다. python tools/wbkit.py keycheck 로 확인하세요.")
        out("키: {} ({}) · 모델 {} · 목소리 {}".format(mask(key), src, model, voice))
    for s in scenes:
        text = "\n".join(s["lines"])
        url, body = request_body(model, text, voice, style)
        target = outdir / (s["id"] + ".wav")
        if dry:
            out("[{}] {}\n{}".format(s["id"], url, json.dumps(body, ensure_ascii=False, indent=1)[:600]))
            continue
        if target.exists() and target.stat().st_mtime > Path(script).stat().st_mtime:
            out("[{}] 이미 있음 — 건너뜀 (대본을 고치면 다시 만듭니다)".format(s["id"]))
            continue
        found = find_audio(call_api(url, body, key))
        if not found:
            raise RuntimeError("{}: 응답에서 오디오를 찾지 못했습니다.".format(s["id"]))
        save_audio(base64.b64decode(found[0]), target)
        out("[{}] {} — {:.1f}초".format(s["id"], target.name, wav_seconds(target)))
    return scenes


# ---------------------------------------------------------------- 자막 · 장면 길이
def fmt_ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "{:02d}:{:02d}:{:02d},{:03d}".format(h, m, s, ms)


def build_srt(script, audio_dir, srt_out, scenes_out, hold=0.5):
    """장면마다 실제 음성 길이 + 끝 정지(hold)를 장면 길이로, 장면 안 문장은 글자 수 비례로 시간 배분."""
    scenes = read_script(script)
    t, n, cues, table = 0.0, 1, [], []
    for s in scenes:
        wav = Path(audio_dir) / (s["id"] + ".wav")
        if not wav.exists():
            raise ValueError("{}가 없습니다. 먼저 tts를 실행하세요.".format(wav))
        dur = wav_seconds(wav)
        weights = [max(1, len(re.sub(r"\s", "", l))) for l in s["lines"]]
        total = float(sum(weights))
        start = t
        for line, w in zip(s["lines"], weights):
            end = start + dur * w / total
            cues.append("{}\n{} --> {}\n{}\n".format(n, fmt_ts(start), fmt_ts(end), line))
            n, start = n + 1, end
        scene_sec = dur + hold
        table.append({"id": s["id"], "title": s["title"], "audio": wav.name, "audioSec": round(dur, 3),
                      "start": round(t, 3), "sceneDurationMs": int(round(scene_sec * 1000)),
                      "subtitles": s["lines"], "video": s["id"] + "-whiteboard.mp4"})
        t += scene_sec
    Path(srt_out).write_text("\n".join(cues), encoding="utf-8")
    Path(scenes_out).write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
    return table


# ---------------------------------------------------------------- 그리기 시간 맞추기
def sync(scenes_json, srt, ann_dir, lead_ms=200, gap_ms=300):
    """annotation.json의 sceneDurationMs와 각 요소의 startMs·durationMs를 실제 음성 자막에 맞춘다.
    요소 수와 자막 줄 수가 같으면 1:1, 다르면 말하는 구간을 요소 수로 고르게 나눈다."""
    table = json.loads(Path(scenes_json).read_text(encoding="utf-8"))
    cues = parse_srt(srt)
    done = []
    for s in table:
        files = sorted(Path(ann_dir).glob(s["id"] + "*.annotation.json"))
        if not files:
            done.append((s["id"], "annotation.json 없음 — 건너뜀"))
            continue
        f = files[0]
        ann = json.loads(f.read_text(encoding="utf-8"))
        t0, t1 = s["start"], s["start"] + s["audioSec"]
        mine = [c for c in cues if c[0] >= t0 - 0.01 and c[1] <= t1 + 0.01]
        els = sorted(ann["elements"], key=lambda e: e.get("sequence", 0))
        if len(mine) == len(els):
            spans = [(c[0] - t0, c[1] - t0, c[2]) for c in mine]
            mode = "자막 줄과 1:1"
        else:
            step = (t1 - t0) / max(1, len(els))
            spans = [(i * step, (i + 1) * step, None) for i in range(len(els))]
            mode = "말하는 구간을 {}등분".format(len(els))
        for e, (a, b, text) in zip(els, spans):
            e["reveal"]["startMs"] = int(round(a * 1000)) + lead_ms
            e["reveal"]["durationMs"] = max(800, int(round((b - a) * 1000)) - gap_ms)
            if text:
                e["subtitle"] = text
        ann["sceneDurationMs"] = s["sceneDurationMs"]
        f.write_text(json.dumps(ann, ensure_ascii=False, indent=2), encoding="utf-8")
        done.append((s["id"], "{} · {} · sceneDurationMs {}".format(f.name, mode, s["sceneDurationMs"])))
    return done


# ---------------------------------------------------------------- 조립 (ffmpeg)
def probe_sec(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def assemble(scenes_json, video_dir, audio_dir, output, srt=None, burn=False, bgm=None, bgm_volume=0.12,
             width=1920, height=1080, fps=30):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg가 없습니다. 설치 후 다시 실행하세요.")
    table = json.loads(Path(scenes_json).read_text(encoding="utf-8"))
    work = Path(output).parent / "_wbkit_parts"
    work.mkdir(parents=True, exist_ok=True)
    parts = []
    for s in table:
        v = Path(video_dir) / s["video"]
        a = Path(audio_dir) / s["audio"]
        for f in (v, a):
            if not f.exists():
                raise ValueError("{} 없음".format(f))
        need = s["sceneDurationMs"] / 1000.0
        vsec = probe_sec(v)
        part = work / (s["id"] + ".mp4")
        # 영상이 음성보다 짧으면 마지막 장면(완성된 그림)을 늘려 맞추고, 길면 잘라 맞춘다
        vf = ("scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0xF5EBD7,"
              "fps={fps},tpad=stop_mode=clone:stop_duration={pad:.3f},trim=duration={need:.3f},setpts=PTS-STARTPTS").format(
            w=width, h=height, fps=fps, pad=max(0.0, need - vsec) + 0.1, need=need)
        af = "apad=whole_dur={:.3f},atrim=duration={:.3f}".format(need, need)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-i", str(a), "-vf", vf, "-af", af,
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(part)], check=True)
        parts.append(part)
        out("  {} — 영상 {:.1f}초 / 음성 {:.1f}초 → 장면 {:.1f}초".format(s["id"], vsec, s["audioSec"], need))
    lst = work / "list.txt"
    lst.write_text("".join("file '{}'\n".format(p.resolve().as_posix()) for p in parts), encoding="utf-8")
    joined = work / "joined.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)], check=True)
    # 마지막 단계: 배경음악 섞기 · 자막(내장 또는 새김)
    inputs, idx = ["-i", str(joined)], 1
    graph, vmap, amap = [], "0:v", "0:a"
    if bgm:
        inputs += ["-stream_loop", "-1", "-i", str(bgm)]
        graph.append("[{}:a]volume={}[b];[0:a][b]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[a]".format(idx, bgm_volume))
        amap, idx = "[a]", idx + 1
    sub_idx = None
    if srt and burn:
        style = "FontName=Noto Sans CJK KR,FontSize=22,Outline=1,MarginV=40"
        graph.append("[0:v]subtitles='{}':force_style='{}'[v]".format(Path(srt).resolve().as_posix().replace(":", "\\:"), style))
        vmap = "[v]"
    elif srt:
        inputs += ["-i", str(srt)]
        sub_idx = idx
    cmd = ["ffmpeg", "-v", "error", "-y"] + inputs
    if graph:
        cmd += ["-filter_complex", ";".join(graph)]
    cmd += ["-map", vmap, "-map", amap]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18"] if vmap == "[v]" else ["-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "192k"] if bgm else ["-c:a", "copy"]
    if sub_idx is not None:
        cmd += ["-map", "{}:s".format(sub_idx), "-c:s", "mov_text", "-metadata:s:s:0", "language=kor"]
    cmd += ["-movflags", "+faststart", str(output)]
    subprocess.run(cmd, check=True)
    shutil.rmtree(work, ignore_errors=True)
    return probe_sec(output)


# ---------------------------------------------------------------- HyperFrames 구성 파일
HF_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@500;700&display=swap">
<style>
  html, body {{ margin: 0; background: #F5EBD7; }}
  #stage {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; background: #F5EBD7;
           font-family: "Noto Sans KR", sans-serif; }}
  .scene {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; }}
  .cap {{ position: absolute; left: 8%; right: 8%; bottom: 6%; text-align: center; font-size: 46px; line-height: 1.35;
         color: #2b2b2b; background: rgba(245,235,215,.88); border-radius: 14px; padding: 14px 24px; }}
</style>
</head>
<body>
<div id="stage" data-composition-id="whiteboard" data-no-timeline data-start="0" data-duration="{total:.3f}" data-width="{w}" data-height="{h}" data-fps="{fps}">
{clips}
</div>
</body>
</html>
"""


def parse_srt(path):
    cues = []
    for block in re.split(r"\n\s*\n", Path(path).read_text(encoding="utf-8-sig").strip()):
        lines = block.strip().splitlines()
        if len(lines) >= 3 and "-->" in lines[1]:
            a, b = [x.strip() for x in lines[1].split("-->")]
            to = lambda ts: sum(float(x) * m for x, m in zip(ts.replace(",", ".").split(":"), (3600, 60, 1)))
            cues.append((to(a), to(b), " ".join(lines[2:])))
    return cues


def hyperframes(scenes_json, srt, outdir, video_prefix="media/", audio_prefix="media/", bgm=None, w=1920, h=1080, fps=30):
    table = json.loads(Path(scenes_json).read_text(encoding="utf-8"))
    clips = []
    total = table[-1]["start"] + table[-1]["sceneDurationMs"] / 1000.0
    for s in table:
        d = s["sceneDurationMs"] / 1000.0
        # id가 없으면 렌더러가 영상을 멈춘 화면으로, 음성을 무음으로 처리한다
        clips.append('  <video id="{0}-video" class="scene clip" data-start="{1:.3f}" data-duration="{2:.3f}" data-track-index="0" src="{3}{4}" muted playsinline></video>'.format(
            s["id"], s["start"], d, video_prefix, s["video"]))
        clips.append('  <audio id="{0}-voice" data-start="{1:.3f}" data-duration="{2:.3f}" data-track-index="1" data-volume="1" src="{3}{4}"></audio>'.format(
            s["id"], s["start"], s["audioSec"], audio_prefix, s["audio"]))
    if bgm:
        clips.append('  <audio id="bgm" data-start="0" data-duration="{:.3f}" data-track-index="2" data-volume="0.12" src="{}{}"></audio>'.format(
            total, audio_prefix, Path(bgm).name))
    for i, (a, b, text) in enumerate(parse_srt(srt) if srt else [], 1):
        cid = "cap{}".format(i)
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        clips.append('  <div id="{}" class="cap clip" data-start="{:.3f}" data-duration="{:.3f}" data-track-index="3">{}</div>'.format(
            cid, a, b - a, safe))
    outdir = Path(outdir)
    (outdir / "media").mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(HF_TEMPLATE.format(w=w, h=h, fps=fps, total=total, clips="\n".join(clips)),
                                       encoding="utf-8")
    return outdir / "index.html"


# ---------------------------------------------------------------- 실행
def main(argv=None):
    ap = argparse.ArgumentParser(description="화이트보드 영상 음성·자막·조립 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("keycheck")
    k.add_argument("--project", default=".")
    t = sub.add_parser("tts")
    t.add_argument("script")
    t.add_argument("--out", default="assets/audio")
    t.add_argument("--model", default=DEFAULT_MODEL)
    t.add_argument("--voice", default="Kore")
    t.add_argument("--style", help="말투 지시(예: 차분하고 따뜻한 강의 톤)")
    t.add_argument("--dry-run", action="store_true", help="API를 부르지 않고 요청 내용만 보기")
    t.add_argument("--project", default=".")
    s = sub.add_parser("srt")
    s.add_argument("script")
    s.add_argument("--audio", default="assets/audio")
    s.add_argument("--out", default="narration.srt")
    s.add_argument("--scenes", default="scenes.json")
    s.add_argument("--hold", type=float, default=0.5, help="장면 끝 정지 시간(초), 기본 0.5")
    y = sub.add_parser("sync")
    y.add_argument("--scenes", default="scenes.json")
    y.add_argument("--srt", default="narration.srt")
    y.add_argument("--annotations", required=True, help="장면 PNG·annotation.json이 있는 폴더")
    a = sub.add_parser("assemble")
    a.add_argument("--scenes", default="scenes.json")
    a.add_argument("--video-dir", required=True)
    a.add_argument("--audio-dir", default="assets/audio")
    a.add_argument("--srt")
    a.add_argument("--burn", action="store_true", help="자막을 화면에 새김(한글 글꼴 필요)")
    a.add_argument("--bgm")
    a.add_argument("--bgm-volume", type=float, default=0.12)
    a.add_argument("--out", default="final.mp4")
    h = sub.add_parser("hyperframes")
    h.add_argument("--scenes", default="scenes.json")
    h.add_argument("--srt")
    h.add_argument("--bgm")
    h.add_argument("--out-dir", default="hf-video")
    g = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        if g.cmd == "keycheck":
            rows = keycheck(g.project)
            out("API 키 점검 — {}\n".format(Path(g.project).resolve()))
            for level, d in rows:
                out("[{}] {}".format(level, d))
            return 1 if any(r[0] == "실패" for r in rows) else 0
        if g.cmd == "tts":
            tts(g.script, g.out, g.model, g.voice, g.style, g.dry_run, g.project)
        elif g.cmd == "srt":
            table = build_srt(g.script, g.audio, g.out, g.scenes, g.hold)
            out("저장: {} · {}".format(g.out, g.scenes))
            for s in table:
                out("  {} 시작 {:.1f}초 · 음성 {:.1f}초 · sceneDurationMs {}".format(s["id"], s["start"], s["audioSec"], s["sceneDurationMs"]))
            out("다음: 장면마다 annotation.json의 sceneDurationMs를 위 값으로 맞춘 뒤 화이트보드를 렌더하세요.")
        elif g.cmd == "sync":
            for sid, msg in sync(g.scenes, g.srt, g.annotations):
                out("  {} — {}".format(sid, msg))
            out("다음: 미리보기 화면(preview.html)에서 확인한 뒤 render_stream_whiteboard.py로 렌더하세요.")
        elif g.cmd == "assemble":
            sec = assemble(g.scenes, g.video_dir, g.audio_dir, g.out, g.srt, g.burn, g.bgm, g.bgm_volume)
            out("저장: {} ({:.1f}초)".format(g.out, sec))
        else:
            p = hyperframes(g.scenes, g.srt, g.out_dir, bgm=g.bgm)
            out("저장: {} — 장면 영상·음성을 {}/media/ 에 복사한 뒤 npx hyperframes render {}".format(p, g.out_dir, g.out_dir))
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as e:
        out("오류: " + str(e))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
