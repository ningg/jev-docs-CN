> ## Documentation Index
> Fetch the complete documentation index at: https://docs.typesafe.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Confidence

> How TypeSafe reports certainty, how it differs from probability, and how to use it to control system behavior.

export function ScoreConfidenceExplorer() {
  const [probabilities, setProbabilities] = useState([0, 5, 90, 5, 0]);
  const levels = [0, 1, 2, 3, 4];
  function changeProbability(index, value) {
    setProbabilities(current => {
      const others = levels.filter(i => i !== index);
      const remaining = 100 - value;
      const previousRemaining = others.reduce((sum, i) => sum + current[i], 0);
      const next = [...current];
      next[index] = value;
      for (const i of others) {
        next[i] = previousRemaining > 0 ? remaining * current[i] / previousRemaining : remaining / others.length;
      }
      return next;
    });
  }
  function formatProbability(value) {
    return `${Number(value.toFixed(1))}%`;
  }
  function scoreConfidence(values) {
    const count = values.length;
    const total = values.reduce((sum, value) => sum + value, 0);
    const p = values.map(value => value / total);
    const peak = p.indexOf(Math.max(...p));
    const spread = p.reduce((sum, value, i) => sum + value * Math.abs(i - peak), 0);
    const evenSpread = p.reduce((sum, _, i) => sum + Math.abs(i - (count - 1) / 2), 0) / count;
    return Math.max(0, Math.min(1, 1 - spread / evenSpread));
  }
  function choiceConfidence(values) {
    const count = values.length;
    const peak = Math.max(...values) / 100;
    return Math.max(0, Math.min(1, (count * peak - 1) / (count - 1)));
  }
  const confidence = scoreConfidence(probabilities);
  const choiceComparison = choiceConfidence(probabilities);
  const score = probabilities.reduce((sum, value, i) => sum + i * value / 100, 0);
  const peak = probabilities.indexOf(Math.max(...probabilities));
  const buttonClass = "border px-3 py-2 text-sm hover:bg-zinc-100 dark:hover:bg-zinc-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-500";
  const buttonStyle = {
    borderColor: "#71717a"
  };
  const eyebrow = {
    fontSize: "0.6875rem",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase"
  };
  return <section aria-label="Explore Score probabilities and confidence" className="not-prose my-6 border border-zinc-300 dark:border-zinc-700 p-5 sm:p-6 text-zinc-800 dark:text-zinc-200">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-zinc-600 dark:text-zinc-400" style={eyebrow}>Score question with five levels</div>
          <div className="mt-2 text-base font-semibold">See how distance between levels changes confidence</div>
        </div>
        <div className="text-right" role="status" aria-live="polite" aria-atomic="true">
          <div className="text-sm text-zinc-600 dark:text-zinc-400">Confidence</div>
          <output className="block text-3xl font-semibold tabular-nums" style={{
    color: "#E551BA"
  }}>
            {confidence.toFixed(2)}
          </output>
        </div>
      </div>

      <div role="img" aria-label={`Probability distribution: ${levels.map(level => `level ${level} ${formatProbability(probabilities[level])}`).join(", ")}. Most likely level ${peak}.`} className="my-6">
        <div className="text-xs text-zinc-600 dark:text-zinc-400">Probability</div>
        <div aria-hidden="true" style={{
    position: "relative",
    height: "180px",
    margin: "34px 0 52px 44px"
  }}>
          {[0, 50, 100].map(tick => <div key={tick} style={{
    position: "absolute",
    bottom: `${tick}%`,
    width: "100%",
    borderBottom: "1px solid",
    borderColor: "color-mix(in srgb, currentColor 18%, transparent)"
  }}>
              <span className="text-xs" style={{
    position: "absolute",
    right: "calc(100% + 8px)",
    transform: "translateY(-50%)"
  }}>{tick}%</span>
            </div>)}
          <div style={{
    position: "absolute",
    inset: 0,
    display: "flex",
    justifyContent: "space-around",
    alignItems: "flex-end"
  }}>
            {levels.map(level => <div key={level} style={{
    position: "relative",
    width: "14%",
    height: `${probabilities[level]}%`
  }}>
                <span className="text-sm font-semibold tabular-nums" style={{
    position: "absolute",
    bottom: "calc(100% + 6px)",
    left: "50%",
    transform: "translateX(-50%)",
    whiteSpace: "nowrap"
  }}>{formatProbability(probabilities[level])}</span>
                <div style={{
    height: "100%",
    background: level === peak ? "#E551BA" : "currentColor",
    opacity: level === peak ? 1 : 0.45
  }} />
                <span className="text-sm" style={{
    position: "absolute",
    top: "calc(100% + 8px)",
    left: "50%",
    transform: "translateX(-50%)"
  }}>{level}</span>
                <span className="text-xs text-zinc-600 dark:text-zinc-400" style={{
    position: "absolute",
    top: "calc(100% + 28px)",
    left: "50%",
    transform: "translateX(-50%)",
    whiteSpace: "nowrap"
  }}>
                  {level === peak ? "peak" : `${Math.abs(level - peak)} away`}
                </span>
              </div>)}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {levels.map(level => <label key={level} className="flex items-center gap-3 text-sm">
            <span className="w-5 font-semibold">{level}</span>
            <input type="range" min="0" max="100" step="1" value={probabilities[level]} onChange={event => changeProbability(level, Number(event.target.value))} aria-label={`Probability of level ${level}`} aria-valuetext={formatProbability(probabilities[level])} className="min-w-0 flex-1 cursor-pointer" style={{
    accentColor: "#E551BA",
    minHeight: "44px"
  }} />
            <output className="w-16 text-right tabular-nums">{formatProbability(probabilities[level])}</output>
          </label>)}
      </div>
      <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">Move a slider to change a level's probability. The other probabilities adjust to keep the total at 100%.</p>

      <div className="mt-4 flex flex-wrap gap-2" aria-label="Example distributions">
        <button type="button" className={buttonClass} style={buttonStyle} onClick={() => setProbabilities([0, 5, 90, 5, 0])}>Clear peak</button>
        <button type="button" className={buttonClass} style={buttonStyle} onClick={() => setProbabilities([0, 55, 45, 0, 0])}>Split between neighbors</button>
        <button type="button" className={buttonClass} style={buttonStyle} onClick={() => setProbabilities([55, 0, 0, 0, 45])}>Split between ends</button>
        <button type="button" className={buttonClass} style={buttonStyle} onClick={() => setProbabilities([20, 20, 20, 20, 20])}>Even spread</button>
      </div>
      <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-sm" aria-live="polite">
        <div className="flex gap-2"><dt className="text-zinc-600 dark:text-zinc-400">Score</dt><dd className="tabular-nums">{score.toFixed(2)}</dd></div>
        <div className="flex gap-2"><dt className="text-zinc-600 dark:text-zinc-400">Choice formula on the same probabilities</dt><dd className="tabular-nums">{choiceComparison.toFixed(2)}</dd></div>
      </dl>
      <details className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">
        <summary className="cursor-pointer">How this demo calculates Confidence</summary>
        <p className="mt-3">This demo uses the <a href="#score">Score formula</a>. It takes the average distance, in levels, between the answer and the peak, weighted by probability. It divides that by 1.2, the same average for an even spread over five levels measured from the middle level, and subtracts the result from 1, stopping at 0. Probability on a level next to the peak lowers confidence less than probability far from it, which the Choice formula does not take into account.</p>
      </details>
    </section>;
}

