#this is the backend code
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import traceback

app = FastAPI(title="Resume Matcher API")

# Allow local access from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JDRequest(BaseModel):
    jd_text: str
    top_n: int = 5

@app.post("/match")
def match_jobs(req: JDRequest):
    jd_text = req.jd_text
    top_n = req.top_n

    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text is required")

    try:
        from matching2 import find_matching_resumes_by_similarity
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import matching function: {e}\n{traceback.format_exc()}"
        )

    try:
        results = find_matching_resumes_by_similarity(jd_text, top_n=top_n, debug=False)

        if not results:
            raise HTTPException(
                status_code=404,
                detail="No matching resumes found."
            )

        return {"matches": results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running matching logic: {e}\n{traceback.format_exc()}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
