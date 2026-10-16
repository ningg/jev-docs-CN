> ## Documentation Index
> Fetch the complete documentation index at: https://docs.typesafe.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Quick start

> Prefer to just dive in? Here's everything you need to get started immediately.

## Try it: the Playground

1. **Open the [Playground](https://console.typesafe.ai/playground)** and log in.
2. **Paste any text** as the state.

```plaintext title="Sample state" theme={null}
Hi, I've been trying to connect my Stripe account for 3 days and the integration keeps failing. I'm losing sales. Please help ASAP.
```

3. **Add a question.** Try a Noul question: `"Does this message express urgency?"`

```json theme={null}
{
  "urgency": {
    "type": "noul",
    "instructions": "Does this message express urgency?"
  }
}
```

4. **Add more questions.** Mix Noul, Choice, and Score in one call and see all results at once.

## Call it: the API

1. **Get your API key** from the [dashboard](https://console.typesafe.ai/keys)
2. **Make a POST request** to the API endpoint
3. **Review the [API Reference](/api)** for all the details.

```http theme={null}
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

### Sample cURL command

```bash theme={null}
curl -X POST https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
  {
    "state": "Hi, I've been trying to connect my Stripe account for 3 days and the integration keeps failing. I'm losing sales. Please help ASAP.",
    "model": "jev-latest",
    "questions": {
      "urgency": {
        "type": "noul",
        "instructions": "Does this message express urgency?"
      }
    }
  }
EOF
```

### Request body

```json theme={null}
{
  "state": "Hi, I've been trying to connect my Stripe account for 3 days and the integration keeps failing. I'm losing sales. Please help ASAP.",
  "model": "jev-latest",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this",
      "criteria": {
        "billing": "Payment or subscription issues",
        "technical": "Bugs or integration problems",
        "sales": "Pricing or account questions"
      }
    },
    "frustration": {
      "type": "score",
      "instructions": "How frustrated the customer appears",
      "criteria": [
        "Calm, just stating facts",
        "Frustrated but civil",
        "Very angry, strong language"
      ]
    },
    "is_urgent": {
      "type": "noul",
      "instructions": "The message conveys urgency or time-sensitivity"
    }
  }
}
```

### Response body

```json theme={null}
{
  "model": "jev-1.13.0",
  "answers": {
    "department": {
      "type": "choice",
      "choice": "technical",
      "confidence": 0.78,
      "probabilities": {
        "technical": 0.85,
        "sales": 0.0,
        "billing": 0.15
      }
    },
    "frustration": {
      "type": "score",
      "score": 1.0,
      "confidence": 1.0,
      "legend": {
        "0": "Calm, just stating facts",
        "1": "Frustrated but civil",
        "2": "Very angry, strong language"
      },
      "probabilities": {
        "0": 0.0,
        "1": 1.0,
        "2": 0.0
      }
    },
    "is_urgent": {
      "type": "noul",
      "noul": 1.0
    }
  },
  "usage": {
    "input_tokens": 392,
    "output_tokens": 65
  }
}
```

> **Tips**: 
>
> **1.返回结果中，`confidence` 、 `probabilities` 的含义。**
> 
> Re：可以简单认为 `confidence` 就是 `置信度`，基于选项概率分布计算出的`集中程度`指标； `probabilities` 就是选项的概率分布。
>
> **2.Score 类型的返回结果中，`legend` 的含义**
> 
> Re：本质就是 Score 类型问题的 选项，但是 Jev 进行了编码，特别注意： Jev 会严格按照 criteria 数组的顺序，从 0 开始编码，不会根据文字含义自动调整顺序。因此，我们针对 Score 类型问题，选项一定要自己填入「有序的选项」。
>
> 更多细节，参考文末的`附录`部分。






See the [API Reference](/api) for all the details.

## Code it: the Python SDK

1. **Install the SDK** (requires Python >= 3.10).

```bash title="With pip" theme={null}
pip install typesafe-sdk
```

```bash title="With uv" theme={null}
uv add typesafe-sdk
```

2. **Use the SDK.** The client reads `TYPESAFE_API_KEY` from the environment and calls `jev-latest` by default.

```python theme={null}
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

client = TypeSafeClient()

ticket = "Hi, I've been trying to connect my Stripe account for 3 days and the integration keeps failing. I'm losing sales. Please help ASAP."

