from enum import Enum


class DocumentStatus(Enum):
    PROCESSING = 1
    PROCESSED = 2


class DocumentType(Enum):
    MD = 1
