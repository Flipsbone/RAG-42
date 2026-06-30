import hashlib
from pathlib import Path
from src.exceptions import FileSecurityError, FileAccessError


def verify_file_hash(target_file: Path) -> None:
    """Verifies if the current file hash matches the stored hash."""
    hash_path = target_file.with_suffix(target_file.suffix + ".hash")
    if not hash_path.exists():
        raise FileAccessError(
            f"Signature file missing for {target_file.name}")

    with open(hash_path, "r") as f:
        stored_hash = f.read().strip()

    if calculate_file_hash(target_file) != stored_hash:
        raise FileSecurityError(
            f"Alert: {target_file.name} has been changed!")


def calculate_file_hash(file_path: Path) -> str:
    """Calculates SHA-256 hash."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except OSError as e:
        raise FileAccessError(
            f"Could not read file for hashing: {file_path}") from e


def save_hash_file(target_file: Path) -> None:
    """Generates a .hash file next to the target file."""
    hash_path = target_file.with_suffix(target_file.suffix + ".hash")
    file_hash = calculate_file_hash(target_file)
    try:
        with open(hash_path, "w") as f:
            f.write(file_hash)
    except OSError as e:
        raise FileAccessError(
            f"Could not save hash for {target_file.name}") from e
