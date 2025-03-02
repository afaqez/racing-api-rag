from fastapi import FastAPI
from sqlalchemy import text
from app.api.endpoints import racing, chat, session, formatting, ingestion
from app.core import scheduler
from app.core.database import engine
from app.models import (
    racing as racing_models,
    course as course_models,
    horse as horse_models,
    jockey as jockey_models,
    trainer as trainer_models,
    owner as owner_models,
    session as session_models,
    embedding as embedding_models,
)
from app.core.logging import logger
import uvicorn

# Ensure pgvector extension is enabled
with engine.connect() as connection:
    logger.info("Ensuring pgvector extension is enabled...")
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    connection.commit()

# Create database tables (for production, use migrations)
racing_models.Base.metadata.create_all(bind=engine)
course_models.Base.metadata.create_all(bind=engine)
horse_models.Base.metadata.create_all(bind=engine)
jockey_models.Base.metadata.create_all(bind=engine)
trainer_models.Base.metadata.create_all(bind=engine)
owner_models.Base.metadata.create_all(bind=engine)
session_models.Base.metadata.create_all(bind=engine)
embedding_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Racing Data & Chat API")

app.include_router(racing.router, prefix="/api/racing", tags=["Racing"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(session.router, prefix="/api/session", tags=["Session"])
app.include_router(formatting.router, prefix="/api/formatting", tags=["Formatting"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["Ingestion"])


@app.on_event("startup")
def startup_event():
    from app.core.scheduler import start_scheduler

    start_scheduler()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
