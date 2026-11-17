from sandbox import COMMAND_TIMEOUT, Sandbox

import subprocess
from pathlib import Path

from langchain_core.tools import tool 
from langgraph.types import interrupt


WORKSPACE = Path.cwd().resolve()
sandbox = Sandbox(WORKSPACE)

def resolve_workspace_path(path: str) -> Path | None:
    """Resolve a path and return None if it escapes the workspace."""
    requested_path = Path(path)

    if requested_path.is_absolute():
        file_path = requested_path.resolve()
    else:
        file_path = (WORKSPACE / requested_path).resolve()

    try:
        file_path.relative_to(WORKSPACE)
    except ValueError:
        return None

    return file_path

@tool
def read_file(path: str) -> str:
    """Read a text file inside the current workspace.

    Use this when you need to inspect an existing file before answering
    or making a change. The path can be relative to the workspace.
    """
    file_path = resolve_workspace_path(path)
    if file_path is None:
        return "Error: the requested path is outside the workspace."

    if not file_path.exists():
        return f"Error: file does not exist: {path}"

    if not file_path.is_file():
        return f"Error: path is not a file: {path}"

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: file is not a UTF-8 text file: {path}"
    except OSError as error:
        return f"Error reading {path}: {error}"

    max_characters = 20_000
    if len(content) > max_characters:
        content = content[:max_characters]
        content += f"\n\n[File truncated after {max_characters} characters.]"

    return content


def request_approval(action: str, details: str) -> bool:
    """Pause the graph and wait for the user to approve an action."""
    answer = interrupt(
        {
            "action": action,
            "details": details,
            "question": "Allow this action? Type y or n.",
        }
    )

    return str(answer).strip().lower() in {"y", "yes"}

@tool
def write_file(path: str, content: str) -> str:
    """Create or replace a UTF-8 text file inside the current workspace."""
    file_path = resolve_workspace_path(path)
    if file_path is None:
        return "Error: the requested path is outside the workspace."

    approved = request_approval(
        "write_file",
        f"Write {len(content)} characters to: {file_path}",
    )

    if not approved:
        return "User denied the file write."

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    except OSError as error:
        return f"Error writing {path}: {error}"

    return f"Successfully wrote {len(content)} characters to {path}."


@tool
def run_command(command: str) -> str:
    """Run a shell command inside an isolated Linux container.

    The workspace is mounted at /workspace, which is the working directory,
    so use paths relative to the workspace. Python 3.12, pytest and git are
    installed. There is no internet access, so installing packages will fail.
    """
    approved = request_approval(
        "run_command",
        f"Run this command in the sandbox:\n{command}",
    )

    if not approved:
        return "User denied the command."

    try:
        completed = sandbox.run(command)
    except subprocess.TimeoutExpired:
        return "Error: the sandbox did not respond."
    except OSError as error:
        return f"Error running command: {error}"

    if completed.returncode == 124:
        return f"Error: command timed out after {COMMAND_TIMEOUT} seconds."

    output = (completed.stdout + completed.stderr).strip()
    max_characters = 10_000
    if len(output) > max_characters:
        output = output[-max_characters:]
        output = (
            f"[Output truncated to the last {max_characters} characters.]\n"
            f"{output}"
        )

    if not output:
        output = "(command produced no output)"

    return f"Exit code: {completed.returncode}\n{output}"

tools = [read_file, write_file, run_command]
