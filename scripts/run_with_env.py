import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values


ROOT_DIR = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run any command with variables loaded from a selected .env file.",
    )
    parser.add_argument(
        "--env-file",
        default="config/.env",
        help="Path to the .env file relative to the project root.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run. Put '--' before the command.",
    )
    return parser.parse_args()


def resolve_env_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path.resolve()


def main() -> int:
    args = parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]

    if not command:
        print("No command provided. Example:")
        print("  uv run python scripts/run_with_env.py --env-file config/.env.smoke -- uv run main.py")
        return 2

    env_path = resolve_env_path(args.env_file)
    if not env_path.exists():
        print(f"Env file not found: {env_path}")
        return 1

    child_env = os.environ.copy()
    for key, value in dotenv_values(env_path).items():
        if value is not None:
            child_env[key] = value

    print(f"Using env file: {env_path}")
    print(f"Running command: {' '.join(command)}")

    completed = subprocess.run(command, cwd=ROOT_DIR, env=child_env)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
