import hashlib
from pathlib import Path
from src.exceptions import FileSecurityError, FileAccessError


def verify_file_hash(target_file: Path) -> None:
    """Verify that a file hash matches the stored signature.

    Args:
        target_file: The file whose companion ``.hash`` file should be
            validated.

    Raises:
        FileAccessError: If the signature file is missing or cannot be read.
        FileSecurityError: If the stored hash does not match the file.
    """
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
    """Calculate the SHA-256 hash for a file.

    Args:
        file_path: The path to the file to hash.

    Returns:
        The hexadecimal SHA-256 digest for the file contents.

    Raises:
        FileAccessError: If the file cannot be read.
    """
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
    """Write a companion ``.hash`` file for the given target file.

    Args:
        target_file: The file whose hash should be persisted.

    Raises:
        FileAccessError: If the hash file cannot be written.
    """
    hash_path = target_file.with_suffix(target_file.suffix + ".hash")
    file_hash = calculate_file_hash(target_file)
    try:
        with open(hash_path, "w") as f:
            f.write(file_hash)
    except OSError as e:
        raise FileAccessError(
            f"Could not save hash for {target_file.name}") from e
