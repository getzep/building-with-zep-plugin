---
name: tuning-zep-ingestion
description: >-
  Procedure for an agent that must turn a dataset (database records, documents,
  email, chat messages, meeting transcripts, event logs, or a mix) into a
  domain-specific Zep Context Graph, with or without a gold question set. The
  procedure splits the data into a deterministic import and narrative episodes,
  shapes each episode, designs the ontology and the custom instructions, runs a
  versioned ingestion on a new graph, measures the graph shape, reads the debug
  logs and the Ingestion Traces, and changes one variable per run. Use when a
  user asks to "ingest my data into Zep", "improve extraction quality", "why
  does my graph have duplicate or untyped entities", "tune the ontology or the
  instructions", or "evaluate Zep on my dataset". Use together with the
  building-with-zep skill, which holds the product concepts and the
  documentation index.
---

# Tuning Zep ingestion for a dataset

This skill is a procedure. The Zep documentation holds the method names, the
parameters, the limits, and the plan availability. Read the documentation
through the `zep-docs` MCP server, or at `https://help.getzep.com/<slug>.md`.
When this skill and the documentation disagree, the documentation is correct.

## Terms

| Term | Meaning in this skill |
|---|---|
| Record | One unit of the source data: one database row, one email, one chat message, one document, one event. |
| Structured field | A field of a record with a fixed meaning and a short value: an ID, a name, a category, a status, a date, a reference to another record. |
| Prose field | A field of a record with free text: a message body, a document body, a transcript, a ticket description. |
| Deterministic import | Nodes and edges that you write into the graph from structured fields with `graph.add_nodes` and `graph.add_fact_triple`. No LLM is involved. |
| Narrative episode | Text that you send to Zep for LLM extraction, through `graph.add` or the Batch API. |
| Lead sentence | The first sentence of a narrative episode. It names the record kind, the subject, the author, the time, and the source, with the same identifiers that the deterministic import used. |
| Configuration version | An integer that you increase each time you change the ontology, the instructions, or the episode preparation. One graph holds one configuration version. |
| Manifest | A file that records, for one run, the configuration version, a hash of the configuration, a hash of the prepared data, the graph ID, the start time, and the end time. |
| Field repeat | An extracted edge that restates a structured field that the deterministic import already wrote, with the same source node and edge name and a different target. |
| Needle check | For one gold question, a check that the episodes that hold the answer exist in the graph, were processed, and produced a fact that contains the gold answer. |

## Principles

1. Import what the data already states. Extract only what the prose adds.
   A structured field is already a fact. Write it into the graph with the
   deterministic import before the first episode. Send only the prose fields
   through LLM extraction. When the LLM also sees the structured fields, it
   extracts them again, and the deduplication merges only exact repeats.
2. Each episode must stand alone. The extractor sees one episode. In a batch of
   `text` episodes, the extractor does not see the previous episodes. Put the
   identity of the subject, the author, the time, and the source into the lead
   sentence. Episode metadata is for search filters. The extractor does not
   read it.
3. Identity is a data decision. Decide the canonical name and the identifier of
   each entity type before the ingestion. When you have an authoritative alias
   map, rewrite the aliases in the data. Declare `identity_properties` for the
   types that carry an ID. An instruction about identity helps only when the
   data is already unambiguous.
4. The model reads a type description as a list of answers. When a type
   description lists the permitted values (the issue categories, the status
   codes), the model emits those values also when the episode text does not
   contain them. Keep a closed vocabulary in the deterministic import. Do not
   list the values in the type description.
5. An instruction cannot stop a repeat. A rule such as "these facts already
   exist, do not repeat them" has no measured effect. The extractor cannot see
   the graph, so the rule has no reference. Remove the fact from the text and
   from the type descriptions (principle 4), or accept the repeat.
6. Change one variable per run. Each run has a configuration version, a new
   graph, and a manifest. Zep itself changes between runs. When you compare two
   runs, state every difference, including the dates of the runs.
7. Measure the graph shape before you measure the answers. The counts of nodes
   and edges by type, the untyped nodes, the edge names outside the ontology,
   the identity correctness against the source records, and the field repeats
   are deterministic, and they explain most answer failures.
8. Treat each LLM explanation as a claim. The Ingestion Traces show the stage
   inputs and outputs. Count what the stages did. Do not report the generated
   explanation text as the cause.
