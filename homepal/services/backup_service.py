from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path


class BackupService:
    def should_prompt(self, last_backup: datetime | None) -> bool:
        if last_backup is None:
            return True
        return datetime.now() - last_backup > timedelta(days=7)

    def create_backup(self, db_path: Path, target_path: Path) -> str:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_path, target_path)
        digest = hashlib.sha256(target_path.read_bytes()).hexdigest()
        return digest
