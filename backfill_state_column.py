import psycopg2
import re

# Mapping of known city/region keywords to Indian states
state_keywords = {
    "bangalore": "karnataka",
    "bengaluru": "karnataka",
    "mumbai": "maharashtra",
    "pune": "maharashtra",
    "nagpur": "maharashtra",
    "hyderabad": "telangana",
    "delhi": "delhi",
    "new delhi": "delhi",
    "chennai": "tamil nadu",
    "coimbatore": "tamil nadu",
    "kolkata": "west bengal",
    "howrah": "west bengal",
    "noida": "uttar pradesh",
    "ghaziabad": "uttar pradesh",
    "lucknow": "uttar pradesh",
    "kanpur": "uttar pradesh",
    "patna": "bihar",
    "bhopal": "madhya pradesh",
    "indore": "madhya pradesh",
    "jaipur": "rajasthan",
    "udaipur": "rajasthan",
    "goa": "goa",
    "guwahati": "assam",
    "chandigarh": "chandigarh",
    "ranchi": "jharkhand",
    "jamshedpur": "jharkhand",
    "bhubaneswar": "odisha",
    "cuttack": "odisha",
    "amritsar": "punjab",
    "ludhiana": "punjab",
    "panaji": "goa"
}

def extract_state(location):
    if not location:
        return None
    location = location.lower()
    for keyword, state in state_keywords.items():
        if re.search(rf'\b{keyword}\b', location):
            return state
    return None


conn = psycopg2.connect(
    dbname="dbresume",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

# Fetch all records
cursor.execute("SELECT id, location FROM resumes")
rows = cursor.fetchall()

for resume_id, location in rows:
    state = extract_state(location)
    if state:
        cursor.execute("UPDATE resumes SET state = %s WHERE id = %s", (state, resume_id))
        print(f" Updated ID {resume_id} with state: {state}")
    else:
        print(f"Could not extract state for ID {resume_id}, location: {location}")

conn.commit()
cursor.close()
conn.close()

print("State backfill complete.")


print(" State backfill complete.")
