from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from PySide6.QtWidgets import QApplication, QMessageBox

from homepal.config import AppPaths, ensure_directories
from homepal.db import Base, SessionLocal, configure_session, create_sqlite_engine, run_integrity_check
from homepal.models import AssetCategory, AttributeDefinition
from homepal.services.task_service import TaskService
from homepal.views.main_window import MainWindow


def configure_logging(paths: AppPaths) -> None:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not any(isinstance(handler, RotatingFileHandler) for handler in root_logger.handlers):
        handler = RotatingFileHandler(
            paths.log_dir / "homepal.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


def bootstrap_db(paths: AppPaths) -> None:
    engine = create_sqlite_engine(str(paths.db_path))
    integrity_result = run_integrity_check(engine)
    if integrity_result != "ok":
        logging.error("Database integrity check failed: %s", integrity_result)
    configure_session(engine)
    Base.metadata.create_all(engine)


def verify_seed_data(session) -> bool:
    category_count = session.query(AssetCategory).count()
    attr_count = session.query(AttributeDefinition).count()
    if category_count == 0 or attr_count == 0:
        QMessageBox.critical(
            None,
            "Database setup error",
            "Required seed data is missing (asset_categories / attribute_definitions).\nRun migrations before launching Homepal.",
        )
        return False
    return True


def main() -> int:
    paths = ensure_directories()
    configure_logging(paths)
    bootstrap_db(paths)

    app = QApplication(sys.argv)
    session = SessionLocal()
    if not verify_seed_data(session):
        session.close()
        return 1

    task_service = TaskService(session)
    window = MainWindow(task_service)
    window.show()
    exit_code = app.exec()
    session.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
