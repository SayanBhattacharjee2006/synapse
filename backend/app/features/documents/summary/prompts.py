
def get_mapper_prompt(input_text: str) -> str:
    return f"""
You are the Mapper stage of a hierarchical document summarization pipeline.

ROLE
You receive ONE consecutive section of a document.

This is NOT the final summarization stage.

Your summary will later be merged with summaries from other document sections.

Therefore your primary objective is INFORMATION RETENTION.

Compress wording, NOT knowledge.

--------------------------------------------------
WHAT TO PRESERVE
--------------------------------------------------

Always preserve:

• Main ideas
• Technical concepts
• Definitions
• Important terminology
• Algorithms
• Architectures
• Mathematical ideas
• Experimental setup
• Results
• Hyperparameters
• Important numbers
• Examples that help understanding
• Relationships between concepts

--------------------------------------------------
WHAT TO REMOVE
--------------------------------------------------

Remove only:

• Repeated sentences
• Filler
• Unnecessary explanations
• Redundant wording

Never remove important technical information.

--------------------------------------------------
GOOD EXAMPLES
--------------------------------------------------

Example 1

Input

"The Transformer replaces recurrent layers with self-attention.
Self-attention allows every token to attend to every other token.
Multi-head attention enables the model to capture different relationships simultaneously."

Good Summary

"The Transformer replaces recurrent networks with self-attention, allowing every token to attend to every other token. Multi-head attention captures multiple relationships simultaneously."

--------------------------------------------------

Example 2

Input

"Vector embeddings are dense numerical representations.
Cosine similarity is commonly used to compare embeddings.
Embedding models are trained using contrastive learning."

Good Summary

"Vector embeddings are dense numerical representations of text. Similarity between embeddings is commonly measured using cosine similarity. Embedding models are typically trained with contrastive learning."

--------------------------------------------------

Example 3

Input

"The experiment used Adam with learning rate 0.0001.
Training ran for 30 epochs.
Batch size was 64.
Validation accuracy reached 95.2%."

Good Summary

"The model was trained using Adam (learning rate 0.0001) for 30 epochs with batch size 64, achieving 95.2% validation accuracy."

--------------------------------------------------

Example 4

Input

"The paper first introduces Retrieval-Augmented Generation.
It then explains vector databases.
Finally it describes hybrid search."

Good Summary

"The section introduces Retrieval-Augmented Generation, explains vector databases, and describes hybrid search."

--------------------------------------------------

Example 5

Input

"The API authenticates users using JWT.
Every request passes through middleware.
Invalid tokens return HTTP 401."

Good Summary

"The API authenticates requests using JWT middleware, rejecting invalid tokens with HTTP 401."

--------------------------------------------------

Example 6

Input

"The cache stores frequently accessed embeddings.
Redis reduces repeated embedding generation.
This improves latency."

Good Summary

"Redis caches frequently accessed embeddings, preventing repeated embedding generation and reducing latency."

--------------------------------------------------

Example 7

Input

"The retrieval pipeline performs query embedding, vector search, reranking and context expansion before passing context to the language model."

Good Summary

"The retrieval pipeline embeds the query, performs vector search, reranks retrieved results, expands context, and provides the final context to the language model."

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------

• Produce ONE comprehensive summary.
• Keep important technical information.
• Keep important numbers.
• Keep terminology exactly.
• Do not invent information.
• Do not write bullet points.
• Do not explain your reasoning.

Return ONLY the following JSON:

{{
    "summary": "<comprehensive summary>"
}}

Document Section

{input_text}
"""

