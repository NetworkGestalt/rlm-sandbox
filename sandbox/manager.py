from pathlib import Path

from e2b_code_interpreter import Sandbox

from config import SANDBOX_WORKDIR, SANDBOX_TEMPLATE

DEFAULT_IGNORE = {
    ".git",
    ".env",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".DS_Store",
    "Thumbs.db",
}


def _should_ignore(relative: Path, ignore: set[str]) -> bool:
    return any(part in ignore for part in relative.parts)


def collect_files(
    directory: Path,
    ignore: set[str] | None = None,
) -> list[dict]:
    """Walk *directory* and return a list of {path, data} dicts ready for upload."""
    directory = directory.resolve()
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")
    ignore = DEFAULT_IGNORE if ignore is None else ignore

    files: list[dict] = []
    for local_path in directory.rglob("*"):
        if not local_path.is_file():
            continue

        relative = local_path.relative_to(directory)
        if _should_ignore(relative, ignore):
            continue

        try:
            data = local_path.read_bytes()
        except PermissionError:
            print(f"  Skipping unreadable file: {relative}")
            continue

        sandbox_path = f"{SANDBOX_WORKDIR}/{relative.as_posix()}"
        files.append({"path": sandbox_path, "data": data})

    print(f"Collected {len(files)} files from {directory}")
    return files


def upload_files(sandbox: Sandbox, directory: Path, ignore: set[str] | None = None):
    """Collect files from *directory* and upload them to the sandbox."""
    files = collect_files(directory, ignore)
    if files:
        sandbox.files.write_files(files)
        print(f"Uploaded {len(files)} files to {SANDBOX_WORKDIR}")


def create_sandbox(
    directory: Path,
    timeout: int = 300,
) -> Sandbox:
    """Create a network-isolated E2B sandbox with *directory* uploaded into it."""
    sandbox = Sandbox.create(
        template=SANDBOX_TEMPLATE,
        timeout=timeout,
        allow_internet_access=False,
    )
    print(f"Sandbox created: {sandbox.sandbox_id}")

    upload_files(sandbox, directory)

    return sandbox
