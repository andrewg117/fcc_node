from dataclasses import dataclass
import httpx2

from backend.core.exceptions import HttpError


@dataclass(frozen=True)
class StoredObject:
    content_type: str
    size: int


class MediaStorage:
    """Talks to Supabase Storage's REST API with the project's secret key."""

    def __init__(
        self,
        supabase_url: str,
        secret_key: str,
        bucket: str,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = f"{supabase_url}/storage/v1"
        self._bucket = bucket
        # Supabase's own client libraries send the key in both headers.
        self._headers = {"apikey": secret_key, "Authorization": f"Bearer {secret_key}"}
        # Tests pass an httpx2.MockTransport here instead of making real requests.
        self._transport = transport

    def public_url(self, path: str) -> str:
        return f"{self._base_url}/object/public/{self._bucket}/{path}"

    async def _request(self, method: str, url: str, **kwargs) -> httpx2.Response:
        try:
            async with httpx2.AsyncClient(
                base_url=self._base_url,
                headers=self._headers,
                timeout=10,
                transport=self._transport,
            ) as client:
                return await client.request(method, url, **kwargs)
        except httpx2.HTTPError:
            raise HttpError("File storage is unavailable", 502) from None

    async def create_upload_url(self, path: str) -> str:
        """Return a URL the browser can PUT one file to, without any key."""
        res = await self._request(
            "POST", f"/object/upload/sign/{self._bucket}/{path}", json={}
        )
        if res.status_code != 200:
            raise HttpError("File storage is unavailable", 502)
        # Supabase returns a path relative to /storage/v1, with the token in the query string.
        return self._base_url + res.json()["url"]

    async def get_file_info(self, path: str) -> StoredObject | None:
        """Return the uploaded file's real type and size, or None if it isn't there."""
        res = await self._request("HEAD", self.public_url(path))
        if res.status_code in (400, 404):
            return None
        if res.status_code != 200:
            raise HttpError("File storage is unavailable", 502)
        content_type = res.headers.get("content-type", "").split(";")[0].strip().lower()
        return StoredObject(
            content_type=content_type, size=int(res.headers.get("content-length", "0"))
        )

    async def delete(self, paths: list[str]) -> None:
        if not paths:
            return
        res = await self._request(
            "DELETE", f"/object/{self._bucket}", json={"prefixes": paths}
        )
        if res.status_code != 200:
            raise HttpError("File storage is unavailable", 502)
