import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from addclg import router as college_router
from adex import router as adex_router
from exam import router as exam_router
from tab_router import router as tab_router  # <-- Import Gemini router
import os
import logging

# ---------- FastAPI App Instance ----------
app = FastAPI(
    title="Combined College & Exam API",
    description="Unified API for College and Exam data + Gemini table parser",
    version="1.0"
)

# ---------- CORS Middleware ----------
origins = [
    "https://admin-page-josaa.netlify.app",
    "https://josaa-admin-page.netlify.app",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Logger ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("combined-api")
logger.info("🚀 Combined Backend starting...")

# ---------- Include Routers ----------
app.include_router(college_router)
app.include_router(adex_router)
app.include_router(exam_router)
app.include_router(tab_router)  # <-- Attach Gemini table parsing

# -------------------------
# Main Execution
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting backend on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
