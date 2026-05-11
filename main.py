import streamlit as st
import pandas as pd
import numpy as np
import time
import textwrap
import google.generativeai as genai

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Review Delta · Analysis", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&display=swap');
    
    :root {
        --bg: #07090f;
        --surface: #0e1118;
        --accent: #3b82f6;
        --text: #e2e8f0;
    }

    .stApp { background: var(--bg); color: var(--text); font-family: 'IBM Plex Mono', monospace; }

    /* The Focus Ring Container */
    .focus-ring {
        background: var(--surface);
        border: 1px solid rgba(59, 130, 246, 0.5);
        border-radius: 14px;
        padding: 2rem;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
        margin-top: 2rem;
        line-height: 1.8;
    }

    /* Pulsing Scan Animation */
    .scan-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin: 20px 0;
    }
    .pulse-circle {
        width: 15px;
        height: 15px;
        background: var(--accent);
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.9); opacity: 1; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
        70% { transform: scale(1.1); opacity: 0.3; box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
        100% { transform: scale(0.9); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_api_key)
except KeyError:
    st.error("Missing `GEMINI_API_KEY` in `.streamlit/secrets.toml`")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.title("🔬 Review Delta Analysis")
st.caption("Senior Product Analyst Diagnostic Engine")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload review dataset (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    if "rating" not in df.columns:
        st.error("Dataset must contain a 'rating' column.")
    else:
        # Pre-process
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        low_df = df[df['rating'].isin([1, 2])]
        high_df = df[df['rating'].isin([3, 4, 5])]
        
        st.success(f"Loaded {len(df)} reviews. Found {len(low_df)} Low vs {len(high_df)} High.")

        # Column Selection
        text_col = st.selectbox("Select Review Text Column", [c for c in df.columns if c != 'rating'])

        if st.button("⚡ Run Diagnostic Scan"):
            # Animation
            scan_placeholder = st.empty()
            with scan_placeholder.container():
                st.markdown('<div class="scan-container"><div class="pulse-circle"></div><span>AI Senior Analyst is performing contribution delta scan...</span></div>', unsafe_allow_html=True)
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.02) # Total ~2 seconds
                    progress_bar.progress(i + 1)
            scan_placeholder.empty()

            # Prepare Data Samples
            low_text = "\n".join(low_df[text_col].astype(str).tail(20).tolist())
            high_text = "\n".join(high_df[text_col].astype(str).tail(20).tolist())

            # ─────────────────────────────────────────────────────────────────
            # AI PROMPT
            # ─────────────────────────────────────────────────────────────────
            prompt = f"""
            You are a senior product analyst. Conduct a "contribution analysis" explaining the delta 
            between Low Ratings (1-2) and High Ratings (3-5).

            LOW RATING SAMPLES:
            {low_text}

            HIGH RATING SAMPLES:
            {high_text}

            TASK:
            1. Provide a professional Executive Summary paragraph for stakeholder review.
            2. Identify the top 3 contributing factors that explain why reviews drop into the 1-2 star range.
            3. Format those 3 factors as a bulleted list with specific percentage impacts (e.g., "Feature Friction - 45%").
            4. End with one actionable strategic recommendation.

            Return the response as a single cohesive report in plain text/paragraphs. 
            Do not use JSON or code fences.
            """

            try:
                model = genai.GenerativeModel("gemini-2.5-flash") # Use flash for speed
                response = model.generate_content(prompt)
                full_analysis = response.text

                # ─────────────────────────────────────────────────────────────
                # DISPLAY RESULTS (The Focus Ring)
                # ─────────────────────────────────────────────────────────────
                st.markdown(f"""
                <div class="focus-ring">
                    {full_analysis}
                </div>
                """, unsafe_allow_html=True)

                # ─────────────────────────────────────────────────────────────
                # SLACK READY BUTTON
                # ─────────────────────────────────────────────────────────────
                st.divider()
                if st.button("📋 Copy for Slack"):
                    # Basic JS copy implementation
                    st.write("Report ready for clipboard. (Select text above to copy)")
                    st.info("Slack Formatting Tip: Use Shift+Enter for clean paragraphs.")
                    st.code(full_analysis, language=None)

            except Exception as e:
                st.error(f"Analysis failed: {e}")
