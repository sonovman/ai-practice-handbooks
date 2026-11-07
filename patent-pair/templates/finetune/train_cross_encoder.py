#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_cross_encoder.py — 텍스트 쌍 판별 모델 미세 조정 (출원발명의 학습 방식을 그대로 옮긴 참고 코드)

  · 입력: pairkit.py pairs가 만든 pairs.jsonl ({"claim","desc","label","src_claim",...})
  · 구조: [CLS] 청구항 [SEP] 설명 [SEP] → 사전 학습 인코더 → 이진 분류 층
  · 학습: 레이블 1 묶음(dataloader1)과 레이블 0 묶음(dataloader2)을 zip으로 번갈아 넣고 두 손실의 평균을 줄임
  · 검증: 같은 특허가 학습·검증에 동시에 들어가지 않도록 '청구항 출처 특허' 단위로 나눔

설치(내 PC·Colab, GPU 권장):  pip install torch transformers
실행:  python train_cross_encoder.py --pairs pairs.jsonl --model klue/bert-base --out model-dir
예측:  python train_cross_encoder.py --predict new_pairs.jsonl --out model-dir  → predictions.csv (chart_check.py score 형식)

모델 예: 한국어 klue/bert-base · 다국어 bert-base-multilingual-cased · 영어 특허 AI-Growth-Lab/PatentSBERTa
이 파일은 참고 구현입니다. 핸드북 작성 환경에서는 모델 내려받기가 막혀 문법 검사까지만 했습니다.
"""
import argparse
import csv
import json
import random

import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup


def read(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def split_by_patent(rows, ratio=0.2, seed=13):
    """같은 특허의 텍스트가 학습과 검증에 함께 들어가면 점수가 부풀려지므로 특허 단위로 나눈다."""
    names = sorted({r["src_claim"] for r in rows})
    random.Random(seed).shuffle(names)
    held = set(names[:max(1, int(len(names) * ratio))])
    return [r for r in rows if r["src_claim"] not in held], [r for r in rows if r["src_claim"] in held]


def make_collate(tok, max_len):
    def collate(batch):
        enc = tok([b["claim"] for b in batch], [b["desc"] for b in batch], truncation="only_second",
                  max_length=max_len, padding=True, return_tensors="pt")
        enc["labels"] = torch.tensor([int(b["label"]) for b in batch])
        return enc
    return collate


@torch.no_grad()
def predict(model, tok, rows, max_len, device, bs=16):
    model.eval()
    probs = []
    col = make_collate(tok, max_len)
    for i in range(0, len(rows), bs):
        enc = {k: v.to(device) for k, v in col(rows[i:i + bs]).items() if k != "labels"}
        probs += torch.softmax(model(**enc).logits, dim=-1)[:, 1].tolist()
    return probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs")
    ap.add_argument("--predict")
    ap.add_argument("--model", default="klue/bert-base")
    ap.add_argument("--out", default="pair-model")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-len", type=int, default=512)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if a.predict:
        tok = AutoTokenizer.from_pretrained(a.out)
        model = AutoModelForSequenceClassification.from_pretrained(a.out).to(device)
        rows = read(a.predict)
        probs = predict(model, tok, rows, a.max_len, device)
        with open("predictions.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["pred", "score"])
            for p in probs:
                w.writerow([int(p >= 0.5), round(p, 4)])
        print("저장: predictions.csv ({}줄)".format(len(probs)))
        return

    rows = read(a.pairs)
    train, val = split_by_patent(rows)
    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForSequenceClassification.from_pretrained(a.model, num_labels=2).to(device)
    col = make_collate(tok, a.max_len)
    dl1 = DataLoader([r for r in train if r["label"] == 1], batch_size=a.bs, shuffle=True, collate_fn=col)
    dl2 = DataLoader([r for r in train if r["label"] == 0], batch_size=a.bs, shuffle=True, collate_fn=col)
    steps = a.epochs * min(len(dl1), len(dl2))
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr)
    sched = get_linear_schedule_with_warmup(opt, int(steps * 0.1), steps)
    for ep in range(1, a.epochs + 1):
        model.train()
        total, n = 0.0, 0
        # zip은 짧은 쪽에서 멈춘다. 레이블 0이 더 많으면 에포크마다 섞이는 다른 0 묶음이 쓰인다.
        for b1, b2 in zip(dl1, dl2):
            b1 = {k: v.to(device) for k, v in b1.items()}
            b2 = {k: v.to(device) for k, v in b2.items()}
            loss = (model(**b1).loss + model(**b2).loss) / 2      # 두 그룹 손실의 평균
            loss.backward()
            opt.step()
            sched.step()
            opt.zero_grad()
            total, n = total + loss.item(), n + 1
        msg = "epoch {}/{} loss {:.4f}".format(ep, a.epochs, total / max(1, n))
        if val:
            p = predict(model, tok, val, a.max_len, device)
            acc = sum(int(x >= 0.5) == r["label"] for x, r in zip(p, val)) / len(val)
            msg += " · 검증 정확도 {:.1%} (특허 {}건 분리)".format(acc, len({r['src_claim'] for r in val}))
        print(msg)
    model.save_pretrained(a.out)
    tok.save_pretrained(a.out)
    print("저장: " + a.out)


if __name__ == "__main__":
    main()
