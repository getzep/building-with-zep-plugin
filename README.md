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

These disclosures are the terms of service and privacy policy relating to the
Build with Zep plugin (the "**Plugin**"), made available by Zep Software, Inc.
("**Zep**," "**we**," or "**us**"). They apply to installation and use of the
Plugin. They do **not** govern access to or use of Zep's commercial memory and
context-engineering platform (the "**Zep Service**").

### Terms of Service

**Last updated:** August 18, 2026

**1. Acceptance.** By installing, accessing, or using the Plugin, you agree to
these Terms of Service. If you do not agree, do not install or use the Plugin.

**2. License.** The Plugin, including without limitation the skill, manifests,
marketplace catalogs, and MCP configuration, is licensed under the
[Apache License, Version 2.0](LICENSE) (the "**License**"). The License is the
agreement that governs your rights to use, reproduce, modify, and distribute
the Plugin. Nothing in these Terms of Service grants rights beyond those set
forth in the License.

**3. Nature of the Plugin.** The Plugin consists of (a) locally installed
guidance for building applications with Zep, and (b) configuration that permits
your agent environment to query Zep's publicly available documentation server
at `https://docs-mcp.getzep.com/mcp`. The Plugin does not provide access to the
Zep Service, does not issue or accept API keys, does not create a Zep account,
and does not store user, graph, or memory data in the Zep Service.

**4. Relationship to the Zep Service.** Installation of the Plugin does not
constitute an account for, or a subscription to, the Zep Service. If you later
access or use the Zep Service (including Zep's APIs) in your own application,
that use is governed by Zep's [Terms of Service](https://www.getzep.com/legal/terms/)
and [Privacy Policy](https://www.getzep.com/legal/privacy/), and not by these
Plugin terms.

**5. Disclaimer of warranties; limitation of liability.** THE PLUGIN IS
PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS. Warranty disclaimers and
limitations of liability applicable to the Plugin are as set forth in the
License.

**6. Changes.** Zep may revise these Plugin terms by updating this section.
Your continued use of the Plugin following such an update constitutes
acceptance of the revised terms.

### Privacy Policy

**Last updated:** August 18, 2026

This Privacy Policy describes Zep's collection, use, and disclosure of
information in connection with the Plugin. It applies solely to the Plugin.
If you use the Zep Service, Zep's [Privacy Policy](https://www.getzep.com/legal/privacy/)
governs that use.

**1. No account or memory data.** Use of the Plugin does not require a Zep
account, API key, or other credentials. The Plugin is not Zep Memory and does
not create, store, or update user, graph, or memory data in the Zep Service.

**2. Information processed through the documentation MCP.** The Plugin skill is
a local file. The only network communication initiated by the Plugin is to
Zep's public documentation MCP server at `https://docs-mcp.getzep.com/mcp`, for
the purpose of searching and retrieving publicly available documentation. When
your agent environment submits a documentation query or page request, Zep
receives that request and ordinary technical information reasonably necessary
to provide, secure, and operate the connection (which may include Internet
Protocol address, timestamps, and standard request headers). Zep uses this
information solely to operate, secure, and improve the documentation service.

**3. Use limitations.** Documentation requests made through the Plugin are not
used to build, update, or personalize a user memory graph. Zep does not sell
information received through the Plugin. Zep does not use information received
through the Plugin to train artificial intelligence or machine learning models.

**4. Third-party hosts.** The Plugin runs inside a third-party agent host.
Information collected by that host is governed by that host's own terms and
privacy policy, not this Privacy Policy.

**5. Children's privacy.** The Plugin is not directed to children under the
age of 13, and Zep does not knowingly collect personal information from
children under 13 through the Plugin.

**6. Contact.** Questions regarding this Privacy Policy may be sent to
info@getzep.com.

## Portable core plus vendor compatibility

The repository root conforms to
[Agent Plugins 1.0.0](https://agent-plugins.org/): `plugin.json` identifies the
package, `skills/` contains the portable skill, and `mcp.json` declares the
Streamable HTTP documentation server.

Vendor files remain alongside that portable core so clients do not need to
adopt the standard before installing the plugin:

- **Claude Code** — `.claude-plugin/plugin.json` and Claude-shaped `.mcp.json`
- **OpenAI Codex / ChatGPT Work** — `.codex-plugin/plugin.json` and `.mcp.json`
- **Cursor** — loads the Agent Plugins package; `.cursor-plugin/marketplace.json`
  is the Cursor marketplace catalog and points at this repo root (`.`)

Every package path loads the same `skills/building-with-zep/` tree.

Marketplace catalogs live in this repository:

- Claude Code — `.claude-plugin/marketplace.json`
- Codex / ChatGPT Work — `.agents/plugins/marketplace.json`
- Cursor — `.cursor-plugin/marketplace.json`

Each entry uses a same-repo path (`./` or `.`) so hosts do not clone a second
remote for the plugin package.

## MCP configuration

`zep-docs` is declared in two schema-specific files because the portable and
vendor MCP schemas use different transport names:

| File | Read by | Shape |
|---|---|---|
| `mcp.json` | Agent Plugins clients, including Cursor | `{"type":"streamable-http","url":...}` plus the 1.0.0 schema |
| `.mcp.json` | Claude Code, OpenAI Codex / ChatGPT Work | `{"type":"http","url":...}` |

Both point at `https://docs-mcp.getzep.com/mcp`. Change both together.

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
├── .cursor-plugin/marketplace.json
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

Keep the Agent Plugins manifest and the Claude and Codex vendor manifests on one version:

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
