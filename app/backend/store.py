"""Object-store interface — truth lives here.

v0.1 ships a filesystem-backed ``FilesystemStore``. Same surface will be
implemented by ``MinIOStore`` (TODO) — see design §9.

Layout (under ``root``):

    traces/{YYYY-MM-DD}/{session_id}.jsonl
    workflows/{workflow_id}.yaml
    generated/{workflow_id}_v{n}.py
    needs_review/{kind}/{id}.json

Only ``Store`` is the public contract. Path layout helpers stay in
``trace.py`` / ``registry.py`` so the store stays dumb.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Protocol


class Store(Protocol):
    """Minimal blob store. Matches MinIO's surface for v1."""

    def put(self, key: str, content: bytes | str) -> None: ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...

    def list(self, prefix: str) -> Iterable[str]: ...

    def delete(self, key: str) -> None: ...


class FilesystemStore:
    """Local-disk store rooted at ``root``. Creates parent dirs on put."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Key must be a relative posix path. We don't escape — caller owns it.
        if key.startswith("/"):
            raise ValueError(f"store key must be relative, got {key!r}")
        return self.root / key

    def put(self, key: str, content: bytes | str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            path.write_bytes(content)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def list(self, prefix: str) -> Iterable[str]:
        base = self._path(prefix)
        if not base.exists():
            return iter(())
        if base.is_file():
            return iter([prefix])
        return (
            str(p.relative_to(self.root))
            for p in base.rglob("*")
            if p.is_file()
        )

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()


# TODO(minio): MinIOStore implementation. Same surface; ``put`` becomes
# ``put_object``, ``get`` becomes ``get_object`` (read .data), ``list``
# becomes ``list_objects`` (prefix=). Configuration via existing
# MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY / MINIO_BUCKET.
