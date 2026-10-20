
## 1. Framework structure

### Layer 1: Generic criteria

Always applicable, regardless of content type or audience.

Consistency · Clarity · Structure · Findability

### Layer 2: Custom criteria

Configured for the specific piece of content.

Audience · Content type · Purpose · Technical depth · Other requirements

### Evaluation output

Each criterion produces a score, with optional reasoning and evidence. The scores can then be combined into an overall assessment.

One important distinction: generic does not mean the evaluation question must be identical in every context. It means the criterion applies universally. For example, clarity is always relevant, but what counts as clear writing for a beginner tutorial differs from what counts as clear writing for a specialist deep dive.

Also, I'd keep the two groups independent. Audience is a universal consideration, but its expected value is content-specific. You can therefore use it in both layers without duplicating the same evaluation.

## 2. Recommended criteria catalogue

I'd start with six generic criteria and add custom criteria only when a document has a specific requirement worth evaluating.

| Criterion         | Group    | What it measures                                                                     |
| ----------------- | -------- | ------------------------------------------------------------------------------------ |
| Clarity           | Generic  | How easily readers understand the intended meaning                                   |
| Structure         | Generic  | How logically the content is organised                                               |
| Consistency       | Generic  | Whether terminology, naming, language conventions and presentation remain consistent |
| Findability       | Generic  | How easily readers can locate relevant information and scan the content              |
| Audience fit      | Custom   | How well the content serves the defined reader, role and goal                        |
| Content-type fit  | Custom   | How well the content matches its intended format and conventions                     |
| Examples          | Optional | Whether examples make concepts easier to understand or apply                         |
| Technical depth   | Optional | Whether the level of detail matches the reader's needs                               |
| Voice             | Optional | Whether the writing has the intended and appropriate authorial character             |
| Tone              | Optional | Whether the writing's attitude and level of formality suit the context               |
| Purpose alignment | Custom   | Whether the content achieves its intended outcome                                    |

### Which criteria should be generic?

- Always include: clarity, structure, consistency and findability.
- Always define, but parameterise: audience fit and content-type fit.
- Include when relevant: examples, technical depth, voice and tone.
- Add when the goal requires it: purpose alignment, factual accuracy, completeness, actionable instructions, evidence quality, SEO or accessibility.

I would not make every item mandatory. For example, examples are useful in a tutorial but not necessarily in a short announcement. A technical article may need factual accuracy as a mandatory criterion, while a personal blog post may put more emphasis on voice.

## 3. Turn each criterion into a reusable question

Each criterion should have three parts:

- Definition: what the criterion means.
- Instructions: the question used for scoring.
- Parameters: optional context supplied for the specific content.

Here is a first draft of the question catalogue.

| Criterion         | Scoring question                                                                                                                       |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Clarity           | How easily can the intended reader understand the ideas, explanations and relationships presented in the content?                      |
| Structure         | How well does the organisation and sequence of sections support the reader's understanding and progress?                               |
| Consistency       | How consistently does the content use terminology, naming, formatting, language conventions and style?                                 |
| Findability       | How easily can readers scan the content and locate the information they need?                                                          |
| Audience fit      | How well does the content address the needs, knowledge level, role and goal of the intended audience: `{{audience}}`?                  |
| Content-type fit  | How well does the content follow the conventions and serve the purpose of the intended format: `{{type}}`?                             |
| Examples          | How effectively do the examples illustrate the concepts, demonstrate their application or help readers transfer knowledge to practice? |
| Technical depth   | How well does the depth of explanation match the audience's knowledge and the content's intended purpose?                              |
| Voice             | How consistently and appropriately does the writing express its intended authorial character: `{{voice}}`?                             |
| Tone              | How appropriately does the writing's attitude and level of formality fit the audience, subject and context: `{{tone}}`?                |
| Purpose alignment | How well does the content achieve its intended outcome: `{{purpose}}`?                                                                 |

The parameters in double braces are placeholders, not literal instructions to the evaluator. Populate them before submitting the question, or omit that criterion when the required context is unavailable.

