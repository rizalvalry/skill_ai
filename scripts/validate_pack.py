#!/usr/bin/env python3
"""Static validator for the skill-ai Claude Code plugin.

Exit 1 on any ERROR. Checks:
  * skills/*/SKILL.md and agents/*.md have frontmatter with name + description
  * name == directory / file name, kebab-case, unique, not a Claude Code built-in command
  * description length (warn > WARN_DESCRIPTION, error > MAX_DESCRIPTION)
  * layer rules: command  => disable-model-invocation: true, argument-hint, $ARGUMENTS,
                            and (if context: fork) an `agent:` that exists (namespaced `skill-ai:<agent>` or bare)
                 reference => user-invocable: false and NOT disable-model-invocation
                 subagent  => read-only tool block {Edit, Write, NotebookEdit, Agent, Artifact, WebFetch, WebSearch}
                            unless the agent is in MUTABLE_AGENTS; only project-manager may keep Agent
  * agents' `skills:` preloads exist; `model` in sonnet/opus/haiku/inherit
  * rulebook references use ${CLAUDE_PLUGIN_ROOT}/guidence/... inside skills/ and agents/
  * plugin.json / marketplace.json parse, versions match, skills paths exist
  * .mcp.json.example is exactly {"mcpServers": {}}; a populated .mcp.json at the root is an error
  * secret-looking VALUES anywhere in skills/, agents/, mcp/, templates/, manifests
  * stale identifiers (renamed roles) outside changelog lines
  * required files exist

Frontmatter is parsed with PyYAML when available; otherwise a conservative fallback parser
is used and a warning is printed, because the fallback can diverge on exotic YAML.
Untrusted strings from the repository are printed with repr() to keep the report unforgeable.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "skill-ai"

BUILTIN_COMMANDS = {
    "plan", "debug", "code-review", "review", "security-review", "run", "verify", "batch", "loop",
    "doctor", "diff", "context", "compact", "permissions", "mcp", "tasks", "agents", "init",
    "memory", "model", "effort", "goal", "clear", "resume", "branch", "fork", "background",
    "copy", "export", "help", "config", "login", "logout", "status", "cost", "bug", "vim",
    "terminal-setup", "add-dir", "hooks", "ide", "install-github-app", "pr-comments",
    "release-notes", "rewind", "upgrade", "deep-research", "simplify", "fast", "workflows",
    "reload-plugins", "reload-skills", "skills", "plugin", "feedback", "usage", "stats", "exit", "quit",
}
BUILTIN_AGENT_TYPES = {"general-purpose", "Explore", "Plan", "claude"}
VALID_MODELS = {"sonnet", "opus", "haiku", "inherit"}
READ_ONLY_BLOCK = {"Edit", "Write", "NotebookEdit", "Agent", "Artifact", "WebFetch", "WebSearch"}
MUTABLE_AGENTS = {"developer", "project-manager"}      # allowed to Edit/Write by design
ORCHESTRATOR_AGENTS = {"project-manager"}              # allowed to use Agent by design
REQUIRED_FILES = [
    ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "README.md", "CLAUDE.md",
    "LICENSE", ".gitignore", "guidence/GUIDE.md", "guidence/MCP-GUIDE.md", ".mcp.json.example",
    "mcp/README.md", "templates/CLAUDE.project.md",
]
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WARN_DESCRIPTION = 800
MAX_DESCRIPTION = 1024
STALE_IDENTIFIERS = {"qa-analysis"}
# value patterns, not just key names
SECRET_VALUE_PATTERNS = [
    re.compile(r"://[^/\s'\"<>:@]+:[^\s'\"<>/]+@[A-Za-z0-9<\[$(]"),  # user:pass@host in URLs; greedy so `@` inside the password is spanned
    re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),  # GitHub tokens
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),                    # OpenAI/Anthropic-style keys
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                       # AWS access key id
    re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}"),             # Azure storage key
    re.compile(r"[?&]sig=[A-Za-z0-9%+/=]{20,}"),               # Azure SAS signature
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"),              # Slack tokens
]
SECRET_KEY = re.compile(r"(token|secret|password|passwd|api[_-]?key|authorization)", re.I)

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")   # tolerate a BOM
    except UnicodeDecodeError as exc:
        err(f"{rel(path)}: not valid UTF-8 ({exc.reason} at byte {exc.start})")
        return None


# --------------------------------------------------------------------------- frontmatter

def split_frontmatter(text: str, path: Path) -> str | None:
    if not text.startswith("---"):
        err(f"{rel(path)}: missing frontmatter (file must start with ---)")
        return None
    end = re.search(r"\r?\n---[ \t]*(\r?\n|$)", text[3:])
    if end is None:
        err(f"{rel(path)}: unterminated frontmatter")
        return None
    return text[3:3 + end.start()].strip("\r\n")


try:
    import yaml as _yaml  # type: ignore
except ImportError:  # pragma: no cover
    _yaml = None


def parse_fallback(block: str, path: Path) -> dict:
    """Conservative parser for the subset used here: scalars, `- item` lists, one nested mapping,
    folded/literal block scalars (`>` / `|`). Anything else is reported instead of guessed."""
    data: dict = {}
    key: str | None = None
    block_scalar: list[str] | None = None
    lines = block.splitlines()
    for raw in lines:
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            err(f"{rel(path)}: tab indentation in frontmatter is not valid YAML")
            return data
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if block_scalar is not None:
            if indent > 0 or line == "":
                block_scalar.append(line)
                continue
            data[key] = " ".join(s for s in block_scalar if s).strip()  # type: ignore[index]
            block_scalar = None
        if not line or line.startswith("#"):
            continue
        if indent == 0:
            if ":" not in line:
                err(f"{rel(path)}: cannot parse frontmatter line {line!r}")
                return data
            k, _, v = line.partition(":")
            key, v = k.strip(), v.strip()
            if v in (">", "|", ">-", "|-"):
                block_scalar = []
            elif v == "":
                data[key] = None
            else:
                data[key] = _scalar(v)
        else:
            if key is None:
                err(f"{rel(path)}: indented frontmatter line without a parent key: {line!r}")
                return data
            cur = data.get(key)
            if line.startswith("- "):
                if cur is None:
                    cur = data[key] = []
                if not isinstance(cur, list):
                    err(f"{rel(path)}: frontmatter key {key!r} mixes list and mapping items")
                    return data
                cur.append(_scalar(line[2:].strip()))
            elif ":" in line:
                if cur is None:
                    cur = data[key] = {}
                if not isinstance(cur, dict):
                    err(f"{rel(path)}: frontmatter key {key!r} mixes list and mapping items")
                    return data
                k2, _, v2 = line.partition(":")
                cur[k2.strip()] = _scalar(v2.strip())
            else:
                err(f"{rel(path)}: cannot parse frontmatter line {line!r}")
                return data
    if block_scalar is not None and key is not None:
        data[key] = " ".join(s for s in block_scalar if s).strip()
    return data


def _scalar(value: str):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    low = value.lower()
    if low in {"true", "yes", "on"}:
        return True
    if low in {"false", "no", "off"}:
        return False
    return value


def load_frontmatter(path: Path) -> dict | None:
    text = read_text(path)
    if text is None:
        return None
    block = split_frontmatter(text, path)
    if block is None:
        return None
    if _yaml is not None:
        try:
            parsed = _yaml.safe_load(block) or {}
        except Exception as exc:
            err(f"{rel(path)}: frontmatter YAML error: {str(exc).splitlines()[0]}")
            return None
        if not isinstance(parsed, dict):
            err(f"{rel(path)}: frontmatter is not a mapping")
            return None
        return parsed
    return parse_fallback(block, path)


def as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value]
    return [v.strip() for v in str(value).split(",") if v.strip()]


def strip_ns(name: str) -> str:
    prefix = PLUGIN_NAME + ":"
    return name[len(prefix):] if name.startswith(prefix) else name


# --------------------------------------------------------------------------- checks

def check_required_files() -> None:
    for r in REQUIRED_FILES:
        if not (ROOT / r).exists():
            err(f"missing required file: {r}")


def check_description(path: Path, desc) -> None:
    if not desc or not isinstance(desc, str):
        err(f"{rel(path)}: missing or non-string `description`")
        return
    n = len(desc)
    if n > MAX_DESCRIPTION:
        err(f"{rel(path)}: description is {n} chars (> {MAX_DESCRIPTION})")
    elif n > WARN_DESCRIPTION:
        warn(f"{rel(path)}: description is {n} chars (> {WARN_DESCRIPTION}); trim to routing triggers")


def check_skills() -> tuple[dict[str, dict], dict[str, str]]:
    skills: dict[str, dict] = {}
    layers: dict[str, str] = {}
    for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
        fm = load_frontmatter(skill_md)
        if fm is None:
            continue
        name = fm.get("name")
        dirname = skill_md.parent.name
        if not isinstance(name, str) or not name:
            err(f"{rel(skill_md)}: missing `name`")
            continue
        if name != dirname:
            err(f"{rel(skill_md)}: name {name!r} != directory {dirname!r}")
        if not KEBAB.match(name):
            err(f"{rel(skill_md)}: name {name!r} is not kebab-case")
        check_description(skill_md, fm.get("description"))
        if name in skills:
            err(f"{rel(skill_md)}: duplicate skill name {name!r}")
        if name in BUILTIN_COMMANDS:
            err(f"{rel(skill_md)}: skill name {name!r} shadows a Claude Code built-in command")
        skills[name] = fm

        meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
        layer = str(meta.get("layer", "")) if meta else ""
        if layer not in {"command", "role", "reference"}:
            err(f"{rel(skill_md)}: metadata.layer must be command|role|reference (got {layer or 'none'!r})")
        layers[name] = layer

        dmi = fm.get("disable-model-invocation") is True
        ui_false = fm.get("user-invocable") is False
        body = read_text(skill_md) or ""
        if layer == "command":
            if not dmi:
                err(f"{rel(skill_md)}: command skill must set `disable-model-invocation: true`")
            if not fm.get("argument-hint"):
                warn(f"{rel(skill_md)}: command skill has no `argument-hint`")
            if "$ARGUMENTS" not in body:
                warn(f"{rel(skill_md)}: command skill body does not use $ARGUMENTS")
            if fm.get("context") == "fork" and not fm.get("agent"):
                err(f"{rel(skill_md)}: forked command without `agent:` would run with the default full-tool subagent")
        if layer == "reference":
            if not ui_false:
                err(f"{rel(skill_md)}: reference skill must set `user-invocable: false`")
            if dmi:
                err(f"{rel(skill_md)}: reference skill with `disable-model-invocation: true` would be uninvocable by anyone")
        if layer == "role" and (dmi or ui_false):
            warn(f"{rel(skill_md)}: role skill hides itself from model or user — intended?")

        if fm.get("context") == "fork":
            if fm.get("agent"):
                skills[name]["_fork_agent"] = str(fm["agent"])
        elif fm.get("agent"):
            warn(f"{rel(skill_md)}: `agent:` set without `context: fork` — has no effect")
        elif fm.get("context") not in (None, "fork"):
            err(f"{rel(skill_md)}: unknown `context` value {fm.get('context')!r}")
    if not skills:
        err("no skills found under skills/*/SKILL.md")
    return skills, layers


def check_agents(skills: dict[str, dict]) -> dict[str, dict]:
    agents: dict[str, dict] = {}
    for agent_md in sorted((ROOT / "agents").glob("*.md")):
        fm = load_frontmatter(agent_md)
        if fm is None:
            continue
        name = fm.get("name")
        if not isinstance(name, str) or not name:
            err(f"{rel(agent_md)}: missing `name`")
            continue
        if name != agent_md.stem:
            err(f"{rel(agent_md)}: name {name!r} != file name {agent_md.stem!r}")
        if not KEBAB.match(name):
            err(f"{rel(agent_md)}: name {name!r} is not kebab-case")
        check_description(agent_md, fm.get("description"))
        if name in agents:
            err(f"{rel(agent_md)}: duplicate agent name {name!r}")
        agents[name] = fm

        model = fm.get("model")
        if model is None:
            warn(f"{rel(agent_md)}: no `model` — prefer explicit `inherit`")
        elif str(model) not in VALID_MODELS:
            err(f"{rel(agent_md)}: model {model!r} not in {sorted(VALID_MODELS)}")

        for s in as_list(fm.get("skills")):
            if s not in skills:
                err(f"{rel(agent_md)}: preloads unknown skill {s!r}")

        meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
        if str(meta.get("layer", "")) != "subagent":
            err(f"{rel(agent_md)}: metadata.layer must be 'subagent'")

        disallowed = set(as_list(fm.get("disallowedTools")))
        allowed = as_list(fm.get("tools"))
        if name not in MUTABLE_AGENTS:
            blocked = disallowed if not allowed else (READ_ONLY_BLOCK - set(allowed))
            missing = READ_ONLY_BLOCK - blocked
            if missing:
                err(f"{rel(agent_md)}: analysis agent {name!r} must block {sorted(missing)} "
                    f"(disallowedTools: {', '.join(sorted(READ_ONLY_BLOCK))})")
            if allowed and "Bash" in allowed:
                warn(f"{rel(agent_md)}: Bash is allowed on a read-only agent — prompt-restricted only")
        if name not in ORCHESTRATOR_AGENTS and "Agent" not in disallowed and (not allowed or "Agent" in allowed):
            err(f"{rel(agent_md)}: only {sorted(ORCHESTRATOR_AGENTS)} may spawn agents — add `Agent` to disallowedTools")
    if not agents:
        err("no agents found under agents/*.md")
    return agents


def check_fork_targets(skills: dict[str, dict], agents: dict[str, dict]) -> None:
    for name, fm in skills.items():
        target = fm.get("_fork_agent")
        if not target:
            continue
        bare = strip_ns(target)
        if bare not in agents and target not in BUILTIN_AGENT_TYPES:
            err(f"skills/{name}/SKILL.md: `agent: {target}` does not exist in agents/")
        elif bare in agents and not target.startswith(PLUGIN_NAME + ":"):
            warn(f"skills/{name}/SKILL.md: `agent: {target}` is not namespaced; plugin agents register as {PLUGIN_NAME}:{bare}")


def check_plugin_root_refs() -> None:
    pat = re.compile(r"guidence/(GUIDE|MCP-GUIDE|README|CLAUDE\.user\.template)\.md")
    for path in list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "agents").glob("*.md")):
        text = read_text(path) or ""
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in pat.finditer(line):
                if line[:m.start()].endswith("${CLAUDE_PLUGIN_ROOT}/"):
                    continue
                err(f"{rel(path)}:{lineno}: `guidence/...` path not prefixed by ${{CLAUDE_PLUGIN_ROOT}}/ resolves in the consumer project")


def check_manifests() -> None:
    try:
        plugin = json.loads(read_text(ROOT / ".claude-plugin/plugin.json") or "")
        market = json.loads(read_text(ROOT / ".claude-plugin/marketplace.json") or "")
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as exc:
        err(f"manifest JSON error: {exc}")
        return
    pv = plugin.get("version")
    entries = [p for p in market.get("plugins", []) if p.get("name") == plugin.get("name")]
    if not entries:
        err("marketplace.json has no plugin entry matching plugin.json name")
    elif entries[0].get("version") != pv:
        err(f"version mismatch: plugin.json {pv!r} vs marketplace.json {entries[0].get('version')!r}")
    if market.get("version") not in (None, pv):
        warn(f"marketplace.json top-level version {market.get('version')!r} differs from plugin version {pv!r}")
    skills_field = plugin.get("skills", [])
    if isinstance(skills_field, str):
        skills_field = [skills_field]
    for r in skills_field:
        if not isinstance(r, str) or not (ROOT / r).exists():
            err(f"plugin.json skills path does not exist: {r!r}")
    if plugin.get("name") != PLUGIN_NAME:
        err(f"plugin.json name {plugin.get('name')!r} != expected {PLUGIN_NAME!r}")


def check_mcp() -> None:
    example = ROOT / ".mcp.json.example"
    if example.exists():
        try:
            data = json.loads(read_text(example) or "")
        except json.JSONDecodeError as exc:
            err(f".mcp.json.example JSON error: {exc}")
        else:
            if data != {"mcpServers": {}}:
                err('.mcp.json.example must be exactly {"mcpServers": {}} (GUIDE.md §11: no guessed server definitions)')
    real = ROOT / ".mcp.json"
    if real.exists():
        try:
            data = json.loads(read_text(real) or "")
        except json.JSONDecodeError as exc:
            err(f".mcp.json JSON error: {exc}")
            return
        if data.get("mcpServers"):
            err(".mcp.json at the plugin root is populated — it would auto-load into every consumer session; keep servers out of this repo")
        else:
            warn(".mcp.json exists at the plugin root (empty) — remove it; .mcp.json.example is the documented placeholder")


PLACEHOLDER_WORDS = {"user", "username", "usr", "pass", "password", "passwd", "pwd", "secret", "token", "key", "xxx", "redacted", "changeme"}


def _is_placeholder(match: str) -> bool:
    """True for documentation placeholders (`://user:pass@host`, `<host>`, `***`, `${VAR}`) and regex literals.
    A real-looking password (e.g. `P@ssw0rd!`) is never a placeholder, even if the user part is generic."""
    if any(ch in match for ch in "<>*$[](\\"):
        return True
    m = re.search(r"://([^:@]+):(.+)@[^@]*$", match)
    if m:
        pw = m.group(2).lower()
        if pw in PLACEHOLDER_WORDS or set(pw) <= set("*x."):
            return True
    return False


def _selftest() -> None:
    """Guard regression cases from the review (run with --selftest)."""
    cases = {
        "rtsp://admin:P@ssw0rd!@192.168.1.100:554/stream": True,
        "mongodb://root:p@ssword@cluster0.mongodb.net/db": True,
        "rtsp://admin:Secret123@192.168.1.100:554/stream": True,
        "rtsp://<user>:<password>@<camera-host>:554/stream": False,
        "postgres://user:pass@host/db": False,
        "replaces `://user:pass@` with `://***:***@`": False,
        "amqp://svc:${RABBIT_PASSWORD}@broker": False,
    }
    bad = []
    for text, expect_flag in cases.items():
        m = SECRET_VALUE_PATTERNS[0].search(text)
        flagged = bool(m) and not _is_placeholder(m.group(0))
        if flagged != expect_flag:
            bad.append((text, flagged))
    if bad:
        for text, flagged in bad:
            print(f"SELFTEST FAIL {text!r}: flagged={flagged}")
        sys.exit(2)
    print("SELFTEST OK")


def check_secrets() -> None:
    paths = (list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "agents").glob("*.md"))
             + list((ROOT / "mcp").glob("*")) + list((ROOT / "templates").glob("*"))
             + list((ROOT / ".claude-plugin").glob("*.json")) + [ROOT / ".mcp.json.example", ROOT / ".mcp.json",
             ROOT / "README.md", ROOT / "CLAUDE.md"])
    for path in paths:
        if not path.is_file():
            continue
        text = read_text(path)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pat in SECRET_VALUE_PATTERNS:
                m = pat.search(line)
                if m and not _is_placeholder(m.group(0)):
                    err(f"{rel(path)}:{lineno}: secret-looking value {m.group(0)[:12]!r}... - mask or remove")
                    break
        if path.suffix == ".json":
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                continue

            def walk(o, trail: str) -> None:
                if isinstance(o, dict):
                    for k, v in o.items():
                        if SECRET_KEY.search(str(k)) and isinstance(v, str) and v and not v.startswith("${"):
                            err(f"{rel(path)}: `{trail}{k}` looks like a committed secret value")
                        walk(v, f"{trail}{k}.")
                elif isinstance(o, list):
                    for i, v in enumerate(o):
                        walk(v, f"{trail}[{i}].")

            walk(obj, "")


def check_stale_identifiers() -> None:
    paths = (list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "agents").glob("*.md"))
             + list((ROOT / "templates").glob("*")) + list((ROOT / "mcp").glob("*"))
             + list((ROOT / ".claude-plugin").glob("*.json")) + [ROOT / "README.md", ROOT / "CLAUDE.md"])
    for path in paths:
        if not path.is_file():
            continue
        text = read_text(path)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if "renamed" in line.lower():
                continue
            for s in STALE_IDENTIFIERS:
                if s in line:
                    err(f"{rel(path)}:{lineno}: stale identifier {s!r}")


def check_subagent_type_refs(agents: dict[str, dict]) -> None:
    pat = re.compile(r"subagent_type[:=]?\s*`?([A-Za-z0-9_:-]+)")
    for path in list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "agents").glob("*.md")):
        text = read_text(path) or ""
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in pat.finditer(line):
                ref = m.group(1)
                if strip_ns(ref) in agents and not ref.startswith(PLUGIN_NAME + ":"):
                    err(f"{rel(path)}:{lineno}: `subagent_type: {ref}` must be namespaced `{PLUGIN_NAME}:{ref}`")


# --------------------------------------------------------------------------- main

def main() -> int:
    if _yaml is None:
        warn("PyYAML not installed — using the conservative fallback parser (pip install pyyaml for exact results)")
    check_required_files()
    skills, layers = check_skills()
    agents = check_agents(skills)
    check_fork_targets(skills, agents)
    check_subagent_type_refs(agents)
    check_plugin_root_refs()
    check_manifests()
    check_mcp()
    check_secrets()
    check_stale_identifiers()

    by_layer: dict[str, list[str]] = {}
    for name, layer in layers.items():
        by_layer.setdefault(layer or "?", []).append(name)
    print("skill-ai pack summary")
    for layer in ("command", "role", "reference"):
        names = sorted(by_layer.get(layer, []))
        print(f"  {layer:<10} {len(names):>2}  {' '.join(repr(n)[1:-1] for n in names)}")
    print(f"  {'subagent':<10} {len(agents):>2}  {' '.join(repr(n)[1:-1] for n in sorted(agents))}")
    forks = sorted(f"{n}->{fm['_fork_agent']}" for n, fm in skills.items() if fm.get("_fork_agent"))
    print(f"  forks      {len(forks):>2}  {' '.join(forks)}")
    print()
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print()
    print(f"RESULT {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    sys.exit(main())
