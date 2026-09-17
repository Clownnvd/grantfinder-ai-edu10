# Architecture — GrantFinder AI

## System overview

```mermaid
flowchart LR
  R[Researcher] --> UI[Next.js 16]
  M[Research manager] --> UI
  UI --> API[FastAPI BFF]
  API --> LG[LangGraph runtime]
  LG --> RET[Hybrid retrieval]
  RET --> PG[(PostgreSQL + pgvector)]
  LG --> EL[Deterministic eligibility]
  LG --> RR[Reranker]
  LG --> H1[Researcher checkpoint]
  H1 --> D[Grounded draft]
  D --> GUARD[Output guard]
  GUARD --> H2[Research-office checkpoint]
  PG --> G[Grants.gov]
  PG --> N[NAFOSTED]
```

## Match graph

```mermaid
flowchart TD
  S([START]) --> A[search_opportunities]
  A -->|có ứng viên| B[check_eligibility]
  A -->|không có căn cứ| X[handle_no_results]
  B --> C[rerank_candidates]
  C --> H[request_researcher_review]
  H --> E([END / waiting_for_human])
  X --> E2([END / refine_profile])
```

## Draft graph

```mermaid
flowchart TD
  S([START]) --> A[load_grounded_opportunity]
  A -->|không tồn tại| F[draft_failed]
  A --> B[check_researcher_confirmation]
  B -->|chưa xác nhận| H1[researcher_confirmation_required]
  B -->|đã xác nhận| C[build_proposal_draft]
  C --> D[optional_grounded_llm_rewrite]
  D --> G[validate_draft_output]
  G -->|guard pass| H2[request_research_office_review]
  G -->|guard fail| F
  H1 --> E([END])
  H2 --> E
  F --> E
```

## State và persistence

- Mỗi run có `thread_id`, checkpoint và tool trace.
- Local/test dùng `InMemorySaver`.
- Production đặt `LANGGRAPH_CHECKPOINT_BACKEND=postgres`; `PostgresSaver` dùng cùng PostgreSQL với pgvector.
- Serializer chỉ cho phép các model nội bộ đã khai báo và bật `LANGGRAPH_STRICT_MSGPACK=true`.

## Ranh giới trách nhiệm

| Thành phần | Chịu trách nhiệm |
|---|---|
| Next.js | Nhập hồ sơ, hiển thị shortlist, citation, trace và cổng duyệt |
| FastAPI | Validation, role gate, API contract, lỗi HTTP |
| LangGraph | State, nodes, conditional routing, checkpoint, trace |
| PostgreSQL/pgvector | Hard fields, JSON gốc, full-text và vector search |
| Deterministic rules | Deadline, budget ceiling, applicant type, eligibility sơ bộ |
| LLM tùy chọn | Viết lại draft trong context đã khóa; không quyết định hard facts |
