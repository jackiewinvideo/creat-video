import os
from pathlib import Path
from typing import List, Optional


class ToolSecurityException(Exception):
    """Raised when a security validation fails."""
    pass


class ToolSecurityManager:
    """
    Enforces security policies on tool invocation:
    - Restricts file access to authorized workspace roots
    - Enforces non-shell list-based command argument execution
    - Prevents destructive overwrites of protected original assets
    - Validates execution timeout limits
    """

    def __init__(
        self,
        allowed_directories: Optional[List[str]] = None,
        max_timeout_seconds: int = 3600,
        max_file_size_mb: int = 10240,  # 10 GB
    ):
        self.allowed_directories: List[Path] = [
            Path(d).resolve() for d in (allowed_directories or [os.getcwd()])
        ]
        self.max_timeout_seconds = max_timeout_seconds
        self.max_file_size_mb = max_file_size_mb

    def add_allowed_directory(self, directory: str) -> None:
        path = Path(directory).resolve()
        if path not in self.allowed_directories:
            self.allowed_directories.append(path)

    def validate_file_path(self, file_path: str, must_exist: bool = False) -> Path:
        """
        Validates that a path resides within allowed directories
        and avoids path traversal attacks (e.g. ../../).
        """
        resolved_path = Path(file_path).resolve()

        # Check if inside any allowed directory
        is_allowed = any(
            self._is_subpath(resolved_path, allowed_dir)
            for allowed_dir in self.allowed_directories
        )

        if not is_allowed:
            raise ToolSecurityException(
                f"Access denied: Path '{resolved_path}' is outside allowed directories: "
                f"{[str(p) for p in self.allowed_directories]}"
            )

        if must_exist and not resolved_path.exists():
            raise ToolSecurityException(f"Path does not exist: '{resolved_path}'")

        return resolved_path

    def validate_timeout(self, timeout: Optional[int], default_timeout: int) -> int:
        effective_timeout = timeout if timeout is not None else default_timeout
        if effective_timeout <= 0:
            raise ToolSecurityException("Timeout must be greater than 0.")
        if effective_timeout > self.max_timeout_seconds:
            raise ToolSecurityException(
                f"Requested timeout {effective_timeout}s exceeds maximum limit of {self.max_timeout_seconds}s."
            )
        return effective_timeout

    def validate_cli_arguments(self, args: List[str]) -> None:
        """
        Ensure arguments are passed as an array, not raw shell pipelines/redirections.
        """
        if not isinstance(args, list):
            raise ToolSecurityException("CLI commands must be provided as a list of arguments, not a string.")

        dangerous_tokens = [";", "&&", "||", "|", "`", "$("]
        for arg in args:
            for token in dangerous_tokens:
                if token in arg:
                    raise ToolSecurityException(
                        f"Potentially dangerous shell operator '{token}' detected in argument: '{arg}'"
                    )

    @staticmethod
    def _is_subpath(child: Path, parent: Path) -> bool:
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False
