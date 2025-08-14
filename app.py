import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000/match"
BACKEND_URL = "http://127.0.0.1:8000"  # Added

st.set_page_config(page_title="Resume Matcher", layout="wide")
st.title("Resume Matcher")

st.markdown("Paste the Job Description and click **Find Top 5 Matches** — results come from your DB via the matching logic.")

jd_text = st.text_area("Job Description", height=300, placeholder="Paste full JD here...")

col1, col2 = st.columns([1, 1])
with col1:
    top_n = st.number_input("Top N results", min_value=1, max_value=20, value=5, step=1)
with col2:
    min_score = st.slider("Min similarity (optional filter)", 0.0, 1.0, 0.0, step=0.01)

# Upload resumes section
uploaded_files = st.file_uploader(
    "Upload Resume PDFs or DOCXs (optional)", type=['pdf', 'docx'], accept_multiple_files=True
)
if uploaded_files:
    for f in uploaded_files:
        st.write(f"Uploading {f.name}…")
        try:
            result = requests.post(
                f"{BACKEND_URL}/upload_resume",
                files={'file': (f.name, f.getvalue())}
            )
            if result.ok:
                st.success(f"{f.name} uploaded!")
            else:
                st.error(f"Failed to upload {f.name}: {result.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Upload failed: {e}")

if st.button("Find Top Matches"):
    if not jd_text.strip():
        st.warning("Please paste a Job Description.")
    else:
        payload = {"jd_text": jd_text, "top_n": int(top_n)}
        try:
            with st.spinner("Requesting matches from backend..."):
                resp = requests.post(API_URL, json=payload, timeout=60)
            if resp.status_code != 200:
                st.error(f"Backend error {resp.status_code}: {resp.text}")
            else:
                data = resp.json()
                matches = data.get("matches", [])

                if not matches:
                    st.info("No matches returned by backend.")
                else:
                    df = pd.DataFrame(matches)

                    sim_col = next((c for c in [
                        "similarity_score", "similarity", "score", 
                        "weighted_similarity", "weighted_score"
                    ] if c in df.columns), None)

                    if sim_col:
                        df = df[df[sim_col] >= min_score]
                        df = df.sort_values(by=sim_col, ascending=False).head(int(top_n))
                        df[sim_col] = df[sim_col].round(4)

                    st.subheader("Top matches")
                    st.dataframe(df, use_container_width=True)

                    st.markdown("---")
                    st.markdown("### Detailed view")
                    for i, row in df.head(int(top_n)).iterrows():
                        st.markdown(f"**Match #{i+1}**")
                        for col in df.columns:
                            st.write(f"**{col}:** {row[col]}")
                        st.markdown("---")
        except requests.exceptions.RequestException as e:
            st.error(f"Request to backend failed: {e}")
