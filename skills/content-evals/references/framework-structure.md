Keep this as a small Python package with one criteria catalogue, one scoring configuration per use case, and one TypeSafe adapter. The CLI should be a thin layer on top of the same Python API, not a separate implementation.

The goal is to make a new scoring setup a configuration task rather than a coding task.

## 1. Suggested project structure

```
writing-score/
├── pyproject.toml
├── README.md
├── configs/
│   └── technical-blog.yaml
├── src/
│   └── writing_score/
│       ├── __init__.py
│       ├── models.py
│       ├── criteria.py
│       ├── presets.py
│       ├── evaluator.py
│       ├── typesafe_adapter.py
│       ├── results.py
│       └── cli.py
└── tests/
    ├── test_criteria.py
    ├── test_config.py
    └── test_evaluator.py
```

Keep the initial version this small. No plugin architecture, database, registry service, or separate CLI package.

| File                  | Responsibility                                                  |
| --------------------- | --------------------------------------------------------------- |
| `models.py`           | Data structures for criteria, scoring configuration and results |
| `criteria.py`         | Definitions and reusable question templates                     |
| `presets.py`          | Default criteria and ready-to-use presets                       |
| `evaluator.py`        | Main Python API, orchestration and overall score calculation    |
| `typesafe_adapter.py` | Converts your criteria and questions into TypeSafe API calls    |
| `results.py`          | Per-criterion scores, overall score and confidence              |
| `cli.py`              | Future command-line interface                                   |
| `configs/`            | User-editable configurations for different scoring tasks        |

Keep `models.py` independent of TypeSafe-specific classes. That way, if the API changes or you later want a local evaluator, you only need to change the adapter.

## 2. Make each new scoring task a YAML file

For example, `configs/technical-blog.yaml`:

```

name: technical-blog
description: Evaluate technical blog posts for developers

context:
  audience: "Developers familiar with basic programming"
  content_type: "Technical blog article"
  purpose: "Explain a technical concept clearly"

scoring:
  levels:
    - "Poor: substantial problems prevent the intended outcome"
    - "Needs improvement: noticeable weaknesses hinder readers"
    - "Good: meets expectations with minor issues"
    - "Excellent: particularly effective for the intended reader"

  criteria:
    clarity:
      enabled: true
      weight: 1.0

    structure:
      enabled: true
      weight: 1.0

    consistency:
      enabled: true
      weight: 1.0

    findability:
      enabled: true
      weight: 1.0

    audience_fit:
      enabled: true
      weight: 1.5

    content_type_fit:
      enabled: true
      weight: 1.5

```

This configuration controls the task without duplicating the actual question templates or criterion definitions.

The six criteria are always available in the catalogue, but the configuration determines which ones to run and how much each contributes to the overall score.

One refinement: eventually, give each criterion its own scoring levels where the generic levels are not specific enough. Keep the global four-level scale as the initial default.

## 3. Define a simple Python API first

Aim for an interface that feels natural in code:

```
from writing_score import evaluateresult = evaluate(    content=article_text,    config="configs/technical-blog.yaml",)print(result.overall_score)print(result.criteria["clarity"].score)
```

Then add support for custom overrides:

```
result = evaluate(    content=article_text,    config="configs/technical-blog.yaml",    context={        "audience": "Junior QA engineers",        "purpose": "Explain how to design reliable UI tests",    },)
```

The configuration file supplies the defaults. Explicit overrides replace individual values without requiring a new file for every article.

Internally, `evaluate()` should:

1. Load and validate the configuration.
2. Resolve enabled criteria and their question templates.
3. Populate context placeholders.
4. Build TypeSafe `Score` questions.
5. Submit all questions in one `system_one` call.
6. Normalize scores, calculate the weighted overall score and return structured results.

TypeSafe supports sending multiple independent scoring questions in a single request, then combining their normalized scores using weights in your own code.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.typesafe.ai\&sz=32)

TypeSafe

## 4. Keep the CLI thin

Once the Python API works, expose the same functionality through commands like these:

```
# Evaluate with a preset
writing-score evaluate article.md \
  --config configs/technical-blog.yaml

# Override context for one evaluation
writing-score evaluate article.md \
  --config configs/technical-blog.yaml \
  --audience "Junior developers"

# Save structured results
writing-score evaluate article.md \
  --config configs/technical-blog.yaml \
  --output result.json

# List available criteria
writing-score criteria list
```

I'd postpone implementing the CLI until the configuration format and Python API feel stable. A library-first design keeps it easy to use from scripts, notebooks, automated content pipelines and eventually a CLI.

## 5. Define the overall score explicitly

For each criterion, normalize its TypeSafe score to a range of 0 to 1:

\\[ s_i^{\*}=\frac{s_i}{L_i} \\]

Here, \\(L_i\\) is the highest level number for that criterion. With four levels numbered 0 to 3, divide by 3.

Then calculate the weighted average:

\\[ S=100 \times \frac{\sum_i w_i s_i^{\*}}{\sum_i w_i} \\]

This produces an overall score from 0 to 100. Higher weights give criteria more influence.

Keep the individual scores, probability distributions and confidence values in the results. The overall score is useful for ranking content, but the individual scores explain what needs improvement.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.typesafe.ai\&sz=32)