9. Separate the evidence types in each report: direct measurement, behavior
   that the documentation confirms, interpretation, and open hypothesis. The
   reader will act on the report. A hypothesis must not look like a fact.

## Procedure

### Step 0. Learn the data

Read a sample of each record kind. For each kind, fill one row of this table
and keep the table in the project notes:

| Kind | Structured fields | Prose fields | Natural identifier | Event time field | Related record kinds |
|---|---|---|---|---|---|

Also record:

- The number of records per kind.
- The size distribution of the prose fields. The documentation gives the
  episode size limit. Zep rejects an episode above the limit and does not
  truncate it.
- The alias patterns: short names, logins, email addresses, IDs with prefixes.
- Whether a gold question set exists. When one exists, read each question kind
  and note which structured fields and which prose each kind needs.

Then read these documentation pages: `prepare-data-for-ingestion`,
`adding-fact-triplets`, `customizing-graph-structure`, `custom-instructions`,
`documents`, `adding-batch-data`, and `debug-mode`. Read them on each project,
because the limits and the method names change.

### Step 1. Split the dataset

Write the split as a table before you write code:

| Deterministic import | Narrative episodes | Dropped |
|---|---|---|
| Entities with a natural ID: people, accounts, cases, products, tickets, documents, channels, meetings | The prose fields, each with a lead sentence | Records with no prose and no relationship, for example a code table |
| Relationships that the records state: reports-to, works-on, authored, attends, filed-against, has-status | Facts that only the prose states: what happened, who said what, decisions, amounts, reasons | Header lines, MIME lines, signatures, redaction markers |
| Attributes with a closed vocabulary: categories, statuses, regions | | |

Rules for the deterministic import:

- Create one node per entity. Store the natural ID in a node attribute, so that
  you can join the graph to the source.
- Create one edge per stated relationship. Write a `fact` sentence that names
  both endpoints in full, with the date when the record has one. Example:
  `"Ana Ruiz attends the meeting 'Q3 plan review' on 2026-03-04."` The sentence
  `"The employee attends the meeting."` is not searchable.
- Set `valid_at` from the record time.
- Make the import resumable. Write a state file with the keys of the nodes and
  edges that are already created. Zep does not deduplicate nodes by name, so a
  retry without the state file creates each node twice.
- Validate the import before you send it: each node key is unique, and each
  edge endpoint refers to a known node key. Stop the run on an unknown key.

Rules for the narrative episodes:

- Start each episode with a lead sentence. Example:
  `"Email from Ana Ruiz <ana.ruiz@example.com> to Ben Ott <ben.ott@example.com>, 2026-03-04, subject 'Q3 plan review'."`
- Put the prose after the lead sentence. Remove the structural noise (header
  lines, signatures, redaction markers).
- Set the episode time to the event time of the record. Do not use the
  ingestion time.
- When a prose field is longer than the episode limit, split it at a sentence
  or paragraph end. Repeat the lead sentence in each part, add `(part i of n)`,
  and give the parts of one source the same `document_id`. Do not give
  unrelated records the same `document_id`.
- For an event log with many similar rows (one row per process step), write
  one sentence per row that names the case, the activity, the actor, and the
  time. State in the instructions which activity gives the current state and
  which activities are final.

### Step 2. Design the ontology

- An entity type is a noun with a natural identity. An edge type is a verb
  between two named types. Start with the types that the questions or the use
  case need. The documentation gives the maximum number of types.
- Give each type a short description that defines membership and gives one
  example. Do not list values in the description (principle 4).
- Declare `identity_properties` for each type that has an ID in the lead
  sentence.
- Declare the `source_targets` of each edge type. Zep stores an extracted edge
  whose endpoints do not match a declared pair under a generic classification.
  Count these edges in Step 5.
- Keep a type that exists only for the import in the ontology, because a search
  filter needs the label. Tell the extractor in the instructions that these
  nodes exist, and that the prose adds facts to them. Expect partial compliance
  and measure it.
- Decide `strict_ontology` per run, from a measurement. With `false`, the graph
  has more recall and a tail of edge names and untyped entities outside the
  ontology. With `true`, Zep drops the tail and some true facts with it. When
  the tail is large, measure both settings.