def get_intermediate_reducer_prompt(input_text: str) -> str:
    return f"""
You are the Intermediate Reducer stage of a hierarchical document summarization pipeline.

ROLE

You receive multiple summaries generated from consecutive sections of the SAME document.

Your task is NOT to aggressively compress them.

Instead, merge them into one coherent summary while preserving as much information as possible.

Think of yourself as an editor combining multiple chapter summaries into one larger chapter summary.

Information preservation is your highest priority.

--------------------------------------------------
WHAT TO PRESERVE
--------------------------------------------------

Always preserve:

• Main ideas
• Technical terminology
• Definitions
• Algorithms
• Architectures
• Mathematical concepts
• Important examples
• Experimental setup
• Results
• Hyperparameters
• Important numbers
• Relationships between concepts
• Conclusions

--------------------------------------------------
WHAT TO REMOVE
--------------------------------------------------

Remove only:

• Duplicate explanations
• Repeated sentences
• Overlapping descriptions
• Redundant wording

Never remove unique technical information.

--------------------------------------------------
GOOD EXAMPLES
--------------------------------------------------

Example 1

Input Summary 1

"The Transformer replaces recurrent neural networks with self-attention."

Input Summary 2

"Multi-head attention enables multiple attention patterns to be learned simultaneously."

Good Output

"The Transformer replaces recurrent neural networks with self-attention. Multi-head attention enables the model to learn multiple attention patterns simultaneously."

--------------------------------------------------

Example 2

Input Summary 1

"The encoder contains stacked self-attention and feed-forward layers."

Input Summary 2

"The decoder contains masked self-attention, encoder-decoder attention and feed-forward layers."

Good Output

"The Transformer architecture consists of an encoder and decoder. The encoder uses stacked self-attention and feed-forward layers, while the decoder combines masked self-attention, encoder-decoder attention and feed-forward layers."

--------------------------------------------------

Example 3

Input Summary 1

"Training uses Adam with learning rate warmup."

Input Summary 2

"The model is trained for 100,000 steps using label smoothing."

Good Output

"The model is trained using Adam with learning rate warmup for 100,000 steps and employs label smoothing during training."

--------------------------------------------------

Example 4

Input Summary 1

"Embeddings are compared using cosine similarity."

Input Summary 2

"Embeddings capture semantic meaning of text."

Good Output

"Embeddings provide dense semantic representations of text and are commonly compared using cosine similarity."

--------------------------------------------------

Example 5

Input Summary 1

"The retrieval pipeline performs vector search."

Input Summary 2

"Retrieved chunks are reranked before context expansion."

Good Output

"The retrieval pipeline performs vector search, reranks retrieved chunks and expands context before passing information to the language model."

--------------------------------------------------

Example 6

Input Summary 1

"Redis stores frequently accessed embeddings."

Input Summary 2

"Redis reduces repeated embedding computation."

Good Output

"Redis caches frequently accessed embeddings, reducing repeated embedding computation and improving latency."

--------------------------------------------------

Example 7

Input Summary 1

"The experiments compare Transformer against recurrent and convolutional models."

Input Summary 2

"The Transformer achieves better BLEU scores while requiring significantly less training time."

Good Output

"The experiments compare the Transformer with recurrent and convolutional architectures, showing higher BLEU scores while requiring significantly less training time."

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------

• Merge all summaries into one coherent document.
• Preserve every important technical detail.
• Remove only duplicated information.
• Keep terminology exactly.
• Maintain logical flow.
• Do not invent information.
• Do not explain your reasoning.
• Do not use bullet points.

Return ONLY the following JSON:

{{
    "summary": "<merged comprehensive summary>"
}}

Intermediate Summaries

{input_text}
"""

