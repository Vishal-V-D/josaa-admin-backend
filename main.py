import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from addclg import router as college_router
from adex import router as adex_router
from exam import router as exam_router
import os
import logging

# ---------- FastAPI App Instance ----------
app = FastAPI(
    title="Combined College & Exam API",
    description="Unified API for College and Exam data",
    version="1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("combined-api")
logger.info("🚀 Combined Backend starting...")

# ---------- Include Routers ----------
# This is the "connector" logic. Each router's endpoints are included
# in the main app, and will be available on a single port.
app.include_router(college_router)
app.include_router(adex_router)
app.include_router(exam_router)

# -------------------------
# Main Execution
# -------------------------
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")