from fastapi import HTTPException
from app.core.config import settings
from app.integretions.s3.client import s3_client
from botocore.exceptions import ClientError
from typing import BinaryIO


def generate_s3_key(user_id: str,conversation_id: str,document_id: str,filename: str)-> str:
    return f"documents/{user_id}/{conversation_id}/{document_id}/{filename}"


async def upload_to_s3(file_obj: BinaryIO, key: str) -> None:
    try:
        s3_client.upload_fileobj(file_obj, settings.AWS_S3_BUCKET_NAME, key)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {e}")