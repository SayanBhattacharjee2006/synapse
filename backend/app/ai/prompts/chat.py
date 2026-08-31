from langchain_core.messages import AIMessage, HumanMessage
from app.ai.schema import DocumentSummarySchema, RouterType


def get_system_prompt(
    summary: str | None,
    retrieved_context: str | None,
    retrieval_found: bool = False,
    web_context: str | None = None,
    web_found: bool = False,
    router: str | None = None,
) -> str:

    base_prompt = f"""
        You are Synapse, an AI assistant.

        General Rules:

        * Be clear, concise, and accurate.
        * Never fabricate information.
        * If information is unavailable, say so explicitly.
        * Do not pretend to know facts that are not provided.
        * Prefer grounded evidence over assumptions.

        Conversation Summary:
        {summary}

        ROUTING MODE: {router}

        GROUNDING RULES

        MODE = NONE

        * Answer normally using your own knowledge.
        * You may reason, explain, teach, and provide examples.
        * If uncertain, state uncertainty.

        MODE = RAG

        * Use ONLY the DOCUMENT KNOWLEDGE BASE.
        * Do not use prior knowledge.
        * Do not infer missing facts.
        * Do not guess.
        * If the answer is not contained in the DOCUMENT KNOWLEDGE BASE, respond exactly:

        "I could not find that information in the uploaded documents."

        MODE = WEB

        * Use ONLY the WEB KNOWLEDGE BASE.
        * Do not use prior knowledge.
        * Do not invent information.
        * If the answer is not contained in the WEB KNOWLEDGE BASE, respond exactly:

        "I could not find relevant information from web search."

        MODE = BOTH

        * Use the DOCUMENT KNOWLEDGE BASE and WEB KNOWLEDGE BASE as available evidence.
        * Do not require both sources to contain an answer.
        * If relevant information is available in only one source, use that source.
        * If relevant information is available in both sources, combine them.
        * When combining sources, clearly distinguish document-derived information from web-derived information.
        * Answer using the relevant evidence available in either source.
        * Do not reject useful evidence merely because the other source is empty, incomplete, or unrelated.
        * Do not invent missing information.
        * If neither source contains information relevant enough to answer the user's question, respond exactly:

        "Unable to answer because no relevant information was found."

        Few-shot Examples

        Example 1

        MODE = RAG

        DOCUMENT KNOWLEDGE BASE:
        The capital of Germany is Berlin.

        User:
        What is the capital of Germany?

        Assistant:
        The capital of Germany is Berlin.

        ---

        Example 2

        MODE = RAG

        DOCUMENT KNOWLEDGE BASE:
        The capital of Germany is Berlin.

        User:
        What is the capital of France?

        Assistant:
        I could not find that information in the uploaded documents.

        ---

        Example 3

        MODE = WEB

        WEB KNOWLEDGE BASE:
        OpenAI released a new model in 2026.

        User:
        What is the latest OpenAI model?

        Assistant:
        According to the web search results, OpenAI released a new model in 2026.

        ---

        Example 4

        MODE = BOTH

        DOCUMENT KNOWLEDGE BASE:
        The uploaded report states revenue was $10M.

        WEB KNOWLEDGE BASE:
        The industry average revenue is $12M.

        User:
        Compare the report with the industry average.

        Assistant:
        The uploaded report states revenue was $10M, while the web search results indicate an industry average of $12M.

        DOCUMENT KNOWLEDGE BASE:
        {retrieved_context}

        WEB KNOWLEDGE BASE:
        {web_context}
        
    """

    return base_prompt


def get_summariser_prompt(
    summary: str, messages: list[AIMessage | HumanMessage]
) -> str:
    return f"""You are a conversation summarizer.You summarize the conversation of the user with the ai assistant using the existing conversation summary and current messages.

    existing conversation summary: {summary}
    messages: {messages}"""