TypeSafe

## 6. What I'd implement first

1. Criteria catalogue: define the six criteria, reusable question templates and required context parameters.
2. Configuration loader: load YAML, apply overrides and reject missing required parameters.
3. TypeSafe adapter: submit the questions and map responses into your own result model.
4. Scoring and tests: calculate the weighted score and test normalization, missing values and configuration errors.
5. CLI: add the command-line interface after the underlying API is stable.

My main recommendation is to avoid building a general-purpose evaluation framework. Start with one working preset, six criteria and one evaluation function. Add flexibility only when a real scoring task needs it.

One thing worth testing early: whether your audience and content-type questions work better as two independent scores or whether you need separate context fields for audience knowledge, reader goal and document format. Keep them separate if combining them into one question makes the score ambiguous.

----


Typesafe recommends breaking a complex judgment into separate Scores and then combining them with weights in your code is called the Composite scoring pattern. Would this be possible ?

Yes. Composite scoring is a natural fit for this project, and I'd make it the core evaluation model rather than treating the overall score as an afterthought.

The idea is to break a broad judgment into smaller, independently scored questions, then combine their scores using weights in your own code. This gives you more control over what the overall score means and makes custom criteria easy to add. See TypeSafe's [Composite scoring pattern](https://docs.typesafe.ai/patterns/composite-scoring?utm_source=chatgpt.com).

For example, instead of asking one vague question, "How good is this technical article?", you could evaluate:

- Clarity
- Structure
- Consistency
- Findability
- Audience fit
- Content-type fit
- Example quality
- Example coverage
- Coverage of specified topics

The first six form your default preset. The others can be added when needed, without changing the evaluator.

## How I'd reflect this in the project

I'd make three small design changes.

### 1. Each criterion becomes an independent `Score`

```
from typesafe_sdk import Scorequestions = {    "clarity": Score(        instructions="How easily can the intended reader understand the content?",        criteria=[            "Meaning is frequently unclear.",            "Noticeable clarity problems hinder understanding.",            "The content is clear, with minor issues.",            "The content communicates ideas clearly and precisely.",        ],    ),    "example_quality": Score(        instructions=(            "How useful, relevant and technically correct "            "are the examples?"        ),        criteria=[            "Examples are misleading or unusable.",            "Examples have significant gaps or weaknesses.",            "Examples are useful, with minor limitations.",            "Examples are accurate and directly support the reader's goal.",        ],    ),}
```

These are illustrative level descriptions. In practice, each criterion should have levels tailored to the dimension being evaluated. TypeSafe returns each answer separately, including its score, probability distribution and confidence.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.typesafe.ai\&sz=32)

TypeSafe

### 2. Store weights alongside the configuration

```
criteria:
  clarity:
    weight: 1.0
  example_quality:
    weight: 1.5
  topic_coverage:
    weight: 2.0
```

This allows each preset to have its own weighting without changing the evaluator.

### 3. Combine the results in one reusable function

```
def composite_score(scores, weights, max_levels):    total_weight = sum(weights[key] for key in scores)    if total_weight <= 0:        raise ValueError("Total weight must be positive")    return 100 * sum(        weights[key] * scores[key] / max_levels[key]        for key in scores    ) / total_weight
```

Here, `scores` contains TypeSafe's returned scores, and `max_levels` contains the highest level number for each criterion. Validate missing scores and invalid weights before calling this function.

One important detail: this weighted average allows a high score in one dimension to compensate for a low score in another. If you later want requirements such as "topic coverage must score at least 70%", handle those as separate acceptance thresholds rather than relying on the composite score alone.

Final design: configurable independent `Score` questions, one TypeSafe request per document, and a local weighted aggregation step. Custom criteria become additional questions, not new code paths. That follows TypeSafe's documented Composite scoring pattern directly.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.typesafe.ai\&sz=32)


--- 
does it mean that for each new profile with custom questions I need to modify python code too, not only yaml ?


No. You should be able to define a completely new scoring profile in YAML without changing any Python code.

The Python code should interpret the configuration and build TypeSafe `Score` objects dynamically.

For example, adding this to a new YAML profile should be enough:

```
name: technical-blog

criteria:
  clarity:
    weight: 1.0
    question: "How clear is the content for its intended audience?"
    levels:
      - "Poor: frequently difficult to understand"
      - "Fair: noticeable clarity issues"
      - "Good: generally clear"
      - "Excellent: consistently clear and precise"

  example_quality:
    weight: 1.5
    question: "How accurate, relevant and useful are the examples?"
    levels:
      - "Poor: examples are misleading or unusable"
      - "Fair: examples have significant weaknesses"
      - "Good: examples are useful with minor issues"
      - "Excellent: examples are accurate and highly effective"
```

Your existing Python code would:

1. Load the YAML profile.
2. Iterate over its criteria.
3. Create a TypeSafe `Score` for each criterion using its question and levels.
4. Submit the scores for evaluation.
5. Combine the results using the configured weights.

The same code works for your default six criteria or fifty custom criteria.

One important design rule: keep the scoring engine generic. Put criterion definitions, questions, score levels and weights in YAML. Python should handle execution, validation and aggregation.

You only need to modify Python when adding a new capability, such as a different aggregation method or a new kind of evaluator, not when adding another question.
