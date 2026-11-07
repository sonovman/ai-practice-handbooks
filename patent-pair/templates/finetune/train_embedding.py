#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_embedding.py — 청구항·설명 검색용 임베딩 모델 미세 조정 (참고 코드)

  · 입력: pairkit.py pairs --triplets가 만든 triplets.csv (anchor=청구항, positive=같은 문헌 설명,
          negative=가장 비슷한 다른 문헌 설명)
  · 손실: MultipleNegativesRankingLoss — 한 배치 안의 다른 문헌 설명이 모두 음성(레이블 0)이 되므로,
          '같은 문헌 = 1, 다른 문헌 = 0'이라는 자동 레이블 규칙을 대량으로 쓰는 방식입니다.
  · 쓰임: 학습한 모델로 청구항 구성요소와 대상 문서 조각의 내적을 구해 근거 후보를 고릅니다
          (pairkit.py의 글자 유사도를 대신).

설치:  pip install sentence-transformers
실행:  python train_embedding.py --triplets triplets.csv --model intfloat/multilingual-e5-base --out emb-model
이 파일은 참고 구현입니다. 핸드북 작성 환경에서는 모델 내려받기가 막혀 문법 검사까지만 했습니다.
"""
import argparse
import csv

from sentence_transformers import InputExample, SentenceTransformer, losses
from torch.utils.data import DataLoader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--triplets", required=True)
    ap.add_argument("--model", default="intfloat/multilingual-e5-base")
    ap.add_argument("--out", default="emb-model")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--bs", type=int, default=16)
    a = ap.parse_args()
    with open(a.triplets, encoding="utf-8-sig", newline="") as f:
        ex = [InputExample(texts=[r["anchor"], r["positive"], r["negative"]]) for r in csv.DictReader(f)]
    model = SentenceTransformer(a.model)
    dl = DataLoader(ex, shuffle=True, batch_size=a.bs)
    loss = losses.MultipleNegativesRankingLoss(model)
    model.fit(train_objectives=[(dl, loss)], epochs=a.epochs, warmup_steps=max(1, int(len(dl) * 0.1)))
    model.save(a.out)
    print("저장: {} ({}개 삼중쌍으로 학습)".format(a.out, len(ex)))


if __name__ == "__main__":
    main()