export function ConfidenceExplorer() {
  const [probabilities, setProbabilities] = useState([90, 6, 4]);
  const options = ["A", "B", "C"];
  function changeProbability(index, value) {
    setProbabilities(current => {
      const others = [0, 1, 2].filter(i => i !== index);
      const remaining = 100 - value;
      const previousRemaining = current[others[0]] + current[others[1]];
      const next = [...current];
      next[index] = value;
      next[others[0]] = previousRemaining > 0 ? remaining * current[others[0]] / previousRemaining : remaining / 2;
      next[others[1]] = remaining - next[others[0]];
      return next;
    });
  }
  function formatProbability(value) {
    if (Math.abs(value - 100 / 3) < 0.000001) return "33⅓%";
    return `${Number(value.toFixed(1))}%`;
  }
  function choiceConfidence(values) {
    const count = values.length;
    const peak = Math.max(...values) / 100;
    return Math.max(0, Math.min(1, (count * peak - 1) / (count - 1)));
  }
  const confidence = choiceConfidence(probabilities);
  const maximum = Math.max(...probabilities);
  const winners = options.filter((option, i) => Math.abs(probabilities[i] - maximum) < 0.000001);
  const selected = winners.length === 1 ? `Option ${winners[0]}` : `Tie: ${winners.join(", ")}`;
  const buttonClass = "border px-3 py-2 text-sm hover:bg-zinc-100 dark:hover:bg-zinc-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-500";
  const buttonStyle = {
    borderColor: "#71717a"
  };
  const eyebrow = {
    fontSize: "0.6875rem",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase"
  };
  return <section aria-label="Explore probabilities and confidence" className="not-prose my-6 border border-zinc-300 dark:border-zinc-700 p-5 sm:p-6 text-zinc-800 dark:text-zinc-200">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-zinc-600 dark:text-zinc-400" style={eyebrow}>Choice question with three options</div>
          <div className="mt-2 text-base font-semibold">See how probability distribution changes confidence</div>
        </div>
        <div className="text-right" role="status" aria-live="polite" aria-atomic="true">
          <div className="text-sm text-zinc-600 dark:text-zinc-400">Confidence</div>
          <output className="block text-3xl font-semibold tabular-nums" style={{
    color: "#E551BA"
  }}>
            {confidence.toFixed(2)}
          </output>
        </div>
      </div>

      <div role="img" aria-label={`Probability distribution: ${options.map((option, i) => `${option} ${formatProbability(probabilities[i])}`).join(", ")}. ${selected}.`} className="my-6">
        <div className="text-xs text-zinc-600 dark:text-zinc-400">Probability</div>
        <div aria-hidden="true" style={{
    position: "relative",
    height: "180px",
    margin: "34px 0 36px 44px"
  }}>
          {[0, 50, 100].map(tick => <div key={tick} style={{
    position: "absolute",
    bottom: `${tick}%`,
    width: "100%",
    borderBottom: "1px solid",
    borderColor: "color-mix(in srgb, currentColor 18%, transparent)"
  }}>
              <span className="text-xs" style={{
    position: "absolute",
    right: "calc(100% + 8px)",
    transform: "translateY(-50%)"
  }}>{tick}%</span>
            </div>)}
          <div style={{
    position: "absolute",
    inset: 0,
    display: "flex",
    justifyContent: "space-around",
    alignItems: "flex-end"
  }}>
            {options.map((option, index) => <div key={option} style={{
    position: "relative",
    width: "21%",
    height: `${probabilities[index]}%`
  }}>
                <span className="text-sm font-semibold tabular-nums" style={{
    position: "absolute",
    bottom: "calc(100% + 6px)",
    left: "50%",
    transform: "translateX(-50%)",
    whiteSpace: "nowrap"
  }}>{formatProbability(probabilities[index])}</span>
                <div style={{
    height: "100%",
    background: winners.length === 1 && winners[0] === option ? "#E551BA" : "currentColor",
    opacity: winners.length === 1 && winners[0] === option ? 1 : 0.45
  }} />
                <span className="text-sm" style={{
    position: "absolute",
    top: "calc(100% + 8px)",
    left: "50%",
    transform: "translateX(-50%)"
  }}>{option}</span>
              </div>)}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {options.map((option, index) => <label key={option} className="flex items-center gap-3 text-sm">
            <span className="w-5 font-semibold">{option}</span>
            <input type="range" min="0" max="100" step="1" value={probabilities[index]} onChange={event => changeProbability(index, Number(event.target.value))} aria-label={`Probability of ${option}`} aria-valuetext={formatProbability(probabilities[index])} className="min-w-0 flex-1 cursor-pointer" style={{
    accentColor: "#E551BA",
    minHeight: "44px"
  }} />
            <output className="w-16 text-right tabular-nums">{formatProbability(probabilities[index])}</output>
          </label>)}
      </div>
      <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">Move a slider to change an option's probability. The other probabilities adjust to keep the total at 100%.</p>

      <div className="mt-4 flex flex-wrap gap-2" aria-label="Example distributions">
        <button type="button" className={buttonClass} style={buttonStyle} onClick={() => setProbabilities([90, 6, 4])}>Clear winner</button>
        <button type="button" className={buttonClass} style={buttonStyle} onClick={() => setProbabilities([40, 33, 27])}>Spread out</button>
        <button type="button" className={buttonClass} style={buttonStyle} onClick={() => setProbabilities([100 / 3, 100 / 3, 100 / 3])}>Even split</button>
      </div>
      <div className="mt-4 text-sm" aria-live="polite">{winners.length === 1 ? `Selected: ${selected}` : selected}</div>
      <details className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">
        <summary className="cursor-pointer">How this demo calculates Confidence</summary>
        <p className="mt-3">TypeSafe computes confidence from how the probability is spread across the options. All of it on one option gives 1.0; the more evenly it spreads, the lower the confidence. With three options, the <a href="#choice">Choice formula</a> is <code>(3 × largest probability − 1) / 2</code>, which is what this demo shows.</p>
      </details>
    </section>;
}

