> ## Documentation Index
> Fetch the complete documentation index at: https://docs.typesafe.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Primitives (Questions)

> The three TypeSafe question types (Choice, Score, Noul), the typed answers they return, how to choose between them, and how to ask several at once.



TypeSafe's primitives are the small, typed building blocks you compose in code. They come in pairs: a question defines one judgment for a [System One model](/concepts/system-one) to make about a [state](/concepts/state), and its answer is the typed value that comes back. You compose the answers in your code to make decisions. There are three question types, each returning a different shape of answer.

问的问题，必须有对应的答案选项。

| Type | What it answers | Returns |
| - | - | - |
| [Choice](/primitives/choice) | Which of these options? | `choice`, `probabilities`, `confidence` |
| [Score](/primitives/score) | Which level? | `score`, `legend`, `probabilities`, `confidence` |
| [Noul](/primitives/noul) | Is this true? | `noul` (0 to 1) |

You can ask one question or send several together. Every question in a request sees the same state, is evaluated independently, and returns a typed answer under the ID you chose.

可以一次 API 调用中，传入多个 question，这些会共享 state，但是，问题之间不干扰。

## Ask for one snap judgment per question


System One models are built for fast, focused judgments. Ask for a judgment a knowledgeable person makes in a second given the right context. "Does this message convey urgency?" is a good question. "Analyze this message and determine the best course of action" is not. That needs slow reasoning, and it is a signal to break the task into small questions and compose the answers in code.

针对复杂问题，一定要拆解为细粒度的明确的多个问题，并且给出每个问题的选项。

