#!/usr/bin/env python3
"""Validate this package against Agent Plugins 1.0.0 without dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")


def fail(message: str) -> None:
    raise ValueError(message)


def load_object(name: str) -> dict:
    try:
        value = json.loads((ROOT / name).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{name}: {exc}")
    if not isinstance(value, dict):
        fail(f"{name}: expected a JSON object")
    return value


def validate_manifest() -> dict:
    manifest = load_object("plugin.json")
    allowed = {
        "$schema",
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "extensions",
    }
    unknown = set(manifest) - allowed
    if unknown:
        fail(f"plugin.json: unknown fields: {', '.join(sorted(unknown))}")
    if manifest.get("$schema") != PLUGIN_SCHEMA:
        fail(f"plugin.json: $schema must be {PLUGIN_SCHEMA}")
    name = manifest.get("name")
    if not isinstance(name, str) or not 1 <= len(name) <= 64 or not NAME_RE.fullmatch(name):
        fail("plugin.json: invalid Agent Plugins name")
    for field in ("version", "description", "homepage", "repository", "license"):
        if field in manifest and not isinstance(manifest[field], str):
            fail(f"plugin.json: {field} must be a string")
    author = manifest.get("author")
    if author is not None:
        if not isinstance(author, dict) or set(author) - {"name", "email", "url"}:
            fail("plugin.json: author must contain only name, email, and url")
        if any(not isinstance(value, str) for value in author.values()):
            fail("plugin.json: author values must be strings")
    keywords = manifest.get("keywords")
    if keywords is not None and (
        not isinstance(keywords, list)
        or any(not isinstance(value, str) for value in keywords)
    ):
        fail("plugin.json: keywords must be an array of strings")
    extensions = manifest.get("extensions")
    if extensions is not None and (
        not isinstance(extensions, dict)
        or any(not isinstance(value, dict) for value in extensions.values())
    ):
        fail("plugin.json: extension values must be objects")
    return manifest


def validate_remote(name: str, server: dict, expected_type: str) -> None:
    allowed = {"type", "url", "headers"}
    if set(server) - allowed or server.get("type") != expected_type:
        fail(f"mcp.json: {name} has fields invalid for {expected_type}")
    url = server.get("url")
    if not isinstance(url, str) or not url:
        fail(f"mcp.json: {name}.url must be a non-empty string")
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        fail(f"mcp.json: {name}.url is not an allowed absolute HTTP URL")
    loopback = parsed.hostname == "localhost" or parsed.hostname in {"127.0.0.1", "::1"}
    if not loopback and parsed.scheme != "https":
        fail(f"mcp.json: {name}.url must use HTTPS")
    headers = server.get("headers")
    if headers is not None and (
        not isinstance(headers, dict)
        or any(not isinstance(key, str) or not isinstance(value, str) for key, value in headers.items())
    ):
        fail(f"mcp.json: {name}.headers must contain string values")


def validate_stdio(name: str, server: dict) -> None:
    allowed = {"type", "command", "args", "env", "cwd"}
    if set(server) - allowed:
        fail(f"mcp.json: {name} has unknown stdio fields")
    command = server.get("command")
    if not isinstance(command, str) or not command or any(char.isspace() for char in command):
        fail(f"mcp.json: {name}.command must be one executable token")
    if "/" in command and not command.startswith("./"):
        fail(f"mcp.json: {name}.command paths must begin with ./")
    args = server.get("args")
    if args is not None and (
        not isinstance(args, list) or any(not isinstance(value, str) for value in args)
    ):
        fail(f"mcp.json: {name}.args must be an array of strings")
    env = server.get("env")
    if env is not None and (
        not isinstance(env, dict)
        or set(env) & {"PLUGIN_ROOT", "PLUGIN_DATA"}
        or any(not isinstance(value, str) for value in env.values())
    ):
        fail(f"mcp.json: {name}.env is invalid")
    cwd = server.get("cwd")
    if cwd is not None and (
        not isinstance(cwd, str)
        or not cwd.startswith(("./", "${PLUGIN_ROOT}", "${PLUGIN_DATA}"))
    ):
        fail(f"mcp.json: {name}.cwd is invalid")


def validate_mcp() -> None:
    config = load_object("mcp.json")
    if set(config) != {"$schema", "mcpServers"}:
        fail("mcp.json: top-level fields must be exactly $schema and mcpServers")
    if config["$schema"] != MCP_SCHEMA:
        fail(f"mcp.json: $schema must be {MCP_SCHEMA}")
    servers = config["mcpServers"]
    if not isinstance(servers, dict):
        fail("mcp.json: mcpServers must be an object")
    for name, server in servers.items():
        if not isinstance(server, dict):
            fail(f"mcp.json: {name} must be an object")
        transport = server.get("type")
        if transport == "stdio":
            validate_stdio(name, server)
        elif transport in {"streamable-http", "sse"}:
            validate_remote(name, server, transport)
        else:
            fail(f"mcp.json: {name} has unsupported transport {transport!r}")


def main() -> int:
    try:
        validate_manifest()
        validate_mcp()
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("OK — Agent Plugins 1.0.0 manifest and MCP configuration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