response = client.system_one(
    state=ticket,
    questions={
        "department": Choice(
            instructions="Which team should handle this",
            criteria={
                "billing": "Payment or subscription issues",
                "technical": "Bugs or integration problems",
                "sales": "Pricing or account questions",
            },
        ),
        "frustration": Score(
            instructions="How frustrated the customer appears",
            criteria=[
                "Calm, just stating facts",
                "Frustrated but civil",
                "Very angry, strong language",
            ],
        ),
        "is_urgent": Noul(
            instructions="The message conveys urgency or time-sensitivity",
        ),
    },
)

print(response.answers["department"].choice)  # "technical"
print(response.answers["frustration"].score)  # 1.0
print(response.answers["is_urgent"].noul)     # 1.0
```

See [client SDKs](/sdk) for installation options and detailed usage.

## Vibe it: the agent skill

1. **[Install the TypeSafe skill](/agent-skill#installation)** using the Claude Code plugin or `npx skills add typesafe-ai/skills --skill typesafe-ai`. You can also [read SKILL.md on GitHub](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md).

<Tabs>
  <Tab title="Claude Code">
    Run these two commands in your terminal:

    ```bash theme={null}
    claude plugin marketplace add typesafe-ai/skills
    claude plugin install typesafe@typesafe-ai
    ```
  </Tab>

  <Tab title="Other agents">
    ```bash theme={null}
    npx skills add typesafe-ai/skills --skill typesafe-ai
    ```

    Choose your agent when prompted. Installation is project-local by default; add `-g` to install globally.
  </Tab>

  <Tab title="Copy to your agent">
    Paste this prompt into your coding agent:

    ```text wrap theme={null}
    Install the TypeSafe skill. If you're in Claude Code, run `claude plugin marketplace add typesafe-ai/skills`, then `claude plugin install typesafe@typesafe-ai`. If you're in another agent, run `npx skills add typesafe-ai/skills --skill typesafe-ai` and select your agent. Use one installation method. You can read the skill directly at https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md (raw: https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md). Then use the TypeSafe skill when working on this project.
    ```
  </Tab>
</Tabs>

2. **Tell your coding agent** to use the TypeSafe skill as you build!

```plaintext title="Coding agent prompt" theme={null}
Let's build a simple CLI that uses the TypeSafe API to evaluate a set of supplied documents on multiple dimensions. Use the TypeSafe skill to understand how to use the TypeSafe API and how to structure the system. Ask me questions about what kinds of documents I want to evaluate and on what dimensions.
```

See the [Agent Skill](/agent-skill) page for more details.




## 附录

### 附录 A：`confidence` 与 `probabilities`

Jev 返回结果中的 `confidence` 和 `probabilities` 都与模型判断的不确定性有关，但两者不是同一个东西。

一句话理解：

- `probabilities`：模型认为每个候选答案分别有多大可能性。
- `confidence`：把这些候选答案的概率分布，进一步压缩成一个数，用来描述分布有多集中。

根据 Jev 的文档，`choice` 和 `score` 类型会返回这两个字段；`noul` 类型则直接返回判断为真的概率，不额外返回 `confidence`。

#### 一、用一个实际例子理解

假设营销平台需要判断用户反馈属于哪个部门，Jev 返回：

```json
{
  "type": "choice",
  "choice": "technical",
  "probabilities": {
    "technical": 0.85,
    "sales": 0.00,
    "billing": 0.15
  },
  "confidence": 0.775
}
```

这里的 `confidence: 0.775` 是为了说明计算方式而构造的示例值，并非上述概率对应的 Jev 实际返回值。

逐个看：

| 字段 | 含义 |
| --- | --- |
| `choice: "technical"` | 模型最终选择了技术支持 |
| `probabilities.technical: 0.85` | 技术支持这一候选项获得 85% 的概率 |
| `probabilities.billing: 0.15` | 账单问题获得 15% 的概率 |
| `confidence` | 根据完整概率分布计算出的集中程度指标 |

注意：`choice` 是最终选择，`probabilities` 展示候选答案的分布，而 `confidence` 是对分布的进一步概括。不能直接把 `confidence` 当成最终答案正确的概率。

#### 二、`probabilities`：完整的候选答案概率分布

对于 `choice` 类型，假设候选项有三个：

**示例 A：模型判断比较明确**

| 候选项 | 概率 |
| --- | --- |
| technical | 85% |
| billing | 10% |
| sales | 5% |

最高概率 85%，明显高于其他选项。

**示例 B：模型判断比较模糊**

| 候选项 | 概率 |
| --- | --- |
| technical | 38% |
| billing | 34% |
| sales | 28% |

最高概率只有 38%，其他选项也很接近。

这两个例子说明：

- 概率分布越集中，通常表示模型对候选项的区分越明确。
- 概率分布越平坦，通常表示模型难以明确区分候选项。
- 所有候选项的概率之和应为 1。

#### 三、`confidence`：概率分布的集中程度

对于 `choice` 类型，Jev 的置信度计算公式为：

```text
confidence = (p_max - 1/n) / (1 - 1/n)
```

其中：

- `p_max`：最高的候选项概率。
- `n`：候选项总数。
- `1/n`：所有选项均匀分布时，每个选项的概率。

该公式把均匀分布映射为 0，把概率全部集中于一个选项的分布映射为 1。

以三个候选项为例：

| 概率分布 | 最高概率 | `confidence` |
| --- | --- | --- |
| 0.38 / 0.34 / 0.28 | 0.38 | 0.07 |
| 0.60 / 0.25 / 0.15 | 0.60 | 0.40 |
| 0.85 / 0.10 / 0.05 | 0.85 | 0.78 |
| 1.00 / 0.00 / 0.00 | 1.00 | 1.00 |

以上为按公式计算并四舍五入的示例值。

关键区别：最高概率为 85%，不意味着 `confidence` 也等于 0.85。对于三个选项，85% 的最高概率对应的 `confidence` 约为 0.775。

对于 `score` 类型，Jev 也会返回 `probabilities` 和 `confidence`，但 `confidence` 的计算还会考虑概率分布在评分档位上的位置，因此不能直接套用上面的 Choice 公式。

#### 四、工程上应该如何使用这两个字段？

结合营销平台和 AI 决策系统，可以这样设计：

| 判断情况 | 建议处理方式 |
| --- | --- |
| `confidence` 高，且错误代价低 | 自动执行 |
| `confidence` 中等，或前两名概率接近 | 补充判断或人工复核 |
| `confidence` 低，或输入信息不足 | 暂缓自动决策，转人工或调用更强的推理模型 |

这里的阈值必须用你自己的标注数据验证，不能直接认为 `confidence > 0.8` 就代表答案有 80% 的正确率。

另外，建议保留完整的 `probabilities`，不要只保存 `confidence`。这样后续才能分析模型经常混淆哪些类别、是否存在类别偏差，以及模型版本升级后判断是否发生变化。

最后区分一个容易混淆的概念：

- **Confidence（置信度）**：Jev 根据输出概率分布计算的集中程度指标。
- **Calibration（校准）**：检验模型声称的概率与实际正确率是否一致。

如果一批结果都给出 0.8 的正确性概率，那么经过良好校准后，这批结果的实际正确率才应当接近 80%。但 Jev 的 `confidence` 本身并不保证这一点。


`confidence` 翻译为**置信度**，但不能直接认为它就是准确率。

在 Jev 中，需要区分三个概念：

| 概念   | 英文          | 含义                    |
| ---- | ----------- | --------------------- |
| 置信度  | Confidence  | Jev 根据输出概率分布计算的确定程度指标 |
| 准确率  | Accuracy    | 一批预测结果中，预测正确的比例       |
| 概率校准 | Calibration | 模型给出的概率是否与实际发生的频率相符   |

举个例子：

假设 Jev 处理了 1,000 条营销文案，全部给出 `confidence = 0.9`。

- 如果 900 条判断正确，那么这批结果的准确率是 90%。
- 如果只有 700 条判断正确，那么准确率就是 70%。

因此，不能仅凭 `confidence = 0.9` 就断定准确率是 90%。

而且，对 Jev 的 `choice` 类型来说，`confidence` 是根据候选项的概率分布计算的。例如，三个选项的概率为 `0.85、0.10、0.05` 时，按照前面介绍的公式，`confidence` 约为 `0.775`，并不是 `0.85`。

工程建议： 如果你要在 AI 评估系统中使用 Jev，建议同时记录 `confidence`、最终预测结果和真实标签，再按置信度区间统计实际准确率。

这样才能知道 Jev 的置信度是否可靠，以及应该将自动执行的阈值设置在哪里。

### 附录 B：`score` 返回结果中的 `legend`

在 Jev 的 `score` 问题中，`legend` 的含义是：把模型使用的数字等级，映射回你在请求中定义的文字描述。

它不是模型自动生成的一套新选项，也不是分数的解释规则，而是你提供的 `criteria` 的编号映射。

#### 1. `legend` 是什么？

假设你提交了一个用户情绪评分问题：

```json
{
  "type": "score",
  "instructions": "判断用户的愤怒程度",
  "criteria": [
    "平静",
    "不满，但表达克制",
    "非常愤怒"
  ]
}
```

Jev 会按照 `criteria` 数组的顺序，从 0 开始编号。

返回结果可能是：

```json
{
  "type": "score",
  "score": 1.0,
  "legend": {
    "0": "平静",
    "1": "不满，但表达克制",
    "2": "非常愤怒"
  },
  "probabilities": {
    "0": 0.0,
    "1": 1.0,
    "2": 0.0
  },
  "confidence": 1.0
}
```

这里：

- `legend["0"]` 对应第一个等级「平静」。
- `legend["1"]` 对应第二个等级「不满，但表达克制」。
- `legend["2"]` 对应第三个等级「非常愤怒」。

因此，`score = 1.0` 表示模型的概率分布全部集中在第二个等级上。

#### 2. 会自动编号吗？

会。但准确地说，是 Jev 根据你提供的 `criteria` 数组顺序，自动为等级分配从 0 开始的索引。

| `criteria` 中的位置 | 自动编号 | `legend` 的 key |
| --- | --- | --- |
| 第 1 个元素 | 0 | `"0"` |
| 第 2 个元素 | 1 | `"1"` |
| 第 3 个元素 | 2 | `"2"` |
| 第 4 个元素 | 3 | `"3"` |

编号是系统按数组顺序分配的，不需要你在文字描述中写上数字。官方文档规定，Score 的等级至少为 2 个，最多为 10 个。

#### 3. 编号是等距的吗？

这里需要区分两个问题。

第一，编号本身是等间隔的整数。例如 0、1、2、3，每个编号相差 1。

第二，等级在实际业务含义上不一定等距。例如：

- 0：普通问题
- 1：需要关注的问题
- 2：严重问题

数字 0、1、2 是等间隔的，但「普通」到「需要关注」的严重程度差距，不一定等于「需要关注」到「严重」的差距。

Jev 的 `score` 是按各等级编号和对应概率计算的加权平均值：

```text
score = Σ (i × p_i)    ，i 从 0 到 n-1
```

因此，如果 `probabilities` 为 `{"0": 0.2, "1": 0.5, "2": 0.3}`，那么：

```text
score = 0×0.2 + 1×0.5 + 2×0.3 = 1.1
```

这里的 `1.1` 不是第四个等级，也不是模型自动生成了一个新选项，而是概率加权后的连续数值。

工程建议：如果你要用 Jev 做风险评分、营销文案合规或工单优先级判断，应该按照业务标准定义由低到高的 `criteria`。不要仅仅写「0、1、2、3」或「低、中、高」，最好为每一级提供清晰、可区分的实际情境描述。这样评分结果更容易解释，也更适合在不同模型版本之间进行评估。

Jev 会严格按照 `criteria` 数组的顺序，从 `0` 开始编码，不会根据文字含义自动调整顺序。

你的输入是：

```json
"criteria": [
  "平静",
  "非常愤怒",
  "不满，但表达克制"
]
```

对应的 `legend` 将是：

```json
{
  "0": "平静",
  "1": "非常愤怒",
  "2": "不满，但表达克制"
}
```

需要特别注意：虽然编号是 `0、1、2`，但语义顺序是混乱的：

- `0`：平静
- `1`：非常愤怒
- `2`：不满，但表达克制

Jev 的 `score` 会将这些编号视为有序等级，并根据概率计算加权分数。因此，如果你希望分数越高代表愤怒程度越高，当前顺序就不合适。

建议改为：

```json
"criteria": [
  "平静",
  "不满，但表达克制",
  "非常愤怒"
]
```

这样 `0` 表示平静，`1` 表示克制的不满，`2` 表示非常愤怒，分数越高就代表愤怒程度越高。