### Step 3. Write the custom instructions

Use at most five short named blocks:

| Block | Content |
|---|---|
| `corpus` | What the data is, what one episode is, what the lead sentence contains, how reliable the text is |
| `identity` | Which field identifies each type, which short names map to which canonical names, which values must never merge |
| `temporality` | Which field is the event time, the date format, when a fact starts to hold |
| `record` | Which record states the current or final state, which state supersedes which |
| `narrative` | What the prose adds: the event edges to extract and their names, which statements are facts on an existing node, which redacted values must not become entities |

Write what the extractor must do. A rule about what the extractor must not do
works only when the prompt does not offer the forbidden value in another place
(principle 5).

### Step 4. Run a versioned ingestion

1. Create a new graph. Put the dataset name, the configuration version, and the
   first eight characters of the data hash in the graph ID.
2. Set the ontology and the instructions. Record their hashes in the manifest.
   The ontology and the instructions apply only to episodes that Zep processes
   after you set them.
3. Enable debug mode on the project. The `debug-mode` page gives the active
   window per plan, the retention, and the plan requirement for Ingestion
   Traces. When the window is shorter than the run, enable debug mode again
   during the run, or make the slice smaller. The same page states whether
   batch ingestion writes per-episode debug logs in the current release.
4. Run the deterministic import. Wait for its tasks. Count the created nodes and
   edges and compare the counts with the plan from Step 1.
5. Submit all narrative episodes through the Batch API in event-time order, in
   batches of the documented maximum size, without a wait between the batches.
6. Record the start time in the manifest.
7. Poll until each batch and each item is terminal. Record each failed item by
   key. Record the end time.
8. Keep the graph until the comparison report is written.

Zep processes the items of one graph in the order of submission. Run one graph
per dataset at a time.

### Step 5. Measure the graph shape

Export each node, edge, and episode of the graph (`graph.node.get_by_graph_id`,
`graph.edge.get_by_graph_id`, `graph.episode.get_by_graph_id`, with paging).
Write one script that produces this table, and keep the script in the project,
because you will run it on each configuration version:

| Check | Method | Meaning of a bad value |
|---|---|---|
| Nodes by type, and untyped nodes | Count the labels. A node with only the generic label is untyped. | Many untyped nodes: the ontology lacks a type that the prose needs, or a type description is unclear. |
| Edges by name, inside and outside the ontology | Compare each edge name with the declared set. | A long tail (many names with one to five edges each): the prose has event facts with no declared edge type. Declare a closed event set, or accept the tail and rank. |
| Generic edges | Count the edges with the generic classification. | The endpoints did not match a declared pair, or no type matched. |
| Identity correctness | For each imported entity, compare the ID attribute and the name in the graph with the source record. | A wrong ID: a later extraction changed an imported attribute, or two records merged. |
| Identity collisions | Nodes of one type with the same name or the same ID. Edges between two nodes of a type that must not be related, for example case to case. | Context leaked across records, or aliases merged. |
| Field repeats | Extracted edges with the same name and source as an imported edge, and a different target. | The extractor emitted a structured field again (principle 4). |
| Node coverage | The share of extracted node names that occur in the episode text. | A low share for one type: the model takes the values from the type description. |
| Episode coverage | Each prepared episode key is present and processed. Failed items by key. | Missing episodes: a payload limit or a rejected field. |
| Import integrity | The imported node and edge counts equal the plan. | A retry doubled the import, or a chunk failed. |
| Timing | Items per minute, per batch. | A slow run. Do not infer the cause from one run. |

When a reference graph or a gold question set exists, add the entity recall and
precision by type against the reference, and the needle check for each
question.

When no gold set exists, build a small one from the data. For each record
kind, write 10 to 25 questions of the kinds that the use case needs (point in
time, current state, count, sequence, who did what). Give each question the
episode keys that hold the evidence and a short gold answer. Write the
questions from the records, not from memory. The identity checks and the field
repeat check need no gold set, and they are the first checks to make pass.

### Step 6. Read the debug logs and the Ingestion Traces

Select the episodes that produced a bad value in Step 5, and a random sample of
20 episodes. For each selected episode, open the debug logs and the Ingestion
Traces in the dashboard, or through the API when your plan and SDK expose
them. Record:

