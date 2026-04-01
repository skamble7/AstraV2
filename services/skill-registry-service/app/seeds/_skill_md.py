"""
Complete SKILL.md content (YAML frontmatter + Markdown body) for all seeded skills.

Each entry is the full document the Astra Agent parses at invocation time:
- Frontmatter (between --- delimiters): execution config, produces_kinds, tags, etc.
- Markdown body: instructions, inputs, outputs, chain position, notes.

The `description` field on GlobalSkill drives skill *selection*.
The `skill_md_body` frontmatter + body drives skill *execution*.

Consumed by seed_skills.py, seed_data_pipeline_skills.py, and
seed_microservices_skills.py via `skill_md_body=SKILL_MD["sk.xxx"]`.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Shared / Core Skills
# ─────────────────────────────────────────────────────────────────────────────

_DIAGRAM_GENERATE_ARCH = """\
---
name: sk.diagram.generate_arch
version: 1.0.0
status: published
tags: [data, diagram, docs, guidance, mcp]
description: >-
  Calls the MCP server to produce a Markdown architecture guidance document
  grounded on discovered data-engineering artifacts and RUN INPUTS; emits
  cam.governance.data_pipeline_arch_guidance. Use when a completed data pipeline
  discovery run is available in the workspace and a prose-style architecture
  guidance document is required for stakeholder review.
produces_kinds:
  - cam.governance.data_pipeline_arch_guidance
depends_on: []
execution:
  mode: mcp
  transport: http
  base_url: "http://host.docker.internal:8004"
  protocol_path: /mcp
  tool_name: generate_data_pipeline_arch_guidance
  timeout_sec: 3600
  verify_tls: false
  retry:
    max_attempts: 3
    backoff_ms: 250
    jitter_ms: 50
  auth:
    method: none
---

## Purpose
Calls the architecture guidance MCP server to produce a structured Markdown
document (`cam.governance.data_pipeline_arch_guidance`) that narrates the
complete data pipeline architecture discovered in the workspace. This is the
final human-facing deliverable of the data pipeline discovery pack — a
stakeholder-ready document grounded on all preceding artifacts.

## When to Use
Invoke as the **last step** in a data pipeline discovery run, after
`sk.architecture.assemble_pipeline` and `sk.deployment.plan_pipeline` are
complete. Use when a prose-style architecture document is required for
stakeholder review, design authority approval, or project handoff.

Do **not** invoke mid-run; the document quality depends on the full set of
discovery artifacts being present in the workspace.

## Inputs
The MCP tool (`generate_data_pipeline_arch_guidance`) reads directly from the
workspace via the MCP server — pass the `workspace_id` and `run_inputs`
(project name, goals, any stakeholder context). The server reads all artifact
kinds from the workspace internally; you do not need to pass artifact payloads
explicitly.

## Output: `cam.governance.data_pipeline_arch_guidance`
A Markdown governance document containing:
- Executive summary of the discovered architecture
- Architecture decisions and pattern rationale
- Dataset contracts summary
- Lineage and governance overview
- SLA and observability commitments
- Deployment and rollout guidance
- Tech stack recommendations

## Position in Discovery Chain
**Final step** — runs after all discovery, specification, and synthesis skills
are complete.

## Notes
- Timeout: 3600 seconds. Document generation is long-running; do not cancel
  prematurely.
- TLS verification is disabled for local development (`verify_tls: false`).
- If the MCP server is unavailable, inform the user and offer to produce a
  summary from the workspace artifacts instead using the LLM path.
"""

_DIAGRAM_MERMAID = """\
---
name: sk.diagram.mermaid
version: 1.0.0
status: published
tags: [diagram, mermaid, enrichment]
description: >-
  Given an artifact JSON payload and requested diagram views, returns validated
  Mermaid instructions. Use as an enrichment skill after any discovery step to
  attach visual diagrams to artifacts.
produces_kinds: []
depends_on: []
execution:
  mode: mcp
  transport: http
  base_url: "http://host.docker.internal:8001"
  protocol_path: /mcp
  tool_name: diagram.mermaid.generate
  timeout_sec: 120
  verify_tls: false
  retry:
    max_attempts: 3
    backoff_ms: 250
    jitter_ms: 50
  headers:
    host: "localhost:8001"
  auth:
    method: none
---

## Purpose
Enrichment skill. Given any structured artifact from the workspace, calls the
Mermaid diagram MCP server (`diagram.mermaid.generate`) to produce validated
Mermaid diagram instructions that visually represent the artifact. Used
automatically after each discovery step by the agent's enrichment phase.

## When to Use
This skill is an **agent enrichment skill** — it runs automatically after each
primary discovery skill, not as a user-facing step. Do **not** invoke it
directly in the playbook unless explicitly generating a standalone diagram.

Invoke directly only when the user explicitly requests a visual representation
of a specific artifact that was produced earlier in the session.

## Inputs
The MCP tool (`diagram.mermaid.generate`) accepts:
- `artifact` — the artifact JSON payload to visualise
- `diagram_views` — list of requested diagram types (e.g. `["flowchart", "ER"]`)

Discover the live input schema at runtime via `tools/list`.

## Output
Mermaid diagram instructions attached to the source artifact's `diagrams` field.
Does **not** produce a standalone `cam.*` artifact — diagrams are embedded
in the originating artifact's envelope.

## Notes
- Timeout: 120 seconds.
- Failures are **non-fatal** — if diagram generation fails, the run continues.
  Log the failure and proceed.
- The `host` header must be set correctly to reach the diagram server in Docker
  networking (already configured in execution headers).
"""

# ─────────────────────────────────────────────────────────────────────────────
# Data Pipeline Skills
# ─────────────────────────────────────────────────────────────────────────────

_ASSET_FETCH_RAINA_INPUT = """\
---
name: sk.asset.fetch_raina_input
version: 1.0.0
status: published
tags: [inputs, raina, discovery, mcp]
description: >-
  Fetches a Raina input JSON (AVC/FSS/PSS) from a URL via the MCP
  raina-input-fetcher and emits a validated cam.asset.raina_input artifact.
  Use when a workspace run requires architecture discovery inputs and a URL
  pointing to an AVC/FSS/PSS JSON payload is available. This is typically the
  first skill invoked in any RAINA-domain run — no upstream artifacts are
  required.
produces_kinds:
  - cam.asset.raina_input
depends_on: []
execution:
  mode: mcp
  transport: http
  base_url: "http://host.docker.internal:8003"
  protocol_path: /mcp
  tool_name: raina.input.fetch
  timeout_sec: 180
  verify_tls: false
  retry:
    max_attempts: 3
    backoff_ms: 250
    jitter_ms: 50
  headers:
    host: "localhost:8003"
  auth:
    method: none
---

## Purpose
Fetches and validates a Raina input document — the primary specification
artifact that drives all downstream architecture discovery. Supports three
document formats: **AVC** (Application Value Context), **FSS** (Functional
Specification Sheet), and **PSS** (Platform Specification Sheet).

## When to Use
Invoke **first** in any RAINA-domain discovery run (data pipeline or
microservices) when the user provides a URL to an AVC/FSS/PSS JSON document.

Do **not** invoke if `cam.asset.raina_input` already exists in the workspace —
use the existing artifact and proceed to the next skill.

## Inputs
The MCP tool (`raina.input.fetch`) accepts:
- `url` — URL pointing to the AVC/FSS/PSS JSON payload (required)
- `workspace_id` — target workspace identifier (required)

Discover the live input schema at runtime via `tools/list` on the MCP server.
The server validates the document format before emitting the artifact.

## Output: `cam.asset.raina_input`
A validated Raina input artifact containing the raw AVC/FSS/PSS payload:
- `format` — one of `AVC`, `FSS`, or `PSS`
- `application_context` — application name, domain, goals, NFRs (AVC)
- `functional_specs` — business flows, actors, datasets, user stories (FSS)
- `platform_specs` — infrastructure constraints, tech hints, environments (PSS)

All downstream LLM skills read this artifact directly from the workspace.

## Position in Discovery Chain
**Step 1** (v1.1 pack) — no upstream dependencies. All discovery skills
depend on this artifact.

## Notes
- Timeout: 180 seconds.
- The MCP server validates the JSON schema — malformed inputs fail at the
  server with a descriptive error. Report the error to the user.
- One `cam.asset.raina_input` per workspace. A second invocation overwrites
  the first; warn the user before re-fetching.
- If the URL requires auth, configure headers in the skill execution config.
"""

_CATALOG_INVENTORY_SOURCES = """\
---
name: sk.catalog.inventory_sources
version: 1.0.0
status: published
tags: [astra, data, inventory]
description: >-
  Enumerates principal data sources and sinks implied by flows, entities, and
  constraints. Use early in a data pipeline discovery run, after
  cam.asset.raina_input is available.
produces_kinds:
  - cam.catalog.data_source_inventory
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Enumerates all principal data sources and sinks implied by the business flows,
entities, and platform constraints in the Raina input. This inventory anchors
the data pipeline's integration surface and informs dataset contract, lineage,
and tech stack decisions.

## When to Use
Invoke early in the data pipeline discovery chain, immediately after
`cam.asset.raina_input` is available. Runs **in parallel** with
`sk.workflow.discover_business_flows` and `sk.data.discover_logical_model`
in the v1.0 playbook.

## Inputs
From the workspace:
- `cam.asset.raina_input` — FSS business flows and actors provide source/sink
  hints; AVC application context supplies domain constraints; PSS platform
  specs identify existing systems and infrastructure.

## Output: `cam.catalog.data_source_inventory`
A catalog of data sources and sinks:
- `sources` — list of `{name, type, format, owner, description, latency_class}`
- `sinks` — list of `{name, type, format, purpose}`
- `integration_notes` — cross-cutting integration constraints (auth, throttling,
  protocol requirements)

## Position in Discovery Chain
**Step 1** (v1.0 playbook). Feeds into:
- `sk.contract.define_dataset` (dataset contracts reference source systems)
- `sk.catalog.rank_tech_stack` (tech choices consider existing sources)
- `sk.data.map_lineage` (lineage starts from these sources)

