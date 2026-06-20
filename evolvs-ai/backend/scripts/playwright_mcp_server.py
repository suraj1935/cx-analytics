"""
MCP server for the remote Playwright test orchestrator.

Wraps the SSH + Playwright + Slack workflow already implemented in
ai_test_orchestrator.py as MCP tools, so an MCP client (Claude Code,
Cursor, etc.) can trigger a remote test run and read back the report
directly during a coding session, instead of you running
`npm run mcp-test` by hand and pasting the output back into chat.

This file deliberately does NOT duplicate the SSH/SCP logic - it
imports the existing private helpers from ai_test_orchestrator.py and
exposes them as tools, so both entry points (the old CLI script and
this server) stay in sync automatically.

--------------------------------------------------------------------
Setup
--------------------------------------------------------------------
1. Install dependencies (separate from backend/requirements.txt -
   this is a local dev tool, not something that should ship inside
   the production Docker image):

       pip install "mcp[cli]" python-dotenv

2. Make sure backend/.env has MCP_HOST, MCP_USER, MCP_SSH_KEY,
   REMOTE_PROJECT_PATH, and PLAYWRIGHT_CMD set (same vars
   ai_test_orchestrator.py already uses).

3. Register it with Claude Code, run from the repo root:

       claude mcp add --transport stdio --scope project test-runner \
           -- python /absolute/path/to/backend/scripts/playwright_mcp_server.py

   ("--scope project" writes it to .mcp.json so it's shared with
   anyone else who clones the repo - drop that flag to keep it local
   to just your machine.)

   For Cursor, add the equivalent block to .cursor/mcp.json:

       {
         "mcpServers": {
           "test-runner": {
             "command": "python",
             "args": ["/absolute/path/to/backend/scripts/playwright_mcp_server.py"]
           }
         }
       }

4. Restart Claude Code / Cursor, then just ask it things like
   "run the playwright suite and tell me what failed."

--------------------------------------------------------------------
Why a separate logging setup
--------------------------------------------------------------------
This server talks to its MCP client over stdio. The JSON-RPC protocol
messages travel over stdout, so anything else written to stdout (a
stray print(), a library logging to stdout by default) corrupts the
stream and silently breaks the connection. All logging here is
explicitly routed to stderr instead.
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from ai_test_orchestrator import (
    MCP_HOST,
    MCP_USER,
    REMOTE_PROJECT_PATH,
    _check_git_changes,
    _fetch_report,
    _post_to_slack,
    _require_config,
    _summarize_report,
    _trigger_playwright_tests,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("playwright_mcp_server")

mcp = FastMCP("evolvs-test-runner")


@mcp.tool()
def check_config() -> dict:
    """Report whether the orchestrator is configured and safe to run.

    Checks that the required environment variables are set and
    whether the local working tree has uncommitted changes (the
    underlying script refuses to run tests against a dirty tree by
    default). Call this first if you're not sure the setup is wired
    up correctly.
    """
    try:
        _require_config()
        configured, config_error = True, None
    except RuntimeError as e:
        configured, config_error = False, str(e)

    return {
        "configured": configured,
        "config_error": config_error,
        "mcp_host": MCP_HOST,
        "mcp_user": MCP_USER,
        "remote_project_path": REMOTE_PROJECT_PATH,
        "git_clean": _check_git_changes(),
    }


@mcp.tool()
def run_tests(allow_dirty_git: bool = False) -> dict:
    """Trigger the Playwright suite on the remote host over SSH.

    Note: this blocks until the remote command returns, which means
    until the whole remote Playwright run finishes (PLAYWRIGHT_CMD
    runs synchronously) - it is not "fire and forget." For a long
    suite, expect this tool call to take a while rather than
    returning instantly.

    By default this refuses to run if there are uncommitted local
    changes, matching the original script. Pass allow_dirty_git=True
    to override that for an in-progress debugging session.
    """
    try:
        _require_config()
    except RuntimeError as e:
        return {"success": False, "stage": "config", "error": str(e)}

    if not allow_dirty_git and not _check_git_changes():
        return {
            "success": False,
            "stage": "git_check",
            "error": (
                "Uncommitted local changes detected. Commit or stash them, "
                "or call run_tests(allow_dirty_git=True) to override."
            ),
        }

    try:
        _trigger_playwright_tests()
    except RuntimeError as e:
        return {"success": False, "stage": "trigger", "error": str(e)}

    return {
        "success": True,
        "stage": "completed",
        "message": "Remote Playwright run finished. Call get_report() to read the results.",
    }


@mcp.tool()
def get_report(notify_slack: bool = False) -> dict:
    """Fetch and summarize the most recent Playwright JSON report.

    Call this after run_tests() to read back pass/fail counts. Set
    notify_slack=True to also post the summary to the configured
    Slack webhook (no-op if SLACK_WEBHOOK isn't set).
    """
    try:
        _require_config()
    except RuntimeError as e:
        return {"success": False, "stage": "config", "error": str(e)}

    try:
        report = _fetch_report()
    except RuntimeError as e:
        return {"success": False, "stage": "fetch", "error": str(e)}

    summary = _summarize_report(report)

    if notify_slack:
        try:
            _post_to_slack(summary)
        except Exception as e:  # network/webhook errors shouldn't fail the whole tool call
            logger.warning("Slack notification failed: %s", e)

    return {"success": True, "summary": summary, "stats": report.get("stats", {})}


@mcp.tool()
def run_tests_and_report(allow_dirty_git: bool = False, notify_slack: bool = False) -> dict:
    """Convenience tool: run the suite, then immediately fetch and summarize the report.

    Equivalent to calling run_tests() followed by get_report() - use
    the two separately if you want to check in between (e.g. confirm
    the trigger succeeded before waiting on the report).
    """
    run_result = run_tests(allow_dirty_git=allow_dirty_git)
    if not run_result["success"]:
        return run_result

    return get_report(notify_slack=notify_slack)


if __name__ == "__main__":
    mcp.run()  # defaults to stdio transport
