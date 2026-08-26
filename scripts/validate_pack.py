#!/usr/bin/env python3
"""Static validator for the skill-ai Claude Code plugin.

Checks (exit 1 on any ERROR):
  * every skills/*/SKILL.md and agents/*.md has YAML frontmatter with name + description
  * skill/agent `name` matches its directory / file name and is kebab-case
  * no duplicate skill names, no duplicate agent names
  * no skill name collides with a known Claude Code built-in command
  * forked skills (`context: fork`) reference an agent that exists (or a built-in agent type)
  * agents' `skills:` entries exist; `model` is one of sonnet/opus/haiku/inherit
  * layer consistency: command => disable-model-invocation: true (+ argument-hint, warn)
                       reference => user-invocable: false and NOT disable-model-invocation
                       subagent => read-only tool block unless declared mutable
  * plugin.json / marketplace.json parse and their plugin versions match
  * .mcp.json.example parses, has `mcpServers`, and contains no secret-looking values
  * required files exist

Only the standard library is used (a hand-rolled parser for the simple YAML subset
these frontmatters use); PyYAML is used when available.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BUILTIN_COMMANDS = {
    # session / runtime
    "plan", "debug", "code-review", "review", "security-review", "run", "verify", "batch", "loop",
    "doctor", "diff", "context", "compact", "permissions", "mcp", "tasks", "agents", "init",
    "memory", "model", "effort", "goal", "clear", "resume", "branch", "fork", "background",
    "copy", "export", "help", "config", "login", "logout", "status", "cost", "bug", "vim",
    "terminal-setup", "add-dir", "hooks", "ide", "install-github-app", "pr-comments",
    "release-notes", "rewind", "upgrade", "deep-research", "simplify", "fast", "workflows",
    "reload-skills", "skills", "plugin", "feedback", "usage", "stats", "exit", "quit",
}
BUILTIN_AGENT_TYPES = {"general-purpose", "Explore", "Plan", "claude", "fork"}
VALID_MODELS = {"sonnet", "opus", "haiku", "inherit"}
REQUIRED_FILES = [
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "README.md",
    "CLAUDE.md",
    "LICENSE",
    "guidence/GUIDE.md",
    "guidence/MCP-GUIDE.md",
    ".mcp.json.example",
    "mcp/README.md",
    "templates/CLAUDE.project.md",
]
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SECRET_KEY = re.compile(r"(token|secret|password|passwd|api[_-]?key|authorization)", re.I)
MAX_DESCRIPTION = 1024

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


# --------------------------------------------------------------------------- frontmatter

def split_frontmatter(text: str, path: Path) -> str | None:
    if not text.startswith("---"):
        err(f"{path}: missing frontmatter (file must start with ---)")
        return None
    end = text.find("\n---", 3)
    if end == -1:
        err(f"{path}: unterminated frontmatter")
        return None
    return text[3:end].strip("\n")


def parse_simple_yaml(block: str) -> dict:
    """Minimal parser: top-level scalars, `key:` + `- item` lists, one nested mapping level."""
    data: dict = {}
    current_key: str | None = None
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            current_key = key
            if value == "":
                data[key] = {}  # list or mapping decided by children
            else:
                data[key] = _scalar(value)
        else:
            if current_key is None:
                continue
            container = data.get(current_key)
            if line.startswith("- "):
                if not isinstance(container, list):
                    container = [] if not container else container
                    data[current_key] = container
                container.append(_scalar(line[2:].strip()))
            elif ":" in line:
                if not isinstance(container, dict):
                    container = {}
                    data[current_key] = container
                k, _, v = line.partition(":")
                container[k.strip()] = _scalar(v.strip())
    return data


def _scalar(value: str):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    low = value.lower()
    if low in {"true", "yes", "on"}:
        return True
    if low in {"false", "no", "off"}:
        return False
    return value


def load_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    block = split_frontmatter(text, path)
    if block is None:
        return None
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(block) or {}
        if not isinstance(parsed, dict):
            err(f"{path}: frontmatter is not a mapping")
            return None
        return parsed
    except ImportError:
        return parse_simple_yaml(block)
    except Exception as exc:  # pragma: no cover
        err(f"{path}: frontmatter YAML error: {exc}")
        return None


def as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [v.strip() for v in str(value).split(",") if v.strip()]


# --------------------------------------------------------------------------- checks

def check_required_files() -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            err(f"missing required file: {rel}")


def check_skills() -> tuple[dict[str, dict], dict[str, str]]:
    skills: dict[str, dict] = {}
    layers: dict[str, str] = {}
    skills_dir = ROOT / "skills"
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        fm = load_frontmatter(skill_md)
        if fm is None:
            continue
        rel = skill_md.relative_to(ROOT)
        name = fm.get("name")
        desc = fm.get("description")
        dirname = skill_md.parent.name
        if not name:
            err(f"{rel}: missing `name`")
            continue
        if name != dirname:
            err(f"{rel}: name `{name}` != directory `{dirname}`")
        if not KEBAB.match(str(name)):
            err(f"{rel}: name `{name}` is not kebab-case")
        if not desc:
            err(f"{rel}: missing `description`")
        elif len(str(desc)) > MAX_DESCRIPTION:
            err(f"{rel}: description is {len(str(desc))} chars (> {MAX_DESCRIPTION})")
        if name in skills:
            err(f"{rel}: duplicate skill name `{name}`")
        if name in BUILTIN_COMMANDS:
            err(f"{rel}: skill name `{name}` shadows a Claude Code built-in command")
        skills[name] = fm

        meta = fm.get("metadata") or {}
        layer = str(meta.get("layer", "")) if isinstance(meta, dict) else ""
        if layer not in {"command", "role", "reference"}:
            err(f"{rel}: metadata.layer must be command|role|reference (got `{layer or 'none'}`)")
        layers[name] = layer

        dmi = fm.get("disable-model-invocation") is True
        ui_false = fm.get("user-invocable") is False
        if layer == "command":
            if not dmi:
                err(f"{rel}: command skill must set `disable-model-invocation: true`")
            if not fm.get("argument-hint"):
                warn(f"{rel}: command skill has no `argument-hint`")
            body = skill_md.read_text(encoding="utf-8")
            if "$ARGUMENTS" not in body:
                warn(f"{rel}: command skill body does not use $ARGUMENTS")
        if layer == "reference":
            if not ui_false:
                err(f"{rel}: reference skill must set `user-invocable: false`")
            if dmi:
                err(f"{rel}: reference skill with `disable-model-invocation: true` would be uninvocable by anyone")
        if layer == "role" and (dmi or ui_false):
            warn(f"{rel}: role skill hides itself from model or user — intended?")

        ctx = fm.get("context")
        if ctx == "fork":
            agent = fm.get("agent")
            if not agent:
                warn(f"{rel}: `context: fork` without `agent:` — will use the default subagent (full tools)")
            else:
                skills[name]["_fork_agent"] = str(agent)
        elif fm.get("agent"):
            warn(f"{rel}: `agent:` set without `context: fork` — has no effect")
    if not skills:
        err("no skills found under skills/*/SKILL.md")
    return skills, layers


def check_agents(skills: dict[str, dict]) -> dict[str, dict]:
    agents: dict[str, dict] = {}
    for agent_md in sorted((ROOT / "agents").glob("*.md")):
        fm = load_frontmatter(agent_md)
        if fm is None:
            continue
        rel = agent_md.relative_to(ROOT)
        name = fm.get("name")
        if not name:
            err(f"{rel}: missing `name`")
            continue
        if name != agent_md.stem:
            err(f"{rel}: name `{name}` != file name `{agent_md.stem}`")
        if not KEBAB.match(str(name)):
            err(f"{rel}: name `{name}` is not kebab-case")
        if not fm.get("description"):
            err(f"{rel}: missing `description`")
        if name in agents:
            err(f"{rel}: duplicate agent name `{name}`")
        agents[name] = fm

        model = fm.get("model")
        if model is not None and str(model) not in VALID_MODELS:
            err(f"{rel}: model `{model}` not in {sorted(VALID_MODELS)}")
        if model is None:
            warn(f"{rel}: no `model` — Claude Code defaults apply; prefer explicit `inherit`")

        for s in as_list(fm.get("skills")):
            if s not in skills:
                err(f"{rel}: preloads unknown skill `{s}`")

        meta = fm.get("metadata") or {}
        layer = str(meta.get("layer", "")) if isinstance(meta, dict) else ""
        if layer != "subagent":
            err(f"{rel}: metadata.layer must be `subagent` (got `{layer or 'none'}`)")

        disallowed = set(as_list(fm.get("disallowedTools")))
        allowed = as_list(fm.get("tools"))
        mutable = fm.get("permissionMode") not in (None, "plan") and False  # reserved
        read_only_block = {"Edit", "Write"} <= disallowed or (allowed and not ({"Edit", "Write"} & set(allowed)))
        if not read_only_block:
            # only developer and project-manager are allowed to write by design
            if name not in {"developer", "project-manager"}:
                err(f"{rel}: analysis agent `{name}` can Edit/Write — add `disallowedTools: Edit, Write, NotebookEdit, Agent`")
        if "Agent" not in disallowed and name != "project-manager":
            err(f"{rel}: only `project-manager` may spawn agents — add `Agent` to disallowedTools")
    if not agents:
        err("no agents found under agents/*.md")
    return agents


def check_fork_targets(skills: dict[str, dict], agents: dict[str, dict]) -> None:
    for name, fm in skills.items():
        target = fm.get("_fork_agent")
        if target and target not in agents and target not in BUILTIN_AGENT_TYPES:
            err(f"skills/{name}/SKILL.md: `agent: {target}` does not exist in agents/")


def check_manifests() -> None:
    try:
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return  # reported by required-files check
    except json.JSONDecodeError as exc:
        err(f"manifest JSON error: {exc}")
        return
    pv = plugin.get("version")
    entries = [p for p in market.get("plugins", []) if p.get("name") == plugin.get("name")]
    if not entries:
        err("marketplace.json has no plugin entry matching plugin.json name")
    elif entries[0].get("version") != pv:
        err(f"version mismatch: plugin.json {pv} vs marketplace.json {entries[0].get('version')}")
    for rel in plugin.get("skills", []):
        if not (ROOT / rel).exists():
            err(f"plugin.json skills path does not exist: {rel}")


def check_mcp_example() -> None:
    path = ROOT / ".mcp.json.example"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        err(f".mcp.json.example JSON error: {exc}")
        return
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        err(".mcp.json.example must contain an object `mcpServers`")
        return

    def walk(obj, trail: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if SECRET_KEY.search(str(k)) and isinstance(v, str) and v and not v.startswith("${"):
                    err(f".mcp.json.example: `{trail}{k}` looks like a committed secret value")
                walk(v, f"{trail}{k}.")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{trail}[{i}].")

    walk(servers, "mcpServers.")
    if (ROOT / ".mcp.json").exists():
        warn(".mcp.json exists at plugin root — it will be auto-loaded into every consumer session; make sure that is intended and secret-free")


def check_cross_references(skills: dict[str, dict], agents: dict[str, dict]) -> None:
    """Warn on stale role names in bodies (e.g. after a rename)."""
    stale = {"qa-analysis"}
    for path in list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "agents").glob("*.md")) + [ROOT / "README.md", ROOT / "CLAUDE.md"]:
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "renamed" in line.lower():  # changelog entries may name the old identifier
                continue
            for s in stale:
                if s in line:
                    err(f"{path.relative_to(ROOT)}:{lineno}: stale reference `{s}`")


# --------------------------------------------------------------------------- main

def main() -> int:
    check_required_files()
    skills, layers = check_skills()
    agents = check_agents(skills)
    check_fork_targets(skills, agents)
    check_manifests()
    check_mcp_example()
    check_cross_references(skills, agents)

    by_layer: dict[str, list[str]] = {}
    for name, layer in layers.items():
        by_layer.setdefault(layer or "?", []).append(name)
    print("skill-ai pack summary")
    for layer in ("command", "role", "reference"):
        names = sorted(by_layer.get(layer, []))
        print(f"  {layer:<10} {len(names):>2}  {' '.join(names)}")
    print(f"  {'subagent':<10} {len(agents):>2}  {' '.join(sorted(agents))}")
    forks = sorted(f"{n}->{fm['_fork_agent']}" for n, fm in skills.items() if fm.get("_fork_agent"))
    print(f"  forks      {len(forks):>2}  {' '.join(forks)}")
    print()
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print()
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
