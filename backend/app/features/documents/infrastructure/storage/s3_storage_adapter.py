from typing import Any
import aioboto3
from botocore.exceptions import ClientError

from app.features.documents.application.exceptions import ObjectNotFoundError
from app.features.documents.application.interfaces.object_storage import (
    ObjectStorage,
)


class S3StorageAdapter(ObjectStorage):

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        session: aioboto3.Session | None = None,
    ) -> None:
        self._bucket_name = bucket_name
        self._session = session or aioboto3.Session()
        self._client_kwargs = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "region_name": region_name,
        }

    async def generate_presigned_upload_url(
        self, key: str, content_type: str, expires_in: int = 900
    ) -> str:
        async with self._session.client("s3", **self._client_kwargs) as client:
            url = await client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self._bucket_name,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            return str(url)

    async def get_object_metadata(self, key: str) -> dict[str, Any]:
        async with self._session.client("s3", **self._client_kwargs) as client:
            try:
                resp = await client.head_object(
                    Bucket=self._bucket_name, Key=key
                )
                return {
                    "size": int(resp.get("ContentLength", 0)),
                    "content_type": str(resp.get("ContentType", "")),
                    "etag": str(resp.get("ETag", "")),
                }
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code in ("404", "NoSuchKey", "NotFound"):
                    raise ObjectNotFoundError(
                        f"Object '{key}' not found in storage bucket '{self._bucket_name}'"
                    ) from e
                raise

    async def download_file(self, key: str, destination_path: str) -> str:
        async with self._session.client("s3", **self._client_kwargs) as client:
            try:
                resp = await client.get_object(
                    Bucket=self._bucket_name, Key=key
                )
                async with resp["Body"] as stream:
                    content = await stream.read()
                    with open(destination_path, "wb") as f:
                        f.write(content)
                return destination_path
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code in ("404", "NoSuchKey", "NotFound"):
                    raise ObjectNotFoundError(
                        f"Object '{key}' not found for download"
                    ) from e
                raise

    async def delete_object(self, key: str) -> None:
        async with self._session.client("s3", **self._client_kwargs) as client:
            try:
                await client.delete_object(Bucket=self._bucket_name, Key=key)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code in ("404", "NoSuchKey", "NotFound"):
                    return
                raise

