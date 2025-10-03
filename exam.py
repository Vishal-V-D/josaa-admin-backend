import os
import logging
import uuid
from fastapi import APIRouter, HTTPException, Request,Body
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SUPABASE_URL: str = os.environ.get("SUPABASE_URL") or "https://drdxhvqstjlxguyqpetq.supabase.co"
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRyZHhodnFzdGpseGd1eXFwZXRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQyOTI0NTksImV4cCI6MjA2OTg2ODQ1OX0.xd8YlNV8qV58-n1BG5jvcMGmtkH5dWUh92xzKR4JAnI"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be set in the .env file")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Router Setup ----------
router = APIRouter()

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("exam-api")

# ---------- Endpoints ----------
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

@router.get("/college-exams/{item_uuid}")
async def get_college_exam(item_uuid: str):
    try:
        basic_res = supabase.table("college_specific_exams").select("id, data").eq("id", item_uuid).execute()
        full_res = supabase.table("collegespecificexams").select("details").eq("uuid", item_uuid).execute()

        if basic_res.data:
            basic_data = basic_res.data[0]
            full_details = full_res.data[0]['details'] if full_res.data else {}
            return {"id": basic_data["id"], "uuid": item_uuid, "data": {**basic_data["data"], **full_details}}

        basic_res = supabase.table("exams_name").select("id, data").eq("id", item_uuid).execute()
        full_res = supabase.table("exams").select("details").eq("uuid", item_uuid).execute()

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

@router.post("/college-exams/create")
async def create_college_exam(request: Request):
    try:
        payload = await request.json()
        basic_data = payload.get("basic_data")
        full_details = payload.get("full_details")
        
        new_uuid = str(uuid.uuid4())
        
        supabase.table("college_specific_exams").insert({"data": basic_data, "uuid": new_uuid}).execute()
        supabase.table("collegespecificexams").insert({"name": basic_data.get("InstituteName"), "details": full_details, "uuid": new_uuid}).execute()
        
        return {"message": "College exam created successfully", "uuid": new_uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating college exam: {e}")

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
            supabase.table("collegespecificexams").delete().eq("uui", item_uuid).execute()
            return {"message": "College exam deleted successfully", "uuid": item_uuid}

        raise HTTPException(status_code=404, detail="UUID not found in any table for deletion")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/college-exams/{item_uuid}")
async def delete_college_exam(item_uuid: str):
    try:
        basic_res = supabase.table("college_specific_exams").select("id").eq("id", item_uuid).execute()
        if basic_res.data:
            supabase.table("college_specific_exams").delete().eq("id", item_uuid).execute()
            supabase.table("collegespecificexams").delete().eq("uui", item_uuid).execute()
            return {"message": "College exam deleted successfully", "uuid": item_uuid}

        basic_res = supabase.table("exams_name").select("id").eq("id", item_uuid).execute()
        if basic_res.data:
            supabase.table("exams_name").delete().eq("id", item_uuid).execute()
            supabase.table("exams").delete().eq("uuid", item_uuid).execute()
            return {"message": "Exam deleted successfully", "uuid": item_uuid}

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

@router.get("/college-exams")
async def get_college_exams():
    try:
        response = supabase.table("college_specific_exams").select("*").execute()
        return {"count": len(response.data), "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 



@app.post("/update-exam-order")
async def update_college_exams_order(payload: dict = Body(...)):
    """
    Update only the 'sort_order' column in the 'exams_name' table.
    Now accepts both 'general' and 'college' arrays for flexibility.
    """
    general = payload.get("general", [])
    college = payload.get("college", [])
    
    # Combine both arrays (you're only using general now)
    items_to_update = general + college
    
    if not items_to_update:
        raise HTTPException(status_code=400, detail="Missing exam data to update.")

    try:
        updated_count = 0
        for item in items_to_update:
            # Fetch the row first to check if it exists
            existing = supabase.table("exams_name").select("id, sort_order") \
                .eq("id", item["id"]).execute()

            if existing.data:
                logger.info(f"Updating sort_order for id={item['id']} from {existing.data[0]['sort_order']} to {item['sort_order']}")
                
                # Update the sort_order
                supabase.table("exams_name").update(
                    {"sort_order": int(item["sort_order"])}
                ).eq("id", item["id"]).execute()
                
                updated_count += 1
            else:
                logger.warning(f"Skipping id={item['id']} — not found in DB")

        return {
            "message": f"Sort order updated successfully for {updated_count} exam(s).",
            "updated_count": updated_count
        }

    except Exception as e:
        logger.error(f"⚠ Failed to update sort order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