## Notes
- Pure LLM skill — output quality depends on AVC/FSS richness.
- If the input has minimal FSS content, note the limitation and produce a
  best-effort inventory based on AVC application context.
"""

_WORKFLOW_DISCOVER_BUSINESS_FLOWS = """\
---
name: sk.workflow.discover_business_flows
version: 1.0.0
status: published
tags: [astra, workflow, discovery]
description: >-
  Extracts actor-centric flows mapped to datasets from AVC/FSS and architectural
  context. Use after cam.asset.raina_input is available.
produces_kinds:
  - cam.workflow.business_flow_catalog
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Extracts actor-centric business flows from the Raina input and maps each flow
to the datasets it reads or produces. This establishes the functional demand
that the data pipeline must satisfy and drives pipeline pattern selection.

## When to Use
Invoke after `cam.asset.raina_input` is available, in parallel with
`sk.catalog.inventory_sources` and `sk.data.discover_logical_model`.

## Inputs
From the workspace:
- `cam.asset.raina_input` — FSS functional specification provides actor
  definitions, use cases, and data flows; AVC provides business context.

## Output: `cam.workflow.business_flow_catalog`
A catalog of business flows:
- `flows` — list of flow objects, each with:
  - `name`, `description`, `actors[]`
  - `steps[]` — ordered steps with the datasets read/written at each step
  - `frequency`, `latency_requirement`, `criticality`
- `cross_flow_dependencies` — shared datasets across flows

## Position in Discovery Chain
**Step 2** (v1.0 playbook). Feeds into:
- `sk.architecture.select_pipeline_patterns` (flows determine batch vs stream)
- `sk.workflow.spec_batch_job` and `sk.workflow.spec_stream_job`
- `sk.workflow.define_orchestration`

## Notes
- Focus on functional flows as the user described them — do not infer
  technical implementation details at this stage.
- If FSS is absent (AVC or PSS only), derive implied flows from application
  goals and note the inference.
"""

_DATA_DISCOVER_LOGICAL_MODEL = """\
---
name: sk.data.discover_logical_model
version: 1.0.0
status: published
tags: [astra, data, modeling]
description: >-
  Derives entities, attributes, keys, and relationships from AVC/FSS/PSS and
  goals/NFRs. Use after cam.asset.raina_input is available to produce the
  logical data model.
produces_kinds:
  - cam.data.model_logical
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Derives the logical data model for the system: entities, attributes,
primary and foreign keys, relationships, and cardinalities. This model is the
structural backbone that all downstream dataset contracts, transforms, and
lineage artifacts are grounded on.

## When to Use
Invoke after `cam.asset.raina_input` is available, in parallel with
`sk.catalog.inventory_sources` and `sk.workflow.discover_business_flows`.

## Inputs
From the workspace:
- `cam.asset.raina_input` — entity hints from AVC (application value context),
  data entities from FSS functional flows, and platform constraints from PSS.

From run inputs (if provided):
- Domain scope (e.g., "focus on billing entities only")
- Naming conventions or existing schema references

## Output: `cam.data.model_logical`
The logical data model:
- `entities[]` — each with `name`, `description`, `attributes[]`, `primary_key`,
  `natural_key`, and business-domain owner
- `relationships[]` — `{from_entity, to_entity, type, cardinality, description}`
- `modeling_notes` — cross-cutting decisions and assumptions made

## Position in Discovery Chain
**Step 3** (v1.0 playbook). Feeds into:
- `sk.contract.define_dataset` (entities become dataset contracts)
- `sk.data.spec_transforms` (transforms operate on these entities)
- `sk.data.map_lineage` (entities are nodes in the lineage graph)

## Notes
- Use business-domain naming conventions for entities and attributes —
  not technical/database naming.
- If the input is PSS-only, entity derivation is limited; flag this clearly
  in `modeling_notes` and derive what is possible from platform constraints.
"""

_ARCHITECTURE_SELECT_PIPELINE_PATTERNS = """\
---
name: sk.architecture.select_pipeline_patterns
version: 1.0.0
status: published
tags: [astra, architecture, patterns]
description: >-
  Evaluates Batch/Stream/Lambda/Microservices/Event-driven patterns against
  FR/NFRs and constraints. Use after logical model and business flows are
  available.
produces_kinds:
  - cam.architecture.pipeline_patterns
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Evaluates and selects the appropriate data pipeline architecture patterns
(Batch, Streaming, Lambda, Kappa, Microservices, Event-Driven) based on the
functional requirements, NFRs, and constraints captured in the Raina input and
the discovered business flows and logical model.

## When to Use
Invoke after `sk.workflow.discover_business_flows` and
`sk.data.discover_logical_model` are complete. The pattern selection informs
all downstream specification skills.

## Inputs
From the workspace:
- `cam.asset.raina_input` — NFRs (latency, throughput, availability, cost),
  platform constraints, and tech hints from AVC/PSS
- `cam.workflow.business_flow_catalog` — flow frequencies, latency requirements,
  and criticality ratings
- `cam.data.model_logical` — entity relationships and data volumes

## Output: `cam.architecture.pipeline_patterns`
A pattern selection document:
- `selected_patterns[]` — each with `pattern_name`, `rationale`, `scope`
  (which flows/datasets it applies to), and `tradeoffs_accepted`
- `rejected_patterns[]` — patterns considered but excluded, with reasoning
- `hybrid_notes` — if multiple patterns are combined (e.g., Lambda for some
  flows, pure streaming for others)

## Position in Discovery Chain
**Step 4** (v1.0 playbook). Feeds into every downstream skill that needs to
know how data moves: batch job specs, stream job specs, orchestration,
tech stack ranking, and pipeline assembly.

## Notes
- This is the most consequential decision in the pipeline discovery chain —
  a wrong pattern choice cascades downstream. If NFRs are ambiguous, surface
  the ambiguity explicitly and propose alternatives.
- If latency < 1 minute is required for any flow, streaming must be included.
- Lambda/Kappa patterns should only be selected when the input explicitly
  signals both batch and real-time requirements for the same dataset.
"""

_CONTRACT_DEFINE_DATASET = """\
---
name: sk.contract.define_dataset
version: 1.0.0
status: published
tags: [astra, data, contracts]
description: >-
  Produces implementation-grade dataset contracts with schema, keys, PII flags,
  stewardship, quality rules, and retention. Use after pipeline patterns are
  selected.
produces_kinds:
  - cam.data.dataset_contract
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Produces implementation-grade dataset contracts for every dataset identified in
the logical model and business flows. Each contract specifies schema, keys,
PII flags, data stewardship, quality rules, and retention — making datasets
first-class, governed artifacts.

## When to Use
Invoke after `sk.architecture.select_pipeline_patterns` and
`sk.data.discover_logical_model` are complete.

## Inputs
From the workspace:
- `cam.data.model_logical` — entities and attributes become dataset fields
- `cam.architecture.pipeline_patterns` — pattern selection determines which
  datasets are streaming topics vs. batch tables vs. CDC streams
- `cam.catalog.data_source_inventory` — source system types inform field
  types and constraints
- `cam.asset.raina_input` — NFRs and domain constraints

## Output: `cam.data.dataset_contract`
A collection of dataset contracts:
- `datasets[]` — each contract contains:
  - `name`, `description`, `owner`, `domain`
  - `schema` — fields with `name`, `type`, `nullable`, `pii`, `description`
  - `primary_key[]`, `natural_key[]`
  - `quality_rules[]` — completeness, uniqueness, range, referential integrity
  - `retention_days`, `classification` (public/internal/confidential/restricted)
  - `steward`, `consumers[]`

## Position in Discovery Chain
**Step 5** (v1.0 playbook). One of the most-referenced artifacts — consumed by:
- `sk.data.spec_transforms`, `sk.workflow.spec_batch_job`,
  `sk.workflow.spec_stream_job`, `sk.data.map_lineage`,
  `sk.governance.derive_policies`, `sk.security.define_access_control`,
  `sk.security.define_masking`, `sk.catalog.data_products`

## Notes
- Every entity from the logical model should produce at least one dataset
  contract. Flag any entities without a corresponding contract.