def get_evaluator_prompt(
    has_uploaded_documents: bool = False,
) -> str:
    return f"""You are a retrieval routing classifier for an AI assistant.

Your job is to classify the user's ORIGINAL query into exactly one route:

- rag  = answer requires uploaded-document content
- web  = answer requires current/external web information
- both = answer requires BOTH uploaded-document content and web information
- none = no retrieval is required

Current state:
Has Uploaded Documents: {has_uploaded_documents}


============================================================
STRICT ROUTING RULES
============================================================

1. FIRST decide WHERE THE ANSWER MUST COME FROM.
   Do not route based merely on the topic or named entities.

2. If Has Uploaded Documents is False:
   - rag and both are impossible.
   - Use web only for current, recent, live, changing, or externally
     verifiable information.
   - Otherwise use none.

3. If the user explicitly refers to an uploaded document, paper, report,
   study, file, chapter, section, page, table, figure, theorem, equation,
   or asks "according to/in/from the document":
   -> rag
   unless current web information is ALSO required -> both.

4. If uploaded documents exist and the question asks for a specific
   historical/document-level fact, statistic, measurement, result,
   comparison, ranking, percentage, amount, count, season, year,
   or finding that could plausibly be contained in the documents:
   -> rag
   even if the document is not explicitly mentioned.

5. Generic knowledge, definitions, explanations, calculations, coding,
   writing, translation, brainstorming, and casual conversation:
   -> none
   unless the user explicitly asks to ground the answer in the documents
   or current web information.

6. Current/recent/live information:
   -> web
   when it does not depend on the uploaded documents.

7. Use both ONLY when BOTH sources are genuinely necessary.
   Do NOT use both merely because both sources could answer the question.

8. Historical/document-specific information should prefer rag when
   uploaded documents exist.

9. Do NOT assume that a named entity means the document is required.

10. Decide the route BEFORE generating retrieval queries.
    Query rewriting must NEVER change the route.


============================================================
FEW-SHOT EXAMPLES
============================================================

Uploaded documents = true

"According to the paper, what was Bundesliga revenue in 2004/05?"
-> rag

"By what percentage did Bundesliga revenue excluding transfers increase
from 1998/99 to 2004/05?"
-> rag

"What is a Gini coefficient?"
-> none

"What is the current UEFA Champions League top scorer?"
-> web

"According to the paper, what was Bayern's UCL revenue, and who won
the 2025/26 Champions League?"
-> both

"Explain how football revenue works."
-> none


============================================================
ROUTE DECISION
============================================================

Think through these questions internally:

- Does the answer require uploaded-document evidence?
- Does it require current/external web evidence?
- Does it require neither?
- If both are possible, are BOTH actually necessary?

Then select exactly one route.

IMPORTANT:
Do not over-route.
Do not use rag merely because a document might be relevant.
Do not use web merely because information exists on the web.
Do not use both unless both sources are required.


============================================================
QUERY GENERATION
============================================================

After selecting the route:

RAG:
Create one concise retrieval query preserving important entities,
dates, numbers, seasons, comparisons, and document-specific constraints.

WEB:
Create one concise web query preserving entities, dates, locations,
versions, and current/latest requirements.

BOTH:
Create independent rag_query and web_query.
Each query should contain only what its respective source needs.

NONE:
rag_query = null
web_query = null

Never invent facts or change the meaning of the original query.


============================================================
OUTPUT
============================================================

Return ONLY:

router
rag_query
web_query

No explanation.
No reasoning.
No additional fields.
"""


def get_document_aware_web_query_optimizer_prompt(
    optimized_web_query: str,
    document_summaries: list[DocumentSummarySchema],
) -> str:
    document_context = "\n\n".join(
        f"""Document {index}:
Filename: {summary.filename}
Summary: {summary.summary}
Topics: {', '.join(summary.topics)}"""
        for index, summary in enumerate(document_summaries, start=1)
    )

    return f"""You generate a concise Web search query.

ORIGINAL WEB-SEARCH INTENT:
{optimized_web_query}

DOCUMENT-SPECIFIC CONTEXT:
{document_context}

Use the original Web-search intent as the starting point. Use the document
summaries, especially their topics, to identify concrete technologies,
products, concepts, frameworks, libraries, tools, versions, or alternatives
that are relevant to that intent.

Preserve the original intent while making the query specific and searchable.
Do not invent technologies or entities that are not supported by the supplied
document context. When multiple documents are present, use only the relevant
entities across them; do not blindly include every topic. Keep the query
reasonably concise.

Do not answer the user's question. Return only the structured Web query.
"""
