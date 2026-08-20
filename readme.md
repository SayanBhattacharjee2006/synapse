# Synapse

> An end-to-end AI assistant built with LangGraph that dynamically
> routes user queries between direct reasoning, uploaded-document
> retrieval, web search, or a combination of both.

## Overview

Synapse is a retrieval-aware AI assistant that selects the appropriate
information source for each query:

-   **`none`** --- no retrieval required.
-   **`rag`** --- retrieve information from uploaded documents.
-   **`web`** --- retrieve current or time-sensitive information from
    the web.
-   **`both`** --- combine uploaded-document retrieval with web
    information.

The project also includes an automated evaluation framework using a
golden dataset and LLM-based evaluators for routing, retrieval, and
answer quality.

## Architecture

``` text
User Query
    |
    v
LangGraph
    |
    +--> Router / Evaluator
             |
             +--> none
             |
             +--> rag --> Query Optimizer --> Retriever
             |
             +--> web --> Web Search
             |
             +--> both --> Document Retrieval + Web Search
                              |
                              v
                         Answer LLM
                              |
                              v
                           Response
```

## Core Capabilities

### Intelligent routing

The router classifies queries into four strategies:

  -----------------------------------------------------------------------
  Route                               Purpose
  ----------------------------------- -----------------------------------
  `none`                              Direct questions, reasoning,
                                      coding, mathematics, and other
                                      queries that do not require
                                      retrieval

  `rag`                               Questions requiring information
                                      from uploaded documents

  `web`                               Questions requiring current or
                                      changing information

  `both`                              Questions requiring both
                                      uploaded-document information and
                                      current web information
  -----------------------------------------------------------------------

### Document-aware question answering

Queries requiring information from uploaded files use the RAG pipeline
to retrieve relevant document context before answer generation.

### Web-aware question answering

Queries involving current or changing information can be routed to web
retrieval instead of relying on potentially stale model knowledge.

### Combined retrieval

Queries requiring both document-specific and current external
information can use the `both` route.

### Query optimization

Retrieval queries can pass through a query-optimization stage before
document retrieval.

### Observability

LangSmith tracing provides visibility into:

-   LangGraph runs
-   Individual graph nodes
-   LLM calls
-   Query optimization
-   Retrieval
-   Latency
-   Token usage
-   Cost

## Evaluation Framework

Synapse evaluates the **actual end-to-end LangGraph application**
against a golden dataset.

Each test case contains:

``` json
{
  "question": "...",
  "expected_route": "rag",
  "reference_answer": "...",
  "reference_evidence": {
    "doc": ["..."],
    "web": []
  }
}
```

### Evaluation flow

``` text
Golden Dataset
      |
      v
Evaluation Runner
      |
      v
Actual Synapse Graph
      |
      +--> Router
      +--> Query Optimizer
      +--> Retriever / Web Search
      +--> Answer Generation
      |
      v
Evaluation Layer
      |
      +--> Router Evaluation
      +--> Answer Evaluation
      +--> Retrieval Evaluation
      |
      v
Result Aggregator
      |
      +--> Global Metrics
      +--> Per-route Metrics
      +--> Failure Reports
      |
      v
JSON Result
```

## Metrics

### Router accuracy

Router accuracy measures whether the predicted route matches the
expected route.

``` text
Router Accuracy =
(correctly routed tests / total tests) × 100
```

### Answer evaluation

Answer quality is scored from **0 to 5**:

  -----------------------------------------------------------------------
  Metric                              Meaning
  ----------------------------------- -----------------------------------
  **Correctness**                     How accurately the generated answer
                                      matches the reference answer

  **Relevance**                       How directly and appropriately the
                                      answer addresses the question

  **Groundedness**                    How well the answer is supported by
                                      provided retrieval context; `None`
                                      when grounding is not applicable

  **Overall**                         Overall quality of the generated
                                      answer
  -----------------------------------------------------------------------

