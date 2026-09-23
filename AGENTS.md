# Agent rules

- Aim for a testable outcome per task. Use the user's goal if given; otherwise propose a measurable one or clarify when success is ambiguous. Iterate until verified or report a real blocker; escalate architecture changes or missing access instead of inventing workarounds.
- Keep solutions simple and readable; no premature abstractions. Prefer self-explanatory code; docstrings for public APIs where useful, few inline comments.
- Deploy Azure infrastructure with Terraform and **AzAPI** (not AzureRM). Reconcile portal-created/changed resources into Terraform: describe, import, plan for no unexpected drift, then verify.
- Write application code in Python; use `uv` and `pyproject.toml`, not `requirements.txt`. Preserve the lockfile. Follow approved package-feed settings.
- Keep concise English docs under `Docs/`: product intent in `PRD.md` (create from `Docs/Templates/PRD.md` when scoped), high-level design in `architecture.md`, numbered decisions in `ADR/`, interface definitions in `Contracts/`. Use `Docs/Templates/ADR.md` and `Docs/Contracts/README.md`. Add detailed `spec.md`, `security.md`, deployment or observability docs only when useful; keep `CHANGELOG.md` brief. Git is the primary history.
- Record significant architectural choices as ADRs, including alternatives, rationale, consequences and observable review conditions. Keep contracts in the appropriate machine-readable format; update specs and tests with behavior.
- For AI products: user-facing communication primarily Czech; system/developer prompts preferably English, explicitly instruct Czech responses.
- Prefer GPT-6 Sol for routine work. Delegate only when useful: GPT-6 Astra for demanding planning/framing, GPT-6 Sol for implementation, GPT-6 Luna/Terra for simple research or triage. For high-stakes decisions, seek an independent Claude Opus 5.5 critique when available; choose subagent models by task and cost, not by habit.
- In Copilot App, when a human needs to inspect or manually exercise an API, MCP server, or database, provide and open a suitable Canvas UI alongside automated tests. Visualize progress in a Canvas when it materially helps.
- Work in Git/GitHub: descriptive, coherent commits and regular pushes at authorized milestones; resolve conflicts deliberately. Do not overwrite unrelated work.
