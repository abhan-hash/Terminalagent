import subprocess
from pathlib import Path


WORKSPACE = Path.cwd().resolve()

def build_repository_context() -> str:
    """Build a small, safe snapshot of the current repository."""
    ignored_directories = {".git", ".venv", "__pycache__"}
    sensitive_files = {".env", ".env.local", ".env.production"}
    files = []

    try:
        for path in sorted(WORKSPACE.rglob("*")):
            if not path.is_file():
                continue
            if any(part in ignored_directories for part in path.parts):
                continue
            if path.name in sensitive_files:
                files.append(f"- {path.relative_to(WORKSPACE)} [contents hidden]")
            else:
                files.append(f"- {path.relative_to(WORKSPACE)}")
    except OSError as error:
        files.append(f"[Could not scan workspace: {error}]")

    if len(files) > 200:
        files = files[:200]
        files.append("- [file list truncated after 200 files]")

    sections = [
        f"Workspace: {WORKSPACE}",
        "\nFiles:\n" + ("\n".join(files) if files else "- [no files found]"),
    ]

    for filename in ("README.md", "AGENTS.md"):
        path = WORKSPACE / filename
        if not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as error:
            content = f"[Could not read {filename}: {error}]"

        max_characters = 6_000
        if len(content) > max_characters:
            content = content[:max_characters]
            content += f"\n[Truncated after {max_characters} characters.]"

        sections.append(f"\n{filename}:\n{content}")

    try:
        git_result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=5,
        )
        git_status = git_result.stdout.strip()
        if git_result.returncode != 0:
            git_status = "[Not a Git repository]"
    except (OSError, subprocess.TimeoutExpired) as error:
        git_status = f"[Could not read Git status: {error}]"

    sections.append(f"\nGit status:\n{git_status or '[clean]'}")
    return "\n".join(sections)