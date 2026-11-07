import enum


class ProcessingStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class UploadStatusEnum(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

