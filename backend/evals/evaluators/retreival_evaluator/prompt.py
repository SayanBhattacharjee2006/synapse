def get_retrieval_eval_prompt(
    question: str,
    reference_answer: str,
    retrieved_context: str | None,
    reference_evidence: dict | None,
) -> str:

    return f"""
You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.

Your task is to evaluate the quality of the retrieved document context for a
specific user question.

You are NOT evaluating the generated answer.

You are evaluating ONLY whether the retrieved context is relevant and
sufficient for answering the question.

--------------------------------------------------
QUESTION
--------------------------------------------------

{question}

--------------------------------------------------
REFERENCE ANSWER
--------------------------------------------------

{reference_answer}

The reference answer represents the information that a correct retrieval
should make possible to answer.

--------------------------------------------------
EXPECTED REFERENCE EVIDENCE
--------------------------------------------------

{reference_evidence}

This identifies the expected source of the evidence when available.

--------------------------------------------------
RETRIEVED CONTEXT
--------------------------------------------------

{retrieved_context}

--------------------------------------------------
YOUR TASK
--------------------------------------------------

Evaluate the retrieved context using two metrics:

1. RELEVANCE
2. COMPLETENESS

Both metrics must be scored independently on a 0-5 scale.

--------------------------------------------------
1. RELEVANCE
--------------------------------------------------

Measure how relevant the retrieved context is to the user's question.

Ask:

- Does the retrieved context contain information directly related to the
  question?
- Does it discuss the entities, concepts, facts, values, or relationships
  needed to answer the question?
- Is the retrieved information useful rather than merely sharing superficial
  keywords with the question?
- Is most of the retrieved context relevant, or is it mostly unrelated noise?

Scoring:

0 = Completely irrelevant.
    The retrieved context has no useful information for answering the question.

1 = Very low relevance.
    The context is mostly unrelated and provides little useful information.

2 = Low relevance.
    Some information is related to the question, but most of the useful
    information is missing or unrelated.

3 = Moderate relevance.
    The context contains meaningful information related to the question,
    but also contains noticeable irrelevant information or misses important
    aspects.

4 = High relevance.
    The context is directly relevant and contains most of the information
    needed for the question, with only minor irrelevant material or omissions.

5 = Excellent relevance.
    The retrieved context is directly and specifically relevant to the
    question and contains the key information required to answer it.

--------------------------------------------------
2. COMPLETENESS
--------------------------------------------------

Measure whether the retrieved context contains enough information to fully
answer the question.

Do NOT judge completeness based on whether the generated answer is correct.

Instead, determine whether the retrieved context itself contains the evidence
necessary to derive the reference answer.

Ask:

- Can the reference answer be derived from the retrieved context?
- Are all important facts, values, entities, dates, relationships, or
  calculations required by the question present?
- If the question asks for multiple pieces of information, are all of them
  present?
- Is important evidence missing?
- Would an answer generated using ONLY the retrieved context be able to
  correctly answer the question?

Scoring:

0 = No required evidence is present.
    The question cannot be answered from the retrieved context.

1 = Almost completely incomplete.
    Only extremely minor or incidental information is present and the answer
    cannot reasonably be derived.

2 = Partially complete.
    Some required information is present, but important evidence is missing.

3 = Mostly complete.
    The retrieved context contains most of the required evidence, but one or
    more meaningful pieces of information are missing or ambiguous.

4 = Nearly complete.
    The retrieved context contains essentially all required evidence, with
    only minor omissions that do not substantially prevent answering.

5 = Fully complete.
    The retrieved context contains all information necessary to derive the
    reference answer confidently.

--------------------------------------------------
IMPORTANT EVALUATION RULES
--------------------------------------------------

1. Evaluate the RETRIEVED CONTEXT, not the generated answer.

2. Do not give a high score merely because the retrieved context contains
   similar keywords.

3. Semantic relevance is more important than keyword overlap.

4. If the retrieved context contains the exact fact required by the question,
   this strongly supports a high relevance and completeness score.

5. If the retrieved context discusses the correct topic but does not contain
   the specific fact needed to answer the question, relevance may be high but
   completeness must be reduced.

6. If the question asks for a specific number, date, name, percentage, ranking,
   amount, or other precise fact, that specific information must be present in
   the retrieved context for completeness to receive a high score.

7. If the question requires multiple facts, all required facts must be present
   for a completeness score of 5.

8. If the retrieved context is empty or None:
   - relevance = 0
   - completeness = 0

9. Do not use outside knowledge to compensate for missing retrieved context.

10. Do not assume that information exists in the source document simply
    because the reference answer contains it.

11. Judge only the evidence actually present in RETRIEVED CONTEXT.

12. The reference answer is used to determine what information should have
    been retrieved. It is NOT itself evidence.

13. The reference evidence is additional guidance about the expected source.
    Do not assume that the expected evidence was successfully retrieved.

14. If the retrieved context contains enough evidence to derive the reference
    answer even if it does not reproduce the exact wording of the reference
    answer, give appropriate credit.

15. If retrieved context contains contradictory information, reduce the
    completeness and/or relevance score depending on how seriously the
    contradiction affects answering the question.

--------------------------------------------------
EXAMPLES
--------------------------------------------------

Example 1:

Question:
"What percentage of Bundesliga revenue was accounted for by UCL revenue?"

Reference answer:
"6.4%."

Retrieved context:
"The total UCL revenue equals 6.4% of the total overall revenue
(excluding transfers) of the Bundesliga."

Evaluation:
relevance = 5
completeness = 5

Reason:
The retrieved context directly contains the exact fact required to answer
the question.

--------------------------------------------------

Example 2:

Question:
"How much revenue did Bayern Munich receive from the UCL?"

Reference answer:
"Bayern Munich received €172.929 million."

Retrieved context:
"Bayern Munich participated in the UEFA Champions League during several
seasons and won the competition in 2000/01."

Evaluation:
relevance may be 3 or 4,
completeness must be low because the required revenue amount is absent.

--------------------------------------------------

Example 3:

Question:
"What was the peak Bundesliga transfer expenditure and in which season?"

Reference answer:
"2002/03, at €192.816 million."

Retrieved context:
"Transfer expenditure increased significantly during the period."

Evaluation:
The context is related to the question, so relevance may be moderate,
but completeness must be low because neither the peak season nor the
€192.816 million figure is present.

--------------------------------------------------

Example 4:

Question:
"What is 15% of 240?"

Retrieved context:
None.

Evaluation:
relevance = 0
completeness = 0

--------------------------------------------------

FINAL INSTRUCTION
--------------------------------------------------

Return ONLY the structured evaluation output.

Do not answer the user's question.

Do not provide information that is not present in the retrieved context.

Do not use external knowledge.

Score relevance and completeness independently from 0 to 5.
"""