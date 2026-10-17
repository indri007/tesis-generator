"""Disaster Recovery & Backup Automation Engine.

Implements proportionate, verifiable, and secure backup and recovery drills for:
- Source configuration (config.yaml, .streamlit/config.toml, pyproject.toml)
- SQLite WAL Database (workspace/tesis_check.db) via atomic SQLite online backup
- SHA-256 cryptographic manifests for tamper detection
- Non-destructive restore drills in isolated temporary directories
- Strict exclusions: NEVER backs up .env, credentials, uploaded manuscripts, or caches.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tarfile
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Explicit allowlist of relative paths permitted in automated backups
APPROVED_BACKUP_ALLOWLIST = [
    "config.yaml",
    ".streamlit/config.toml",
    "pyproject.toml",
    "requirements.txt",
    "Makefile",
]

# Strict forbidden patterns to prevent credential or raw manuscript leakage
FORBIDDEN_PATTERNS = [
    ".env",
    "secrets.toml",
    ".key",
    ".pem",
    "credentials",
    ".venv",
    ".venv-test",
    "__pycache__",
    ".git",
    "data/raw",
    ".coverage",
    ".pytest_cache",
    ".ruff_cache",
]


@dataclass
class BackupManifestItem:
    """Record of a single file included in a backup."""

    relative_path: str
    size_bytes: int
    sha256: str
    modified_time: str


@dataclass
class BackupResult:
    """Result of a backup creation or verification operation."""

    success: bool
    archive_path: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    items_count: int = 0
    total_bytes: int = 0
    manifest: list[BackupManifestItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 checksum for a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_path_safe_for_backup(relative_path: str) -> bool:
    """Checks whether a relative path is approved and does not match forbidden patterns."""
    path_str = relative_path.replace("\\", "/").lower()
    for forbidden in FORBIDDEN_PATTERNS:
        if forbidden in path_str:
            return False
    return True


def backup_sqlite_database(src_db: Path, dest_db: Path) -> None:
    """Safely backs up SQLite database using the online backup API to prevent WAL corruption."""
    if not src_db.exists():
        return
    dest_db.parent.mkdir(parents=True, exist_ok=True)
    con_src = sqlite3.connect(str(src_db))
    con_dest = sqlite3.connect(str(dest_db))
    with con_dest:
        con_src.backup(con_dest)
    con_src.close()
    con_dest.close()


def create_backup_archive(
    project_root: str | Path,
    output_directory: str | Path,
    backup_tag: str = "tesischeck_backup",
) -> BackupResult:
    """Creates a verifiable tar.gz backup archive with cryptographic SHA-256 manifest."""
    root = Path(project_root).resolve()
    out_dir = Path(output_directory).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{backup_tag}_{timestamp_str}.tar.gz"
    temp_archive = out_dir / f"tmp_{archive_name}"
    final_archive = out_dir / archive_name

    manifest_items: list[BackupManifestItem] = []
    errors: list[str] = []

    # Use a temporary directory for staging SQLite backup and manifest.json
    with tempfile.TemporaryDirectory() as stage_dir:
        stage_path = Path(stage_dir)

        # 1. Stage SQLite DB if it exists
        live_db = root / "workspace" / "tesis_check.db"
        staged_db = stage_path / "tesis_check.db"
        has_db = False
        if live_db.exists():
            try:
                backup_sqlite_database(live_db, staged_db)
                has_db = True
            except Exception as err:
                errors.append(f"Gagal mencadangkan database SQLite: {err}")

        # 2. Collect approved files
        files_to_pack: list[tuple[Path, str]] = []  # (absolute_source, archive_arcname)

        for rel in APPROVED_BACKUP_ALLOWLIST:
            src_file = root / rel
            if src_file.exists() and src_file.is_file():
                if is_path_safe_for_backup(rel):
                    files_to_pack.append((src_file, rel))
                else:
                    errors.append(f"Berkas ditolak oleh filter keamanan: {rel}")

        if has_db and staged_db.exists():
            files_to_pack.append((staged_db, "workspace/tesis_check.db"))

        # 3. Compute manifest
        total_bytes = 0
        for src, arcname in files_to_pack:
            try:
                sha = compute_sha256(src)
                sz = src.stat().st_size
                mtime = datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                manifest_items.append(
                    BackupManifestItem(
                        relative_path=arcname,
                        size_bytes=sz,
                        sha256=sha,
                        modified_time=mtime,
                    )
                )
                total_bytes += sz
            except Exception as err:
                errors.append(f"Gagal menghitung hash untuk {arcname}: {err}")

        # Write manifest.json to stage
        manifest_file = stage_path / "manifest.json"
        manifest_data = {
            "version": "1.0",
            "timestamp": timestamp_str,
            "project": "TesisCheck MIKOM 2026",
            "items_count": len(manifest_items),
            "total_bytes": total_bytes,
            "files": [asdict(item) for item in manifest_items],
        }
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        files_to_pack.append((manifest_file, "manifest.json"))

        # 4. Create compressed tarball atomically
        try:
            with tarfile.open(temp_archive, "w:gz") as tar:
                for src, arcname in files_to_pack:
                    tar.add(src, arcname=arcname)
            # Atomic rename to final archive
            temp_archive.rename(final_archive)
        except Exception as err:
            if temp_archive.exists():
                temp_archive.unlink()
            return BackupResult(
                success=False,
                archive_path="",
                errors=[f"Gagal membuat arsip kompresi: {err}"] + errors,
            )

    return BackupResult(
        success=len(manifest_items) > 0 and len(errors) == 0,
        archive_path=str(final_archive),
        items_count=len(manifest_items),
        total_bytes=total_bytes,
        manifest=manifest_items,
        errors=errors,
    )


def verify_backup_archive(archive_path: str | Path) -> tuple[bool, list[str]]:
    """Verifies the integrity of a backup archive against its embedded manifest.json."""
    archive = Path(archive_path)
    if not archive.exists():
        return False, [f"Berkas arsip tidak ditemukan: {archive}"]

    errors: list[str] = []
    with tempfile.TemporaryDirectory() as inspect_dir:
        inspect_path = Path(inspect_dir)
        try:
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(path=inspect_path)
        except Exception as err:
            return False, [f"Gagal mengekstrak atau membaca arsip kompresi: {err}"]

        manifest_file = inspect_path / "manifest.json"
        if not manifest_file.exists():
            return False, ["Arsip tidak memiliki berkas 'manifest.json' yang valid."]

        try:
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            files_list = manifest_data.get("files", [])
        except Exception as err:
            return False, [f"Gagal mem-parsing manifest.json: {err}"]

        for item in files_list:
            rel = item["relative_path"]
            expected_sha = item["sha256"]
            expected_size = item["size_bytes"]
            target = inspect_path / rel

            if not target.exists():
                errors.append(f"Berkas yang tercantum di manifest tidak ditemukan: {rel}")
                continue

            actual_size = target.stat().st_size
            if actual_size != expected_size:
                errors.append(
                    f"Ukuran berkas tidak cocok untuk {rel}: diharapkan {expected_size}, aktual {actual_size}"
                )

            actual_sha = compute_sha256(target)
            if actual_sha != expected_sha:
                errors.append(
                    f"SHA-256 hash mismatch untuk {rel}: diharapkan {expected_sha}, aktual {actual_sha}"
                )

    return len(errors) == 0, errors


def run_restore_drill(
    archive_path: str | Path,
    restore_target_dir: str | Path | None = None,
) -> tuple[bool, str, list[str]]:
    """Executes a non-destructive recovery drill into an isolated temporary directory.

    Guarantees zero mutation of live production data.
    """
    is_valid, errors = verify_backup_archive(archive_path)
    if not is_valid:
        return False, "", [f"Drill dibatalkan, arsip tidak lolos verifikasi integritas: {errors}"]

    # Use isolated temporary directory if none specified
    temp_target = None
    if restore_target_dir is None:
        temp_target = tempfile.mkdtemp(prefix="drill_restore_")
        target_path = Path(temp_target)
    else:
        target_path = Path(restore_target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=target_path)

        # Verify restored database readability if present
        restored_db = target_path / "workspace" / "tesis_check.db"
        if restored_db.exists():
            con = sqlite3.connect(str(restored_db))
            cursor = con.cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()[0]
            con.close()
            if res.lower() != "ok":
                return False, str(target_path), [f"Database yang dipulihkan gagal uji integritas: {res}"]

        return True, str(target_path), []
    except Exception as err:
        return False, str(target_path), [f"Drill pemulihan gagal: {err}"]
    finally:
        # Clean up temporary drill directory if created automatically
        if temp_target and Path(temp_target).exists():
            import shutil
            shutil.rmtree(temp_target, ignore_errors=True)
