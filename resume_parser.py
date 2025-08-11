import os
import shutil
from extract_text import extract_text
from clean_text import clean_text
from groq_extractor import extract_structured_info_groq
from db import insert_resume_into_db, get_db_connection

RESUME_FOLDER = "./resumes"
PROCESSED_FOLDER = "./resumes/processed"

# Create processed folder if it doesn't exist
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def process_all_resumes():
    conn = get_db_connection()

    for file in os.listdir(RESUME_FOLDER):
        path = os.path.join(RESUME_FOLDER, file)

        if not os.path.isfile(path) or not file.lower().endswith(('.pdf', '.docx', '.doc')):
            continue

        print(f"\n Processing: {file}")
        try:
            raw_text = extract_text(path)
            cleaned_text = clean_text(raw_text)

            structured_info = extract_structured_info_groq(cleaned_text)
            if structured_info:
                success = insert_resume_into_db(conn, structured_info)
                if success:
                    print(f" Inserted: {file}")
                else:
                    print(f" Skipped (already exists): {file}")
            else:
                print(f"✗ Skipped {file} due to empty structured_info.")

            # Optional: Move processed file (whether inserted or skipped)
            shutil.move(path, os.path.join(PROCESSED_FOLDER, file))

        except Exception as e:
            print(f" Error processing {file}: {e}")

    conn.close()

if __name__ == "__main__":
    process_all_resumes()
