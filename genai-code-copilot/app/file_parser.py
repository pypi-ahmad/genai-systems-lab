from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict


ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".md"}
IGNORED_DIRECTORIES = {".venv", "node_modules", ".git"}


class ParsedFile(TypedDict):
	path: str
	content: str


def _should_ignore_directory(path: Path) -> bool:
	return any(part in IGNORED_DIRECTORIES for part in path.parts)


def _read_text_file(path: Path) -> str:
	return path.read_text(encoding="utf-8", errors="replace")


def scan_directory(directory: str | Path) -> list[ParsedFile]:
	root = Path(directory).expanduser().resolve()

	if not root.exists():
		raise FileNotFoundError(f"Directory does not exist: {root}")
	if not root.is_dir():
		raise NotADirectoryError(f"Path is not a directory: {root}")

	parsed_files: list[ParsedFile] = []

	for current_root, dir_names, file_names in os.walk(root):
		dir_names[:] = sorted(
			name for name in dir_names if name not in IGNORED_DIRECTORIES
		)

		current_path = Path(current_root)
		if _should_ignore_directory(current_path):
			continue

		for file_name in sorted(file_names):
			file_path = current_path / file_name

			if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
				continue

			parsed_files.append(
				{
					"path": str(file_path),
					"content": _read_text_file(file_path),
				}
			)

	return parsed_files


__all__ = ["ParsedFile", "scan_directory"]
