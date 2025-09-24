import os
import json
import uuid
import re
import logging
from fastapi import APIRouter, HTTPException, Request
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------
# Load ENV
# -------------------------
load_dotenv()
SUPABASE_URL: str = os.environ.get("SUPABASE_URL") or "https://drdxhvqstjlxguyqpetq.supabase.co"
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRyZHhodnFzdGpseGd1eXFwZXRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQyOTI0NTksImV4cCI6MjA2OTg2ODQ1OX0.xd8YlNV8qV58-n1BG5jvcMGmtkH5dWUh92xzKR4JAnI"
GOOGLE_API_KEY = "AIzaSyDBZrol2DDNOExT3b0qS8yl-nZkO3DQldA"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be set")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

# -------------------------
# Router and Logger
# -------------------------
router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adex-api")

# -------------------------
# Constants and Helper Functions
# -------------------------
PARENT_KEYS = [
    "About", "Exam Dates", "Eligibility Criteria", "Exam Pattern & Syllabus",
    "Yearly Cutoff", "Application Fee", "Resources", "Applylink"
]
SCHEMA_EXAMPLE = {
    "About": {"Exam Highlights": [{"type": "paragraph", "content": "A paragraph about the exam."}]},
    "Applylink": "https://example.com"
}

def get_prompt(exam_name, raw_content):
    prompt = f"""
    You are an expert at extracting and structuring exam information.
    Convert the raw content about "{exam_name}" into **valid JSON**.
    The JSON must contain these parent keys:
    {", ".join(PARENT_KEYS)}.
    If data is missing, generate meaningful educational content.
    Each section should be rich with details, include tables/lists when appropriate.
    Match the schema below for formatting:
    {json.dumps(SCHEMA_EXAMPLE, indent=2)}
    Raw Content:
    ---
    {raw_content}
    ---
    Output only valid JSON. No markdown, no explanations.
    """
    return prompt

# -------------------------
# Endpoints
# -------------------------
@router.post("/generate-json")
async def generate_json(request: Request):
    try:
        body = await request.json()
        exam_name = body.get("exam_name")
        raw_content = body.get("raw_content")
        
        if not exam_name or not raw_content:
            raise HTTPException(status_code=400, detail="exam_name and raw_content are required")
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = get_prompt(exam_name, raw_content)
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        
        response_text = response.text.strip()
        try:
            json_output = json.loads(response_text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not match:
                raise ValueError("No valid JSON found")
            json_output = json.loads(match.group(0))
        
        return json_output
    except Exception as e:
        logger.error(f"❌ generate_json error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exams")
async def add_exam(request: Request):
    try:
        payload = await request.json()
        basic_data = payload.get("basic_data", {})
        full_details = payload.get("full_details", {})
        
        if not basic_data.get("Name"):
            raise HTTPException(status_code=400, detail="Name is required in basic_data")
            
        item_uuid = payload.get("uuid") or str(uuid.uuid4())
        
        supabase.table("exams_name").insert({"id": item_uuid, "data": basic_data}).execute()
        supabase.table("exams").insert({"uuid": item_uuid, "name": basic_data["Name"], "details": full_details}).execute()
        
        return {"message": "Exam added successfully", "uuid": item_uuid}
    except Exception as e:
        logger.error(f"❌ add_exam error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/college-exams")
async def add_college_exam(request: Request):
    try:
        payload = await request.json()
        basic_data = payload.get("basic_data", {})
        full_details = payload.get("full_details", {})
        
        if not basic_data.get("Name"):
            raise HTTPException(status_code=400, detail="Name is required in basic_data")
            
        item_uuid = payload.get("uuid") or str(uuid.uuid4())
        
        supabase.table("college_specific_exams").insert({"id": item_uuid, "data": basic_data}).execute()
        supabase.table("collegespecificexams").insert({"uuid": item_uuid, "details": full_details}).execute()
        
        return {"message": "College exam added successfully", "uuid": item_uuid}
    except Exception as e:
        logger.error(f"❌ add_college_exam error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# ✅ Updated PUT Endpoints
# -------------------------
@router.put("/exams/{item_uuid}")
async def update_exam(item_uuid: str, request: Request):
    try:
        payload = await request.json()
        basic_data = payload.get("basic_data", {})
        full_details = payload.get("full_details", {})

        print(f"➡️ Received update request for UUID: {item_uuid}")
        print(f"📦 Incoming payload: {payload}")

        # ✅ Check in exams_name
        basic_res = supabase.table("exams_name").select("id").eq("id", item_uuid).execute()
        if basic_res.data:
            print(f"✅ Found in exams_name, updating...")

            supabase.table("exams_name").update({"data": basic_data}).eq("id", item_uuid).execute()
            exam_name = basic_data.get("Name") or basic_data.get("name") or "Unknown"

            supabase.table("exams").upsert({
                "uuid": item_uuid,
                "name": exam_name,
                "details": full_details
            }, on_conflict="uuid").execute()

            return {"message": "Exam replaced successfully", "uuid": item_uuid}

        # ✅ Check in college_specific_exams
        basic_res = supabase.table("college_specific_exams").select("id").eq("id", item_uuid).execute()
        if basic_res.data:
            print(f"✅ Found in college_specific_exams, updating...")

            supabase.table("college_specific_exams").update({"data": basic_data}).eq("id", item_uuid).execute()
            exam_name = basic_data.get("Name") or basic_data.get("name") or "Unknown"

            supabase.table("collegespecificexams").upsert({
                "uuid": item_uuid,
                "name": exam_name,
                "details": full_details
            }, on_conflict="uuid").execute()

            return {"message": "College exam replaced successfully", "uuid": item_uuid}

        raise HTTPException(status_code=404, detail="UUID not found in any table")
    except Exception as e:
        print(f"🔥 Error while replacing exam: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/college-exams/{item_uuid}")
async def update_college_exam(item_uuid: str, request: Request):
    try:
        payload = await request.json()
        basic_data = payload.get("basic_data", {})
        full_details = payload.get("full_details", {})

        print(f"➡️ Received update request for College UUID: {item_uuid}")
        print(f"📦 Incoming payload: {payload}")

        # ✅ Check in college_specific_exams
        basic_res = supabase.table("college_specific_exams").select("id").eq("id", item_uuid).execute()
        if basic_res.data:
            print(f"✅ Found in college_specific_exams, updating...")

            supabase.table("college_specific_exams").update({"data": basic_data}).eq("id", item_uuid).execute()
            exam_name = basic_data.get("Name") or basic_data.get("name") or "Unknown"

            supabase.table("collegespecificexams").upsert({
                "uuid": item_uuid,
                "name": exam_name,
                "details": full_details
            }, on_conflict="uuid").execute()

            return {"message": "College exam replaced successfully", "uuid": item_uuid}

        # ✅ Check in exams_name
        basic_res = supabase.table("exams_name").select("id").eq("id", item_uuid).execute()
        if basic_res.data:
            print(f"✅ Found in exams_name, updating...")

            supabase.table("exams_name").update({"data": basic_data}).eq("id", item_uuid).execute()
            exam_name = basic_data.get("Name") or basic_data.get("name") or "Unknown"

            supabase.table("exams").upsert({
                "uuid": item_uuid,
                "name": exam_name,
                "details": full_details
            }, on_conflict="uuid").execute()

            return {"message": "Exam replaced successfully", "uuid": item_uuid}

        raise HTTPException(status_code=404, detail="UUID not found in any table")
    except Exception as e:
        print(f"🔥 Error while replacing college exam: {e}")
        raise HTTPException(status_code=500, detail=str(e))
