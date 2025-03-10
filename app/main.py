from fastapi import FastAPI
from sqlalchemy import text
from app.api.endpoints import racing, chat, session, formatting, ingestion
from app.core import scheduler
from app.core.database import engine
from app.core.logging import logger
import uvicorn
from app.create_tables import create_tables
from fastapi.middleware.cors import CORSMiddleware

# Create all tables using our custom function
create_tables()

app = FastAPI(title="Racing Data & Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", 'https://racing-insights.vercel.app'],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)



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
