# Build with Zep plugin maintainer instructions

These instructions apply to every file in this repository.

The plugin helps Claude Code, Codex, and Cursor build applications with Zep. For
installation, usage, supported agents, and an overview, use the canonical
[Implement Zep with agents](https://help.getzep.com/implement-zep-with-agents)
documentation.

The maintainer guidance is deliberately repeated in
`AGENTS.md` and `README.md` so agents and maintainers receive the same guidance.
When changing repeated guidance, update both files and keep them consistent.

## Package architecture

This repository root is an Agent Plugins 1.0.0 package with vendor compatibility
files for Claude Code, OpenAI Codex / ChatGPT Work, and Cursor. Every runtime
loads the same `skills/building-with-zep/` tree.

- Do not create ecosystem-specific copies of the skill.
- Keep the plugin name `building-with-zep` in every manifest.
- Keep the portable and vendor manifest versions identical:
  - `plugin.json`
  - `.claude-plugin/plugin.json`
  - `.codex-plugin/plugin.json`
  - `.cursor-plugin/plugin.json`
- Keep root `plugin.json` and `mcp.json` conformant to Agent Plugins 1.0.0.
- Preserve `.claude-plugin/plugin.json` and `.mcp.json`; Claude support must not
  depend on Claude adopting the portable format.
- Preserve `.codex-plugin/plugin.json` and `.mcp.json`; OpenAI support must not
  depend on OpenAI adopting the portable format.
- Keep marketplace catalog entries free of `version`. Each ecosystem resolves
  the version from its own plugin manifest.
- Preserve `.codex-plugin/plugin.json`; it is required for the Codex package.
- Do not add `CLAUDE.md` at this plugin root. Claude's strict plugin validator
  rejects it because installed plugins load context from skills, not that file.
  Keep maintainer guidance in this `AGENTS.md`.

The portable and ecosystem-specific files are:

- Agent Plugins: `plugin.json`, `mcp.json`, and `skills/`.
- Claude Code: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  and `.mcp.json`.
- OpenAI Codex / ChatGPT Work: `.codex-plugin/plugin.json`,
  `.agents/plugins/marketplace.json`, and `.mcp.json`.
- Cursor: the portable Agent Plugins files plus `.cursor-plugin/plugin.json`,
  `.cursor-plugin/mcp.json`, and `.cursor-plugin/marketplace.json`.
- This repository hosts its own marketplace catalogs. Plugin `source` entries
  must stay same-repo paths (`./` or `.`). Do not switch them to remote
  `github` / `url` sources.

## MCP configuration

The `zep-docs` server is intentionally declared in three schema-specific files:

- `mcp.json` is the Agent Plugins 1.0.0 configuration. Its server entry contains
  `{"type":"streamable-http","url":...}` and the canonical `$schema`.
- `.mcp.json` is read by Claude Code and OpenAI. Its server entry contains
  `{"type":"http","url":...}`.
- `.cursor-plugin/mcp.json` is read by the Cursor vendor wrapper and uses
  Cursor's URL-inferred transport shape.

All three files must point to `https://docs-mcp.getzep.com/mcp`. Whenever one
endpoint changes, update the others in the same change. Do not consolidate the
files unless each affected vendor documents the portable schema as supported.

## Releasing

How a merge reaches users depends on the distribution channel.

### Repo ritual (always)

For loaded plugin content changes:

1. From the repository root, bump the portable and vendor manifests together:

   ```bash
   python3 scripts/plugin_manifests.py set <version>
   ```

2. Add an entry to `CHANGELOG.md`.
3. Validate the Claude plugin package and the marketplace catalog separately.
   With both files under `.claude-plugin/`, `claude plugin validate .` only
   checks the marketplace:

   ```bash
   claude plugin validate .claude-plugin/plugin.json --strict
   claude plugin validate . --strict
   ```

4. Run the repository plugin-manifest check and confirm the `test-plugin.yml`
   workflow passes in the pull request. The workflow also runs
   `scripts/validate_agent_plugin.py` against the portable manifest and MCP
   configuration, and checks marketplace catalogs for same-repo sources.
5. Open a PR and merge to the default branch.

There is no npm publish, GitHub Release, or required git tag for this package.
The `zep-docs` MCP server at `https://docs-mcp.getzep.com/mcp` ships separately —
server-only changes do not require a plugin version bump unless package
metadata or the skill change too.

Bump the synced `version` fields whenever you want installed clients to treat
the package as new. With an explicit version set, Claude Code caches by that
string and skips updates if it is unchanged (see
[version management](https://code.claude.com/docs/en/plugins-reference#version-management)).

Changes limited to the maintainer-only `README.md`, `CHANGELOG.md`, or
`AGENTS.md` do not require a version bump. The CI version-bump check only
covers these loaded-content paths — not every non-docs file in the repo:

- `plugin.json`, `mcp.json`, `.mcp.json`
- `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`,
  `.cursor-plugin/plugin.json`
- `.cursor-plugin/mcp.json`
- `skills/`

Paths outside that list (for example `.cursor-plugin/marketplace.json` or
`scripts/`) will not fail the bump check; bump when the change still affects
what agents load. If multiple plugin changes are being prepared in the same
unreleased branch, one semantic version increase covering that release is
sufficient.

### Distribution channels

This repository is the source of truth. Channels differ in what happens after
merge. User-facing install and update steps live in
[Implement Zep with agents](https://help.getzep.com/implement-zep-with-agents).

#### This repository as marketplace — primary today

Not Anthropic's, OpenAI's, or Cursor's official public directories. Users add
**this** GitHub repository as the marketplace, then install the same-repo
plugin. Marketplace entries must stay free of `version`; each host resolves the
release from this package's manifests. Ordinary plugin releases do not need a
separate marketplace PR elsewhere.

```bash
claude plugin marketplace add getzep/building-with-zep-plugin
claude plugin install building-with-zep@building-with-zep
```

```bash
codex plugin marketplace add getzep/building-with-zep-plugin
codex plugin add building-with-zep@building-with-zep
```

After the package is on `main`:

- **Claude Code:** users with the `building-with-zep` marketplace refresh and
  update (`claude plugin marketplace update building-with-zep` then
  `claude plugin update building-with-zep@building-with-zep`), or enable
  marketplace auto-update (off by default for third-party marketplaces).
  Administrators can set `"autoUpdate": true` on the marketplace's
  [`extraKnownMarketplaces`](https://code.claude.com/docs/en/settings#extraknownmarketplaces)
  entry. Because this package sets an explicit `version`, bump it or Claude Code
  will keep the cached release.
- **Codex:** refreshes configured git marketplaces on startup. Immediate pull:
  `codex plugin marketplace upgrade building-with-zep`, then start a new
  session.
- **Cursor `/add-plugin` from a GitHub URL:** currently pins the install to the
  commit used at install time; re-run / Update / Reinstall does not advance past
  that snapshot. Prefer a Cursor team marketplace import of **this** repo (below)
  when you need refreshable team distribution.

#### Claude Code community marketplace (later / optional)

Third-party listing in
[`anthropics/claude-plugins-community`](https://github.com/anthropics/claude-plugins-community)
(`claude-community`). Submit via the in-app Claude Code / Console forms (not the
same as Anthropic's curated official marketplace). Approved plugins are pinned to
a commit SHA; community CI can advance the pin as you push, and the public
catalog syncs on a delay (nightly). Merging this repo alone does not list the
plugin there.

#### Anthropic official Claude Code marketplace (later / optional)

`claude-plugins-official` is curated by Anthropic at its discretion. There is no
application process that adds third-party plugins to the official catalog; the
submission forms target the community marketplace. Treat official inclusion as a
separate conversation with Anthropic, not a merge-triggered release.

#### Codex — local / repo marketplaces (internal)

Not the universal public Plugins Directory. Point
`.agents/plugins/marketplace.json` (repo-scoped) or
`~/.agents/plugins/marketplace.json` (personal) at a plugin folder, restart /
refresh, and install from that source. OpenAI caches installed copies by
marketplace + name + version.

#### OpenAI universal public Plugins Directory (later)

Official public listing shared by ChatGPT and Codex surfaces
([submission guide](https://developers.openai.com/plugins/deploy/submission)).
Submit through the OpenAI plugin submission portal (review → approve →
**Publish**). Updates require a new draft with a **new** manifest `version`,
release notes, resubmit, approval, then Publish again. Merging to GitHub does
not update the live directory listing. Skills may be snapshotted at review;
live MCP tool calls still hit `https://docs-mcp.getzep.com/mcp`.

#### Cursor team marketplace (Teams / Enterprise)

Import **this** GitHub repository from Cursor **Dashboard → Plugins** (Team
Marketplaces). Cursor reads `.cursor-plugin/marketplace.json` and only resolves
same-repo plugin paths. Keep plugins current with:

- **Auto Refresh** (optional): re-indexes on push to the tracked branch when the
  [Cursor GitHub App](https://cursor.com/docs/integrations/github) can send
  webhooks; re-index is rate-limited (at most about once every 10 minutes).
- **Manual Refresh** in marketplace settings.

Admins set marketplace access and per-plugin install modes (Default Off / On /
Required). This is the supported refreshable path for Cursor teams.

#### Cursor public marketplace (later / optional)

Submit at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).
Listings are manually reviewed; updates are reviewed again before publishing.
GitHub merge alone does not update the public Cursor Marketplace.

## What goes in the skill versus the docs

The skill is the decision-and-workflow layer, not a second copy of the product
documentation.

- Put stable, cross-cutting philosophy, decision rules, mental models, and
  critical invariants in `skills/building-with-zep/SKILL.md`.
- Leave volatile or exhaustive details to the Zep documentation accessed through
  `zep-docs`. This includes method names, parameters, limits, pricing, plan
  availability, exact reranker names, template syntax, and full per-feature
  checklists.
- Add a file under `skills/building-with-zep/references/` only when it provides
  agent-specific value the docs do not serve well, or when a self-contained,
  versioned fallback is deliberately required and has a maintenance plan.
- Stable guidance may be duplicated when it must always be in context. Do not
  duplicate volatile API details without a deliberate reason and maintenance
  plan.

## Local development

Load the plugin directly in Claude Code:

```bash
claude --plugin-dir .
```

For Cursor, symlink the plugin directory into Cursor's local plugin folder, then
run **Developer: Reload Window**:

```bash
ln -s "$PWD" ~/.cursor/plugins/local/building-with-zep
```
