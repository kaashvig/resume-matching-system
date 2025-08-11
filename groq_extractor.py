import requests
import json
import re
import time

#GROQ_API_KEY = ""  # Leave blank or load from environment variable

GROQ_MODEL = "llama3-8b-8192"
# ------------------- Resume Extraction -------------------
def extract_structured_info_groq(resume_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = {
        "role": "system",
        "content": (
            "You're an AI that extracts structured info from resumes. "
            "Return ONLY a valid JSON object with the following fields:\n"
            "- name (string)\n"
            "- location (string)\n"
            "- current_job_title (string)\n"
            "- preferred_job_title (string)\n"
            "- skills (array of strings)\n"
            "- experience (array of objects with company, title, duration, description)\n"
            "- education (array of objects with institution, degree, field, year)\n\n"
            "Example:\n"
            "{\n"
            "  \"name\": \"John Doe\",\n"
            "  \"location\": \"New York, USA\",\n"
            "  \"current_job_title\": \"Software Engineer\",\n"
            "  \"preferred_job_title\": \"Senior ML Engineer\",\n"
            "  \"skills\": [\"Python\", \"Machine Learning\", \"TensorFlow\"],\n"
            "  \"experience\": [\n"
            "    {\n"
            "      \"company\": \"Tech Corp\",\n"
            "      \"title\": \"Software Engineer\",\n"
            "      \"duration\": \"2020-2023\",\n"
            "      \"description\": \"Developed ML models and APIs\"\n"
            "    }\n"
            "  ],\n"
            "  \"education\": [\n"
            "    {\n"
            "      \"institution\": \"University of Technology\",\n"
            "      \"degree\": \"Bachelor's\",\n"
            "      \"field\": \"Computer Science\",\n"
            "      \"year\": \"2020\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
    }

    user_prompt = {"role": "user", "content": resume_text[:4000]}

    payload = {
        "model": GROQ_MODEL,
        "messages": [system_prompt, user_prompt],
        "temperature": 0.2
    }

    response = requests.post(url, headers=headers, json=payload)
    time.sleep(2)

    if response.status_code != 200:
        raise Exception(f"GROQ API error {response.status_code}: {response.text}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    json_text = re.search(r"\{.*\}", content, re.DOTALL)
    if not json_text:
        raise Exception(f"Could not extract JSON block from: {content}")
    
    try:
        return json.loads(json_text.group())
    except json.JSONDecodeError:
        raise Exception("Failed to parse extracted JSON from resume.")

# ------------------- Job Description Extraction -------------------
def extract_structured_info_groq_jd(jd_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = {
        "role": "system",
        "content": (
            "You're an AI that extracts structured info from job descriptions. "
            "Return ONLY a valid JSON object with the following fields:\n"
            "- job_title (string)\n"
            "- required_skills (array of strings)\n"
            "- required_experience (string)\n"
            "- required_education (string)\n"
            "- location (string)\n\n"
            "Example:\n"
            "{\n"
            "  \"job_title\": \"Data Scientist\",\n"
            "  \"required_skills\": [\"Python\", \"SQL\", \"Machine Learning\"],\n"
            "  \"required_experience\": \"3+ years in data science or analytics\",\n"
            "  \"required_education\": \"Bachelor's or higher in Computer Science or related field\",\n"
            "  \"location\": \"Delhi, India\"\n"
            "}"
        )
    }

    user_prompt = {"role": "user", "content": jd_text[:4000]}

    payload = {
        "model": GROQ_MODEL,
        "messages": [system_prompt, user_prompt],
        "temperature": 0.2
    }

    response = requests.post(url, headers=headers, json=payload)
    time.sleep(1)

    if response.status_code != 200:
        raise Exception(f"GROQ API error {response.status_code}: {response.text}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    json_text = re.search(r"\{.*\}", content, re.DOTALL)
    if not json_text:
        raise Exception(f"Could not extract JSON block from: {content}")

    try:
        return json.loads(json_text.group())
    except json.JSONDecodeError:
        raise Exception("Failed to parse extracted JSON from job description.")

# ------------------- Relevant Years of Experience -------------------
def extract_relevant_years_experience_groq(job_title, experience_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert resume analyzer.

Given the job title and experience section of a candidate's resume, estimate the total number of years of relevant experience for the specified job.

Job Title: {job_title}

Experience Section:
\"\"\"
{experience_text}
\"\"\"

Return ONLY a float value. Example: 3.5
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"GROQ API error {response.status_code}: {response.text}")

    content = response.json()["choices"][0]["message"]["content"]
    try:
        return float(content.strip())
    except:
        return 0.0
