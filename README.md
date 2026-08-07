# Build with Zep

The Build with Zep plugin helps Claude Code, Codex, and Cursor build applications
with [Zep](https://www.getzep.com).

This repository is the canonical source for the plugin. The shared Zep
marketplace in [`getzep/zep`](https://github.com/getzep/zep) points here; no
submodule or copied package is required.

## User documentation

For installation, usage, supported agents, and an overview, see
[Implement Zep with agents](https://help.getzep.com/implement-zep-with-agents).

## Portable core plus vendor compatibility

The repository root conforms to
[Agent Plugins 1.0.0](https://agent-plugins.org/): `plugin.json` identifies the
package, `skills/` contains the portable skill, and `mcp.json` declares the
Streamable HTTP documentation server.

Vendor files remain alongside that portable core so clients do not need to
adopt the standard before installing the plugin:

- **Claude Code** — `.claude-plugin/plugin.json` and Claude-shaped `.mcp.json`
- **OpenAI Codex / ChatGPT Work** — `.codex-plugin/plugin.json` and `.mcp.json`
- **Cursor** — natively loads the Agent Plugins package; `.cursor-plugin/`
  remains for Cursor marketplace metadata and team marketplace import

Every package path loads the same `skills/building-with-zep/` tree.

Claude and ChatGPT Work/Codex marketplace entries live in `getzep/zep` and point
at this GitHub repo with no duplicate version. Cursor catalogs only resolve
same-repo plugin paths, so Cursor installs or team-imports **this** repository
directly rather than via the shared `getzep/zep` Cursor catalog.

## MCP configuration

`zep-docs` is declared in three schema-specific files because the portable and
vendor MCP schemas use different transport names:

| File | Read by | Shape |
|---|---|---|
| `mcp.json` | Agent Plugins clients | `{"type":"streamable-http","url":...}` plus the 1.0.0 schema |
| `.mcp.json` | Claude Code, OpenAI Codex / ChatGPT Work | `{"type":"http","url":...}` |
| `.cursor-plugin/mcp.json` | Cursor vendor wrapper | `{"url":...}` |

Both point at `https://docs-mcp.getzep.com/mcp`. Change both together.

## Repository contents

```text
.
├── plugin.json
├── mcp.json
├── skills/building-with-zep/SKILL.md
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
├── .cursor-plugin/plugin.json
├── .cursor-plugin/marketplace.json
├── .cursor-plugin/mcp.json
├── .mcp.json
├── scripts/plugin_manifests.py
├── scripts/validate_agent_plugin.py
├── AGENTS.md
├── CHANGELOG.md
└── README.md
```

## Local development

```bash
claude --plugin-dir .
```

For Cursor, symlink this repository into the local plugin folder, then reload:

```bash
ln -s "$PWD" ~/.cursor/plugins/local/building-with-zep
```

## Releasing

Merging to `main` updates the plugin source consumed by the marketplace. Keep
the Agent Plugins manifest and all three vendor manifests on one version:

```bash
python3 scripts/plugin_manifests.py set <version>
```

Then:

1. Add a `CHANGELOG.md` entry.
2. Run `claude plugin validate . --strict`.
3. Run `python3 scripts/plugin_manifests.py --check`.
4. Run `python3 scripts/validate_agent_plugin.py`.
5. Open the PR and confirm `test-plugin.yml` passes.

There is no package-publish or tag step. Explicit semver is retained as a stable
cross-ecosystem support identifier; CI flags loaded-content changes without a
version increase.

## What goes in the skill vs. the docs

The skill is the **decision-and-workflow layer**, not a second copy of the
product docs. When deciding where a piece of content belongs, follow this rule:

> **Put stable, cross-cutting (not confined to a single doc page) philosophy,
> decision rules, and critical invariants in the skill. Use the docs for
> volatile and exhaustive facts. Add reference files only when they provide
> agent-specific value not well served by the docs — or when a self-contained,
> versioned fallback is intentionally required.**

Concretely:

- **Belongs in `SKILL.md`** — mental models, differentiators, decision rules,
  and invariants that are cross-cutting and stable over time. E.g. "Zep is not a
  chat-log store and not a vector database," "ontology defines the *shape* of the
  graph; instructions define *how to interpret* your domain."
- **Leave to the docs** (via the `zep-docs` MCP and the skill's documentation
  index) — volatile or exhaustive detail: method names, parameters, limits, plan
  availability, pricing, exact reranker names, template syntax, and the **full
  list of best practices for a given feature**. These drift, and the agent can
  retrieve them on demand. A single cross-cutting best-practice *principle* still
  belongs in the skill (e.g. "iterate, don't front-load ontology"); the
  exhaustive per-feature checklist does not.
- **Add a `references/` file only** when it provides agent-specific value the
  docs don't serve well, or when a self-contained, versioned fallback is
  deliberately required — and comes with a maintenance plan.

**Duplication is not forbidden.** Stable guidance *should* be repeated when it
must always be in context. The goal is to avoid duplicating volatile API detail
and exhaustive documentation **without a deliberate reason and a maintenance
plan.**
