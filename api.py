from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import traceback
import sys
import os

# Set working directory to current file's location
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Ensure matching2.py is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Local imports
from matching2 import find_matching_resumes_by_similarity
from db import get_db_connection, insert_resume_into_db
from resume_parser import parse_resume_structured
from extract_text import extract_text
app = FastAPI(title="Resume Matcher API")

# Allow frontend access (change origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- Request Models ----------- #
class JDRequest(BaseModel):
    jd_text: str
    top_n: int = 5


# ----------- Match Endpoint ----------- #
@app.post("/match")
def match_jobs(req: JDRequest):
    jd_text = req.jd_text
    top_n = req.top_n

    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text is required")

    try:
        results = find_matching_resumes_by_similarity(jd_text, top_n=top_n, debug=False)

        if not results:
            raise HTTPException(status_code=404, detail="No matching resumes found.")

        return {"matches": results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running matching logic: {e}\n{traceback.format_exc()}",
        )


# ----------- Resume Upload Endpoint ----------- #
@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = extract_text(content, file.filename)
        structured_info = parse_resume_structured(text)

        conn = get_db_connection()
        success = insert_resume_into_db(conn, structured_info)
        conn.close()

        return {"status": "ok" if success else "skipped"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {e}\n{traceback.format_exc()}",
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    uvicorn.run(app, host="0.0.0.0", port=8000)
