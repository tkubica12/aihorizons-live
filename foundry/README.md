# Foundry project assets

Terraform/AzAPI manages the Foundry account, project, and model deployment. This
directory snapshots the **project data plane** from `aihorizons`:

- `agents/<name>/<version>/definition.json` and `instructions.txt` preserve
  every saved prompt-agent version. `manifest.json` identifies the current one.
  Coded hosted/external agents `pizza-staff-langgraph` and
  `pizza-hello-external` are deployed by `scripts/deploy_agents.py`, not restored
  from prompt-agent definitions here; their staff toolbox and credential-free
  connection metadata are included in this snapshot.
- `datasets/<name>/<version>/data.jsonl` is the exact uploaded JSONL content;
  `dataset.json` records its SHA-256.
- `evaluators/<name>/<version>/evaluator.json` and `prompt.txt` preserve custom
  evaluator versions.
- `evaluations/<name>/evaluation.json` stores the evaluation schema, criteria,
  dataset, and target. `runs.json` records past run IDs, source configurations,
  statuses, counts, and report links; it does not copy item-level results.
- `toolboxes/<name>/<version>/toolbox.json` stores every toolbox version,
  including MCP tool references and RAI policies; the manifest marks its
  default version.
- `memory_stores/<name>/memory_store.json` stores the memory-store definition,
  options and prompt, **not** per-user stored memories.
- `connections.json` inventories project connections (including the MCP
  services, Search knowledge base and Foundry MCP Server), their targets and
  authentication *types*. Credentials and sensitive service metadata are
  deliberately excluded; this is not a connection restoration recipe.

The snapshot was taken from the project endpoint in `manifest.json`. The
original evaluation used an unpinned agent version and evaluator version. The
saved *rerunnable recipe* pins the agent and evaluator versions observed at
snapshot time; the historical run sources in `runs.json` remain unchanged.
Replaying the recipe therefore does not retroactively reproduce the exact
conditions of older runs.

After `az login`, use the existing project dependencies:

```powershell
uv run --no-sync python scripts\foundry_assets.py validate
uv run --no-sync python scripts\foundry_assets.py snapshot
# To intentionally replace locally edited files with the current portal state:
uv run --no-sync python scripts\foundry_assets.py snapshot --overwrite
# Read-only comparison against the Foundry project:
uv run --no-sync python scripts\foundry_assets.py check
# Explicit write operation; do not invoke automatically with Terraform:
uv run --no-sync python scripts\foundry_assets.py apply
```

`snapshot` reads the project's agents, custom evaluators, datasets,
evaluations, toolboxes, memory-store definitions, and connection metadata.
It refuses a partial export if indexes, evaluation rules, skills, routines,
schedules, evaluation taxonomies, insight monitors or red teams are present;
those definitions need a separate exporter if added later. It obtains a
short-lived dataset SAS through the Foundry API and never prints or stores
the SAS. If local files differ, it fails without overwriting them unless
`--overwrite` is provided. Dataset export currently supports one JSONL blob
per dataset version, up to 5 MB; other layouts fail explicitly.

`check` compares the saved connection inventory and existing definitions
without changing Azure. `apply` validates the snapshot and checks existing
remote definitions before writing. It creates missing memory stores and
toolboxes, uploads missing dataset versions, creates missing agents/evaluators,
and creates a separate `<evaluation-name>-repo` evaluation group if absent.
It never replaces the original evaluation group, deletes historical assets, or
starts a paid evaluation run. It rejects a different project endpoint and
divergent definitions or dataset bytes rather than silently overwriting portal
work. Restoring into a different project, recreating the exact original
version numbers, per-user memories, and registering the custom `Guardrails402`
RAI policy are not covered by this script. Restore the Terraform-managed
project, model deployments, RAI policy, identity roles and Search connection
first. Recreate the project MCP connections and their credentials separately:
`scripts/configure_foundry_mcp.py` handles the two demo services, while the
Search knowledge-base and catalog MCP connections require their own
registration/identity configuration. Only then run `check` or explicitly
approve `apply`. The Search knowledge source, index and other Search
data-plane dependencies are separate from this Foundry project snapshot;
`infra/README.md` documents the currently redacted credentials that prevent
a complete read-only reconstruction of that source. This snapshot alone
cannot recover a deleted environment.

**Review datasets, prompts, and results before committing snapshots.** This
repository is public. The saved `pizza_customers` dataset was generated for
the demo; do not add real customer conversations, credentials, signed URLs,
or private evaluation output. Changes made in the portal are not
automatically reflected here: explicitly snapshot, review the diff, and
commit the intended revision.
