from app.ai.schema import RouterType


def get_answer_eval_prompt(
    question: str,
    expected_answer: str,
    answer: str,
    router: RouterType,
    retrieved_context: str | None = None,
    web_context: str | None = None,
) -> str:

    base_prompt = f"""
You are an expert evaluator for an AI question-answering system.

Your task is to evaluate a generated answer against the question,
the expected answer, and the available evidence.

You must return a structured evaluation using the AnswerEvalSchema.

EVALUATION CRITERIA

1. Correctness (0-5)

Evaluate how accurately the generated answer answers the question
compared with the expected answer.

5 = Completely correct. The answer accurately provides the expected
    information and contains no meaningful factual errors.

4 = Mostly correct. The main answer is correct but contains a minor
    error, omission, or imprecision.

3 = Partially correct. The answer contains some correct information
    but misses or incorrectly states an important part.

2 = Mostly incorrect. The answer contains limited correct information
    but has substantial errors.

1 = Almost completely incorrect. The answer provides little useful
    correct information.

0 = Completely incorrect, contradictory, or does not answer the question.

Do not require the generated answer to use the same wording as the
expected answer. Judge semantic correctness.

2. Relevance (0-5)

Evaluate how directly the generated answer addresses the question.

5 = Direct, focused, and completely addresses the question.
4 = Directly answers the question with minor unnecessary information.
3 = Generally relevant but somewhat incomplete or contains noticeable
    irrelevant information.
2 = Only partially addresses the question.
1 = Barely addresses the question.
0 = Does not address the question.

3. Groundedness (0-5 or null)

Evaluate whether factual claims in the generated answer are supported
by the provided evidence.

5 = All important factual claims are clearly supported by the evidence.
4 = Almost all important claims are supported, with only minor
    unsupported details.
3 = Some important claims are supported, but some are unsupported.
2 = Many important claims are unsupported by the evidence.
1 = Almost entirely unsupported by the evidence.
0 = The answer contradicts the evidence or is completely ungrounded.

If the selected route is NONE, groundedness is not applicable and MUST
be returned as null.

4. Overall (0-5)

Give an overall assessment of the generated answer considering
correctness, relevance, and groundedness when applicable.

5 = Excellent
4 = Good
3 = Acceptable
2 = Poor
1 = Very poor
0 = Completely unacceptable

GENERAL RULES

- Compare the generated answer with the expected answer when judging
  correctness.
- Use the provided evidence only when judging groundedness.
- Do not penalize an answer for being concise.
- Do not require the answer to match the expected answer word-for-word.
- Do not invent evidence that is not provided.
- Do not use outside knowledge to establish groundedness.
- A generated answer can be correct even if it is phrased differently
  from the expected answer.
- If the evidence does not support a claim, treat that claim as
  unsupported for the groundedness score.
- Keep the evaluation reason concise and specific.

INPUTS

Question:
{question}

Expected answer:
{expected_answer}

Generated answer:
{answer}

Selected route:
{router.value}
"""

    if router == RouterType.NONE:
        return f"""
{base_prompt}

ROUTE-SPECIFIC INSTRUCTIONS

The selected route is NONE.

No document retrieval or web retrieval was required.

Evaluate:
- Correctness against the expected answer.
- Relevance to the question.

Groundedness is NOT APPLICABLE.
Therefore:

groundedness = null

Do not attempt to evaluate grounding using outside knowledge.
"""

    if router == RouterType.RAG:
        return f"""
{base_prompt}

ROUTE-SPECIFIC INSTRUCTIONS

The selected route is RAG.

The generated answer is expected to be supported by the retrieved
document context below.

Retrieved document context:
---------------------------
{retrieved_context or "[No retrieved context available]"}
---------------------------

Evaluate groundedness by checking whether the claims made in the
generated answer are supported by this retrieved document context.

Groundedness MUST be evaluated.
"""

    if router == RouterType.WEB:
        return f"""
{base_prompt}

ROUTE-SPECIFIC INSTRUCTIONS

The selected route is WEB.

The generated answer is expected to be supported by the web-search
context below.

Web context:
---------------------------
{web_context or "[No web context available]"}
---------------------------

Evaluate groundedness by checking whether the claims made in the
generated answer are supported by this web context.

Groundedness MUST be evaluated.
"""

    if router == RouterType.BOTH:
        return f"""
{base_prompt}

ROUTE-SPECIFIC INSTRUCTIONS

The selected route is BOTH.

The generated answer may use information from both the retrieved
document context and the web-search context.

Retrieved document context:
---------------------------
{retrieved_context or "[No retrieved context available]"}
---------------------------

Web context:
---------------------------
{web_context or "[No web context available]"}
---------------------------

Evaluate groundedness against the combination of both contexts.

A claim is considered grounded if it is supported by either the
retrieved document context or the web context.

Groundedness MUST be evaluated.
"""

    raise ValueError(f"Unsupported router type: {router}")