## 4. Use descriptive score levels

The [TypeSafe Score primitive](https://docs.typesafe.ai/primitives/score?utm_source=chatgpt.com) fits this framework because each question evaluates one dimension against an ordered set of descriptive levels. It returns a score, probabilities for each level and a confidence value.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.typesafe.ai\&sz=32)

TypeSafe

I'd start with a four-level scale. It gives more room to distinguish partially successful writing without requiring an elaborate rubric.

## 0

Poor

The content substantially fails this criterion. Readers encounter significant problems that prevent or undermine the intended outcome.

## 1

Needs improvement

The content partially meets the criterion, but noticeable weaknesses make the reading experience or outcome less effective.

## 2

Good

The content meets the criterion for its intended purpose, with only minor issues that do not substantially hinder readers.

## 3

Excellent

The content meets the criterion particularly well, with clear evidence of deliberate choices that improve the reader's experience or outcome.

These are reusable starting levels, not a final rubric for every criterion. For better results, give each criterion its own concrete level descriptions. For example, the distinction between good and excellent consistency should describe observable differences in terminology and conventions, not just use stronger adjectives. TypeSafe recommends describing situations rather than abstract degrees.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.typesafe.ai\&sz=32)

TypeSafe

## 5. Define the configuration model

Keep the framework's configuration separate from the TypeSafe question objects. This gives you a reusable catalogue from which you can generate the actual scoring questions.

Here's a minimal example:

```python
GENERIC_CRITERIA = {    "clarity": {        "definition": "Ease of understanding the intended meaning.",        "instructions": (            "How easily can the intended reader understand "            "the ideas, explanations and relationships?"        ),    },    "consistency": {        "definition": (            "Consistent terminology, naming and language conventions."        ),        "instructions": (            "How consistently does the content use terminology, "            "naming, formatting and language conventions?"        ),    },}CUSTOM_CRITERIA = {    "audience_fit": {        "definition": "Fit to the intended reader and their goal.",        "instructions": (            "How well does the content serve the intended "            "audience: {audience}?"        ),        "requires": ["audience"],    },    "content_type_fit": {        "definition": "Fit to the intended content format.",        "instructions": (            "How well does the content match the conventions "            "and purpose of {content_type}?"        ),        "requires": ["content_type"],    },}SCORE_LEVELS = [    "Poor: substantially fails the criterion.",    "Needs improvement: partially meets it, "    "with noticeable weaknesses.",    "Good: meets the criterion, with minor issues.",    "Excellent: meets it particularly well, "    "with clear evidence of effective choices.",]
```

This is the framework configuration, not a complete TypeSafe integration. The integration would convert each selected criterion into a `Score` question and submit the questions together using `system_one`.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.typesafe.ai\&sz=32)

TypeSafe

## 6. Three design decisions to settle

1\. Should audience fit be generic or custom?

My recommendation: both, at different levels. The criterion itself belongs to the reusable catalogue. Its required audience definition belongs to the document configuration. This avoids maintaining two versions of the same criterion.

2\. Should voice and tone be separate?

Yes. Voice describes the writer's characteristic way of communicating. Tone describes the attitude and formality appropriate to a particular piece. However, only enable voice scoring when the intended voice is defined or can reasonably be inferred.

3\. Should you calculate one overall score?

Eventually, yes, but preserve individual scores. Normalize each score to a 0-1 range before combining it with weights, especially if different criteria use different numbers of levels. Keep confidence alongside the score, since a single aggregate can hide uncertainty or weak areas.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.typesafe.ai\&sz=32)

TypeSafe

## My recommendation for the first version

Start with six criteria: clarity, structure, consistency, findability, audience fit and content-type fit. Add purpose alignment when the content has a clearly defined goal. Keep examples, technical depth, voice and tone optional.

That is enough to test the framework on several different document types before expanding it.

The next useful step is to define the criterion schema itself: which fields every criterion must have, which are optional, and how to represent parameterised questions and scoring levels without overcomplicating the design.
