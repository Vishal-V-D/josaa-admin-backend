import os
import logging
import uuid
import json
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai

# ---------- Load Environment Variables ----------
load_dotenv()
SUPABASE_URL: str = os.environ.get("SUPABASE_URL") or "https://drdxhvqstjlxguyqpetq.supabase.co"
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRyZHhodnFzdGpseGd1eXFwZXRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQyOTI0NTksImV4cCI6MjA2OTg2ODQ1OX0.xd8YlNV8qV58-n1BG5jvcMGmtkH5dWUh92xzKR4JAnI"

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or "AIzaSyDTCgOkF3YwiLbdjy9x_eTmWNe3aVujAO4"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be set in the .env file")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found. Please set the environment variable.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Configure Gemini ----------
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# ---------- FastAPI App ----------
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Logger ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("exam-api")

# ---------- Routers ----------
router = APIRouter()

# ---------------- Supabase Exam Endpoints ----------------
@router.get("/exams/{item_uuid}")
async def get_exam(item_uuid: str):
    try:
        basic_res = supabase.table("exams_name").select("id, data").eq("id", item_uuid).execute()
        full_res = supabase.table("exams").select("details").eq("uuid", item_uuid).execute()

        if basic_res.data:
            basic_data = basic_res.data[0]
            full_details = full_res.data[0]['details'] if full_res.data else {}
            return {"id": basic_data["id"], "uuid": item_uuid, "data": {**basic_data["data"], **full_details}}

        basic_res = supabase.table("college_specific_exams").select("id, data").eq("id", item_uuid).execute()
        full_res = supabase.table("collegespecificexams").select("details").eq("uuid", item_uuid).execute()

        if basic_res.data:
            basic_data = basic_res.data[0]
            full_details = full_res.data[0]['details'] if full_res.data else {}
            return {"id": basic_data["id"], "uuid": item_uuid, "data": {**basic_data["data"], **full_details}}

        raise HTTPException(status_code=404, detail="UUID not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exams/create")
async def create_exam(request: Request):
    try:
        payload = await request.json()
        basic_data = payload.get("basic_data")
        full_details = payload.get("full_details")
        new_uuid = str(uuid.uuid4())

        supabase.table("exams_name").insert({"data": basic_data, "uuid": new_uuid}).execute()
        supabase.table("exams").insert({"name": basic_data.get("Name"), "details": full_details, "uuid": new_uuid}).execute()
        
        return {"message": "Exam created successfully", "uuid": new_uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating exam: {e}")

@router.delete("/exams/{item_uuid}")
async def delete_exam(item_uuid: str):
    try:
        basic_res = supabase.table("exams_name").select("id").eq("id", item_uuid).execute()
        if basic_res.data:
            supabase.table("exams_name").delete().eq("id", item_uuid).execute()
            supabase.table("exams").delete().eq("uuid", item_uuid).execute()
            return {"message": "Exam deleted successfully", "uuid": item_uuid}

        basic_res = supabase.table("college_specific_exams").select("id").eq("id", item_uuid).execute()
        if basic_res.data:
            supabase.table("college_specific_exams").delete().eq("id", item_uuid).execute()
            supabase.table("collegespecificexams").delete().eq("uuid", item_uuid).execute()
            return {"message": "College exam deleted successfully", "uuid": item_uuid}

        raise HTTPException(status_code=404, detail="UUID not found in any table for deletion")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exams")
async def get_exams():
    try:
        response = supabase.table("exams_name").select("*").execute()
        return {"count": len(response.data), "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- Gemini Table Parsing ----------------
class TableParseRequest(BaseModel):
    text: str

def parse_text_to_table_with_gemini(text: str):
    prompt = f"""
    You are a table parser. Convert this text into strict JSON format:
    {{ "type": "table", "content": [ ... ] }}
    Raw text:
    '''{text}'''
    """
    try:
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-len("```")].strip()

        return json.loads(response_text)
    except Exception as e:
        raise ValueError(f"Failed to parse table using Gemini: {e}")

@app.post("/api/parse-table")
async def parse_table_endpoint(request: TableParseRequest):
    try:
        parsed_data = parse_text_to_table_with_gemini(request.text)
        return parsed_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during parsing.")

# ---------- Include Router ----------
app.include_router(router)

# ---------- Run ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
