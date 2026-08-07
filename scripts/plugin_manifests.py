#!/usr/bin/env python3
"""Keep Build with Zep manifests and MCP endpoints synchronized.

Usage:
    python3 scripts/plugin_manifests.py --check
    python3 scripts/plugin_manifests.py set 0.3.0
    python3 scripts/plugin_manifests.py version
    python3 scripts/plugin_manifests.py require-newer 0.3.0 0.2.0
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
# Every managed file holds exactly one "version" key, which lets the rewrite be a
# scoped text substitution that preserves the file's existing formatting.
VERSION_KEY_RE = re.compile(r'("version"\s*:\s*")([^"]*)(")')


@dataclass(frozen=True)
class PluginSpec:
    name: str
    version_sites: list[tuple[str, str, str]]
    mcp_sites: list[tuple[str, str]]
    mcp_server_name: str
    validate_path: str


PLUGINS: list[PluginSpec] = [
    PluginSpec(
        name="building-with-zep",
        version_sites=[
            ("plugin.json", "manifest", "Agent Plugins manifest"),
            (".claude-plugin/plugin.json", "manifest", "Claude plugin manifest"),
            (".codex-plugin/plugin.json", "manifest", "Codex plugin manifest"),
            (".cursor-plugin/plugin.json", "manifest", "Cursor plugin manifest"),
        ],
        mcp_sites=[
            (".mcp.json", "Claude + Codex (.mcp.json)"),
            ("mcp.json", "Agent Plugins (mcp.json)"),
            (".cursor-plugin/mcp.json", "Cursor vendor MCP"),
        ],
        mcp_server_name="zep-docs",
        validate_path=".",
    ),
]
PLUGINS_BY_NAME = {plugin.name: plugin for plugin in PLUGINS}
DEFAULT_PLUGIN = PLUGINS[0]

# Places a version must never appear. Each ecosystem resolves the release version
# from its plugin.json; a second marketplace value is redundant and can drift.
FORBIDDEN_SITES: list[tuple[str, str, str]] = []


class SiteError(Exception):
    """A manifest is missing, unparseable, or not shaped the way this script expects."""


def parse_semver(version: str) -> tuple[tuple[int, int, int], tuple[str, ...] | None]:
    """Parse a strict SemVer string into the parts that determine precedence."""
    match = SEMVER_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"'{version}' is not a semantic version (MAJOR.MINOR.PATCH)")
    core = tuple(int(match.group(index)) for index in (1, 2, 3))
    prerelease = match.group(4)
    return core, tuple(prerelease.split(".")) if prerelease is not None else None


def compare_semver(left: str, right: str) -> int:
    """Return -1, 0, or 1 according to SemVer precedence (build metadata ignored)."""
    left_core, left_pre = parse_semver(left)
    right_core, right_pre = parse_semver(right)
    if left_core != right_core:
        return 1 if left_core > right_core else -1
    if left_pre is None or right_pre is None:
        if left_pre is right_pre:
            return 0
        return 1 if left_pre is None else -1

    for left_part, right_part in zip(left_pre, right_pre):
        if left_part == right_part:
            continue
        left_numeric = left_part.isdigit()
        right_numeric = right_part.isdigit()
        if left_numeric and right_numeric:
            return 1 if int(left_part) > int(right_part) else -1
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return 1 if left_part > right_part else -1
    if len(left_pre) == len(right_pre):
        return 0
    return 1 if len(left_pre) > len(right_pre) else -1


def _load(rel_path: str) -> tuple[Path, str, object]:
    path = REPO_ROOT / rel_path
    try:
        text = path.read_text()
    except OSError as exc:
        raise SiteError(f"{rel_path}: cannot read ({exc})") from exc
    try:
        return path, text, json.loads(text)
    except json.JSONDecodeError as exc:
        raise SiteError(f"{rel_path}: invalid JSON ({exc})") from exc


def _marketplace_entries(rel_path: str, data: object) -> list[dict]:
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, list):
        raise SiteError(f"{rel_path}: expected a top-level 'plugins' array")
    entries: list[dict] = []
    for entry in plugins:
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def read_version(rel_path: str, kind: str) -> str:
    """Return the version declared at a manifest site, or raise if it declares none."""
    if kind != "manifest":
        raise SiteError(f"{rel_path}: read_version only supports kind 'manifest'")
    _, _, data = _load(rel_path)
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not version:
        raise SiteError(f"{rel_path}: no version declared ({kind})")
    return version


def find_forbidden_versions(rel_path: str, kind: str) -> list[tuple[str, str]]:
    """Return (where, version) pairs that must not exist at a forbidden site."""
    _, _, data = _load(rel_path)
    found: list[tuple[str, str]] = []
    if kind == "metadata":
        holder = data.get("metadata") if isinstance(data, dict) else None
        if isinstance(holder, dict):
            version = holder.get("version")
            if isinstance(version, str):
                found.append(("metadata", version))
        return found
    if kind == "entry":
        for entry in _marketplace_entries(rel_path, data):
            version = entry.get("version")
            name = entry.get("name", "<unnamed>")
            if isinstance(version, str):
                found.append((f"plugins[{name}]", version))
        return found
    raise SiteError(f"{rel_path}: unsupported forbidden kind {kind!r}")


def read_mcp_url(rel_path: str, server_name: str) -> str:
    """Return the named MCP server url declared in an MCP config file."""
    _, _, data = _load(rel_path)
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        raise SiteError(f"{rel_path}: expected a top-level 'mcpServers' object")
    server = servers.get(server_name)
    if not isinstance(server, dict):
        raise SiteError(f"{rel_path}: no '{server_name}' server declared")
    url = server.get("url")
    if not isinstance(url, str) or not url:
        raise SiteError(f"{rel_path}: '{server_name}' declares no url")
    return url


def check_plugin(plugin: PluginSpec, problems: list[str]) -> None:
    """Report and validate one plugin's managed values."""
    versions: dict[str, str] = {}
    urls: dict[str, str] = {}

    for rel_path, kind, label in plugin.version_sites:
        try:
            versions[label] = read_version(rel_path, kind)
        except SiteError as exc:
            problems.append(str(exc))
    for rel_path, label in plugin.mcp_sites:
        try:
            urls[label] = read_mcp_url(rel_path, plugin.mcp_server_name)
        except SiteError as exc:
            problems.append(str(exc))

    print(f"{plugin.name} version")
    for label, version in versions.items():
        print(f"  {version:<12} {label}")
    print(f"{plugin.name} {plugin.mcp_server_name} url")
    for label, url in urls.items():
        print(f"  {url}  {label}")

    distinct = set(versions.values())
    if len(distinct) > 1:
        problems.append(
            f"{plugin.name} version drift across manifests: "
            + ", ".join(f"{label}={v}" for label, v in sorted(versions.items()))
            + " — choose the intended release and run: "
            "python3 scripts/plugin_manifests.py set <version>"
        )
    for version in distinct:
        try:
            parse_semver(version)
        except ValueError as exc:
            problems.append(f"{plugin.name}: {exc}")

    if len(set(urls.values())) > 1:
        problems.append(
            f"{plugin.name} '{plugin.mcp_server_name}' points at different endpoints: "
            + ", ".join(f"{label}={u}" for label, u in sorted(urls.items()))
            + " — MCP configs for this plugin must name the same server"
        )


