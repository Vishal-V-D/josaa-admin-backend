# tab_router.py
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

# -------------------- Router --------------------
router = APIRouter(prefix="/api", tags=["Gemini Table Parser"])

# -------------------- Gemini AI Setup --------------------
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or "AIzaSyDTCgOkF3YwiLbdjy9x_eTmWNe3aVujAO4"
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found. Please set the environment variable.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# -------------------- Table Parsing --------------------
class TableParseRequest(BaseModel):
    text: str

def parse_text_to_table_with_gemini(text: str):
    prompt = f"""
        You are a table parser. The following raw text contains a table 
        (possibly irregular, merged rows/columns, or multiline cells).

        Convert it into strict JSON:

        ```json
        {{
        "type": "table",
        "content": [
            ["cell_row1_col1", "cell_row1_col2", ...],
            ["cell_row2_col1", "cell_row2_col2", ...],
            ...
        ]
        }}
        ```

        Rules:
        - Do NOT include a separate "headers" field.
        - Preserve line breaks inside cells.
        - Repeat values for rowspans/colspans.
        - Output only valid JSON, no markdown.

        Raw text:
        '''
        {text}
        '''
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-len("```")].strip()
        return json.loads(response_text)
    except Exception as e:
        raise ValueError(f"Gemini parsing failed: {e}")

@router.post("/parse-table")
async def parse_table_endpoint(request: TableParseRequest):
    try:
        parsed_data = parse_text_to_table_with_gemini(request.text)
        return parsed_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during parsing.")