All Score and Choice answers from TypeSafe include a `probabilities` property representing the probability distribution across the options (for Choice) or levels (for Score). The *shape* of that distribution is what tells you how certain the model is: concentrated on one outcome means a confident answer, spread out means an uncertain one.

The answer's `confidence` property collapses that shape into a single number from 0 to 1, so you can threshold on it without doing the math yourself. It is 1 when all the probability is on one outcome and 0 when the probability is spread evenly. (Noul answers don't carry one; see [Noul](#noul) below.)

## Confidence is derived from the probabilities

`confidence` is a statistic computed from the probability distribution the answer already gives you. TypeSafe computes it for you and returns it on every Choice and Score answer, so the common case needs no extra work on your side.

<ConfidenceExplorer />

For a [Choice](/primitives/choice), the distribution is `probabilities` across your options. For a [Score](/primitives/score), it is the distribution across your levels. In both cases a flatter distribution means lower confidence: low confidence on a Choice often means none of the options are a clear winner over the others, and low confidence on a Score often means the levels are ambiguous, multi-dimensional, or the state doesn't contain enough to go on.

The exact formula for each question type is in [How confidence is calculated](#how-confidence-is-calculated), so you can see how any `confidence` value follows from the answer's own `probabilities`.

## "I don't know" is a useful signal

If an intelligent system, whether human or machine, cannot express honest uncertainty, the system cannot be trusted.

Confidence gives you a built-in mechanism for the model to say "I'm not sure about this one." This lets your code implement different behavior for different levels of certainty, which is the foundation for building systems you can actually rely on.

## Three paths for using confidence in your code

A useful starting pattern is to divide confidence into three ranges, each producing a different system behavior:

**High confidence:** Act automatically. The model has a clear read and you can proceed without human involvement.

**Medium confidence:** Proceed with caution. The model has a reasonable answer but is not certain. Depending on context, you might ask the user to confirm, flag for review, or gather more information before acting.

**Low confidence:** Do not act. Route to a human, request clarification, or fall back to a different system. The model is telling you it does not have enough information or the question is not a good fit.

Where you draw those boundaries depends on the stakes.

## Thresholds scale with risk

A confidence threshold is not one number. Different actions within the same system should be gated at different levels depending on the consequences of getting it wrong.

```python theme={null}
response = client.system_one(
    state=user_message,
    questions={
        "action": Choice(
            instructions="What is the user trying to do?",
            criteria={
                "check_balance": "View account balance",
                "approve_transfer": "Approve the pending withdrawal request",
                "support": "Get help with an issue",
            },
        ),
    },
)

action = response.answers["action"]
confidence = action.confidence

if confidence < 0.5:
    # Model is genuinely unsure. Don't guess.
    route_to_human(user_message)

elif action.choice == "check_balance":
    # Low stakes. Showing the wrong screen is recoverable.
    show_balance(account_id)

elif action.choice == "approve_transfer":
    if confidence > 0.9:
        # High stakes, high confidence. Proceed with confirmation.
        confirm_then_execute(account_id)
    else:
        # High stakes, moderate confidence. Verify first.
        ask_user_to_confirm(account_id)
```

The 0.5 confidence floor catches anything the model reports as genuinely uncertain. Above that, the threshold for acting without confirmation is higher for a destructive operation than for a read-only one. Your code encodes the risk tolerance.

<Note>
  The correct threshold values depend on your domain and the performance of the model for your use case. Start with conservative thresholds, test with your own data, and adjust as you observe results.
</Note>

## How confidence is calculated

Each question type summarizes its distribution a little differently. A Noul has two outcomes, a Choice has any number of options in no particular order, and a Score's levels are ordered, so each formula below builds on the one before it.

TypeSafe's `confidence` is one reasonable way to summarize a distribution, not the only one. We return a fixed measure so that every answer comes with a sensible default: you can gate on `confidence` from your first call, on the same 0 to 1 scale for every question, without first choosing and validating a statistic of your own. Because the formulas below are exact and every answer includes its full `probabilities`, you can compute whichever measure matters most to your application instead.

### Noul

A Noul answer is a single probability $p$ that the answer is yes, and TypeSafe returns no separate `confidence` for it. The probability already carries the uncertainty: a value near 0.5 is the model saying it is unsure, and the [Noul](/primitives/noul) page covers how to threshold on it directly.

If you want a confidence-style number anyway, for example to gate Nouls and Choices with the same code, use the distance from 0.5:

$$
\text{confidence} = |2p - 1|
$$

This gives 0 at $p = 0.5$ and 1 at $p = 0$ or $p = 1$. It is also the Choice formula below applied to a yes-or-no Choice, so it sits on the same scale as Choice confidence.

### Choice

A Choice extends the same idea to any number of options. For a Choice with $n$ options, where $p_{\max}$ is the probability of the selected option:

$$
\text{confidence} = \frac{p_{\max} - \frac{1}{n}}{1 - \frac{1}{n}}
$$

This measures how far the top probability sits above an even split of $\frac{1}{n}$ per option, on a scale where the even split is 0 and certainty is 1. Only the top probability counts, so $(0.6, 0.3, 0.1)$ and $(0.6, 0.2, 0.2)$ both have confidence 0.4.

```python theme={null}
def choice_confidence(probabilities: list[float]) -> float:
    n = len(probabilities)
    return (max(probabilities) - 1 / n) / (1 - 1 / n)


choice_confidence(list(answer.probabilities.values()))
```

The [explorer at the top of this page](#confidence-is-derived-from-the-probabilities) uses this formula with three options.

Two simpler measures, computed from the same `probabilities`, are often very effective in practice and are worth trying alongside `confidence`:

* **Top probability**, $p_{\max}$. It reads directly as "how likely is the selected option", which makes thresholds easy to reason about. Its meaning depends on the number of options, since 0.5 is a weak answer among two options and a strong one among ten, so set its threshold per question.
* **Top-to-second ratio**, $p_{\max} / p_{\text{second}}$. It measures how clearly the selected option beats the runner-up and ignores how the rest is spread. Many real decisions come down to the top two candidates, and this ratio targets exactly that.

### Score

A Score's levels are ordered, so its formula also counts how far probability sits from the most likely level. For a Score with $n$ levels numbered $0$ to $n - 1$, where $p_i$ is the probability of level $i$ and $m$ is the most likely level:

$$
\text{confidence} = \max\left(0,\ 1 - \frac{\sum_i p_i \, |i - m|}{\text{MAD}_{\text{unif}}}\right)
\qquad
\text{MAD}_{\text{unif}} = \frac{1}{n} \sum_i \left| i - \frac{n - 1}{2} \right|
$$

The sum in the numerator is the probability-weighted average distance, in levels, between the answer and the most likely level. $\text{MAD}_{\text{unif}}$ is the same kind of average distance for an even spread across all levels, measured from the middle level. Confidence compares the two, and is floored at 0 when the answer is at least as spread out as an even spread.

Probability on a neighboring level lowers confidence less than the same probability on a level further away. With three levels, $(0, 0.5, 0.5)$ has confidence 0.25, because the model is torn between two adjacent levels. $(0.5, 0, 0.5)$ has confidence 0, because it is torn between opposite ends. The Choice formula would give both distributions 0.25.

<ScoreConfidenceExplorer />

```python theme={null}
def score_confidence(probabilities: list[float]) -> float:
    n = len(probabilities)
    m = probabilities.index(max(probabilities))
    spread = sum(p * abs(i - m) for i, p in enumerate(probabilities))
    even_spread = sum(abs(i - (n - 1) / 2) for i in range(n)) / n
    return max(0.0, 1 - spread / even_spread)


levels = sorted(answer.probabilities)
score_confidence([answer.probabilities[level] for level in levels])
```

The `bug_severity` answer in the [Score response example](/primitives/score#response-structure) has probabilities $(0, 0.57, 0.43)$. The most likely level is 1, the spread is $0.43$, and $\text{MAD}_{\text{unif}}$ for three levels is $\frac{2}{3}$, so confidence is $1 - 0.43 / \frac{2}{3} \approx 0.35$.


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.