- PII classification must be explicit — do not leave it ambiguous.
- Quality rules should be implementable (avoid vague rules like "data must be
  accurate").
"""

_DATA_SPEC_TRANSFORMS = """\
---
name: sk.data.spec_transforms
version: 1.0.0
status: published
tags: [astra, data, transform]
description: >-
  Specifies dataset-to-dataset transforms with logic and associated data quality
  checks. Use after dataset contracts are defined.
produces_kinds:
  - cam.workflow.transform_spec
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Specifies the dataset-to-dataset transformations in the pipeline, including
the transformation logic, input/output datasets, and associated data quality
checks that must pass before the transform is considered successful.

## When to Use
Invoke after `sk.contract.define_dataset` is complete and dataset contracts
exist in the workspace.

## Inputs
From the workspace:
- `cam.data.dataset_contract` — source and target dataset schemas, quality
  rules, and classification
- `cam.architecture.pipeline_patterns` — determines whether transforms run as
  batch SQL, streaming UDFs, or CDC merge operations
- `cam.workflow.business_flow_catalog` — flows indicate which datasets feed
  into which, establishing the transform DAG

## Output: `cam.workflow.transform_spec`
Transform specifications:
- `transforms[]` — each with:
  - `name`, `description`, `type` (ETL/ELT/CDC/merge/aggregate)
  - `source_datasets[]`, `target_dataset`
  - `logic_description` — business-level transformation rules
  - `quality_checks[]` — checks that must pass before writing to target
  - `idempotency_strategy` — how re-runs are handled

## Position in Discovery Chain
**Step 6** (v1.0 playbook). Feeds into:
- `sk.data.map_lineage` (transforms are edges in the lineage graph)
- `sk.workflow.define_orchestration` (transforms are wired into the job DAG)

## Notes
- Describe transformation logic at the business level — not as SQL code.
  The implementation team writes the code; this spec tells them what to build.
- Every source→target pair should have an idempotency strategy. Flag any
  transforms where idempotency is unclear.
"""

_WORKFLOW_SPEC_BATCH_JOB = """\
---
name: sk.workflow.spec_batch_job
version: 1.0.0
status: published
tags: [astra, workflow, batch]
description: >-
  Creates batch job schedules and steps (ETL/ELT/validate) aligned to pipeline
  SLAs and idempotency. Use after pipeline patterns and dataset contracts are
  defined.
produces_kinds:
  - cam.workflow.batch_job_spec
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Creates implementation-grade batch job specifications aligned to the pipeline
SLAs and idempotency requirements. Each spec covers the job schedule, ordered
processing steps (extract, transform, validate, load), error handling, and
retry strategy.

## When to Use
Invoke after `sk.architecture.select_pipeline_patterns` confirms batch
processing is required and `sk.contract.define_dataset` has produced dataset
contracts. Run in parallel with `sk.workflow.spec_stream_job`.

## Inputs
From the workspace:
- `cam.architecture.pipeline_patterns` — confirms batch scope; identifies
  which flows/datasets use batch processing
- `cam.data.dataset_contract` — field schemas, quality rules, and retention
  inform step design
- `cam.workflow.business_flow_catalog` — flow frequencies and SLAs drive
  schedule cadence

## Output: `cam.workflow.batch_job_spec`
Batch job specifications:
- `jobs[]` — each with:
  - `name`, `description`, `schedule` (cron expression)
  - `steps[]` — ordered steps: `{name, type, source, target, logic}`
  - `idempotency_strategy`, `max_retries`, `backoff_policy`
  - `sla_minutes` — maximum acceptable completion time
  - `datasets_read[]`, `datasets_written[]`

## Position in Discovery Chain
**Step 7** (v1.0 playbook). Feeds into:
- `sk.workflow.define_orchestration` (batch jobs are nodes in the DAG)
- `sk.data.map_lineage` (batch jobs are read/write lineage nodes)

## Notes
- Only generate batch job specs for flows/datasets where the selected pattern
  includes batch processing. Skip if the pattern is streaming-only.
- Every job must have an explicit idempotency strategy — no "it depends".
"""

_WORKFLOW_SPEC_STREAM_JOB = """\
---
name: sk.workflow.spec_stream_job
version: 1.0.0
status: published
tags: [astra, workflow, streaming]
description: >-
  Defines streaming jobs with sources, sinks, windowing, processing ops, and
  consistency settings. Use after pipeline patterns and dataset contracts are
  defined.
produces_kinds:
  - cam.workflow.stream_job_spec
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Defines streaming job specifications for real-time data flows: sources, sinks,
windowing strategies, processing operations, stateful/stateless classification,
and exactly-once vs. at-least-once consistency guarantees.

## When to Use
Invoke after `sk.architecture.select_pipeline_patterns` confirms streaming
is required. Run in parallel with `sk.workflow.spec_batch_job`.

## Inputs
From the workspace:
- `cam.architecture.pipeline_patterns` — confirms streaming scope; identifies
  which flows require real-time processing
- `cam.data.dataset_contract` — field schemas and quality rules for stream
  payloads
- `cam.workflow.business_flow_catalog` — latency requirements and event volumes

## Output: `cam.workflow.stream_job_spec`
Streaming job specifications:
- `jobs[]` — each with:
  - `name`, `description`, `trigger` (event-driven or time-based)
  - `sources[]` — `{topic/stream, format, parallelism}`
  - `sinks[]` — `{target, format, delivery_guarantee}`
  - `operations[]` — filter, map, aggregate, join, window operations
  - `window_config` — type (tumbling/sliding/session), size, watermark
  - `consistency` — `exactly_once` or `at_least_once` with rationale
  - `state_backend` — if stateful processing is required

## Position in Discovery Chain
**Step 8** (v1.0 playbook). Feeds into:
- `sk.workflow.define_orchestration`
- `sk.data.map_lineage`

## Notes
- Only generate streaming specs for flows where the selected pattern includes
  streaming or Lambda/Kappa. Skip if batch-only.
- Exactly-once guarantees are expensive — only recommend when the use case
  requires it (e.g., financial transactions). Flag the cost tradeoff.
"""

_WORKFLOW_DEFINE_ORCHESTRATION = """\
---
name: sk.workflow.define_orchestration
version: 1.0.0
status: published
tags: [astra, workflow, orchestration]
description: >-
  Wires batch/stream jobs into a dependency graph with failure policy, consistent
  with selected orchestrator. Use after batch and stream job specs are defined.
produces_kinds:
  - cam.workflow.orchestration_spec
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Wires the batch and stream jobs into a dependency graph (DAG), assigns failure
policies, and produces an orchestration specification consistent with the
selected orchestrator technology. This is the operational blueprint for how
all pipeline jobs are scheduled, monitored, and recovered.

## When to Use
Invoke after `sk.workflow.spec_batch_job` and `sk.workflow.spec_stream_job`
are both complete.

## Inputs
From the workspace:
- `cam.workflow.batch_job_spec` — batch jobs and their schedules/dependencies
- `cam.workflow.stream_job_spec` — streaming jobs and their trigger conditions
- `cam.architecture.pipeline_patterns` — selected orchestration approach
  (Airflow, Prefect, Dagster, etc., if specified in PSS/AVC)

## Output: `cam.workflow.orchestration_spec`
The orchestration specification:
- `orchestrator` — selected technology with rationale
- `dag` — directed acyclic graph of jobs:
  - `nodes[]` — each job with `name`, `type` (batch/stream), `schedule`
  - `edges[]` — `{from, to, condition}` dependency declarations
- `failure_policies[]` — per-job retry, alert, and fallback policies
- `sla_checks[]` — orchestrator-level SLA enforcement rules
- `backfill_strategy` — how historical re-processing is handled

## Position in Discovery Chain
**Step 9** (v1.0 playbook). Feeds into:
- `sk.observability.define_spec` (SLA monitoring hooks)
- `sk.diagram.topology` (jobs appear as topology components)
- `sk.architecture.assemble_pipeline` (included in synthesis)

## Notes
- If the AVC/PSS does not specify an orchestrator, recommend based on the
  selected patterns (e.g., Airflow for complex batch DAGs, Flink for streaming).
- Streaming jobs with event-driven triggers cannot be represented as cron
  schedules — model them as event-triggered nodes in the DAG.
"""

_DATA_MAP_LINEAGE = """\
---
name: sk.data.map_lineage
version: 1.0.0
status: published
tags: [astra, data, lineage]
description: >-
  Builds dataset/job/source lineage graph (reads/writes/derives/publishes) from
  specs and contracts. Use after transforms, batch jobs, and stream jobs are
  specified.
produces_kinds:
  - cam.data.lineage_map
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Builds the complete dataset and job lineage graph — a directed graph where
nodes are datasets, jobs, and sources, and edges represent read, write,
derive, and publish relationships. This artifact is the foundation for impact
analysis, governance audit, and data observability.

## When to Use
Invoke after transforms, batch jobs, stream jobs, and dataset contracts are
all defined. All upstream specification artifacts must be present.

## Inputs
From the workspace:
- `cam.workflow.transform_spec` — transform edges (source → target)
- `cam.workflow.batch_job_spec` — batch job read/write relationships
- `cam.workflow.stream_job_spec` — streaming job source/sink relationships
- `cam.data.dataset_contract` — dataset node metadata
- `cam.catalog.data_source_inventory` — external source nodes

## Output: `cam.data.lineage_map`
The lineage graph:
- `nodes[]` — `{id, name, type: dataset|job|source|sink, metadata}`
- `edges[]` — `{from_node, to_node, operation: reads|writes|derives|publishes,
  field_mapping_summary}`
- `critical_paths[]` — paths from sources to key business datasets
- `impact_zones[]` — clusters of artifacts affected if a source changes

## Position in Discovery Chain
**Step 10** (v1.0 playbook). Feeds into:
- `sk.governance.derive_policies` (lineage informs retention and classification)
- `sk.architecture.assemble_pipeline` (lineage is part of synthesis)

## Notes
- Every dataset in `cam.data.dataset_contract` should appear as a node.
  Flag any orphaned datasets (no incoming or outgoing edges).
- Field-level lineage is aspirational at this stage — capture it if the
  transforms are specific enough, otherwise note "field-level lineage TBD".
"""

_GOVERNANCE_DERIVE_POLICIES = """\
---
name: sk.governance.derive_policies
version: 1.0.0
status: published
tags: [astra, governance, policy]
description: >-
  Outputs classification, access/retention, and lineage requirements from
  AVC/NFR and contracts. Use after dataset contracts and lineage map are
  available.
produces_kinds:
  - cam.governance.data_governance_policies
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Derives the data governance policy set from the classification, sensitivity,
and lineage characteristics of the discovered datasets. Outputs classification
decisions, access and retention requirements, and lineage governance rules
that feed directly into access control and masking definitions.

## When to Use
Invoke after `sk.data.map_lineage` and `sk.contract.define_dataset` are
complete. Governance policies must precede access control and masking.

## Inputs
From the workspace:
- `cam.data.dataset_contract` — classification labels (public/internal/
  confidential/restricted) and PII field flags
- `cam.data.lineage_map` — lineage paths inform cross-boundary data flows
  that require governance controls
- `cam.asset.raina_input` — AVC NFRs for compliance requirements (GDPR,
  HIPAA, SOC2, etc.) and PSS regulatory environment

## Output: `cam.governance.data_governance_policies`
Governance policy document:
- `classification_policy` — rules for applying sensitivity classifications
- `retention_policies[]` — per-dataset or per-classification retention periods
  with legal hold provisions
- `access_policies[]` — who can access what classification at which level
- `lineage_requirements` — mandatory lineage tracking for regulated datasets
- `compliance_notes[]` — specific regulatory obligations identified

## Position in Discovery Chain
**Step 11** (v1.0 playbook). Feeds into:
- `sk.security.define_access_control`
- `sk.security.define_masking`
- `sk.architecture.assemble_pipeline`

## Notes
- Governance policies must be specific and enforceable — avoid generic
  statements like "all PII data must be protected".
- If regulatory requirements (GDPR/HIPAA/PCI) are identified in the input,
  surface them explicitly with specific obligations.
"""

_SECURITY_DEFINE_ACCESS_CONTROL = """\
---
name: sk.security.define_access_control
version: 1.0.0
status: published
tags: [astra, security, policy]
description: >-
  Generates dataset-role access rules (read/write/admin/mask) from
  classifications and governance policy. Use after governance policies are
  derived.
produces_kinds:
  - cam.security.data_access_control
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Generates dataset-level and field-level access control rules — which roles
or principals can read, write, or administer each dataset, and which datasets
require masking before access. Translates governance classifications into
enforceable access policies.

## When to Use
Invoke after `sk.governance.derive_policies` is complete. Runs before
`sk.security.define_masking` (masking builds on access control).

## Inputs
From the workspace:
- `cam.governance.data_governance_policies` — classification and access
  policy requirements
- `cam.data.dataset_contract` — dataset classifications, PII flags,
  consumer lists, and stewardship assignments

## Output: `cam.security.data_access_control`
Access control specification:
- `role_definitions[]` — `{role_name, description, trust_level}`
- `dataset_access_rules[]` — per dataset:
  - `dataset_name`, `classification`
  - `access_grants[]` — `{role, permission: read|write|admin|deny}`
  - `masking_required` — boolean, triggers masking policy definition
  - `conditions[]` — row-level or attribute-based conditions if applicable
- `service_account_rules[]` — pipeline job access grants

## Position in Discovery Chain
**Step 12** (v1.0 playbook). Feeds into:
- `sk.security.define_masking` (masking applies to datasets where
  `masking_required: true`)
- `sk.architecture.assemble_pipeline`

## Notes
- Every `confidential` and `restricted` dataset must have explicit deny rules
  for roles that should not access it — omission is not implicit denial.
- Pipeline service accounts should have the minimum required permissions
  (principle of least privilege).
"""

_SECURITY_DEFINE_MASKING = """\
---
name: sk.security.define_masking
version: 1.0.0
status: published
tags: [astra, security, privacy]
description: >-
  Emits field-level masking/tokenization/generalization policies for PII and
  sensitive data. Use after governance policies and access control are defined.
produces_kinds:
  - cam.security.data_masking_policy
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Emits field-level masking, tokenization, and generalization policies for
datasets containing PII or other sensitive data. Defines which transformation
applies to which field and under what access context, enabling privacy
engineering at the data platform layer.

## When to Use
Invoke after `sk.security.define_access_control` is complete. Only generate
masking policies for datasets where `masking_required: true` is set in the
access control artifact.

## Inputs
From the workspace:
- `cam.governance.data_governance_policies` — compliance requirements and
  sensitivity classifications
- `cam.data.dataset_contract` — PII field flags, field types, and
  classification per dataset
- `cam.security.data_access_control` — `masking_required` flags and
  role-level access grants per dataset

## Output: `cam.security.data_masking_policy`
Field-level masking policies:
- `masking_rules[]` — per field:
  - `dataset`, `field`, `pii_category` (name/email/phone/SSN/etc.)
  - `technique` — one of: `redact`, `tokenize`, `hash`, `pseudonymize`,
    `generalize`, `suppress`
  - `applies_to_roles[]` — roles that see the masked version
  - `cleartext_roles[]` — roles that see unmasked (if any)
  - `reversible` — boolean (for tokenization: can the original be recovered?)

## Position in Discovery Chain
**Step 13** (v1.0 playbook). Feeds into `sk.architecture.assemble_pipeline`.

## Notes
- Irreversible techniques (hash, redact) should be preferred for GDPR-scope
  data where re-identification risk must be eliminated.
- For analytics use cases, generalization (e.g., age → age band) is often
  preferable to redaction for preserving analytical utility.
- Document the tokenization vault strategy if reversible tokenization is chosen.
"""

_QA_DEFINE_DATA_SLA = """\
---
name: sk.qa.define_data_sla
version: 1.0.0
status: published
tags: [astra, quality, sla]
description: >-
  Sets SLA targets and monitoring plan (freshness, latency, availability, DQ
  pass rate). Use after pipeline architecture and dataset contracts are
  assembled.
produces_kinds:
  - cam.qa.data_sla
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Defines Service Level Agreement (SLA) targets and the monitoring plan for the
data pipeline: data freshness, processing latency, availability, data quality
pass rate, and volume expectations. These targets become the contractual
commitments the pipeline makes to its consumers.

## When to Use
Invoke after `sk.architecture.assemble_pipeline` and
`sk.contract.define_dataset` are complete. SLA targets must reference the
assembled pipeline architecture to be achievable.

## Inputs
From the workspace:
- `cam.workflow.data_pipeline_architecture` (if available) or
  `cam.architecture.pipeline_patterns` — pipeline capabilities and constraints
- `cam.data.dataset_contract` — quality rules per dataset become SLA targets
- `cam.workflow.business_flow_catalog` — business latency requirements

From run inputs (if provided):
- Target SLA tier (e.g., "Tier 1 - mission critical" vs. "Tier 3 - best effort")

## Output: `cam.qa.data_sla`
SLA definitions:
- `slas[]` — per dataset or pipeline segment:
  - `name`, `tier`, `description`
  - `freshness_target` — maximum acceptable data age
  - `latency_target_minutes` — end-to-end processing time
  - `availability_target_pct` — uptime commitment
  - `dq_pass_rate_pct` — minimum data quality rule pass rate
  - `volume_expected` — expected row/event counts for anomaly detection
  - `breach_escalation` — notification and incident response path

## Position in Discovery Chain
**Step 14** (v1.0 playbook). Feeds into:
- `sk.observability.define_spec` (SLAs determine what to instrument)

## Notes
- SLA targets must be grounded in what the selected pipeline patterns can
  actually deliver — do not set targets that contradict the architecture.
- At-least-once streaming cannot guarantee exactly-once SLA semantics;
  flag any mismatch.
"""

_OBSERVABILITY_DEFINE_SPEC = """\
---
name: sk.observability.define_spec
version: 1.0.0
status: published
tags: [astra, observability, otel]
description: >-
  Declares required metrics, logs, traces, and exporters to enforce SLAs and
  diagnose issues. Use after SLAs are defined to produce the observability
  specification.
produces_kinds:
  - cam.observability.data_observability_spec
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Declares the observability requirements for the data pipeline: what metrics,
logs, traces, and exporters are needed to enforce SLAs and diagnose issues.
Produces a specification that the platform team implements using their chosen
observability stack (OpenTelemetry, Prometheus, Grafana, Datadog, etc.).

## When to Use
Invoke after `sk.qa.define_data_sla` is complete. SLAs drive which signals
must be captured. Used in **both** data pipeline and microservices discovery
packs.

## Inputs
From the workspace:
- `cam.qa.data_sla` — SLA targets define which metrics must be captured and
  at what granularity
- `cam.workflow.orchestration_spec` (data pipeline) or
  `cam.deployment.microservices_topology` (microservices) — runtime topology
  determines where instrumentation points are placed

## Output: `cam.observability.data_observability_spec`
Observability specification:
- `metrics[]` — `{name, type: gauge|counter|histogram, labels[], sla_ref}`
- `logs[]` — `{event_name, level, required_fields[], retention_days}`
- `traces[]` — `{operation, sampling_rate, propagation_context}`
- `exporters[]` — `{type: prometheus|otel|cloudwatch, endpoint, auth}`
- `alerting_rules[]` — `{metric, condition, threshold, severity, escalation}`
- `dashboards` — list of required dashboard panels keyed to SLAs

## Position in Discovery Chain
**Step 15** (v1.0 data pipeline playbook; Step 11 microservices playbook).
Feeds into `sk.architecture.assemble_pipeline` or
`sk.architecture.assemble_microservices`.

## Notes
- Do not prescribe a specific vendor unless the PSS specifies one.
  Describe requirements in OpenTelemetry-compatible terms.
- Every SLA in `cam.qa.data_sla` must have at least one corresponding alert.
"""

_DIAGRAM_TOPOLOGY = """\
---
name: sk.diagram.topology
version: 1.0.0
status: published
tags: [astra, deployment, topology]
description: >-
  Declares platform components and links (ingest, queue, compute, storage,
  orchestration, catalog, DQ, observability) across environments. Use after
  orchestration and tech stack are defined.
produces_kinds:
  - cam.deployment.data_platform_topology
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Declares the data platform topology — all components (ingest, queue, compute,
storage, orchestration, catalog, DQ, observability) and their connections
across dev/staging/production environments. This is the deployment blueprint
that infrastructure engineers use to provision the platform.

## When to Use
Invoke after `sk.workflow.define_orchestration` and
`sk.catalog.rank_tech_stack` are complete. The topology depends on knowing
which technologies are selected.

## Inputs
From the workspace:
- `cam.workflow.orchestration_spec` — jobs and their scheduling become
  compute component requirements
- `cam.catalog.tech_stack_rankings` — selected tools become topology nodes
- `cam.architecture.pipeline_patterns` — patterns determine which component
  categories are needed
- `cam.asset.raina_input` — PSS platform specs constrain topology choices
  (cloud provider, managed services, on-prem requirements)

## Output: `cam.deployment.data_platform_topology`
Platform topology specification:
- `components[]` — each with `name`, `category`, `technology`, `role`,
  `environment` (dev/staging/prod)
- `connections[]` — `{from, to, protocol, direction}`
- `environment_config` — per-environment sizing and replication
- `network_zones[]` — VPC, subnet, and security zone assignments
- `managed_vs_self_hosted` — decisions per component with rationale

## Position in Discovery Chain
**Step 16** (v1.0 playbook). Feeds into:
- `sk.architecture.assemble_pipeline`
- `sk.deployment.plan_pipeline`

## Notes
- Keep topology at the component level — do not prescribe specific instance
  types or Kubernetes resource limits unless the PSS specifies them.
- Indicate which components are new vs. existing (from the source inventory).
"""

_CATALOG_RANK_TECH_STACK = """\
---
name: sk.catalog.rank_tech_stack
version: 1.0.0
status: published
tags: [astra, architecture, stack]
description: >-
  Produces category-wise ranked tooling (streaming, batch compute, storage,
  orchestration, DQ, catalog, observability) with rationale. Use after pipeline
  patterns and architecture are selected.
produces_kinds:
  - cam.catalog.tech_stack_rankings
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Produces a category-wise ranked list of technology options for the data
pipeline, with selection rationale grounded in the pipeline patterns,
NFRs, source systems, and any technology constraints from the Raina input.
Covers streaming, batch compute, storage, orchestration, DQ, catalog, and
observability tooling.

## When to Use
Invoke after `sk.architecture.select_pipeline_patterns` and
`sk.catalog.inventory_sources` are complete. Run before topology and
pipeline assembly, as tech choices inform both.

## Inputs
From the workspace:
- `cam.architecture.pipeline_patterns` — pattern constraints (e.g., streaming
  requires Kafka or Kinesis; Lambda requires a unified processing engine)
- `cam.catalog.data_source_inventory` — source systems may constrain compatible
  CDC or ingestion tools
- `cam.asset.raina_input` — PSS tech hints, cloud provider preferences,
  existing investments, cost constraints

## Output: `cam.catalog.tech_stack_rankings`
Technology rankings per category:
- `categories[]` — each with:
  - `category` — streaming/batch-compute/storage/orchestration/DQ/catalog/
    observability
  - `ranked_options[]` — `{rank, name, rationale, tradeoffs, fit_score}`
  - `recommendation` — top choice with selection justification

## Position in Discovery Chain
**Step 17** (v1.0 playbook). Feeds into:
- `sk.diagram.topology` (selected tools become topology nodes)
- `sk.architecture.assemble_pipeline` (included in synthesis)

## Notes
- Do not recommend tools not available in the target cloud/environment if PSS
  constrains the platform (e.g., Azure-only, on-prem).
- Rank at least 2 options per category to give the team a viable alternative.
"""

_CATALOG_DATA_PRODUCTS = """\
---
name: sk.catalog.data_products
version: 1.0.0
status: published
tags: [astra, data, product]
description: >-
  Bundles datasets into Data-as-a-Product entries with ownership and SLO
  commitment. Use after dataset contracts and pipeline architecture are
  assembled.
produces_kinds:
  - cam.catalog.data_products
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Bundles the discovered datasets into Data-as-a-Product (DaaP) entries, each
with defined ownership, SLO commitments, access interfaces, and consumer
agreements. Establishes the data mesh-style product boundary for each
significant data asset in the pipeline.

## When to Use
Invoke after `sk.contract.define_dataset` and
`sk.architecture.assemble_pipeline` are complete.

## Inputs
From the workspace:
- `cam.data.dataset_contract` — datasets, their schemas, owners, and consumer
  lists are the foundation for data product definitions
- `cam.workflow.data_pipeline_architecture` — pipeline stages group related
  datasets into logical product boundaries
- `cam.governance.data_governance_policies` — classification and stewardship
  inform product access policies

## Output: `cam.catalog.data_products`
Data product catalog:
- `products[]` — each with:
  - `name`, `description`, `domain`, `owner_team`
  - `datasets[]` — datasets bundled into this product
  - `interfaces[]` — `{type: API|table|stream|file, technology, SLO}`
  - `consumers[]` — teams or systems with access agreements
  - `slo` — freshness, availability, and quality commitments
  - `versioning_policy` — how breaking changes are communicated

## Position in Discovery Chain
**Step 18** (v1.0 playbook). Feeds into `sk.architecture.assemble_pipeline`.

## Notes
- A data product should correspond to a meaningful business domain boundary,
  not just a technical table boundary.
- Every product must have a named owner — "the data team" is not acceptable.
"""

_ARCHITECTURE_ASSEMBLE_PIPELINE = """\
---
name: sk.architecture.assemble_pipeline
version: 1.0.0
status: published
tags: [astra, workflow, architecture]
description: >-
  Synthesizes stages, routing, idempotency strategy, SLAs, and ranked tech stack
  recommendations. Use after all component specs (transforms, jobs,
  orchestration) are complete.
produces_kinds:
  - cam.workflow.data_pipeline_architecture
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
The synthesis skill. Assembles the complete, end-to-end data pipeline
architecture document by integrating all preceding artifacts into a coherent
whole. Resolves any remaining ambiguities, validates consistency across
components, and produces the definitive architectural specification.

## When to Use
Invoke as the **penultimate step** in the data pipeline discovery chain, after
all component skills (patterns, contracts, transforms, jobs, orchestration,
lineage, governance, security, SLAs, observability, topology, tech stack, and
data products) are complete.

## Inputs
From the workspace — reads all of the following:
- `cam.architecture.pipeline_patterns`
- `cam.data.dataset_contract`, `cam.workflow.transform_spec`
- `cam.workflow.batch_job_spec`, `cam.workflow.stream_job_spec`
- `cam.workflow.orchestration_spec`
- `cam.data.lineage_map`
- `cam.governance.data_governance_policies`
- `cam.security.data_access_control`, `cam.security.data_masking_policy`
- `cam.qa.data_sla`, `cam.observability.data_observability_spec`
- `cam.deployment.data_platform_topology`
- `cam.catalog.tech_stack_rankings`, `cam.catalog.data_products`

## Output: `cam.workflow.data_pipeline_architecture`
The complete architecture document:
- `overview` — executive summary and architecture principles applied
- `components` — all pipeline components with their configurations
- `integration_map` — how components connect end-to-end
- `decision_log[]` — key architectural decisions and their rationale
- `open_questions[]` — unresolved issues requiring team input
- `risks[]` — architectural risks with mitigation strategies

## Position in Discovery Chain
**Step 19** (v1.0 playbook). Feeds into `sk.deployment.plan_pipeline`.

## Notes
- Actively look for inconsistencies across the assembled artifacts (e.g., a
  batch SLA requiring sub-minute freshness, or a pattern selection that
  conflicts with a governance requirement) and call them out explicitly.
"""

_DEPLOYMENT_PLAN_PIPELINE = """\
---
name: sk.deployment.plan_pipeline
version: 1.0.0
status: published
tags: [astra, deployment, plan]
description: >-
  Creates deployment plan with phased rollout, backfill/migration, and backout
  across environments. Use as the final step after the pipeline architecture is
  assembled.
produces_kinds:
  - cam.deployment.pipeline_deployment_plan
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Creates the deployment plan for the data pipeline platform: phased rollout
across environments, data migration and backfill strategy, cutover approach,
and backout procedures. Translates the assembled architecture into an
executable delivery plan.

## When to Use
Invoke as the **final analytical step** in the data pipeline discovery chain,
after `sk.architecture.assemble_pipeline` has produced
`cam.workflow.data_pipeline_architecture`.

## Inputs
From the workspace:
- `cam.workflow.data_pipeline_architecture` — the full architecture to deploy
- `cam.deployment.data_platform_topology` — environment configuration
- `cam.asset.raina_input` — PSS deployment constraints, environment targets,
  migration timeline requirements

## Output: `cam.deployment.pipeline_deployment_plan`
Phased deployment plan:
- `phases[]` — each with:
  - `name`, `duration_estimate`, `environments[]`
  - `deliverables[]` — what is deployed/enabled in this phase
  - `entry_criteria[]`, `exit_criteria[]`
  - `rollback_procedure` — how to reverse this phase if it fails
- `migration_strategy` — how historical data is backfilled and validated
- `cutover_plan` — traffic switch from legacy to new pipeline
- `operational_readiness` — monitoring, runbooks, and on-call setup required
  before each phase

## Position in Discovery Chain
**Final step** (v1.0 playbook) — completes the analytical discovery. After
this, `sk.diagram.generate_arch` (MCP) produces the stakeholder document.

## Notes
- Phases should be independently deployable and testable. Do not plan big-bang
  cutovers unless the input explicitly constrains deployment windows.
- Every phase must have a rollback procedure — "TBD" is not acceptable.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Microservices Skills
# ─────────────────────────────────────────────────────────────────────────────

_DOMAIN_DISCOVER_UBIQUITOUS_LANGUAGE = """\
---
name: sk.domain.discover_ubiquitous_language
version: 1.0.0
status: published
tags: [astra, raina, microservices, domain]
description: >-
  Derives a concise ubiquitous language from cam.asset.raina_input (AVC/FSS/PSS).
  Use as the first analytical step after the Raina input is fetched in a
  microservices discovery run.
produces_kinds:
  - cam.domain.ubiquitous_language
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Derives the ubiquitous language for the domain being decomposed into
microservices — a shared vocabulary of domain terms, their precise definitions,
and usage context. This language is the foundation of Domain-Driven Design
(DDD) and must be shared by engineers, product owners, and domain experts.

## When to Use
Invoke as the **first analytical step** in a microservices discovery run, after
`sk.asset.fetch_raina_input` has populated `cam.asset.raina_input`.

## Inputs
From the workspace:
- `cam.asset.raina_input` — AVC application context, FSS functional
  specifications, and user stories are the primary source. The glossary,
  actor names, dataset names, and business process names all become candidate
  language terms.

## Output: `cam.domain.ubiquitous_language`
The domain glossary:
- `terms[]` — each with:
  - `term` — the exact word or phrase as used in the domain
  - `definition` — precise business definition (not a technical definition)
  - `context` — bounded context where this term has this meaning (if ambiguous)
  - `aliases[]` — synonyms used in the input documents
  - `anti_patterns[]` — incorrect usages or common confusions to avoid

## Position in Discovery Chain
**Step 2** (microservices playbook, after fetch). Feeds into:
- `sk.domain.discover_bounded_contexts`
- `sk.contract.define_event_catalog`

## Notes
- Terms should be derived from the input documents, not invented. Prefer the
  language the business uses, even if it is imprecise technically.
- Flag terms that have different meanings in different contexts — these are
  signals for bounded context boundaries.
"""

_DOMAIN_DISCOVER_BOUNDED_CONTEXTS = """\
---
name: sk.domain.discover_bounded_contexts
version: 1.0.0
status: published
tags: [astra, raina, microservices, domain, ddd]
description: >-
  Discovers bounded contexts and relationships using cam.asset.raina_input and
  cam.domain.ubiquitous_language. Use after ubiquitous language is derived.
produces_kinds:
  - cam.domain.bounded_context_map
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Applies Domain-Driven Design (DDD) principles to discover bounded contexts —
the autonomous, internally consistent domains within the system that will
correspond to microservice groups. Identifies context boundaries, relationships
between contexts, and integration patterns at the boundary.

## When to Use
Invoke after `sk.domain.discover_ubiquitous_language` produces
`cam.domain.ubiquitous_language`. The ubiquitous language is essential input
for identifying where term meanings shift across boundaries.

## Inputs
From the workspace:
- `cam.asset.raina_input` — business flows, actors, user stories, and
  system constraints from AVC/FSS define what the system must do
- `cam.domain.ubiquitous_language` — ambiguous terms and context-specific
  meanings signal bounded context boundaries

## Output: `cam.domain.bounded_context_map`
The bounded context map:
- `contexts[]` — each with:
  - `name`, `description`, `domain_responsibility`
  - `language_scope[]` — terms whose meaning is specific to this context
  - `capabilities[]` — business capabilities owned by this context
  - `data_owned[]` — datasets/entities that this context owns
- `relationships[]` — `{from, to, pattern}` where pattern is one of:
  Partnership, Shared Kernel, Customer/Supplier, Conformist, ACL,
  Open Host Service, Published Language, or Separate Ways

## Position in Discovery Chain
**Step 3** (microservices playbook). Feeds into:
- `sk.architecture.discover_microservices`

## Notes
- Bounded contexts should align with business capabilities, not organizational
  reporting structures. Flag if the two conflict.
- Anti-corruption layers (ACL) are commonly needed at the boundary with legacy
  systems — identify them explicitly.
"""

_ARCHITECTURE_DISCOVER_MICROSERVICES = """\
---
name: sk.architecture.discover_microservices
version: 1.0.0
status: published
tags: [astra, raina, microservices, service-design]
description: >-
  Derives candidate microservices aligned to bounded contexts from
  cam.domain.bounded_context_map. Use after bounded contexts are discovered.
produces_kinds:
  - cam.catalog.microservice_inventory
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Derives candidate microservices from the bounded context map, applying
microservice decomposition principles (single responsibility, autonomous
deployability, data isolation, API-first boundaries). Each bounded context
typically yields one or more microservices.

## When to Use
Invoke after `sk.domain.discover_bounded_contexts` produces
`cam.domain.bounded_context_map`.

## Inputs
From the workspace:
- `cam.domain.bounded_context_map` — bounded contexts are the primary unit
  of decomposition; each context yields one or more candidate services

## Output: `cam.catalog.microservice_inventory`
Microservice catalog:
- `services[]` — each with:
  - `name`, `description`, `bounded_context`
  - `responsibilities[]` — what this service owns and does
  - `api_type` — REST/gRPC/GraphQL/event-driven (preliminary)
  - `data_owned[]` — datasets exclusively owned by this service
  - `collaborators[]` — other services this service depends on
  - `team_ownership` — suggested team alignment (if derivable from input)
  - `deployment_unit` — standalone service vs. function vs. module

## Position in Discovery Chain
**Step 4** (microservices playbook). One of the most-referenced artifacts —
consumed by service API contracts, event catalog, data ownership, interactions,
security, and the final assembly.

## Notes
- Prefer fewer, larger services over micro-micro services when the input
  does not demand fine-grained decomposition. Flag services that look too small
  to justify independent deployment.
- Every service must have a clear primary responsibility — if you cannot
  state it in one sentence, the service boundary is wrong.
"""

_CONTRACT_DEFINE_SERVICE_APIS = """\
---
name: sk.contract.define_service_apis
version: 1.0.0
status: published
tags: [astra, raina, microservices, contracts, api]
description: >-
  Defines APIs per service using cam.catalog.microservice_inventory and
  cam.asset.raina_input user stories and constraints. Use after microservice
  inventory is produced.
produces_kinds:
  - cam.contract.service_api
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Defines the API contract for each microservice — operations, request/response
shapes, authentication requirements, versioning strategy, and SLO commitments.
API contracts are the primary integration surface between services and must be
stable, versioned, and consumer-driven.

## When to Use
Invoke after `sk.architecture.discover_microservices` produces
`cam.catalog.microservice_inventory`. Runs in parallel with
`sk.contract.define_event_catalog`.

## Inputs
From the workspace:
- `cam.catalog.microservice_inventory` — service boundaries define which
  operations each service exposes
- `cam.asset.raina_input` — user stories (FSS) and constraints define the
  functional operations each service must support

## Output: `cam.contract.service_api`
Service API contracts:
- `apis[]` — per service:
  - `service`, `protocol` (REST/gRPC/GraphQL)
  - `base_path` or `package`
  - `operations[]` — each with `name`, `method/rpc`, `description`,
    `request_schema_summary`, `response_schema_summary`, `auth_required`,
    `idempotent`
  - `versioning_strategy` — URI/header/media-type versioning
  - `slo` — availability and latency commitments per operation

## Position in Discovery Chain
**Step 5** (microservices playbook). Feeds into:
- `sk.architecture.map_service_interactions`
- `sk.security.define_architecture`

## Notes
- At this stage, define the API shape and semantics — not the implementation.
  Request/response schemas should be summarised (not full JSON Schema).
- Flag operations that cross bounded context boundaries — these are the most
  likely future coupling points.
"""

_CONTRACT_DEFINE_EVENT_CATALOG = """\
---
name: sk.contract.define_event_catalog
version: 1.0.0
status: published
tags: [astra, raina, microservices, events]
description: >-
  Defines domain events for services using cam.catalog.microservice_inventory
  and cam.domain.ubiquitous_language. Use after microservice inventory is
  produced.
produces_kinds:
  - cam.catalog.events
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Defines the domain events that microservices publish and subscribe to,
establishing the asynchronous integration contract between services. Events
are first-class citizens in a microservices architecture — they decouple
services and enable eventual consistency.

## When to Use
Invoke after `sk.architecture.discover_microservices` is complete. Run in
parallel with `sk.contract.define_service_apis`.

## Inputs
From the workspace:
- `cam.catalog.microservice_inventory` — services are event producers and
  consumers
- `cam.domain.ubiquitous_language` — event names must use ubiquitous language
  terms (e.g., `OrderPlaced`, not `OrderStatusChanged`)

## Output: `cam.catalog.events`
Domain event catalog:
- `events[]` — each with:
  - `name` — past-tense domain term (e.g., `PaymentProcessed`)
  - `description` — what business fact this event records
  - `producer` — the service that publishes this event
  - `consumers[]` — services that subscribe to this event
  - `payload_summary` — key fields in the event payload
  - `ordering_guarantee` — ordered/unordered, per-key or global
  - `retention` — how long the event is retained in the broker

## Position in Discovery Chain
**Step 6** (microservices playbook). Feeds into:
- `sk.architecture.map_service_interactions`
- `sk.architecture.select_integration_patterns`

## Notes
- Events should record business facts, not commands ("OrderPlaced" not
  "PlaceOrder"). Commands are API operations; events are state transitions.
- Flag events with multiple producers — this usually signals a bounded context
  violation.
"""

_DATA_DEFINE_OWNERSHIP = """\
---
name: sk.data.define_ownership
version: 1.0.0
status: published
tags: [astra, raina, microservices, data]
description: >-
  Assigns data ownership boundaries and persistence strategy per service using
  cam.catalog.microservice_inventory and cam.asset.raina_input. Use after
  service APIs and event catalog are defined.
produces_kinds:
  - cam.data.service_data_ownership
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Assigns data ownership boundaries and persistence strategy per microservice —
which service owns which data, how data is isolated between services, and
what persistence technology each service uses. Enforces the "database per
service" principle of microservices architecture.

## When to Use
Invoke after service APIs and event catalog are defined. Runs as step 7 in
the microservices playbook.

## Inputs
From the workspace:
- `cam.catalog.microservice_inventory` — services and their declared
  data ownership from the inventory
- `cam.asset.raina_input` — platform constraints from PSS (available
  databases, licensing, cloud provider) and consistency requirements from AVC

## Output: `cam.data.service_data_ownership`
Data ownership assignments:
- `service_data[]` — per service:
  - `service`, `owned_datasets[]`
  - `persistence_technology` — database type (relational/document/column/
    graph/time-series) and specific technology recommendation
  - `isolation_pattern` — schema-per-service/database-per-service/
    schema-per-tenant
  - `shared_data_access` — read-only projections exposed to other services
    (event-sourced read models, API-exposed views)
  - `consistency_model` — strong/eventual/causal

## Position in Discovery Chain
**Step 7** (microservices playbook). Feeds into:
- `sk.architecture.map_service_interactions`
- `sk.security.define_architecture`

## Notes
- Shared databases between services are an anti-pattern. If the input suggests
  a shared database, explicitly flag it and propose the correct decomposition.
- Saga pattern implications for distributed transactions should be noted here.
"""

_ARCHITECTURE_MAP_SERVICE_INTERACTIONS = """\
---
name: sk.architecture.map_service_interactions
version: 1.0.0
status: published
tags: [astra, raina, microservices, interactions]
description: >-
  Maps service interactions based on service APIs and events (sync/async,
  direction, contracts). Use after service APIs, events, and data ownership are
  defined.
produces_kinds:
  - cam.architecture.service_interaction_matrix
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Maps all service-to-service interactions — synchronous API calls and
asynchronous event flows — creating a complete interaction matrix that reveals
coupling, critical paths, and potential failure cascades.

## When to Use
Invoke after service APIs (`cam.contract.service_api`), event catalog
(`cam.catalog.events`), and data ownership (`cam.data.service_data_ownership`)
are all defined.

## Inputs
From the workspace:
- `cam.contract.service_api` — defines synchronous call relationships
- `cam.catalog.events` — defines asynchronous event flows between services
- `cam.data.service_data_ownership` — data ownership informs read patterns
  (e.g., query-side reads from another service's projection)

## Output: `cam.architecture.service_interaction_matrix`
Service interaction map:
- `interactions[]` — each with:
  - `from_service`, `to_service`
  - `type` — sync-api-call / async-event / read-projection
  - `contract` — reference to the API operation or event name
  - `direction` — request-response / fire-and-forget / pub-sub
  - `criticality` — blocking/non-blocking, circuit-break required?
- `critical_paths[]` — chains of interactions that form the core user journeys
- `coupling_hotspots[]` — services with high fan-in or fan-out

## Position in Discovery Chain
**Step 8** (microservices playbook). Feeds into:
- `sk.architecture.select_integration_patterns`
- `sk.security.define_architecture`

## Notes
- Flag any synchronous call chains longer than 3 hops — these are fragility
  risks and candidates for async decomposition.
- Fan-out > 5 from a single service is a design smell — surface it.
"""

_ARCHITECTURE_SELECT_INTEGRATION_PATTERNS = """\
---
name: sk.architecture.select_integration_patterns
version: 1.0.0
status: published
tags: [astra, raina, microservices, integration]
description: >-
  Selects integration patterns (sync/async, saga, outbox, retries, idempotency)
  using interactions and data ownership. Use after service interaction matrix is
  produced.
produces_kinds:
  - cam.architecture.integration_patterns
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Selects the integration patterns that govern how microservices communicate and
coordinate: synchronous vs. asynchronous patterns, saga choreography vs.
orchestration, outbox pattern, idempotency contracts, and retry/circuit-break
strategies. These patterns are the operational backbone of the microservices
architecture.

## When to Use
Invoke after `sk.architecture.map_service_interactions` is complete. The
interaction matrix reveals where each pattern is needed.

## Inputs
From the workspace:
- `cam.architecture.service_interaction_matrix` — interaction types and
  criticality ratings drive pattern selection
- `cam.data.service_data_ownership` — distributed transaction boundaries
  determine where saga patterns apply

## Output: `cam.architecture.integration_patterns`
Integration pattern decisions:
- `patterns[]` — each with:
  - `name` — e.g., Saga/Choreography, Saga/Orchestration, Outbox,
    CQRS, API Gateway, BFF, Circuit Breaker, Bulkhead
  - `applies_to[]` — services or interaction pairs where this applies
  - `rationale` — why this pattern was selected for this context
  - `implementation_notes` — key implementation considerations
- `message_broker` — selected broker technology with rationale (if async)
- `api_gateway` — gateway pattern and routing strategy (if applicable)

## Position in Discovery Chain
**Step 9** (microservices playbook). Feeds into:
- `sk.security.define_architecture`
- `sk.deployment.define_topology`
- `sk.catalog.rank_tech_stack_microservices`

## Notes
- Saga choreography scales better but is harder to debug; saga orchestration
  is easier to reason about but introduces an orchestrator as SPOF. Make the
  tradeoff explicit.
- Outbox pattern is required for any saga step that writes to a database and
  publishes an event atomically.
"""

_SECURITY_DEFINE_ARCHITECTURE_MICROSERVICES = """\
---
name: sk.security.define_architecture
version: 1.0.0
status: published
tags: [astra, raina, microservices, security]
description: >-
  Defines identity, edge security, service-to-service trust, data protection,
  and mitigations using service inventory, API contracts, and inputs. Use after
  interactions and integration patterns are defined.
produces_kinds:
  - cam.security.microservices_security_architecture
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Defines the security architecture for the microservices system: identity and
authentication (human and machine), edge security, service-to-service trust
(zero-trust vs. network trust), data protection in transit and at rest,
and threat mitigations for the specific attack surface this architecture presents.

## When to Use
Invoke after service interactions and integration patterns are defined. Security
architecture requires knowing how services communicate before it can specify
how they authenticate each other.

## Inputs
From the workspace:
- `cam.catalog.microservice_inventory` — service inventory defines the security
  perimeter per service
- `cam.contract.service_api` — API operations determine auth requirements
- `cam.architecture.integration_patterns` — patterns determine which trust
  models apply (mTLS for service mesh, JWT for API gateway, etc.)
- `cam.asset.raina_input` — AVC security NFRs and PSS compliance requirements

## Output: `cam.security.microservices_security_architecture`
Security architecture document:
- `identity` — IdP selection, token format (JWT/PASETO), scopes
- `edge_security` — API gateway auth, WAF, rate limiting, DDoS protection
- `service_to_service_trust` — mTLS/JWT/network policy, service mesh or not
- `data_protection` — encryption at rest per storage type, in-transit (TLS)
- `secrets_management` — vault strategy (HashiCorp Vault, AWS Secrets Manager)
- `threat_model[]` — top threats specific to this architecture with mitigations
- `compliance_controls[]` — specific controls required by regulatory obligations

## Position in Discovery Chain
**Step 10** (microservices playbook). Feeds into:
- `sk.deployment.define_topology`
- `sk.architecture.assemble_microservices`

## Notes
- Zero-trust (mTLS between all services) is preferable for sensitive domains
  but requires a service mesh — note the operational overhead.
- If the input specifies a cloud provider, align recommendations with that
  provider's native security services.
"""

_DEPLOYMENT_DEFINE_TOPOLOGY = """\
---
name: sk.deployment.define_topology
version: 1.0.0
status: published
tags: [astra, raina, microservices, deployment]
description: >-
  Defines runtime topology, networking, environments, and dependencies using
  service inventory and security architecture. Use after security architecture
  is defined.
produces_kinds:
  - cam.deployment.microservices_topology
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Defines the runtime deployment topology for the microservices system: container
orchestration platform, networking topology, service-to-service network policy,
environment configurations (dev/staging/prod), and infrastructure dependencies.

## When to Use
Invoke after `sk.security.define_architecture` is complete — security
architecture constrains network topology choices (e.g., service mesh placement,
network zones).

## Inputs
From the workspace:
- `cam.catalog.microservice_inventory` — services become deployment units
- `cam.security.microservices_security_architecture` — security zones,
  network policies, and mTLS requirements shape topology
- `cam.asset.raina_input` — PSS platform constraints (cloud provider,
  Kubernetes version, on-prem requirements)

## Output: `cam.deployment.microservices_topology`
Deployment topology specification:
- `platform` — container orchestration (Kubernetes, ECS, etc.) with rationale
- `services[]` — per service:
  - `deployment_type` — Deployment/StatefulSet/Function
  - `replicas` — per environment (min/max for autoscaling)
  - `resources` — CPU/memory requests and limits (estimated)
  - `health_check` — liveness and readiness probe specification
- `networking` — ingress, service mesh (if applicable), DNS strategy
- `network_policies[]` — which services can talk to which (allow/deny)
- `environments[]` — dev/staging/prod configuration differences
- `dependencies[]` — managed infrastructure (databases, brokers, caches)

## Position in Discovery Chain
**Step 12** (microservices playbook). Feeds into:
- `sk.catalog.rank_tech_stack_microservices`
- `sk.architecture.assemble_microservices`

## Notes
- Service mesh (Istio/Linkerd) adds significant operational complexity —
  only recommend it when mTLS and fine-grained traffic management are required.
- Do not specify exact resource limits unless the PSS provides load estimates;
  note them as "to be sized during capacity planning".
"""

_CATALOG_RANK_TECH_STACK_MICROSERVICES = """\
---
name: sk.catalog.rank_tech_stack_microservices
version: 1.0.0
status: published
tags: [astra, raina, microservices, tech-stack]
description: >-
  Ranks tech choices aligned to integration patterns, deployment topology, and
  cam.asset.raina_input constraints/tech hints. Use after integration patterns
  and deployment topology are defined.
produces_kinds:
  - cam.catalog.tech_stack_rankings
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Ranks technology options for the microservices system — API gateway, service
mesh, message broker, container orchestration, service discovery, distributed
tracing, and developer tooling — grounded in the selected integration patterns,
deployment topology, and any technology constraints from the Raina input.

## When to Use
Invoke after `sk.architecture.select_integration_patterns` and
`sk.deployment.define_topology` are complete.

## Inputs
From the workspace:
- `cam.architecture.integration_patterns` — pattern choices constrain broker
  and API gateway options
- `cam.deployment.microservices_topology` — platform choice constrains
  compatible tooling
- `cam.asset.raina_input` — PSS technology hints, cloud provider, existing
  investments, cost constraints

## Output: `cam.catalog.tech_stack_rankings`
Technology rankings per category:
- `categories[]` — each with:
  - `category` — api-gateway/service-mesh/message-broker/container-orchestration/
    service-discovery/distributed-tracing/developer-tooling
  - `ranked_options[]` — `{rank, name, rationale, tradeoffs, fit_score}`
  - `recommendation` — top choice with justification

## Position in Discovery Chain
**Step 13** (microservices playbook). Feeds into:
- `sk.architecture.assemble_microservices`

## Notes
- Do not recommend tools from a cloud provider not specified in the PSS.
- This is the microservices-specific tech stack ranking. It produces the same
  artifact kind (`cam.catalog.tech_stack_rankings`) as the data pipeline
  version but covers a different set of categories.
"""

_ARCHITECTURE_ASSEMBLE_MICROSERVICES = """\
---
name: sk.architecture.assemble_microservices
version: 1.0.0
status: published
tags: [astra, raina, microservices, synthesis]
description: >-
  Synthesizes the end-to-end microservices architecture from all preceding
  artifacts into the primary deliverable. Use as the final synthesis step in a
  microservices discovery run.
produces_kinds:
  - cam.architecture.microservices_architecture
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
The synthesis skill for microservices discovery. Integrates all preceding
discovery artifacts into a coherent, complete microservices architecture
document. Resolves inconsistencies, validates the overall design, and produces
the definitive architecture specification that serves as the engineering team's
north star.

## When to Use
Invoke as the **penultimate step** in the microservices discovery chain, after
all preceding skills (ubiquitous language through topology and tech stack) are
complete.

## Inputs
From the workspace — reads all of the following:
- `cam.domain.ubiquitous_language`, `cam.domain.bounded_context_map`
- `cam.catalog.microservice_inventory`
- `cam.contract.service_api`, `cam.catalog.events`
- `cam.data.service_data_ownership`
- `cam.architecture.service_interaction_matrix`
- `cam.architecture.integration_patterns`
- `cam.security.microservices_security_architecture`
- `cam.observability.data_observability_spec`
- `cam.deployment.microservices_topology`
- `cam.catalog.tech_stack_rankings`

## Output: `cam.architecture.microservices_architecture`
Complete microservices architecture document:
- `overview` — executive summary and design principles
- `domain_model` — bounded contexts and service boundaries diagram description
- `service_catalog` — all services with their responsibilities and APIs
- `integration_architecture` — how services communicate and coordinate
- `data_architecture` — data ownership and consistency strategy
- `security_architecture` — end-to-end security model
- `operational_architecture` — observability, deployment, and runbook pointers
- `decision_log[]` — architectural decisions with rationale (ADR format)
- `open_questions[]` — items requiring team validation
- `risks[]` — architectural risks with mitigations

## Position in Discovery Chain
**Step 14** (microservices playbook). Feeds into `sk.deployment.plan_migration`.

## Notes
- Surface any unresolved inconsistencies explicitly in `open_questions` —
  do not paper over contradictions between component artifacts.
- The decision log should capture the 3-5 most consequential decisions made
  during discovery, in ADR format.
"""

_DEPLOYMENT_PLAN_MIGRATION = """\
---
name: sk.deployment.plan_migration
version: 1.0.0
status: published
tags: [astra, raina, microservices, migration]
description: >-
  Creates a phased migration and rollout plan using the final architecture and
  cam.asset.raina_input constraints. Use as the final step after the
  microservices architecture is assembled.
produces_kinds:
  - cam.deployment.microservices_migration_plan
depends_on: []
execution:
  mode: llm
  llm_config_ref: dev.llm.openai.fast
---

## Purpose
Creates a phased migration and rollout plan for transitioning to the discovered
microservices architecture, whether migrating from a monolith, replacing an
existing microservices system, or building greenfield. Covers delivery phases,
strangler-fig pattern application, data migration, and backout procedures.

## When to Use
Invoke as the **final analytical step** in the microservices discovery chain,
after `sk.architecture.assemble_microservices` is complete.

## Inputs
From the workspace:
- `cam.architecture.microservices_architecture` — the target architecture to
  migrate toward
- `cam.asset.raina_input` — AVC/PSS migration constraints (timeline, phased
  rollout requirements, legacy system constraints, compliance gates)

## Output: `cam.deployment.microservices_migration_plan`
Phased migration plan:
- `migration_strategy` — greenfield / strangler-fig / big-bang with rationale
- `phases[]` — each with:
  - `name`, `duration_estimate`, `goal`
  - `services_introduced[]` — microservices introduced in this phase
  - `legacy_components_retired[]` — monolith or legacy services decommissioned
  - `data_migration_steps[]` — how data is migrated for this phase
  - `traffic_routing` — how traffic shifts from legacy to new services
  - `entry_criteria[]`, `exit_criteria[]`
  - `rollback_procedure`
- `risk_register[]` — migration-specific risks and mitigations
- `go_live_checklist` — operational readiness items for production launch

## Position in Discovery Chain
**Final step** (microservices playbook). After this, `sk.architecture.generate_guidance`
(MCP) produces the stakeholder document.

## Notes
- Strangler-fig is almost always safer than big-bang for brownfield migrations —
  recommend it unless the input explicitly constrains this choice.
- Data migration is usually the highest-risk phase — it must have independent
  validation gates before traffic is switched.
"""

_ARCHITECTURE_GENERATE_GUIDANCE_MICROSERVICES = """\
---
name: sk.architecture.generate_guidance
version: 1.0.0
status: published
tags: [microservices, docs, guidance, mcp, raina, astra]
description: >-
  Calls the MCP server to produce a Markdown microservices architecture guidance
  document grounded on discovered microservices artifacts and RUN INPUTS; emits
  cam.governance.microservices_arch_guidance. Use when a completed microservices
  discovery run is available and a prose-style guidance document is required for
  stakeholder review.
produces_kinds:
  - cam.governance.microservices_arch_guidance
depends_on: []
execution:
  mode: mcp
  transport: http
  base_url: "http://host.docker.internal:8004"
  protocol_path: /mcp
  tool_name: generate_microservices_arch_guidance
  timeout_sec: 180
  verify_tls: false
  retry:
    max_attempts: 3
    backoff_ms: 250
    jitter_ms: 50
  auth:
    method: none
---

## Purpose
Calls the architecture guidance MCP server to produce a structured Markdown
document (`cam.governance.microservices_arch_guidance`) that narrates the
complete microservices architecture discovered in the workspace. This is the
final human-facing deliverable — a stakeholder-ready document for design
authority review, team alignment, or project handoff.

## When to Use
Invoke as the **last step** in a microservices discovery run, after
`sk.architecture.assemble_microservices` and `sk.deployment.plan_migration`
are complete.

Do **not** invoke mid-run; the document quality depends on the full set of
microservices discovery artifacts being present.

## Inputs
The MCP tool (`generate_microservices_arch_guidance`) reads directly from the
workspace via the MCP server — pass `workspace_id` and `run_inputs` (project
name, goals, audience context). The server aggregates all workspace artifacts
internally.

## Output: `cam.governance.microservices_arch_guidance`
A Markdown governance document containing:
- Executive summary of the discovered microservices architecture
- Bounded context and service boundary decisions
- Integration and communication architecture
- Security model summary
- Deployment and operational readiness guidance
- Migration plan overview
- Technology recommendations

## Position in Discovery Chain
**Final step** in the microservices discovery pack — runs after all analytical
skills are complete.

## Notes
- Timeout: 180 seconds.
- TLS verification is disabled for local development (`verify_tls: false`).
- If the MCP server is unavailable, offer to produce a summary from the
  workspace artifacts using an LLM-based synthesis instead.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Public registry
# ─────────────────────────────────────────────────────────────────────────────

SKILL_MD: dict[str, str] = {
    # Core / shared
    "sk.diagram.generate_arch": _DIAGRAM_GENERATE_ARCH,
    "sk.diagram.mermaid": _DIAGRAM_MERMAID,
    # Data pipeline
    "sk.asset.fetch_raina_input": _ASSET_FETCH_RAINA_INPUT,
    "sk.catalog.inventory_sources": _CATALOG_INVENTORY_SOURCES,
    "sk.workflow.discover_business_flows": _WORKFLOW_DISCOVER_BUSINESS_FLOWS,
    "sk.data.discover_logical_model": _DATA_DISCOVER_LOGICAL_MODEL,
    "sk.architecture.select_pipeline_patterns": _ARCHITECTURE_SELECT_PIPELINE_PATTERNS,
    "sk.contract.define_dataset": _CONTRACT_DEFINE_DATASET,
    "sk.data.spec_transforms": _DATA_SPEC_TRANSFORMS,
    "sk.workflow.spec_batch_job": _WORKFLOW_SPEC_BATCH_JOB,
    "sk.workflow.spec_stream_job": _WORKFLOW_SPEC_STREAM_JOB,
    "sk.workflow.define_orchestration": _WORKFLOW_DEFINE_ORCHESTRATION,
    "sk.data.map_lineage": _DATA_MAP_LINEAGE,
    "sk.governance.derive_policies": _GOVERNANCE_DERIVE_POLICIES,
    "sk.security.define_access_control": _SECURITY_DEFINE_ACCESS_CONTROL,
    "sk.security.define_masking": _SECURITY_DEFINE_MASKING,
    "sk.qa.define_data_sla": _QA_DEFINE_DATA_SLA,
    "sk.observability.define_spec": _OBSERVABILITY_DEFINE_SPEC,
    "sk.diagram.topology": _DIAGRAM_TOPOLOGY,
    "sk.catalog.rank_tech_stack": _CATALOG_RANK_TECH_STACK,
    "sk.catalog.data_products": _CATALOG_DATA_PRODUCTS,
    "sk.architecture.assemble_pipeline": _ARCHITECTURE_ASSEMBLE_PIPELINE,
    "sk.deployment.plan_pipeline": _DEPLOYMENT_PLAN_PIPELINE,
    # Microservices
    "sk.domain.discover_ubiquitous_language": _DOMAIN_DISCOVER_UBIQUITOUS_LANGUAGE,
    "sk.domain.discover_bounded_contexts": _DOMAIN_DISCOVER_BOUNDED_CONTEXTS,
    "sk.architecture.discover_microservices": _ARCHITECTURE_DISCOVER_MICROSERVICES,
    "sk.contract.define_service_apis": _CONTRACT_DEFINE_SERVICE_APIS,
    "sk.contract.define_event_catalog": _CONTRACT_DEFINE_EVENT_CATALOG,
    "sk.data.define_ownership": _DATA_DEFINE_OWNERSHIP,
    "sk.architecture.map_service_interactions": _ARCHITECTURE_MAP_SERVICE_INTERACTIONS,
    "sk.architecture.select_integration_patterns": _ARCHITECTURE_SELECT_INTEGRATION_PATTERNS,
    "sk.security.define_architecture": _SECURITY_DEFINE_ARCHITECTURE_MICROSERVICES,
    "sk.deployment.define_topology": _DEPLOYMENT_DEFINE_TOPOLOGY,
    "sk.catalog.rank_tech_stack_microservices": _CATALOG_RANK_TECH_STACK_MICROSERVICES,
    "sk.architecture.assemble_microservices": _ARCHITECTURE_ASSEMBLE_MICROSERVICES,
    "sk.deployment.plan_migration": _DEPLOYMENT_PLAN_MIGRATION,
    "sk.architecture.generate_guidance": _ARCHITECTURE_GENERATE_GUIDANCE_MICROSERVICES,
}
