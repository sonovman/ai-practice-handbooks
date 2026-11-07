# Slow Think 프롬프트 (2026 개선판)

> 쓰기 전에: 앱의 '생각' 설정을 먼저 올립니다 — Claude 노력(Effort) 높음, ChatGPT Thinking(Medium·High),
> Gemini Thinking level 확장(Extended)·Pro, Copilot Think deeper. 문구보다 이 설정이 더 큰 차이를 만듭니다.
> 이 프롬프트는 "어떻게 생각할지"가 아니라 "무엇을 점검할지"를 지시합니다.

```
아래 안건에 답하기 전에 다음 순서로 점검한 뒤 결론을 내려 줘. 생각 과정을 길게 보여 줄 필요는 없고, 점검 결과만 표로 보여 줘.

1. 질문 다시 쓰기: 내가 실제로 결정해야 하는 것이 무엇인지 한 문장으로.
2. 전제 점검: 질문에 들어 있는 주장·숫자·인과를 모두 뽑아 표로 정리해.
   | 전제 | 사실 / 가정 / 의심 | 근거 또는 의심하는 이유 |
   서로 모순되거나 상식과 반대인 전제가 있으면 먼저 바로잡고, 바로잡은 전제로 분석해.
3. 제약 조건: 자금, 인력, 시간, 규제·법, 데이터 중 이 결정에 실제로 걸리는 것을 적어.
4. 선택지 비교: 선택지마다 "이것이 1년 뒤 실패했다면 가장 그럴듯한 이유"를 한 줄씩.
5. 결론: 추천안과 그 조건. 이상적인 정답이 아니라 위 제약 안에서 실행 가능한 순서로.
6. 결론을 바꿀 정보: 무엇이 확인되면 추천이 달라지는가.

모르는 사실은 지어내지 말고 '확인 필요'로 표시해.

[안건]
<여기에 안건>
```

---

## 영문 머리말을 붙이는 융합 버전 (선택)

영문 트리거(Take a deep breath · Work through carefully · Complex decision · Examining assumptions ·
Multiple layers)를 쓰고 싶다면 머리말로만 두고, 실제 일은 아래 점검 항목이 하게 합니다.
빠른 모드(ChatGPT Instant, Copilot Quick response, Gemini Fast 등)에서는 조금 도움이 될 수 있고,
추론 모드에서는 있어도 해롭지 않지만 효과는 주로 점검 항목에서 나옵니다. 내 업무에서는 08-ab-test로 확인하세요.

```
[Slow Think Execution Protocol]
Take a deep breath and work through this carefully.
This is a complex strategic decision that requires examining our assumptions and analyzing multiple layers of constraints.

[실행 지시 — 점검 결과만 표로 보여 줘]
1. (Complex decision) 내가 결정해야 하는 것을 한 문장으로 다시 써.
2. (Examining assumptions) 안건 속 주장·숫자·인과를 | 전제 | 사실/가정/의심 | 근거 | 표로 점검하고, 모순 전제는 바로잡은 뒤 분석해.
3. (Multiple layers) 자금·인력·시간·규제·데이터 중 이 결정에 실제로 걸리는 제약을 적어.
4. (Work through carefully) 선택지마다 "1년 뒤 실패했다면 가장 그럴듯한 이유"를 한 줄씩.
5. 현실 제약 안에서 위험을 단계적으로 줄이는 로드맵을 제시하고, 단계마다 다음 단계로 넘어갈 조건을 붙여.
6. 결론을 바꿀 정보와, 아직 확인되지 않은 사실을 목록으로.
모르는 사실은 지어내지 말고 '확인 필요'로 표시해.

[안건]
<여기에 안건>
```
