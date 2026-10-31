from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.investigate import router as investigate_router
from app.api.investigate_image import router as investigate_image_router
from app.api.investigate_qr import router as investigate_qr_router

app = FastAPI(
    title="ScamShield API",
    version="0.1.0"
)

# CORS origins come from the CORS_ORIGINS environment variable (comma separated).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigate_router)
app.include_router(investigate_image_router)
app.include_router(investigate_qr_router)


@app.get("/")
def home():
    return {
        "project": "ScamShield",
        "status": "Backend Running 🚀"
    }