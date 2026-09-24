---
name: building-with-zep
description: Guide for building, designing, reviewing, evaluating, and troubleshooting applications that use Zep — the unified context layer for enterprise data. Zep combines business data, documents, and conversations into shared, governed temporal Context Graphs that agents retrieve from, for three solutions: enterprise context graphs (shared project/product/domain knowledge), agent memory (one user's conversations, activity, and preferences), and customer and account context (personal plus shared account records for one task). Use whenever you write or design code that integrates Zep — giving an agent context or long-term memory, building a shared Context Graph for a team, product, or domain, unifying customer/account data for an agent, ingesting chat/business/document/JSON data into a Context Graph, retrieving a Context Block or searching the graph, choosing between user graphs and shared graphs (graph_id), scoping graphs, defining a custom ontology or custom instructions, applying access policies to context, or deciding how to evaluate and tune Zep for a use case. Triggers on developer requests like "implement Zep for my agent", "integrate Zep into my agent", "add Zep memory to my chatbot", "build a Zep Context Graph for our product docs", "give my support agent account context with Zep", "write an ingestion pipeline for Zep", "implement Zep retrieval as a tool call", "add graph.search to my agent", "set up a Zep ontology", "how should I structure my Zep graphs", "scope Zep access with API key policies", "why is Zep not returning the right context", or "help me evaluate Zep for my use case". Do not trigger for an end user asking an agent to remember, store, or look up something in its own memory; that is the running application, not an implementation task.
---

# Building with Zep

This skill is the **decision-and-workflow layer** for building on Zep: how to
reason about Zep, choose a solution, scope graphs, ingest data, shape the
graph, retrieve context, govern access, and evaluate whether Zep delivers your
use case. It is **not** an API reference or a full
best-practices manual — for exact, current details (method names, parameters,
limits, plan availability) and the complete best practices for any given
feature, query the **`zep-docs` MCP server** first — preferring to load the
whole relevant page (see
[Documentation index](#documentation-index) for how to read pages vs. search). If
it is unavailable, use [help.getzep.com](https://help.getzep.com) and the
[SDK/API reference](https://help.getzep.com/sdk-reference). If this skill and the
live docs ever disagree, **the live docs win** (see [Source authority](#source-authority-and-validation)).

Work backward from the **end use case and the business value** it must deliver.
Agents cannot complete a task correctly when essential context is missing.
Success is whether the agent receives **complete context** and produces
**accurate answers** for that use case — not whether the graph is perfect or the
ingested data is perfect.

> Guidance here targets **Zep V3** (SDK packages `zep-cloud` for
> Python/TypeScript, `github.com/getzep/zep-go/v3` for Go). Ignore the legacy V2
> `Memory` API. Zep is a paid product; some features are plan-gated — confirm
> availability in the docs.

## Conceptual overview

**Zep is the unified context layer for enterprise data.** Context is the
information an agent needs to complete a task. Zep combines business data,
documents, and conversations into **shared, governed context** that agents and
applications retrieve, organized as **temporal Context Graphs**. *You* control
the data that goes in and the context retrieved out. A graph **fuses many data
sources** — conversations, emails, Slack, documents, transcripts, user
interactions, business records, events — into one time-aware picture of a
subject (a user, customer, account, project, product, or business domain). The
**Context Lake** manages and serves many such graphs as one system, with
governance over who can manage Zep and what context each agent can retrieve.
See [Unified context](https://help.getzep.com/concepts) and
[Context Lake](https://help.getzep.com/context-lake).

**Position Zep as a context solution, not only a memory store.** Agent memory
(remembering one user across conversations) is one of Zep's three solutions —
see [Choose the solution](#choose-the-solution) — and every solution uses the
same graphs, ingestion, retrieval, and governance. When you describe or design
with Zep, lead with *the context the agent needs for its task* and *who owns
that context*, then pick the graph scope; do not assume "Zep" means "per-user
chat memory".

The mental model: **Zep is not a chat-log store and not a vector database.** It
extracts structured, time-aware knowledge from whatever you feed it, fuses it
into the graph, and returns the slice that matters for the current moment. That
sets it apart from the tools you might otherwise reach for:

- **vs. a store per data type** — chat, documents, JSON, and business events all
  fuse into *one* graph per subject; you don't stand up and stitch together a
  separate store for each source.
- **vs. plain vector search** — retrieval is **hybrid** (semantic + keyword +
  graph traversal, then reranked), not similarity alone, so it captures exact
  terms and relationships, not just conceptual matches.
- **vs. static GraphRAG** — Zep is built for **change**: it ingests streaming,
  frequently-updated data incrementally and time-stamps every fact (see the
  bitemporal model below), whereas GraphRAG targets one-time summarization of
  static documents. Reach for Zep when knowledge evolves.

Two kinds of graph. A **user graph is a specialization of a shared Context
Graph**: anything a shared graph can do, a user graph can do too. Only some
features are **user-graph-only** — flagged **(user graphs only)** below;
everything else applies to every graph.

- **Shared Context Graph** (`graph_id`; the SDK and API also call this a
  *standalone graph*) — the base graph type, for context that is **not owned by
  one application user**: a customer account, a project, a product and its
  support knowledge, an operational domain, runbooks and policies. See
  [Context Graph overview](https://help.getzep.com/graph-overview) and
  [Create a Context Graph](https://help.getzep.com/create-graph).
- **User graph** (`user_id`) — a Context Graph **specialized for one
  application user**: auto-created per user, the home of agent memory (an agent
  remembering prior conversations and activity of that user). Adds user-only
  features — a **user node**, a **user summary**, and **threads** — and fuses
  all of that user's threads and user-owned business data. See
  [Users and user graphs](https://help.getzep.com/users-and-user-graphs).

An integration with Zep can use **one or both** kinds of graph, and often
several graphs of each kind. The developer integrating Zep decides which graphs
exist and what data feeds each. **Keep each data set in the graph that matches
its subject and access boundary** — do not copy shared account data into every
user graph. Which graphs a request may read from is decided in the
**application layer** at retrieval time and enforced by Zep access policies
(see [Govern](#5-govern-access-to-context)) — for example, a support agent
reads the current person's user graph *and* the authorized account graph *and*
a companywide policy graph, then combines the results. See
[Architecture patterns](https://help.getzep.com/architecture-patterns).

**How an episode is processed.** Each ingested artifact (an "episode") is
processed asynchronously: Zep extracts the **entities** mentioned, extracts the
**facts/relationships** between them, **deduplicates** the new entities and
facts against what is already in the graph, and **invalidates** any facts the
new data supersedes (e.g. a changed preference — the old fact is marked invalid
but kept as history).

**Bitemporal model.** Facts carry validity timestamps (valid/invalid/created/
expired), so you can ask what is true *now* or what was true at a past date.

**Provenance.** Facts and other graph artifacts keep references to the source
**episodes** they were derived from, so retrieved context can be traced back to
the data that produced it. Provenance identifies the source; it does not
guarantee the source or the fact is correct. See
[Source traceability](https://help.getzep.com/source-traceability).

**Context types** (what ingestion creates, what retrieval returns): episodes, entities, facts, thread
summaries, the user summary, and observations. Each captures a different value;
**auto** search finds the most relevant artifacts across all of them. A useful
contrast: **entity/node summaries** give *depth* (a narrative rolling up one
entity's history) while **facts** give *breadth* (granular, individually-dated
claims) — good retrieval draws on both. See
[Context types](https://help.getzep.com/context-types).

## Choose the solution

Start with the information the agent needs, then identify **who owns that
context**. Zep's documentation is organized around three solutions; they share
one lifecycle and differ in graph scope and retrieval path. See
[Choose a Zep solution](https://help.getzep.com/use-cases).

| Solution | Use it when | Graph scope and retrieval path |
| --- | --- | --- |
| [Enterprise context graphs](https://help.getzep.com/enterprise-context-graphs) | Agents need shared context about projects, products, operations, policies, or a business domain — knowledge not owned by one user. | One shared Context Graph (`graph_id`) per subject and access boundary. Ingest business data and documents with `graph.add` / `zep-ingest`; retrieve with `graph.search`. Guide: [Build project, product, and domain context](https://help.getzep.com/give-your-agent-domain-knowledge). |
| [Agent memory](https://help.getzep.com/agent-memory-solution) | An agent needs context from **one user's** previous conversations, activity, and changing preferences. | A user graph (`user_id`) with threads. Ingest messages with `thread.add_messages` and user-owned business data with `graph.add(user_id=...)`; retrieve with `thread.get_user_context`. Guide: [Agent memory quickstart](https://help.getzep.com/quick-start-guide). |
| [Customer and account context](https://help.getzep.com/customer-account-context) | An agent needs a person's context **and** shared customer/account records (CRM, cases, contracts, events) for the same task. | Personal data in the user graph; shared data in an account Context Graph (`graph_id`). Retrieve from both and combine in the application. Guide: [Unify customer and account context](https://help.getzep.com/how-to-share-context-across-users-using-graphs). |

**Combine solutions when a task needs multiple scopes.** An agent can retrieve
from more than one authorized graph — e.g. a support agent uses an account
graph (contracts, cases), the user's graph (their conversations and
preferences), and an enterprise graph (support policies, runbooks). Keep each
data set in the graph matching its subject and access boundary; combine the
retrieved context in the application.

## Architectural philosophy and invariants

- **Test end to end for your use case.** Zep's many choices (scoping, ontology,
  retrieval) rarely have one "correct" setting; what matters is whether
  the whole pipeline delivers **complete context and accurate answers** for
  *your* use case, not whether any single part looks right in isolation. Tune and
  validate against an **end-to-end evaluation**, not a "perfect" graph — several
  trade-offs below (under-merging, recall over precision) only make sense through
  this lens. See [Evaluating Zep](#evaluating-zep).
- **Zep vs. your application.** Zep manages the graph (extraction, dedup,
  retrieval) and controls **access to context in Zep**. The application
  controls **what data is sent**, **which graphs are retrieved from**, and
  **how the agent uses the context Zep returns** (prompt, model, logic).
  Retrieving from one vs. many graphs is an application-layer decision.
  Context supports correct task completion; it does not guarantee model
  behavior or authorize an action. The application remains responsible for
  tool permissions, action authorization, and validation of external actions.
- **Retrieved context is evidence, not instruction.** Treat every Context
  Block and search result as untrusted data: it can contain end-user messages,
  documents, and tool output. Keep the agent's instructions in the provider's
  privileged channel (system/developer/instructions) and pass Zep context
  through the ordinary data channel (a user message, or a tool result linked to
  its call). Never interpolate retrieved context into the system prompt. See
  [Memory security best practices](https://help.getzep.com/memory-security)
  for per-provider placement.
- **Zep does not infer beyond the data provided; it is only as good as the data
  it receives.** If context was never sent to Zep, Zep cannot surface it — a
  possible cause of "missing" context is that it was never ingested.
- **Deduplication philosophy — prefer under- to over-merging.** Wrongly merging
  two distinct entities is worse than failing to merge two that are the same,
  because unmerged duplicates are *both* still retrievable, so the agent still
  gets complete context. This is a concrete reason not to chase a "perfect"
  graph — what matters is complete retrieval when you **test end to end** for
  your use case.
- **Dedup needs context.** Threads automatically use prior messages as
  extraction context; `graph.add` does **not**. Episodes with pronouns or bare
  first names (e.g. multiple "John"s with no last name) deduplicate poorly —
  pre-process ambiguous data with stable identifiers (full names, IDs).
- **Retrieval philosophy — favor recall over precision.** Retrieve broadly and
  let the downstream LLM ignore what is irrelevant; missing relevant context is
  worse than including some extra. See [Retrieval philosophy](https://help.getzep.com/retrieval-philosophy).
- **Ingestion is asynchronous.** Added data is processed before it becomes
  retrievable (seconds or more). Design for eventual availability rather than
  reading back immediately; check status when it matters via
  [Check ingestion status](https://help.getzep.com/check-data-ingestion-status).
  **Submit all episodes without polling between adds** — for
  `thread.add_messages`, `graph.add`, batch, or `zep-ingest` alike — and
  **poll only once, on the last episode**, when you need retrievability.
  Expected wait time scales with total episode count in that graph.

## Implementation: scope → ingest → shape → retrieve → govern

Implementing Zep follows the context lifecycle the docs use under
[Working with Context](https://help.getzep.com/working-with-context) —
**Ingest → Shape the Graph → Retrieve → Govern** — preceded by a scoping
decision and followed by **evaluation**. Ingest and Retrieve are required for
every implementation; shape the graph when the domain needs a specific
ontology, terminology, or summary configuration; apply governance before an
application retrieves production context. Evaluation has its own section
below. These are cross-cutting decisions; confirm exact signatures and limits
in the docs (see the [index](#documentation-index)) rather than guessing.

### 1. Scope your graphs and data sources

- Pick the solution first (see [Choose the solution](#choose-the-solution)),
  then the scope: **user graphs** (`user_id`, context owned by one application
  user) vs. **shared Context Graphs** (`graph_id`, customer/account, project,
  product, or domain context). Create one shared graph with a **stable
  `graph_id`, name, and description** per subject and access boundary — the
  description helps an agent or application select the correct graph (see
  [Graph directory](https://help.getzep.com/graph-directory)). Use **separate
  graphs wherever you need hard data separation** — per user, per account, per
  team, per tenant, per business unit with different access policies. Do not
  put unrelated subjects or data with different access requirements in one
  graph.
- Decide which data sources feed which graphs. One graph can hold many sources;
  you can also have many graphs.
- **Zep threads apply only to user graphs.** A Zep thread represents a
  conversation between the user and the agent; it records that conversation
  history *and* ingests it into the user graph. Note the available episode/data
  types (message, text, JSON). Shared graphs have no first-class thread
  support, but can still ingest arbitrary text — e.g. Slack or email — via
  `graph.add`, or via [`zep-ingest`](https://help.getzep.com/zep-ingest) when
  those sources are already on disk (as text/JSON/episodes, not as a Zep
  thread). Group the chunks of one source (a PDF, an export, a channel) with a
  [`document_id`](https://help.getzep.com/documents) so Zep uses prior chunks
  as extraction context; do not share an ID across independent records.

### 2. Ingest data into graphs

- **Choose an ingestion path** by how the data arrives (see
  [Adding context](https://help.getzep.com/adding-context)):

  | What you are adding | Use |
  | --- | --- |
  | A message in a live conversation, as your agent sends and receives it | [`thread.add_messages`](https://help.getzep.com/adding-messages) in the Zep SDK |
  | Historical data on disk you are loading for the first time: documents, transcripts, email, Slack exports, or past conversations | [`zep-ingest`](https://help.getzep.com/zep-ingest) |
  | A recurring export that lands files on disk (hourly or nightly dump, ETL output) | [`zep-ingest`](https://help.getzep.com/zep-ingest) |
  | An individual document, API response, business event, or webhook payload your application already holds in memory | [`graph.add`](https://help.getzep.com/adding-business-data) with `user_id` or `graph_id` |

- **`zep-ingest`** is a Python package for building **ingestion pipelines**: it
  prepares and loads existing on-disk data into Zep in a defined order
  (canonicalize identities and timestamps, validate, submit, monitor). Prefer it
  for backfills and recurring folder/glob imports. It is a convenience layer over
  the Zep SDK — calling `graph.add` or the
  [Batch API](https://help.getzep.com/adding-batch-data) directly remains fully
  supported. Do **not** use it for live chat turns (`thread.add_messages`) or for
  typical in-memory / webhook payloads (`graph.add` is simpler). For loaders,
  transforms, preview, submission, and monitoring details, read
  [Create an ingestion pipeline](https://help.getzep.com/zep-ingest) — do not
  invent package APIs from memory.
- **Prepare the data.** Anytime you design an ingestion pipeline (SDK or
  `zep-ingest`), **read**
  [Prepare data for ingestion](https://help.getzep.com/prepare-data-for-ingestion)
  and follow those best practices (entity identity, source context, event time,
  and related guidance). Also attach
  [**episode metadata**](https://help.getzep.com/adding-business-data#episode-metadata)
  (such as `source`) at ingest when you need episode-metadata filtering on
  search; chunk oversized documents per
  [Chunking](https://help.getzep.com/chunking-large-documents).
- **Seed vs. stream.** Decide between backfilling initial/historical data
  (`zep-ingest`, or [batch ingestion](https://help.getzep.com/adding-batch-data)
  for large volumes) and live/streaming updates (`thread.add_messages` /
  `graph.add`).
- **Multi-graph backfills — enqueue everything, then wait once.** Graphs do
  not share a processing queue; one graph finishing extraction is not a
  prerequisite for another to accept data. For a backfill into multiple graphs
  (user and/or standalone), create all destinations and configure
  ontology/instructions first — ontology is not retroactive — then **submit all
  episodes to every graph without waiting on another graph's processed status**.
  Use the [Batch API](https://help.getzep.com/adding-batch-data) or `zep-ingest`
  with `method="auto"` or `"batch"`. Waiting for graph A to finish before even
  *sending* to graph B is a common backfill anti-pattern. After all submits are
  queued, wait or poll once (in parallel per graph if you like) until the facts
  you need are searchable — only when you are about to search or demo, not after
  every file or graph. Within a single graph, enqueue all sources together too;
  do not finish one source before submitting the next unless you have a real
  dependency (e.g. seed nodes/triples before episodes that must pin to those
  UUIDs).

### 3. Shape the graph

Zep extracts entities, relationships, facts, and summaries automatically (see
[How graph creation works](https://help.getzep.com/how-graph-creation-works)).
Customize that when the domain needs it — **iterate, don't front-load** — and
configure it **before** the backfill, because ontology and instructions are not
retroactive. Hub: [Shape the Graph](https://help.getzep.com/customizing-context).
Rule of thumb: **ontology defines the *shape* of the graph (which entity/edge
types exist); instructions define *how to interpret* your domain** — don't
conflate them.

- [Custom ontology](https://help.getzep.com/customizing-graph-structure) —
  your entity/edge types. Model entity types as **nouns** and edge types as
  **verbs/relationships**, and start with a few generic types rather than
  modeling everything up front (custom attributes are advanced and often
  unnecessary). Recommended for most production use cases: sharpens extraction
  and enables type-filtered retrieval of domain-specific objects.
- [Custom instructions](https://help.getzep.com/custom-instructions) —
  describe your domain (terminology, concepts) so Zep interprets data better
  on ingest. Not for defining types — that is the ontology's job.
- [User summary instructions](https://help.getzep.com/user-summary-instructions)
  **(user graphs only)** — steer what the always-on user summary captures; a
  reliable baseline for cold-start threads.
- [Observation steering](https://help.getzep.com/steering-observations)
  (experimental, plan-gated) — shape how Zep words and labels
  [observations](https://help.getzep.com/observations), the durable patterns it
  derives across many facts.

### 4. Provide retrieval to agents

- **Choose the context surface:**
  - *Default Context Block* **(user graphs only)** — `thread.get_user_context`;
    returns whole-user-graph context, relevance driven by the most recent thread
    messages. Best for most conversational agents.
  - *Context templates* **(user graphs only)** — automatic relevance, your fixed
    layout/sections. See [Context templates](https://help.getzep.com/context-templates).
  - *Advanced/manual construction* — run searches and assemble the string
    yourself; the **only** context surface for shared Context Graphs, and used
    for custom blocks on any graph. See
    [Advanced construction](https://help.getzep.com/advanced-context-block-construction).
  Hub: [Retrieve](https://help.getzep.com/assembling-context).
- **Search** with `graph.search`: `scope="auto"` (recommended entry point for
  shared-graph/non-thread queries, spans all context types) or a specific scope
  (edges, nodes, episodes, observations, thread_summaries) with rerankers and
  **filters** (metadata, timestamp, entity/edge type, property). See
  [Searching the graph](https://help.getzep.com/searching-the-graph).
- **Decide how the agent retrieves:** expose search as a **tool call** (LLM
  decides when) vs. **deterministic/programmatic** retrieval on every turn.
- **Decide how many graphs** to read (one versus many, using parallel graph
  searches) — an application-layer decision. For customer/account or
  multi-scope tasks, retrieve the user graph via `thread.get_user_context` and
  each authorized shared graph via `graph.search`, then combine in the
  application. See
  [Architecture patterns](https://help.getzep.com/architecture-patterns).
- **Place the context correctly** in the model request (data channel, not the
  privileged instruction channel — see the invariants above). Retain the
  retrieval results and their source references when the application must
  show where a fact came from.

### 5. Govern access to context

Apply governance **before an application retrieves production context**. Zep
separates two problems (hub: [Governance](https://help.getzep.com/governance)):

- **Who can manage the account and projects** (humans in the dashboard) —
  [RBAC](https://help.getzep.com/role-based-access-control) with account- and
  project-scoped roles, plus
  [enterprise SSO](https://help.getzep.com/enterprise-sso).
- **What context each agent or caller can reach** —
  [policy-based access control](https://help.getzep.com/policy-based-access-control)
  (ABAC): attach policy sets to **API keys** for
  [agent access](https://help.getzep.com/attribute-based-access-control) (limit
  which actions, graphs, and data classes an agent can reach — give each agent
  its own key) and to **UserGroups** for
  [Memory MCP users](https://help.getzep.com/usergroup-access). Source-based
  policies evaluate the **episode metadata attached at ingestion** (see
  [Episode metadata projection](https://help.getzep.com/episode-metadata-projection)),
  so decide metadata like `source` at ingest time with governance in mind.
- **Traceability and visibility** —
  [source traceability](https://help.getzep.com/source-traceability) to trace
  facts to source episodes, [Audit Logs](https://help.getzep.com/audit-logging)
  for dashboard activity, and [API Logs](https://help.getzep.com/api-logging)
  for request activity and query-audit workflows.

Zep access policies control access to Zep context only. They do not authorize
an action in an external system; your application enforces its own tool and
action permissions.

## Evaluating Zep

- **Anchor to the end business task** and evaluate **end-to-end**, not each part
  in isolation. See [Evaluate Zep for your use case](https://help.getzep.com/evaluate-zep-for-your-use-case).
- **Two distinct measures:**
  - *Context completeness* — did Zep provide the context needed? (Zep's job.)
  - *Answer accuracy* — did your agent use that context to produce the correct
    result? (Your LLM/prompt's job, assuming context is complete.)
- **Diagnose with them:**
  - Completeness **high**, accuracy **low** → fix the **agent** (prompt, model,
    logic), not Zep.
  - Completeness **low** → accuracy will be low too. Localize the failure: is it
    ingestion or retrieval? First check whether the needed information is in the
    graph **at all** — [read/export the graph](https://help.getzep.com/reading-data-from-the-graph)
    (edges, entities, observations) and inspect the **episodes** (the raw data
    that was sent).
    - Not in the episodes → the data was **never sent** to Zep; fix what your
      application ingests. Not a Zep problem.
    - In the episodes but not in derived artifacts → tune **ingestion** (custom
      instructions, ontology, pre-processing the data).
    - In the derived artifacts but not in the retrieved context → tune
      **retrieval** (search scope, rerankers, filters, context assembly).
- This is why under-deduplication is acceptable (see philosophy above): an
  imperfect graph can still yield complete retrieval, which is what the
  end-to-end evaluation actually measures.
- Zep provides an **evaluation harness** to help measure context completeness
  and answer accuracy — but you supply a **gold dataset**: the kinds of
  questions you want your agent to answer, paired with the correct answers.
  See the full guidance in
  [Evaluate Zep for your use case](https://help.getzep.com/evaluate-zep-for-your-use-case).

## Documentation index

The `zep-docs` MCP server is the source for exact, current details and **best
practices** — query it before relying on memory, and **refer to the
documentation before implementing any feature**. The pages below are curated
entry points ("read X to do Y"), grouped the way the docs are laid out:
solutions and getting started, unified-context concepts, the Working with
Context lifecycle (Ingest, Shape, Retrieve), pages that apply to all graphs,
the smaller sets that are user-graph-only or shared-graph-only, governance, and
reference.

**How to retrieve — read a page (preferred), or search.** Prefer loading a whole
page over searching. The server exposes two mechanisms:

1. **Read a whole page (preferred).** Load a full doc page in one shot as an MCP
   **resource** — `zep-docs://<slug>`, where `<slug>` is the page's
   `help.getzep.com` path (everything after the domain, no leading slash). E.g.
   `https://help.getzep.com/searching-the-graph` →
   `zep-docs://searching-the-graph`; nested paths keep their slashes. Every page
   linked below is reachable at its `zep-docs://<slug>` resource by this rule;
   discover the full list with your client's resource-listing capability (both
   Claude Code and Codex expose MCP resources — Codex via `list_mcp_resources` /
   `read_mcp_resource`). **Prefer this whenever you implement, verify, or debug a
   specific feature** — you get the complete, current page, not fragments — and it
   needs only the MCP connection, so it works even when the agent has no general
   web access.
   - *Fallbacks* if the client can't read MCP resources or a resource errors:
     fetch the identical markdown at `https://help.getzep.com/<slug>.md` (the
     resource is just a cached proxy to that file), or the rendered page at
     `https://help.getzep.com/<slug>`. Both require web access to
     `help.getzep.com`.
2. **Search the docs (discovery).** Use the **`search_documentation`** tool
   (served by `zep-docs`; params: `query`, and optional `max_results`, 1–10,
   default 5) when you don't know where something is documented, whether it exists
   at all, or you want a broad look. It returns reranked text chunks with **no
   page URLs**, so use it to find *what* to read, then load that page in full via
   its `zep-docs://<slug>` resource.

**Solutions and getting started**

| Read | To |
|------|----|
| [Choose a Zep solution](https://help.getzep.com/use-cases) · [Solutions](https://help.getzep.com/solutions) | Pick enterprise context graphs, agent memory, or customer and account context, and combine them |
| [Enterprise context graphs](https://help.getzep.com/enterprise-context-graphs) → [Build project, product, and domain context](https://help.getzep.com/give-your-agent-domain-knowledge) | Shared graph (`graph_id`) implementation path and the shared-graph quick start |
| [Agent memory](https://help.getzep.com/agent-memory-solution) → [Agent memory quickstart](https://help.getzep.com/quick-start-guide) | User/thread implementation path and the user-graph quick start |
| [Customer and account context](https://help.getzep.com/customer-account-context) → [Unify customer and account context](https://help.getzep.com/how-to-share-context-across-users-using-graphs) | User graph + account graph implementation path and worked example |
| [Install SDKs](https://help.getzep.com/install-sdks) · [Implement Zep with agents](https://help.getzep.com/implement-zep-with-agents) | Install the SDK; plugin, docs MCP, and agent-tool setup |
| [Agent frameworks](https://help.getzep.com/memory-for-agent-frameworks) | Add Zep context to LangGraph, CrewAI, Vercel AI, Mastra, ADK, and other frameworks |

**Unified-context concepts**

| Read | To |
|------|----|
| [Unified context](https://help.getzep.com/concepts) | Core concepts: unified context, Context Graphs, Context Lake, governance, retrieval, facts, observations |
| [Context Lake](https://help.getzep.com/context-lake) | How Zep manages and serves many governed graphs as one system; the context lifecycle |
| [Context Graph overview](https://help.getzep.com/graph-overview) · [How graph creation works](https://help.getzep.com/how-graph-creation-works) | Graph data structure, provenance, and how episodes become entities and facts |
| [Architecture patterns](https://help.getzep.com/architecture-patterns) | Scope graphs and choose one-vs-many-graph retrieval |
| [Context types](https://help.getzep.com/context-types) · [Facts](https://help.getzep.com/facts) · [Observations](https://help.getzep.com/observations) | Understand each context type, bitemporal facts, derived patterns, and auto search |
| [Retrieval philosophy](https://help.getzep.com/retrieval-philosophy) | Understand recall-over-precision retrieval |
| [What is context engineering?](https://help.getzep.com/what-is-context-engineering) · [Zep vs. GraphRAG](https://help.getzep.com/zep-vs-graph-rag) | Position Zep against alternatives |

**Working with Context — Ingest** (all graphs)

| Read | To |
|------|----|
| [Ingest](https://help.getzep.com/adding-context) | Choose among `thread.add_messages`, `zep-ingest`, and `graph.add` |
| [Prepare data for ingestion](https://help.getzep.com/prepare-data-for-ingestion) | Best practices — **read before designing any ingestion pipeline** |
| [Create an ingestion pipeline](https://help.getzep.com/zep-ingest) | Backfills and on-disk imports with `zep-ingest` |
| [Adding business data](https://help.getzep.com/adding-business-data) | Individual documents/JSON/API payloads (`graph.add`) and episode metadata |
| [Documents](https://help.getzep.com/documents) | Group the chunks of one source with `document_id` |
| [Batch ingestion](https://help.getzep.com/adding-batch-data) | Large imports / the transport `zep-ingest` submits through |
| [Chunking](https://help.getzep.com/chunking-large-documents) | Split large documents to fit size limits |
| [Check ingestion status](https://help.getzep.com/check-data-ingestion-status) | Handle asynchronous processing |
| [Webhooks](https://help.getzep.com/webhooks) | Receive pushed events (episode processed, batch completed) instead of polling |

**Working with Context — Shape the Graph** (all graphs unless noted)

| Read | To |
|------|----|
| [Shape the Graph](https://help.getzep.com/customizing-context) | Compare ontology, instructions, summary instructions, and observation steering |
| [Customizing graph structure](https://help.getzep.com/customizing-graph-structure) | Define a custom ontology (entity/edge types) |
| [Custom instructions](https://help.getzep.com/custom-instructions) | Steer domain interpretation on ingest |
| [Steering observations](https://help.getzep.com/steering-observations) | Shape observation wording and types (experimental) |

**Working with Context — Retrieve** (all graphs unless noted)

| Read | To |
|------|----|
| [Retrieve](https://help.getzep.com/assembling-context) | Compare the Context Block, context templates, and advanced construction |
| [Searching the graph](https://help.getzep.com/searching-the-graph) | Scoped search, filters, rerankers |
| [Advanced construction](https://help.getzep.com/advanced-context-block-construction) | Build custom context blocks (the only context surface for shared graphs) |
| [Graph directory](https://help.getzep.com/graph-directory) | Discover shared graphs by name and description before searching them |
| [Memory security best practices](https://help.getzep.com/memory-security) | Place retrieved context safely per provider; prevent memory poisoning |
| [Performance best practices](https://help.getzep.com/performance) | Reduce latency and optimize production performance (SDK client reuse, cache warming, concise search) |

**Working with graphs** (all graphs)

| Read | To |
|------|----|
| [Manually updating the graph](https://help.getzep.com/adding-fact-triplets) | Add nodes/fact triplets and update existing edges, nodes, and facts by UUID |
| [Reading data](https://help.getzep.com/reading-data-from-the-graph) · [Deleting data](https://help.getzep.com/deleting-data-from-the-graph) | Inspect or remove graph data |
| [Cloning graphs](https://help.getzep.com/cloning-graphs) | Copy a graph (e.g. for testing) |
| [Debug mode](https://help.getzep.com/debug-mode) | Capture per-episode ingestion logs when diagnosing extraction |
| [Evaluate Zep for your use case](https://help.getzep.com/evaluate-zep-for-your-use-case) | Benchmark completeness vs. accuracy |

**User graphs only**

| Read | To |
|------|----|
| [Users and user graphs](https://help.getzep.com/users-and-user-graphs) | Create users and per-user context |
| [Threads](https://help.getzep.com/threads) | Record conversations and ingest into the user graph |
| [Retrieving context](https://help.getzep.com/retrieving-context) | Get the default Context Block |
| [Context templates](https://help.getzep.com/context-templates) | Fixed custom layout with automatic relevance |
| [User summary](https://help.getzep.com/user-summary) · [summary instructions](https://help.getzep.com/user-summary-instructions) | Shape the always-on user baseline |
| [Add user business data](https://help.getzep.com/how-to-add-user-specific-business-data-to-user-graphs) | Add non-chat data owned by one user to their graph |

**Shared Context Graphs only**

| Read | To |
|------|----|
| [Create a Context Graph](https://help.getzep.com/create-graph) | Create and manage shared graphs (`graph_id`) |
| [Build project, product, and domain context](https://help.getzep.com/give-your-agent-domain-knowledge) | Stand up the basic loop (the shared-graph quick start) |

**Governance**

| Read | To |
|------|----|
| [Governance](https://help.getzep.com/governance) | Hub: RBAC for humans, ABAC policies for agents and callers, traceability, logs |
| [Managing team access (RBAC)](https://help.getzep.com/role-based-access-control) · [Enterprise SSO](https://help.getzep.com/enterprise-sso) | Dashboard permissions for teammates and how they sign in |
| [Policy-based access control](https://help.getzep.com/policy-based-access-control) · [Agent access](https://help.getzep.com/attribute-based-access-control) · [UserGroup access](https://help.getzep.com/usergroup-access) | Attach ABAC policy sets to API keys (agents) and UserGroups (Memory MCP users) for least-privilege access to context |
| [Episode metadata projection](https://help.getzep.com/episode-metadata-projection) | Understand what source-based policies and metadata filters evaluate |
| [Source traceability](https://help.getzep.com/source-traceability) | Trace facts to source episodes and retain references for audit |
| [Audit logging](https://help.getzep.com/audit-logging) · [API logging](https://help.getzep.com/api-logging) | Review dashboard activity and API request activity |
| [Security & compliance](https://help.getzep.com/security-compliance) | SOC 2 Type II, HIPAA BAAs, [BYOK](https://help.getzep.com/bring-your-own-key), BYOM, and Cloud/BYOC deployment models |

**Reference**

- SDK / API reference: <https://help.getzep.com/sdk-reference> — confirm exact
  signatures, parameters, and limits here or via the `zep-docs` MCP.
- Docs MCP server setup: <https://help.getzep.com/docs-mcp-server>.

## Source authority and validation

- **Query the `zep-docs` MCP server first** for anything that must be exact or
  current — method names, parameters, limits, plan availability, newer features.
  Prefer loading the whole relevant page via its **`zep-docs://<slug>` resource**;
  use the **`search_documentation`** tool to find the right page or check whether
  something exists (see [Documentation index](#documentation-index) for both). It
  covers the guides and the SDK/API reference.
- **Fallback if resources or the MCP are unavailable:** fetch the page markdown at
  `https://help.getzep.com/<slug>.md`, else the guides at <https://help.getzep.com>
  and the SDK/API reference at <https://help.getzep.com/sdk-reference>.
- **The live docs win on conflict.** Treat this skill's summaries as stale if
  they disagree with current, version-matched documentation. Verify
  version-sensitive code against the SDK reference and, when available, the
  installed SDK's types/source.
- **Validate behavior, not just plausibility.** Don't stop at code that looks
  right — confirm ingestion completed, retrieval returns the expected context,
  and (per [Evaluating Zep](#evaluating-zep)) the end use case actually improves.
