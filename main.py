from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from homepal.config import AppPaths, ensure_directories
from homepal.db import Base, configure_session, create_sqlite_engine
from homepal.views.main_window import MainWindow


def configure_logging(paths: AppPaths) -> None:
    logging.basicConfig(
        filename=paths.log_dir / "homepal.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def bootstrap_db(paths: AppPaths) -> None:
    engine = create_sqlite_engine(str(paths.db_path))
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
