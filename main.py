from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from PySide6.QtWidgets import QApplication

from homepal.config import AppPaths, ensure_directories
from homepal.db import Base, configure_session, create_sqlite_engine, run_integrity_check
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


def main() -> int:
    paths = ensure_directories()
    configure_logging(paths)
    bootstrap_db(paths)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
