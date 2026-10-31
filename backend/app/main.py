from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.investigate import router as investigate_router
from app.api.investigate_image import router as investigate_image_router
from app.api.investigate_qr import router as investigate_qr_router
from app.config import settings
from app.engine.signals import WEIGHTS_VERSION
from app.intel import reputation

@asynccontextmanager
async def lifespan(_app):
    # Load the phishing feed once so the first request is not slower.
    try:
        reputation.load_openphish()
    except Exception:  # noqa: BLE001
        pass
    yield


app = FastAPI(title="ScamShield API", version="2.0.0", lifespan=lifespan)

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
    return {"project": "ScamShield", "status": "Backend Running", "version": app.version}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": app.version,
        "weights_version": WEIGHTS_VERSION,
        "providers": settings.configured_providers(),
        "phishing_feed_size": len(reputation._phish_set),
    }
