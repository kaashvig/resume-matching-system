import psycopg2
import json
import hashlib
from sentence_transformers import SentenceTransformer

DB_CONFIG = {
    "dbname": "dbresume",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": 5432
}

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_updated_table():
    conn = get_db_connection()

    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id SERIAL PRIMARY KEY,
                name TEXT,
                location TEXT,
                state TEXT,
                current_job_title TEXT,
                preferred_job_title TEXT,
                skills TEXT[],
                experience JSONB,
                education JSONB,
                resume_hash TEXT UNIQUE,
                skills_embedding vector(384),
                experience_embedding vector(384),
                education_embedding vector(384),
                job_titles_embedding vector(384),
                state_embedding vector(384)
            );
        """)
        print("✓ Ensured resumes table exists.")

        for column in ['inline_resume', 'embedding']:
            cur.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'resumes' AND column_name = '{column}'
            """)
            if cur.fetchone():
                cur.execute(f"ALTER TABLE resumes DROP COLUMN {column}")
                print(f"✓ Removed old column: {column}")

    conn.commit()
    conn.close()

# Mapping cities to states
CITY_TO_STATE = {
    "mumbai": "Maharashtra",
    "delhi": "Delhi",
    "bangalore": "Karnataka",
    "chennai": "Tamil Nadu",
    "hyderabad": "Telangana",
    "kolkata": "West Bengal",
    "pune": "Maharashtra",
    "ahmedabad": "Gujarat",
    "jaipur": "Rajasthan",
    "lucknow": "Uttar Pradesh",
    "bhopal": "Madhya Pradesh",
    "indore": "Madhya Pradesh",
    "patna": "Bihar",
    "surat": "Gujarat",
    "nagpur": "Maharashtra",
    "coimbatore": "Tamil Nadu",
    "kochi": "Kerala",
    "visakhapatnam": "Andhra Pradesh",
    "chandigarh": "Chandigarh",
    "noida": "Uttar Pradesh",
    "gurgaon": "Haryana"
}

def infer_state_from_location(location):
    if not location:
        return None
    location = location.lower()
    for city, state in CITY_TO_STATE.items():
        if city in location:
            return state
    return None

def insert_resume_into_db(conn, structured_info):
    resume_content = json.dumps(structured_info, sort_keys=True)
    resume_hash = hashlib.md5(resume_content.encode()).hexdigest()

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM resumes WHERE resume_hash = %s", (resume_hash,))
        if cur.fetchone():
            print(f"Resume with hash {resume_hash[:8]}... already exists. Skipping.")
            return False

    #  Infer missing state from location
    if not structured_info.get("state"):
        inferred_state = infer_state_from_location(structured_info.get("location"))
        if inferred_state:
            structured_info["state"] = inferred_state
            print(f"Inferred state: {inferred_state}")
        else:
            print(f"Could not infer state from location: {structured_info.get('location')}")

    embeddings = {}

    skills_text = ", ".join(structured_info.get("skills", []))
    embeddings["skills"] = model.encode(skills_text).tolist()

    experience_items = structured_info.get("experience", [])
    experience_text = " ".join(
        f"{e.get('title', '')} at {e.get('company', '')} - {e.get('description', '')}" for e in experience_items
    )
    embeddings["experience"] = model.encode(experience_text).tolist()

    education_items = structured_info.get("education", [])
    education_text = " ".join(
        f"{e.get('degree', '')} in {e.get('field', '')} from {e.get('institution', '')}" for e in education_items
    )
    embeddings["education"] = model.encode(education_text).tolist()

    job_titles_text = f"{structured_info.get('current_job_title', '')} {structured_info.get('preferred_job_title', '')}"
    embeddings["job_titles"] = model.encode(job_titles_text.strip()).tolist()

    state_text = structured_info.get("state", "")
    embeddings["state"] = model.encode(state_text).tolist()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO resumes (
                name, location, state, current_job_title, preferred_job_title,
                skills, experience, education, resume_hash,
                skills_embedding, experience_embedding, education_embedding,
                job_titles_embedding, state_embedding
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            structured_info.get("name"),
            structured_info.get("location"),
            structured_info.get("state"),
            structured_info.get("current_job_title"),
            structured_info.get("preferred_job_title"),
            structured_info.get("skills") or [],
            json.dumps(structured_info.get("experience") or []),
            json.dumps(structured_info.get("education") or []),
            resume_hash,
            embeddings["skills"],
            embeddings["experience"],
            embeddings["education"],
            embeddings["job_titles"],
            embeddings["state"]
        ))

    conn.commit()
    print("Inserted resume into database.")
    return True
def fetch_resumes_from_db():
    conn = get_db_connection()
    resumes = []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                name, location, state,
                current_job_title, preferred_job_title,
                skills, experience, education,
                skills_embedding, experience_embedding, education_embedding,
                job_titles_embedding, state_embedding
            FROM resumes
        """)
        rows = cur.fetchall()

        for row in rows:
            resumes.append({
                "name": row[0],
                "location": row[1],
                "state": row[2],
                "current_title": row[3],
                "preferred_title": row[4],
                "skills": row[5],
               "experience": row[6] or [],
               "education": row[7] or [],
                "embeddings": {
                    "skills": row[8],
                    "experience": row[9],
                    "education": row[10],
                    "job_titles": row[11],
                    "state": row[12],
                }
            })
    conn.close()
    return resumes