def check() -> int:
    """Report the managed values; fail on drift, a missing site, or a stray version."""
    problems: list[str] = []

    for plugin in PLUGINS:
        check_plugin(plugin, problems)
        print()

    for rel_path, kind, why in FORBIDDEN_SITES:
        try:
            stray = find_forbidden_versions(rel_path, kind)
        except SiteError as exc:
            problems.append(str(exc))
            continue
        for where, version in stray:
            problems.append(
                f"{rel_path}: remove the {kind} 'version' at {where} ({version}) — {why}"
            )

    if problems:
        sys.stdout.flush()
        print("FAIL", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(
        "OK — "
        + ", ".join(
            f"{plugin.name} ({len(plugin.version_sites)} manifests, "
            f"{len(plugin.mcp_sites)} MCP config(s))"
            for plugin in PLUGINS
        )
    )
    return 0


def set_version(plugin: PluginSpec, new_version: str) -> int:
    """Rewrite every managed site for one plugin to new_version."""
    try:
        parse_semver(new_version)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    pending: list[tuple[Path, str, str, str]] = []
    problems: list[str] = []

    # Resolve every edit before writing anything, so a bad manifest can't leave
    # the tree half-bumped.
    for rel_path, kind, label in plugin.version_sites:
        try:
            path, text, data = _load(rel_path)
            if kind != "manifest" or not isinstance(data, dict):
                raise SiteError(f"{rel_path}: expected a plugin manifest object")
            old = data.get("version")
            if not isinstance(old, str) or not old:
                raise SiteError(f"{rel_path}: no version declared ({kind})")
            try:
                direction = compare_semver(new_version, old)
            except ValueError as exc:
                raise SiteError(f"{rel_path}: {exc}") from exc
            if direction < 0:
                raise SiteError(
                    f"{rel_path}: refusing to decrease the version from {old} to {new_version}"
                )

            matches = VERSION_KEY_RE.findall(text)
            if len(matches) != 1:
                raise SiteError(
                    f"{rel_path}: found {len(matches)} 'version' keys, expected exactly 1 — "
                    "this script rewrites the only one in the file; generalize it before "
                    "adding another"
                )

            new_text = VERSION_KEY_RE.sub(
                lambda m: f"{m.group(1)}{new_version}{m.group(3)}", text, count=1
            )
            written = json.loads(new_text)
            landed = written.get("version") if isinstance(written, dict) else None
            if landed != new_version:
                raise SiteError(f"{rel_path}: rewrite landed on {landed!r}, not {new_version!r}")

            pending.append((path, label, old, new_text))
        except SiteError as exc:
            problems.append(str(exc))

    if problems:
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("\nnothing written", file=sys.stderr)
        return 1

    for path, label, old, new_text in pending:
        if old == new_version:
            print(f"  unchanged  {new_version:<12} {label}")
            continue
        path.write_text(new_text)
        print(f"  {old} -> {new_version:<8} {label}")

    print(f"\nBumped {plugin.name} to {new_version}. Next:")
    print("  1. add a CHANGELOG.md entry describing what users get")
    print(f"  2. claude plugin validate {plugin.validate_path} --strict")
    print("  3. open the PR — merging it is the release; plugins are not tagged")
    return 0


def require_newer(new_version: str, old_version: str) -> int:
    """Fail unless new_version has strictly greater SemVer precedence."""
    try:
        direction = compare_semver(new_version, old_version)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    if direction <= 0:
        print(
            f"{new_version} is not newer than {old_version}; "
            "plugin releases must increase the semantic version",
            file=sys.stderr,
        )
        return 1
    print(f"{old_version} -> {new_version}")
    return 0


def resolve_plugin(name: str | None) -> PluginSpec:
    if name is None:
        return DEFAULT_PLUGIN
    plugin = PLUGINS_BY_NAME.get(name)
    if plugin is None:
        known = ", ".join(PLUGINS_BY_NAME)
        raise SystemExit(f"unknown plugin {name!r}; known: {known}")
    return plugin


def main(argv: list[str]) -> int:
    if argv[1:] == ["--check"]:
        return check()
    if len(argv) == 3 and argv[1] == "set":
        return set_version(DEFAULT_PLUGIN, argv[2])
    if len(argv) == 4 and argv[1] == "set":
        return set_version(resolve_plugin(argv[2]), argv[3])
    if argv[1:] == ["version"]:
        plugin = DEFAULT_PLUGIN
        rel_path, kind, _ = plugin.version_sites[0]
        try:
            print(read_version(rel_path, kind))
        except SiteError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0
    if len(argv) == 3 and argv[1] == "version":
        plugin = resolve_plugin(argv[2])
        rel_path, kind, _ = plugin.version_sites[0]
        try:
            print(read_version(rel_path, kind))
        except SiteError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0
    if len(argv) == 4 and argv[1] == "require-newer":
        return require_newer(argv[2], argv[3])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