### Retrieval evaluation

Retrieval quality is scored from **0 to 5**:

  -----------------------------------------------------------------------
  Metric                              Meaning
  ----------------------------------- -----------------------------------
  **Retrieval Relevance**             How relevant the retrieved context
                                      is to the question

  **Retrieval Completeness**          How completely the retrieved
                                      context supports the information
                                      required to answer the question
  -----------------------------------------------------------------------

### Per-route metrics

Metrics are aggregated separately for:

``` text
none
rag
web
both
```

This exposes route-specific weaknesses that can be hidden by global
averages.

### Failure reporting

The evaluation pipeline reports:

-   Router failures
-   Answer failures
-   Low-groundedness answers
-   Low-relevance answers
-   Low retrieval relevance
-   Low retrieval completeness

Evaluation results are persisted as JSON artifacts under:

``` text
evals/results/
```

## Current Evaluation Baseline

Current benchmark:

  Metric                             Result
  -------------------------- --------------
  **Router Accuracy**               **98%**
  **Average Correctness**      **4.64 / 5**
  **Average Relevance**        **4.72 / 5**
  **Average Groundedness**     **4.61 / 5**
  **Average Overall**          **4.64 / 5**

These values are the current quality baseline and should be updated if
the benchmark or evaluation methodology changes.

## LangSmith

LangSmith is used for tracing and observability of the application and
evaluation runs.

It provides visibility into:

-   End-to-end latency
-   Router/evaluator latency
-   Query-optimizer latency
-   Retrieval latency
-   LLM latency
-   Token consumption
-   Estimated cost
-   Individual inputs and outputs

The evaluation dataset is also uploaded to LangSmith for experiment
tracking.

## Performance

Initial traces show that latency is currently concentrated in several
pipeline stages, especially document retrieval, routing/evaluator calls,
and query optimization.

Latency optimization is treated separately from the quality benchmark so
that improvements can be measured without losing the current evaluation
baseline.

## Project Structure

``` text
backend/
├── app/
│   ├── ai/
│   │   └── graph/
│   ├── core/
│   ├── features/
│   ├── integrations/
│   └── ...
│
├── evals/
│   ├── datasets/
│   │   └── golden.jsonl
│   ├── evaluators/
│   │   ├── answer_evaluator/
│   │   ├── router_evaluator/
│   │   └── retrieval_evaluator/
│   ├── runner/
│   │   └── eval_runner.py
│   ├── results/
│   │   └── evaluation_*.json
│   ├── eval_orchestrator.py
│   └── result.py
│
└── ...
```

## Running the Evaluation

The evaluation entry point is:

``` bash
python -m evals.eval_orchestrator
```

The pipeline:

1.  Validates the golden dataset.
2.  Uploads the dataset to LangSmith.
3.  Runs the real Synapse graph for each test case.
4.  Evaluates routing, answer quality, and retrieval quality.
5.  Calculates global and per-route metrics.
6.  Generates failure reports.
7.  Persists the result as JSON.

## Evaluation Philosophy

Synapse evaluates the system at three complementary levels:

``` text
Routing
  -> Did the system choose the correct information source?

Retrieval
  -> Did it retrieve useful and sufficiently complete information?

Answer
  -> Did it produce a correct, relevant, and grounded response?
```

This provides more useful diagnostics than evaluating only the final
generated answer.


## Technology

The current implementation uses technologies including:

-   Python
-   LangGraph
-   Pydantic
-   PostgreSQL
-   LangSmith
-   LLM-based structured evaluation
-   RAG / document retrieval
-   Web retrieval

Model, embedding, vector-store, and deployment details can be added
during final project cleanup.

## Status

**Current status: Functional evaluation pipeline with strong benchmark
performance.**

The current quality baseline is **98% router accuracy** with
approximately **4.6/5 answer quality**. The next engineering focus is
reducing latency while preserving this quality baseline.
