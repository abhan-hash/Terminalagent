import os
import subprocess
from pathlib import Path

IMAGE = "tagent-sandbox"
CONTAINER_WORKSPACE = "/workspace"
COMMAND_TIMEOUT = 30

class Sandbox:
    """One Docker container that runs every agent command for a session."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.container_id = None

    def start(self):
        """Start the container. It sits idle until commands are sent to it."""
        args = [
            "docker", "run", "--detach", "--rm",
            "--label", "tagent-sandbox",
            # Isolation and limits
            "--network", "none",
            "--memory", "1g",
            "--cpus", "1",
            "--pids-limit", "256",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            # Run as you, so files the agent creates are owned by you
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--env", "HOME=/tmp",
            # The project folder is the only host folder the container can see
            "--volume", f"{self.workspace}:{CONTAINER_WORKSPACE}",
            "--workdir", CONTAINER_WORKSPACE,
        ]

        # Hide the API keys from commands by mounting an empty file over .env
        if (self.workspace / ".env").exists():
            args += ["--volume", f"/dev/null:{CONTAINER_WORKSPACE}/.env:ro"]

        args += [IMAGE, "sleep", "infinity"]

        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Could not start the sandbox: {result.stderr.strip()}\n"
                f"Did you build the image? Run: docker build -t {IMAGE} docker/"
            )
        self.container_id = result.stdout.strip()

    def run(self, command: str) -> subprocess.CompletedProcess:
        """Run one shell command inside the container."""
        return subprocess.run(
            [
                "docker", "exec", self.container_id,
                "timeout", "--signal=KILL", str(COMMAND_TIMEOUT),
                "sh", "-c", command,
            ],
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT + 10,
        )

    def stop(self):
        """Kill and remove the container."""
        if self.container_id:
            subprocess.run(
                ["docker", "rm", "--force", self.container_id],
                capture_output=True,
            )
            self.container_id = None


