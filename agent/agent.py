"""Core agent logic: LLM tool-calling loop with a small, safe toolset.

Works with any OpenAI-compatible chat API (Groq, Gemini OpenAI endpoint,
OpenRouter, Together, etc.). If no API key is set, it runs in a
"tools-only" mode so you can still test web search / file reading.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote_plus, unquote

import httpx

WORKSPACE = Path(os.getenv("AGENT_WORKSPACE", "/tmp/agent_workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
ENABLE_SHELL = os.getenv("ENABLE_SHELL", "0") == "1"
SHELL_ALLOWLIST = {c.strip() for c in os.getenv(
    "SHELL_ALLOWLIST", "ls,cat,head,tail,wc,echo,pwd,date,python3,pip,git,grep,find,unzip,zip,tar,curl"
).split(",") if c.strip()}
GH_TOKEN = os.getenv("GH_TOKEN", "")          # for triggering APK builds
GH_REPO = os.getenv("GH_REPO", "")            # e.g. "codexanta/website"

SYSTEM_PROMPT = (
    "You are a helpful personal AI agent. You can search the web, fetch pages, "
    "read files in the workspace, run allowed shell commands, and trigger an APK build. "
    "Use tools when they help. Answer in the same language the user writes in "
    "(Bangla, Banglish or English)."
)


# ---------------- tools ----------------
def tool_web_search(query: str) -> str:
    """DuckDuckGo HTML search (no API key needed)."""
    try:
        r = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
            follow_redirects=True,
        )
        items = re.findall(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</a>',
            r.text, flags=re.S,
        )
        out = []
        for href, title, snip in items[:6]:
            href = unquote(re.sub(r".*uddg=", "", href)).split("&")[0]
            clean = lambda s: re.sub(r"<[^>]+>|&[a-z#0-9]+;", " ", s).strip()
            out.append(f"- {clean(title)}\n  {href}\n  {clean(snip)}")
        return "\n".join(out) or "No results."
    except Exception as e:  # noqa: BLE001
        return f"search error: {e}"


def tool_fetch_url(url: str) -> str:
    """Fetch a web page and return readable text (truncated)."""
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0"})
        text = re.sub(r"(?is)<(script|style).*?</\1>", " ", r.text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:6000]
    except Exception as e:  # noqa: BLE001
        return f"fetch error: {e}"


def _safe_path(path: str) -> Path:
    p = (WORKSPACE / path).resolve()
    if WORKSPACE not in p.parents and p != WORKSPACE:
        raise ValueError("path outside workspace")
    return p


def tool_read_file(path: str) -> str:
    """Read a text file (txt, md, csv, json, py, html...) from the workspace."""
    try:
        p = _safe_path(path)
        data = p.read_text(encoding="utf-8", errors="replace")
        return data[:20000]
    except Exception as e:  # noqa: BLE001
        return f"read error: {e}"


def tool_write_file(path: str, content: str) -> str:
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {p.relative_to(WORKSPACE)} ({len(content)} chars)"
    except Exception as e:  # noqa: BLE001
        return f"write error: {e}"


def tool_run_shell(command: str) -> str:
    """Run a shell command inside the workspace. Only allowlisted programs run."""
    if not ENABLE_SHELL:
        return "shell is disabled (set ENABLE_SHELL=1 to enable)."
    first = command.strip().split()[0] if command.strip() else ""
    if first not in SHELL_ALLOWLIST:
        return f"'{first}' is not in SHELL_ALLOWLIST."
    if re.search(r"[;&|`$><]", command):
        return "shell operators are not allowed (; & | ` $ > <)."
    try:
        res = subprocess.run(command, shell=True, cwd=WORKSPACE, capture_output=True,
                             text=True, timeout=60)
        return (res.stdout + res.stderr)[-8000:] or f"exit {res.returncode}"
    except Exception as e:  # noqa: BLE001
        return f"shell error: {e}"


def tool_build_apk(ref: str = "main") -> str:
    """Trigger the GitHub Actions APK build workflow."""
    if not (GH_TOKEN and GH_REPO):
        return "APK build not configured (set GH_TOKEN and GH_REPO)."
    r = httpx.post(
        f"https://api.github.com/repos/{GH_REPO}/actions/workflows/build-apk.yml/dispatches",
        headers={"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"},
        json={"ref": ref}, timeout=20,
    )
    return "APK build started. Check the Actions tab in GitHub." if r.status_code == 204 \
        else f"GitHub error {r.status_code}: {r.text[:300]}"


TOOLS = {
    "web_search": (tool_web_search, {"query": "string"}),
    "fetch_url": (tool_fetch_url, {"url": "string"}),
    "read_file": (tool_read_file, {"path": "string"}),
    "write_file": (tool_write_file, {"path": "string", "content": "string"}),
    "run_shell": (tool_run_shell, {"command": "string"}),
    "build_apk": (tool_build_apk, {"ref": "string"}),
}

DESCRIPTIONS = {
    "web_search": "Search the web and return top results.",
    "fetch_url": "Fetch a web page and return its text.",
    "read_file": "Read a text file from the agent workspace.",
    "write_file": "Write a text file into the agent workspace.",
    "run_shell": "Run an allowed shell command in the workspace.",
    "build_apk": "Trigger the Android APK build on GitHub Actions.",
}


def _openai_tools():
    out = []
    for name, (_, params) in TOOLS.items():
        out.append({
            "type": "function",
            "function": {
                "name": name,
                "description": DESCRIPTIONS[name],
                "parameters": {
                    "type": "object",
                    "properties": {k: {"type": "string"} for k in params},
                    "required": [k for k in params if k != "ref"],
                },
            },
        })
    return out


def _call_llm(messages):
    r = httpx.post(
        f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={"model": LLM_MODEL, "messages": messages, "tools": _openai_tools(),
              "tool_choice": "auto"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


def run_agent(user_text: str, history: list[dict] | None = None, max_steps: int = 6) -> dict:
    """Returns {"reply": str, "tool_calls": [..]}."""
    if not LLM_API_KEY:
        # Tools-only fallback: lets you test without any API key.
        m = re.match(r"^(search|fetch|read|shell|apk)\s*:?\s*(.*)$", user_text.strip(), re.I)
        if not m:
            return {"reply": "LLM_API_KEY set kora nei. Ekhon tools-only mode: "
                             "'search: query', 'fetch: url', 'read: file.txt', "
                             "'shell: ls', 'apk'.", "tool_calls": []}
        cmd, arg = m.group(1).lower(), m.group(2)
        mapping = {"search": ("web_search", {"query": arg}),
                   "fetch": ("fetch_url", {"url": arg}),
                   "read": ("read_file", {"path": arg}),
                   "shell": ("run_shell", {"command": arg}),
                   "apk": ("build_apk", {})}
        name, args = mapping[cmd]
        result = TOOLS[name][0](**args)
        return {"reply": result, "tool_calls": [{"name": name, "args": args}]}

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += (history or [])[-20:]
    messages.append({"role": "user", "content": user_text})
    calls_log = []
    for _ in range(max_steps):
        msg = _call_llm(messages)
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return {"reply": msg.get("content") or "", "tool_calls": calls_log}
        messages.append(msg)
        for tc in tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            if name in TOOLS:
                try:
                    result = TOOLS[name][0](**args)
                except TypeError as e:
                    result = f"bad arguments: {e}"
            else:
                result = f"unknown tool {name}"
            calls_log.append({"name": name, "args": args})
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
    return {"reply": "Step limit reached.", "tool_calls": calls_log}
