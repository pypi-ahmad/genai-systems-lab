# Weekly Learning Log

This week reinforced the difference between recall and usefulness in retrieval systems. High-similarity chunks are not always the chunks a user needs. Notes with concrete decisions, dates, and owners consistently beat generic background material.

I also noticed that generated insights become repetitive if the retrieved set contains near-duplicate chunks. Deduplication before summarization would likely improve both summary quality and memory usefulness.

Useful pattern: ask the model for contradictions, dependencies, and unanswered questions instead of a generic summary. That framing produced more valuable cross-document insights during tests.

Next experiment: rank chunks with a blend of semantic similarity, exact-term overlap, and source recency, then compare answer quality against pure embedding search.