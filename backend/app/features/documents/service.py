import uuid
from fastapi import UploadFile, HTTPException
from app.integretions.s3.constants import ALLOWED_EXTENSIONS
from sqlalchemy import select
from app.core.config import settings
from app.integretions.s3.service import upload_to_s3, generate_s3_key
from app.features.documents.model import Document
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.conversations.models import Conversation

async def upload_document(db:AsyncSession ,file: UploadFile, user_id: uuid.UUID,conversation_id: uuid.UUID):
    # extension validation
    if file.filename is None:
        raise HTTPException(status_code=400, detail="File name is required") 
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if file.size is not None and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size too large")
    

    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.is_deleted == False,
        Conversation.user_id == user_id,
    )

    conversation = (await db.scalars(stmt)).one_or_none()

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")


    try:
        # Create document row in postgresql using sqlalchemy

        document_row = Document(
            filename=file.filename,
            mime_type=file.content_type,
            file_size=file.size or 0,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        db.add(document_row)
        await db.flush() #forces SQLAlchemy to execute pending SQL statements immediately
        # by default the processing status is pending 
        
        # generate the s3 key

        key = generate_s3_key(str(user_id),str(conversation_id),str(document_row.id),file.filename)

        # upload to s3

        await upload_to_s3(file.file, key)
        document_row.s3_key = key

        await db.commit()
        await db.refresh(document_row)

        return document_row

    except HTTPException:
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))