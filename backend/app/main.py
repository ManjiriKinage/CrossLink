from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db
from app.api.routes import router as api_router
from app.api.case_routes import router as case_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    init_db()
    yield
    # Shutdown logic if any

app = FastAPI(
    title="Cold Case — Information Retrieval & Knowledge Graph Engine",
    description="Privacy-first Information Retrieval system combining dense semantic retrieval, entity relationship discovery, and verifiable evidence tracing.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(case_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "system": "Cold Case IR Engine",
        "status": "online",
        "version": "2.0.0",
        "docs_url": "/docs",
        "upgrade": "Now with full case management and document isolation!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
