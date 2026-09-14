from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.investigate import router as investigate_router
from app.api.investigate_image import router as investigate_image_router
from app.api.investigate_qr import router as investigate_qr_router

app = FastAPI(
    title="ScamShield API",
    version="0.1.0"
)

# Local-dev CORS: allow the Vite frontend (default port 5173) to call this API
# from the browser. Tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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