def get_final_reducer_prompt(input_text: str) -> str:
    return f"""
You are the Final Reducer stage of a hierarchical document summarization pipeline.

ROLE

You receive the final merged summary of an entire document.

Your task is to generate a comprehensive Document Profile that preserves the document's knowledge for Retrieval-Augmented Generation (RAG).

This Document Profile will later be embedded into a vector database and used to determine whether this document should be retrieved for answering user queries.

Therefore:

Do NOT optimize for brevity.

Optimize for INFORMATION RETENTION.

Compress wording only when it does not remove knowledge.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

Generate a rich document profile that captures the complete knowledge contained in the document.

Someone reading only this profile should understand:

• What the document is about
• What problems it solves
• What concepts it introduces
• What methods or algorithms it describes
• What important findings it presents
• What terminology appears throughout the document

--------------------------------------------------
INCLUDE
--------------------------------------------------

Whenever applicable preserve:

• Purpose of the document
• Main problem
• Core concepts
• Definitions
• Technical terminology
• Algorithms
• Architectures
• Pipelines
• Mathematical ideas
• Important equations (described naturally)
• Experimental setup
• Results
• Important numbers
• Hyperparameters
• Design decisions
• Advantages
• Limitations
• Future work
• Relationships between concepts

--------------------------------------------------
REMOVE
--------------------------------------------------

Remove ONLY:

• Duplicate explanations
• Repeated wording
• Repeated conclusions

Never remove unique information.

--------------------------------------------------
GOOD EXAMPLES
--------------------------------------------------

Example 1

Input

"The document explains Retrieval-Augmented Generation. It discusses dense embeddings, sparse retrieval, reranking and context expansion."

Good Output Summary

"The document introduces Retrieval-Augmented Generation (RAG), explaining how external knowledge improves language model responses. It describes dense embeddings, sparse retrieval, reranking and context expansion as successive stages of the retrieval pipeline, highlighting how each contributes to retrieving relevant context before generation."

Topics

- Retrieval-Augmented Generation
- Dense Embeddings
- Sparse Retrieval
- Reranking
- Context Expansion

--------------------------------------------------

Example 2

Input

"The paper proposes the Transformer architecture. It replaces recurrence with self-attention. The model achieves state-of-the-art translation performance."

Good Output Summary

"The document presents the Transformer architecture for sequence modelling. It replaces recurrent neural networks with self-attention mechanisms, enabling efficient parallel computation and improved modelling of long-range dependencies. The architecture consists of encoder and decoder stacks using multi-head attention and feed-forward layers, achieving state-of-the-art machine translation performance."

Topics

- Transformer
- Self-Attention
- Multi-Head Attention
- Machine Translation
- Sequence Modelling

--------------------------------------------------

Example 3

Input

"The report explains vector databases, embeddings, indexing and similarity search."

Good Output Summary

"The document explains how vector databases store dense numerical representations of data and perform efficient semantic retrieval. It discusses embedding generation, vector indexing, approximate nearest neighbour search and similarity metrics such as cosine similarity, illustrating how these components enable scalable semantic search."

Topics

- Vector Database
- Embeddings
- Approximate Nearest Neighbour
- Cosine Similarity
- Semantic Search

--------------------------------------------------

Example 4

Input

"The document explains JWT authentication, middleware and role-based authorization."

Good Output Summary

"The document describes a JWT-based authentication system in which requests are validated by middleware before accessing protected resources. It explains token verification, user authentication, authorization and role-based access control."

Topics

- JWT
- Authentication
- Authorization
- Middleware
- RBAC

--------------------------------------------------

Example 5

Input

"The paper evaluates several neural architectures and concludes that attention-based models outperform recurrent models while requiring less training time."

Good Output Summary

"The document compares multiple neural architectures and demonstrates that attention-based models outperform recurrent approaches while significantly reducing training time. Experimental evaluation supports the effectiveness of attention mechanisms for sequence modelling."

Topics

- Attention Mechanism
- Neural Networks
- Sequence Modelling
- Experimental Evaluation
- Performance Comparison

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------

Summary:

• Comprehensive and information-rich.
• Preserve important technical details.
• Maintain logical flow.
• Preserve terminology exactly.
• Do not invent information.
• Do not explain your reasoning.
• Do not use bullet points inside the summary.
• The summary should naturally scale with the document size. Large technical documents should produce longer summaries than small documents.

Topics:

Generate 5–15 concise technical topics.

Topics should:

• be noun phrases
• preserve important terminology
• avoid full sentences
• avoid generic words such as "Technology", "Research", "Computer", "Paper"

Return ONLY the following JSON:

{{
    "summary": "<comprehensive document profile>",
    "topics": [
        "Topic 1",
        "Topic 2",
        "Topic 3"
    ]
}}

Merged Document Summary

{input_text}
"""

