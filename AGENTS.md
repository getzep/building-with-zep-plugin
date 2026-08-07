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
- Keep the entries in the Zep marketplace repository free of `version`. Each
  ecosystem resolves the version from its own plugin manifest.
- Preserve `.codex-plugin/plugin.json`; it is required for the Codex package.
- Do not add `CLAUDE.md` at this plugin root. Claude's strict plugin validator
  rejects it because installed plugins load context from skills, not that file.
  Keep maintainer guidance in this `AGENTS.md`.

The portable and ecosystem-specific files are:

- Agent Plugins: `plugin.json`, `mcp.json`, and `skills/`.
- Claude Code: `.claude-plugin/plugin.json` and `.mcp.json`.
- OpenAI Codex / ChatGPT Work: `.codex-plugin/plugin.json` and `.mcp.json`.
- Cursor: the portable Agent Plugins files plus `.cursor-plugin/plugin.json`,
  `.cursor-plugin/mcp.json`, and `.cursor-plugin/marketplace.json` for the
  vendor marketplace path.
- Claude / ChatGPT Work marketplace catalogs remain in `getzep/zep` and point at
  this repo. Cursor catalogs only resolve same-repo paths, so Cursor installs or
  team-imports this repository directly.

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

Merging the plugin change to `main` is the release; there is no separate publish
or tag step.

For loaded plugin content changes:

1. From the repository root, bump the portable and vendor manifests together:

   ```bash
   python3 scripts/plugin_manifests.py set <version>
   ```

2. Add an entry to `CHANGELOG.md`.
3. Validate the Claude package:

   ```bash
   claude plugin validate . --strict
   ```

4. Run the repository plugin-manifest check and confirm the `test-plugin.yml`
   workflow passes in the pull request. The workflow also runs
   `scripts/validate_agent_plugin.py` against the portable manifest and MCP
   configuration.

Changes limited to the maintainer-only `README.md`, `CHANGELOG.md`, or
`AGENTS.md` do not require a version bump. All other
files under this plugin are treated as loaded plugin content by the CI check. If
multiple plugin changes are being prepared in the same unreleased branch, one
semantic version increase covering that release is sufficient.

Do not add a plugin git tag. This plugin has no tag-based publish workflow.

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
