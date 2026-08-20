from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from ..core.config import get_settings


settings = get_settings()

worker_engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
)

WorkerSessionLocal = sessionmaker(
    bind=worker_engine,
    class_=Session,
    expire_on_commit=False,
)