"""Real MinIO ``Store`` implementation.

Same surface as ``FilesystemStore`` in ``store.py``. The MinIO bucket
must exist before construction (``MinIOStore.ensure_bucket`` is a static
helper that creates it if missing — call once at startup).

Configuration via the existing env vars (see ARCHITECTURE.md):
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET

The minio SDK is sync; we offload calls to a thread executor so the
async harness call sites don't block the loop.
"""

from __future__ import annotations

import asyncio
import io
from typing import Iterable


try:  # pragma: no cover - environment-dependent
    from minio import Minio  # type: ignore
    from minio.error import S3Error  # type: ignore

    REAL_AVAILABLE = True
except Exception:  # noqa: BLE001
    Minio = None  # type: ignore[assignment]
    S3Error = Exception  # type: ignore[assignment]
    REAL_AVAILABLE = False


class MinIOStore:
    """MinIO/S3 implementation of the Store protocol."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        *,
        secure: bool = False,
    ) -> None:
        if not REAL_AVAILABLE:
            raise RuntimeError(
                "minio package not installed; install 'minio>=7.2' or "
                "use FilesystemStore"
            )
        self._client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket = bucket
        self._ensure_bucket(bucket)

    def _ensure_bucket(self, bucket: str) -> None:
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
        except S3Error:
            # Bucket race / permissions handled by caller's logs; don't fail
            # construction if the bucket already exists under a different
            # access path.
            pass

    def put(self, key: str, content: bytes | str) -> None:
        if isinstance(content, str):
            content = content.encode("utf-8")
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(content),
            length=len(content),
        )

    def get(self, key: str) -> bytes:
        resp = self._client.get_object(self._bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    def exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except S3Error:
            return False

    def list(self, prefix: str) -> Iterable[str]:
        for obj in self._client.list_objects(
            self._bucket, prefix=prefix, recursive=True
        ):
            yield obj.object_name

    def delete(self, key: str) -> None:
        try:
            self._client.remove_object(self._bucket, key)
        except S3Error:
            pass


class AsyncMinIOStore:
    """Async wrapper around MinIOStore — offloads sync calls to a thread.

    Drop-in for ``Store`` consumers that prefer async ``put``/``get``.
    The synchronous ``MinIOStore`` is already protocol-compatible; this
    is for hot paths that benefit from non-blocking I/O.
    """

    def __init__(self, inner: MinIOStore) -> None:
        self._inner = inner

    async def put(self, key: str, content: bytes | str) -> None:
        await asyncio.to_thread(self._inner.put, key, content)

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._inner.get, key)

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._inner.exists, key)

    async def list(self, prefix: str) -> list[str]:
        return await asyncio.to_thread(lambda: list(self._inner.list(prefix)))

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._inner.delete, key)