| Trace content | Question that it answers |
|---|---|
| Extraction input: episode content, previous episodes, entity types, edge types, instructions | What did the model see? Did the previous-episode list hold anything? Were the instructions present? |
| Extraction output: nodes with labels, edges with names | What did the model emit before deduplication? Which names are not in the text? |
| Node resolution: extracted node, resolved node, candidates | Which nodes merged, into what, and with which candidates? A merge onto a different record is an identity failure. |
| Edge resolution: new edges, merged edges, invalidations | How many exact repeats merged? How many near repeats survived? |
| Attempt count, validation status, error details | Did a stage retry or fail? A failed trace does not change the graph. |
| Stage timestamps | Where did the time go? |

When the API exposes the traces, aggregate the stage outputs over all episodes
with a script. Compare the totals with the graph totals from Step 5. The totals
must match. Use the explanation text as a pointer to where to look.

### Step 7. Decide the next change

Use this table. Make one change, increase the configuration version, run
again, and compare the two Step 5 tables.

| Symptom (Step 5 or 6) | Probable cause | Change |
|---|---|---|
| Extracted values of one type are not in the text | The type description lists a vocabulary | Move the type to the deterministic import. Remove the vocabulary from the description. |
| Field repeats | The extractor saw the structured field | Remove the field from the episode text and from the type description. |
| A wrong ID on an imported node | A later extraction changed the attribute (confirm in the trace) | Remove the attribute from the extractor's view, or write the imported attributes again after the narrative batch. |
| Edges between two records that must not be related | Context leaked between episodes | Check the `document_id` grouping and the lead sentence. Make each part self-identifying. |
| Many untyped nodes | A missing type | Add the noun type that the prose needs, with a membership definition. |
| A long tail of edge names | Free event extraction | Declare a closed event edge set with endpoints, or set `strict_ontology` and measure the recall cost. |
| Many generic edges | Endpoint pairs not declared | Add the `source_targets` that the prose uses. |
| The second part of a document loses its subject | No previous-episode view in a `text` batch | Repeat the identity in each part. Make the parts shorter. |
| Missing episodes | A payload limit or a renamed field | Read the batch item errors. Repair the preparation. |

Stop the iteration when the identity checks pass for each imported record,
the field repeats and the untyped share are at the level that the use case
accepts, and the gold or derived questions show that the needed facts exist in
the graph. Retrieval tuning is a separate loop. Start it after that point.

## Report format

Write one report per configuration version, and one comparison table across
versions. Use the Step 5 table as the comparison. Then write four sections in
this order:

1. Direct measurements.
2. Behavior that the documentation confirms.
3. Interpretations.
4. Open hypotheses.

State each difference between the compared runs, including the dates. Give `n`
for each rate.

Do not put episode text, personal data, or payload samples in a report. Use
aggregate counts and sanitized identifiers.

## Anti-patterns

- Sending the full record as JSON and expecting the model to produce the entity
  graph. The model produces a near copy of the record, with the IDs as entity
  names and a generic relation for each field.
- Listing the taxonomy in the type descriptions.
- Repairing a repeat with an instruction instead of a change to the data.
- Comparing two runs that differ in the data, the configuration, and the date
  at the same time.
- Running the deterministic import again without the state file.
- Deleting the graph before the comparison is written.
- Reading one trace, finding a plausible explanation, and reporting it as the
  cause.

## Documentation pointers

| Page | Content |
|---|---|
| `prepare-data-for-ingestion` | Context in each episode, event time, document IDs, seeding the graph, identity properties, limits |
| `adding-fact-triplets` | `graph.add_nodes`, `graph.add_fact_triple`, node and edge updates |
| `customizing-graph-structure` | Entity and edge types, `source_targets`, `strict_ontology`, type limits |
| `custom-instructions` | Named instruction blocks, upsert, limits |
| `documents`, `chunking-large-documents` | `document_id` and chunking |
| `adding-batch-data`, `check-data-ingestion-status` | Batch API, limits, terminal states |
| `debug-mode` | Debug logs and Ingestion Traces: enablement, retention, plan requirements |
| `reading-data-from-the-graph` | Export of nodes, edges, and episodes for the Step 5 checks |
| `evaluate-zep-for-your-use-case` | Gold-set practice, completeness and accuracy, the Zep evaluation harness |
