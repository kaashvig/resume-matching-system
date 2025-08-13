import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq_extractor import extract_structured_info_groq_jd
import ast
import re

# --- Database config ---
DB_CONFIG = {
    "dbname": "dbresume",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": 5432
}

model = SentenceTransformer("all-MiniLM-L6-v2")

SECTION_WEIGHTS = {
    "skills": 0.25,
    "experience": 0.25,
    "education": 0.15,
    "job_titles": 0.35
}

# --- City to State mapping ---
CITY_TO_STATE = {
    "mumbai": "maharashtra",
    "pune": "maharashtra",
    "nagpur": "maharashtra",
    "bangalore": "karnataka",
    "bengaluru": "karnataka",
    "hyderabad": "telangana",
    "chennai": "tamil nadu",
    "delhi": "delhi",
    "noida": "uttar pradesh",
    "gurgaon": "haryana",
    "kolkata": "west bengal",
    "ahmedabad": "gujarat",
    "jaipur": "rajasthan"
}

# --- Neighbor states dictionary ---
NEIGHBOR_STATES = {
    'maharashtra': ['gujarat', 'madhya pradesh', 'chhattisgarh', 'telangana', 'karnataka', 'goa'],
    'karnataka': ['maharashtra', 'andhra pradesh', 'telangana', 'tamil nadu', 'kerala', 'goa'],
    'telangana': ['maharashtra', 'chhattisgarh', 'andhra pradesh', 'karnataka'],
    'tamil nadu': ['kerala', 'karnataka', 'andhra pradesh'],
    'delhi': ['haryana', 'uttar pradesh'],
    'uttar pradesh': ['uttarakhand', 'delhi', 'haryana', 'rajasthan', 'madhya pradesh', 'bihar'],
    'haryana': ['punjab', 'delhi', 'uttar pradesh', 'rajasthan', 'himachal pradesh'],
    'west bengal': ['bihar', 'jharkhand', 'odisha', 'assam', 'sikkim'],
    'gujarat': ['maharashtra', 'madhya pradesh', 'rajasthan'],
    'rajasthan': ['gujarat', 'madhya pradesh', 'uttar pradesh', 'haryana', 'punjab']
}

def get_allowed_states(jd_location):
    city = jd_location.lower().split(",")[0].strip()
    state = CITY_TO_STATE.get(city, city)
    return [state] + NEIGHBOR_STATES.get(state, [])

def parse_embedding(emb):
    if emb is None:
        return np.array([])
    if isinstance(emb, str):
        try:
            return np.array(ast.literal_eval(emb))
        except:
            return np.array([])
    return np.array(emb)

def create_jd_section_embeddings(jd_text):
    jd_structured = extract_structured_info_groq_jd(jd_text)
    resume_like = {
        'current_job_title': jd_structured.get('job_title', ''),
        'preferred_job_title': '',
        'skills': jd_structured.get('required_skills', []),
        'experience': [{'title': jd_structured.get('required_experience', '')}],
        'education': [{'degree': jd_structured.get('required_education', '')}],
    }

    embeddings = {
        'skills': model.encode(", ".join(resume_like['skills'])),
        'experience': model.encode(" ".join(exp['title'] for exp in resume_like['experience'])),
        'education': model.encode(" ".join(edu['degree'] for edu in resume_like['education'])),
        'job_titles': model.encode(resume_like['current_job_title'])
    }

    return embeddings, jd_structured

def calculate_weighted_similarity(jd_embeddings, resume_embeddings):
    total_similarity = 0
    total_weight = 0
    for section, weight in SECTION_WEIGHTS.items():
        if section in jd_embeddings and section in resume_embeddings:
            jd_vec = jd_embeddings[section].reshape(1, -1)
            res_vec = resume_embeddings[section].reshape(1, -1)
            similarity = cosine_similarity(jd_vec, res_vec)[0][0]
            total_similarity += similarity * weight
            total_weight += weight
    return total_similarity / total_weight if total_weight > 0 else 0

def find_matching_resumes_by_similarity(jd_text, top_n=None, debug=True):
    jd_embeddings, jd_structured = create_jd_section_embeddings(jd_text)

    raw_location = jd_structured.get("location", "").lower().strip()
    jd_location = re.sub(r"\(.*?\)", "", raw_location).strip()
    if debug:
        print(f"Cleaned JD location: '{jd_location}'")

    job_title_vector = jd_embeddings['job_titles']

    if not jd_location:
        if debug:
            print("Location not found in JD.")
        return []

    allowed_states = get_allowed_states(jd_location)
    if debug:
        print(f"Allowed states for filtering: {allowed_states}")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, current_job_title, preferred_job_title, skills,
               experience, education, location, state,
               skills_embedding, experience_embedding, education_embedding, job_titles_embedding
        FROM resumes
        WHERE LOWER(state) = ANY(%s)
        ORDER BY job_titles_embedding <-> %s::vector
        LIMIT 300;
    """, (allowed_states, job_title_vector.tolist()))

    results = cur.fetchall()
    conn.close()

    if not results:
        if debug:
            print("No resumes matched ANN + state filter.")
        return []

    resume_scores = []
    for row in results:
        resume_id, name, current_job_title, preferred_job_title, skills, experience, education, location, state, \
        skills_emb, experience_emb, education_emb, job_titles_emb = row

        resume_embeddings = {
            'skills': parse_embedding(skills_emb),
            'experience': parse_embedding(experience_emb),
            'education': parse_embedding(education_emb),
            'job_titles': parse_embedding(job_titles_emb)
        }

        score = calculate_weighted_similarity(jd_embeddings, resume_embeddings)

        resume_scores.append({
            'id': resume_id,
            'name': name,
            'current_job_title': current_job_title,
            'preferred_job_title': preferred_job_title,
            'skills': skills,
            'experience': experience,
            'education': education,
            'location': location,
            'state': state,
            'similarity_score': score
        })

    resume_scores.sort(key=lambda x: x['similarity_score'], reverse=True)
    top_results = resume_scores if top_n is None else resume_scores[:top_n]

    if debug:
        for i, res in enumerate(top_results, start=1):
            print(f"\nMatch #{i}")
            print(f"Name: {res['name']}")
            print(f"Current Title: {res['current_job_title']}")
            print(f"Preferred Title: {res['preferred_job_title']}")
            print(f"Location: {res['location']} ({res['state']})")
            print(f"Skills: {res['skills']}")
            print(f"Weighted Similarity Score: {res['similarity_score']:.4f}")
            print(f"Experience: {len(res['experience']) if res['experience'] else 0} positions")
            print(f"Education: {len(res['education']) if res['education'] else 0} degrees")

    return top_results
