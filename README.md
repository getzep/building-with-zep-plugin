# Build with Zep

The Build with Zep plugin helps Claude Code, Codex, and Cursor build applications
with [Zep](https://www.getzep.com).

This repository is the canonical source for the plugin **and** its Claude Code,
Codex, and Cursor marketplaces. Each marketplace catalog lists this package with
a same-repo path source.

## Usage

Install from [Implement Zep with agents](https://help.getzep.com/implement-zep-with-agents).
That page covers Claude Code, Codex, and Cursor.

Once installed, the plugin gives the agent:

- The **`building-with-zep` skill** — how to scope graphs, ingest data, retrieve
  context, and evaluate a Zep integration
- The **`zep-docs` MCP server** — live Zep documentation at
  `https://docs-mcp.getzep.com/mcp` (search and full-page reads)

Ask the agent to design, review, or debug a Zep integration. It should use the
skill for decision rules and `zep-docs` for current API details.

### Configuration

None required. `zep-docs` is a public remote MCP server. It does not need an
API key, plugin variables, or other secrets. A Zep API key is only needed later,
in *your* application, when you call the Zep product APIs — not to use this
plugin.

## Legal

This plugin is published by [Zep](https://www.getzep.com) under the
[Apache License 2.0](LICENSE). Using the plugin is also subject to Zep’s:

- [Privacy Policy](https://www.getzep.com/legal/privacy/)
- [Terms of Service](https://www.getzep.com/legal/terms/)

The plugin itself is a skill plus a public documentation MCP server. It does not
require a Zep account or API key. If you later use Zep’s product APIs in your
own application, those APIs are covered by the same terms and privacy policy.

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

Marketplace catalogs live in this repository:

- Claude Code — `.claude-plugin/marketplace.json`
- Codex / ChatGPT Work — `.agents/plugins/marketplace.json`
- Cursor — `.cursor-plugin/marketplace.json`

Each entry uses a same-repo path (`./` or `.`) so hosts do not clone a second
remote for the plugin package.

## MCP configuration

`zep-docs` is declared in three schema-specific files because the portable and
vendor MCP schemas use different transport names:

| File | Read by | Shape |
|---|---|---|
| `mcp.json` | Agent Plugins clients | `{"type":"streamable-http","url":...}` plus the 1.0.0 schema |
| `.mcp.json` | Claude Code, OpenAI Codex / ChatGPT Work | `{"type":"http","url":...}` |
| `.cursor-plugin/mcp.json` | Cursor vendor wrapper | `{"url":...}` |

All three point at `https://docs-mcp.getzep.com/mcp`. Change all three together.

## Repository contents

```text
.
├── plugin.json
├── mcp.json
├── assets/logo.png
├── skills/building-with-zep/SKILL.md
├── .claude-plugin/plugin.json
├── .claude-plugin/marketplace.json
├── .agents/plugins/marketplace.json
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

Keep the Agent Plugins manifest and all three vendor manifests on one version:

```bash
python3 scripts/plugin_manifests.py set <version>
```

Then changelog, validate the plugin and marketplace separately
(`claude plugin validate .claude-plugin/plugin.json --strict`,
`claude plugin validate . --strict`,
`python3 scripts/plugin_manifests.py --check`,
`python3 scripts/validate_agent_plugin.py`), and merge a PR that passes
`test-plugin.yml`.

How that reaches Claude Code, Codex, and Cursor — this repository as marketplace
today, Cursor team marketplace, and public directories later — is documented under
**Releasing** in [`AGENTS.md`](AGENTS.md). CI requires a version bump when
manifests, MCP configs, or `skills/` change; see that file for the exact path
list.

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