If the judgment you want depends on several independent factors, ask about each factor separately and combine the answers with your own logic. Instead of "rate this startup pitch", ask about market size, technical feasibility, and differentiation, then weight them in code based on their relative importance. When priorities shift, change the value of weights rather than rewriting a prompt. [Ask multiple questions together](#ask-multiple-questions-together) shows how to do this.

如果问题是需要多个因素决定的，建议，针对每个因素定一个一个独立问题，每个问题都发给 Jev 模型；最后将所有问题的结果，综合考虑。

## Define a question

Every question has an ID, a `type`, and `instructions`. Choice and Score questions also take `criteria`, which define the options for a Choice question or the levels for a Score. Noul questions accept `criteria` as an optional clarification of what yes and no mean.

问题，需要包含 4 个字段：`ID`、 `type`、`instructions`、`criteria`，即，问题标识ID、类型、描述、答案可选项。

* ID. The key you pick, such as `refund_requested`. It identifies the answer in the response.
* `type`. One of `choice`, `score`, or `noul`.
* `instructions`. The question you are asking about the state. This is where your evaluation logic goes. Write it as a clear, specific question, or as a statement for the model to judge. A string is enough for most questions. It can also be an object or an array, which puts the question in one field and the data it refers to in others; see [Use structure in the questions](/concepts/how-to-build-with-system-one#use-structure-in-the-questions).
* `criteria`. The possible answers: a map of options for a Choice question, an ordered list of levels for a Score, and an optional description of yes and no for a Noul. Each question type's page covers its shape.

其中，instructions 问题描述，可以是 纯文本、或者 Json 对象.

This question asks whether a customer requested a refund:

```python theme={null}
from typesafe_sdk import Noul

questions = {
    "refund_requested": Noul(
        instructions="Does the customer request a refund?",
    ),
}
```

<Tip>
  Question IDs are for your code. They are not sent to the model. Write the complete question in `instructions`, even when the ID seems self-explanatory.
</Tip>

questionID，LLM 并没有感知其含义，只是用于对接 业务代码的，ID 的命名比较灵活。

## Choose a question type

Pick the type that matches the shape of the answer you need.

* **Choice** fits when the answer is one of a known set of options with no order between them: routing a ticket to a department, classifying a document type, detecting a programming language. Give the full list of options, and add an `other` or `none of the above` option when the list might not cover every input.

* **Score** fits when the answer falls on a spectrum and you can describe what each point on that spectrum means: bug severity, customer frustration, skill level. The levels are yours to define, and the model returns a position along them.

* **Noul** fits a clean yes/no question where the probability itself is the useful signal: does this message contain personally identifiable information, is the customer requesting a refund, does the resume mention distributed systems.

<Note>
  Use Noul for a yes/no judgment and Score to measure a position on a spectrum. "Is this candidate strong in Python?" needs a clear definition of "strong". A Noul value of 0.5 means the model gives yes and no equal probability. It does not mean the candidate has a medium skill level. An unclear definition makes that probability hard to interpret.

  If you want to measure skill level, use a Score with defined levels, such as no experience, some familiarity, daily use, and deep expertise. If you need a yes/no decision, define the condition clearly, such as "Does the resume state that the candidate has used Python at work?"
</Note>

If two types both seem to fit, prefer the one whose answer your code can act on directly. A Choice between `refund`, `rebook`, and `information` maps straight onto three code paths. A Score of customer frustration maps onto a threshold. A Noul maps onto an `if`.

业务场景中，如果同一个问题，有多个可选的问题类型，倾向建议选择`代码可以直接应用`的类型。例如，代码逻辑是要分类判断，则，直接 Choice；代码逻辑是 if...else，直接用 Noul；如果是用户风险控制/欺诈风险判断，则，直接 Score.

## What comes back

Answers are primitives too. Each question type returns a typed value that your code can compare, threshold, sort, pass into further logic, or put into the state of a follow-up request (see [When one question depends on another](#when-one-question-depends-on-another)).

| Type | Answer fields | How to read it |
| - | - | - |
| Choice | `choice`, `probabilities`, `confidence` | `choice` is the selected option. `probabilities` is the distribution across every option. `confidence` summarizes how peaked that distribution is. |
| Score | `score`, `legend`, `probabilities`, `confidence` | `score` is a position along your levels, and can fall between two of them. `legend` repeats the levels by number. `probabilities` is the distribution across levels. |
| Noul | `noul` | The probability that the answer is yes. Near 1 is a strong yes, near 0 a strong no, near 0.5 uncertain. Noul has no separate `confidence`. |

Two properties of these answers make them composable:

* **Every answer is constrained to the options you supplied.** The model returns a probability distribution over your options or levels, never a value outside them. Your code never has to recover a value from generated prose.
* **Every answer is independent.** One question's answer is not hidden context for another. You can add or remove questions without changing the others' results.

[Confidence](/confidence) explains how `confidence` is derived from `probabilities` and how to use it to decide when to act automatically and when to escalate to a person.

confidence 置信度，跟 选项的概率分布强相关，且用于判断是否 自动执行 还是 需要人工校正。


## Reference specific fields

The content being evaluated, the [state](/concepts/state), is often a JSON object with several parts: a conversation, a record, a policy. When a question is about one of those parts, name it in the `instructions` with a dot-and-index path to its key, including the backticks. The model then knows which part of the state to judge.

如果 State 是 Json 结构的，可以直接在 question 的 instructions 中，直接采用 `dot-and-index` 格式来引用 State 中的参数，例如下面示例中的 `ticket.messages[0].text`

Take the support conversation from the State page:

```json theme={null}
{
  "ticket": {
    "subject": "Duplicate charge",
    "messages": [
      {"from": "customer", "text": "I was charged twice for order A-104. Please refund the duplicate."},
      {"from": "support", "text": "We are checking the charges."}
    ]
  },
  "order": {
    "id": "A-104",
    "charges": [
      {"amount_usd": 49, "status": "captured"},
      {"amount_usd": 49, "status": "captured"}
    ]
  },
  "refund_policy": "Duplicate charges are eligible for a refund."
}
```

These two questions point at the customer's message, the policy, and the charges by path:

```python theme={null}
questions = {
    "refund_requested": {
        "type": "noul",
        "instructions": "Does `ticket.messages[0].text` request a refund?",
    },
    "policy_supports_refund": {
        "type": "noul",
        "instructions": (
            "Does `refund_policy` support the refund requested "
            "in `ticket.messages[0].text`, given `order.charges`?"
        ),
    },
}
```

Explicit paths make it clear which parts of a structured state should inform each judgment. See [State](/concepts/state) for how to structure the input.

## Ask multiple questions together

Send every question that uses the same state in one request. You can mix question types freely. System One models evaluate every question in a request in parallel. Adding questions barely changes the response time and costs only the tokens for the extra questions, which are cheap. Asking a question you might not need is close to free.

单次请求中，问多个 question 对 rt 的影响很小，每个 question 是并发处理的。

This request classifies a customer message, checks for urgency, and scores frustration all at once:

<TypesafeExample
  example={{
state:
  "Our API integration started returning 500 errors on every request about 20 minutes ago, and we can't process any customer orders until this is fixed.",
questions: {
  department: {
    type: 'choice',
    instructions: 'Which team should handle this',
    criteria: {
      billing: 'Payment or subscription issues',
      technical: 'Bugs or integration problems',
      sales: 'Pricing or account questions',
    },
  },
  is_urgent: {
    type: 'noul',
    instructions: 'The message conveys urgency or time-sensitivity',
  },
  frustration: {
    type: 'score',
    instructions: 'How frustrated the customer appears',
    criteria: [
      'Calm, just stating facts',
      'Frustrated but civil',
      'Very angry, strong language',
    ],
  },
},
}}
/>

Our [client SDKs](/sdk) provide typed questions and answers. In Python, pass a `questions` dictionary of `Choice`, `Noul`, and `Score` objects to `client.system_one(...)`. This request sends a ticket and a refund policy once and gets a typed answer for each question:

```python theme={null}
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

state = {
    "ticket_message": "My flight was cancelled. Can I get a refund?",
    "refund_policy": "Cancelled flights are eligible for a full refund.",
}

with TypeSafeClient() as client:
    response = client.system_one(
        state=state,
        questions={
            "refund_requested": Noul(
                instructions="Does `ticket_message` request a refund?",
            ),
            "request_type": Choice(
                instructions="What is the main request in `ticket_message`?",
                criteria={
                    "refund": "The customer wants money returned.",
                    "rebooking": "The customer wants a replacement flight.",
                    "information": "The customer is asking for information only.",
                },
            ),
            "frustration": Score(
                instructions="How frustrated does the customer appear in `ticket_message`?",
                criteria=[
                    "Calm and neutral.",
                    "Concerned but civil.",
                    "Very angry or using strong language.",
                ],
            ),
        },
    )

print(response.answers["refund_requested"].noul)
print(response.answers["request_type"].choice)
print(response.answers["frustration"].score)
```

See [client SDKs](/sdk) for installation and usage in your language.

### Ask speculative questions

Ask every question your code might need, including ones whose answer only matters for some inputs, and let the code decide which answers to use. If a ticket turns out not to be a bug report, ignore the severity answer. We call this the [Speculative fan-out](/patterns/fan-out) pattern. The [Parallel questions cookbook](/cookbooks/parallel_questions) shows how batching 13 questions into one call is 11.5x cheaper and 9.6x faster than 13 separate calls, with no change in the answers.

一次请求中，就集中问下所有潜在问题，即使有些问题只在部分场景下才需求，无需等待前置问题的答案，可以直接一次性问所有问题，然后，针对问题的结果，再做业务逻辑。这种做法，部分问题看起来浪费资源了，但实际上，成本非常低，相对多次的请求，这种一次问所有问题的做法，耗费的资源降低了 1 个数量级。

<Tip>
  Coding agents fall into the one question per call habit more than people do. The [TypeSafe agent skill](/agent-skill#installation) tells your agent to put many questions in each call, including ones that only matter for some inputs.
</Tip>

### Split a complex judgment into several questions

A judgment that depends on several things is best split into one question per thing. Combine the answers in your code, giving each a weight for its relative importance. The weights are yours. When the combined result doesn't match what your team would decide, change them in code and run again. Adding questions barely changes the response time because they run in parallel within one request. The split costs a few extra question tokens.

For example, ticket priority might be built from three Score questions: how severe the bug is, how frustrated the customer is, and how much the report gives an engineer to work with. The Score page walks through this request and the code that normalizes and weights the answers in [Splitting a complex judgment into several Scores](/primitives/score#splitting-a-complex-judgment-into-several-scores). This technique is called the [Composite scoring](/patterns/composite-scoring) pattern.

### When one question depends on another

Questions in the same request are independent: one answer does not become context for another question. If a later judgment depends on an earlier answer, make a second request in code. The dependency is real only when your code cannot build the second request until it has the first answer: it needs the answer to fetch more data for the state, to decide what the state is made of, or to pick the next question's options. Otherwise, ask the questions together and combine their answers in code.

仅当问题之间有强依赖时，才分为 2 次请求，否则，只有有可能，我们就 1 次请求，获取所有问题的答案。

Two requests are the exception, not the rule. If the second request's questions could have been asked against the original state, ask them in the first request and let the code ignore the ones it doesn't need. Three cookbooks make a second request for a real reason. [Skill suggestion](/cookbooks/skill_suggestion) ranks 182 skills in one request, then fetches the full text of the top three and judges them again against that better evidence. [Structure recovery](/cookbooks/autoformat) asks whether each line break split a sentence, merges lines into blocks from those answers, then classifies the blocks, which did not exist until the first request had answered. [Hierarchical classification](/cookbooks/hierarchical_classification) uses each Choice answer to decide which options the next request offers.

See [How to build with TypeSafe](/concepts/how-to-build-with-system-one) for guidance on breaking a workflow into focused judgments.

## Next steps

<Columns cols={3}>
  <Card title="Choice" href="/primitives/choice" icon="list">
    Pick one option from a fixed list.
  </Card>

  <Card title="Score" href="/primitives/score" icon="gauge">
    Rate the state along ordered levels.
  </Card>

  <Card title="Noul" href="/primitives/noul" icon="circle-check">
    Get the probability that a statement is true.
  </Card>
</Columns>

To see how these compose into system architectures, head to [Patterns](/patterns).
