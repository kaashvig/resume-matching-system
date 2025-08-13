Overview
----------------------------------
Resume Matcher is an AI-powered application that semantically matches job descriptions to candidate resumes using transformer embeddings and weighted multi-section scoring across job titles, skills, experience, and education. It provides:

A Streamlit interface for quick testing and demos.

A FastAPI endpoint for programmatic access.

PostgreSQL + pgvector for fast vector similarity search.
----------------------------------------
Key Features

Semantic matching with Sentence Transformers (all-MiniLM-L6-v2).

Weighted scoring across titles, skills, experience, and education.

Location-aware filtering using state and neighboring states.

REST API: POST /match for integration.

----------------------------------------
app.py — Streamlit UI to input a job description and view top matches.

api.py — FastAPI app exposing the POST /match endpoint.

backfill_state_column.py — Script to infer/fill missing state from location.

clean_text.py — Text normalization helpers.

db.py — Database connection, schema, and embedding storage utilities.

extract_text.py — Utilities to extract plain text from PDF and DOCX files using pdfplumber and python-docx.

groq_extractor.py — Wrapper to call Groq LLM APIs for structured extraction (e.g., skills, titles, experience) from raw resume text.

matching2.py — Matching logic: parsing, embeddings, filters, scoring.

match_resumes.py — CLI utility to run a sample match from terminal.

requirements.txt — Python dependencies for the project.

resume_parser.py — Parses extracted resume text into structured fields (name, email, phone, skills, education, experience) using rules/LLM prompts.
----------------------------------------
Prerequisites
Python 3.10+

PostgreSQL 14+ with pgvector extension enabled

Quick Start (Local)
Create a virtual environment and install dependencies

Windows (PowerShell)

python -m venv .venv

..venv\Scripts\Activate.ps1

pip install -r requirements.txt

macOS/Linux

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

Set up PostgreSQL with pgvector

In psql (or any SQL client):

CREATE DATABASE dbresume;

\c dbresume

CREATE EXTENSION IF NOT EXISTS vector;

Configure database credentials

Open db.py and update DB_CONFIG (host, port, dbname, user, password) to match the local PostgreSQL setup.

Create tables and indexes

Run a small bootstrap via Python REPL:

python

from db import create_updated_table

create_updated_table()

exit()


Start the API server (FastAPI)

uvicorn api:app --reload

The API will be available at http://127.0.0.1:8000

Start the UI (Streamlit)

streamlit run app.py

Ensure the API URL inside app.py points to the running FastAPI (e.g., http://127.0.0.1:8000)

How To Use
Streamlit UI

Enter a job description (include role, key skills, location).

Select top_n (e.g., 5–20).

Click match to view ranked candidates with similarity scores and key fields.

API

Endpoint: POST /match

Request JSON:
{
"jd_text": "Data Scientist Bangalore",
"top_n": 5
}

Example curl:
curl -X POST "http://127.0.0.1:8000/match"
-H "Content-Type: application/json"
-d '{"jd_text": "Data Scientist Bangalore", "top_n": 5}'

How It Works
Parsing and Embeddings

The job description is parsed to extract relevant signals (titles, skills, experience, education, location).

Sentence Transformers model all-MiniLM-L6-v2 generates dense embeddings for resume and JD sections.

Retrieval

Resumes are stored with section embeddings in PostgreSQL using the pgvector extension.

The system filters candidates by allowed states (JD state and neighboring states) and retrieves nearest neighbors via vector similarity.

Ranking

Final scores are computed via weighted similarity:

Job titles: 0.35

Skills: 0.25

Experience: 0.25

Education: 0.15

Top-N matches are returned to the UI/API.

Configuration
Database credentials: db.py → DB_CONFIG

Section weights: matching2.py → SECTION_WEIGHTS

City-to-state and neighbor state mapping: matching2.py

Frontend API endpoint: app.py → API_URL

Model and embedding dimensions: matching2.py/db.py (vector(384) for all-MiniLM-L6-v2)

Data Model (PostgreSQL)
Table: resumes

id SERIAL PRIMARY KEY

name TEXT

location TEXT

state TEXT

current_job_title TEXT

preferred_job_title TEXT

skills TEXT[]

experience JSONB

education JSONB

resume_hash TEXT UNIQUE

skills_embedding vector(384)

experience_embedding vector(384)

education_embedding vector(384)

job_titles_embedding vector(384)

state_embedding vector(384)

Indexes and performance

Ensure pgvector indexes on embedding columns per retrieval strategy.

Add B-Tree index on state for fast filtering.

Development Notes
Ensure pgvector is installed and enabled (CREATE EXTENSION vector).

The transformer model downloads on first run; keep internet access or cache models.

Handle missing sections gracefully; quality improves when resumes have structured fields.

If JD has no location, either relax filtering logic or provide a default/global search mode.

For production, containerize (Docker), pin package versions, and add CI/CD.
