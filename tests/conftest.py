import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.db import apply_migrations, connect  # noqa: E402


@pytest.fixture
def migrated_db(tmp_path):
    """Path to a fresh SQLite database with every migration applied."""
    db_path = str(tmp_path / "t.db")
    conn = connect(db_path)
    apply_migrations(conn)
    conn.close()
    return db_path
