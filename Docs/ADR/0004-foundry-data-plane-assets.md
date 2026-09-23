---
id: 0004
status: accepted
date: 2026-09-23
review_conditions:
  - signal: "Foundry project SDK supports stable declarative lifecycle for agents, datasets and evaluators"
    source: "Azure AI Projects SDK and Foundry API release notes"
    revisit_when: "A supported, idempotent deployment mechanism covers these assets and existing portal imports"
---

# ADR-0004: Version Foundry project assets separately from Terraform

## Context

The account, project and model deployment are Azure control-plane resources,
but the existing prompt agent, evaluation dataset, custom evaluator and
evaluation runs live in the Foundry project's data plane. The web demo calls
the portal-created agent by name. Those definitions and test inputs otherwise
have no reviewed copy in the repository. Terraform state is local and must not
be repurposed as an evaluation-result archive.

## Options

- **Terraform/AzAPI for every object:** one lifecycle, but its ARM resource
  declarations do not represent these project data-plane versions and runs.
- **Preview `azd ai agent eval` and GitHub Action:** useful evaluation workflows,
  but they do not import and preserve the full existing prompt-agent history;
  the installed agent extension is currently incompatible with this host's
  `azd` version.
- **Python SDK plus checked-in assets:** reuses the project's pinned SDK,
  supports reading existing versions, and keeps prompts and JSONL independent
  of deployment code; requires an explicit snapshot/reconcile command.

## Decision and rationale

Keep ARM infrastructure in Terraform. Store project-level definitions and
curated test data under `foundry/`, with large text in separate UTF-8 files.
Use `scripts/foundry_assets.py snapshot` for read-only import and `apply` for
explicit, drift-checked restoration on the same project. Record historical
run IDs and aggregate results, but do not rerun evaluations as a side effect
of infrastructure deployment. Pin versions in the stored rerunnable recipe.
Snapshot toolbox versions and memory-store configuration separately; inventory
connection targets and authentication types without exporting credentials.

## Consequences

Portal edits require a reviewed snapshot update. The checked-in files are
not a replacement for Foundry's run history or the full result artifacts.
User memories and connection credentials are not exported. Search knowledge
sources and their generated indexes are a separate service data plane; the
read API redacts credentials needed to recreate the existing knowledge source.
Recovery of a deleted environment therefore needs independently managed
secrets and a separate Search restoration procedure before agent tools work.
Datasets and prompts must be reviewed before public commits. Changing a
model, RAI policy, connected tool or project endpoint may require a
separate infrastructure or permission change before restoration succeeds.
