import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import re
import textwrap
import google.generativeai as genai

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Review Delta · Contribution Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL CSS  — editorial / clinical dark theme
#  Fonts: "DM Serif Display" (headlines) + "IBM Plex Mono" (data / body)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Mono:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
    --bg:           #07090f;
    --surface:      #0e1118;
    --surface2:     #151923;
    --border:       #1e2535;
    --border-glow:  #2563eb;
    --accent:       #3b82f6;
    --accent-soft:  #1d3461;
    --danger:       #ef4444;
    --danger-soft:  #3b0d0d;
    --success:      #22c55e;
    --success-soft: #0b2d1a;
    --warn:         #f59e0b;
    --warn-soft:    #2d1f03;
    --text:         #e2e8f0;
    --muted:        #64748b;
    --mono:         'IBM Plex Mono', monospace;
    --serif:        'DM Serif Display', serif;
}

html, body, .stApp { background: var(--bg) !important; color: var(--text) !important; }
.stApp { font-family: var(--mono) !important; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; max-width: 1100px !important; }

section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { font-family: var(--mono) !important; }

h1, h2, h3, h4 { font-family: var(--serif) !important; color: var(--text) !important; }

.stTextInput input, .stSelectbox select, .stTextArea textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
}
.stTextInput input:focus {
    border-color: var(--border-glow) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
}

.stButton > button {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--accent) !important;
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    border-radius: 6px !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.2s ease !important;
    text-transform: uppercase !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    box-shadow: 0 0 14px rgba(59,130,246,0.25) !important;
    background: var(--accent-soft) !important;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #1d4ed8, #3b82f6, #60a5fa) !important;
    border-radius: 4px !important;
}
.stProgress > div > div > div {
    background: var(--surface2) !important;
    border-radius: 4px !important;
}

/* Focus ring cards */
.focus-ring {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.6rem 1.8rem;
    position: relative;
    transition: box-shadow 0.3s ease, border-color 0.3s ease;
    margin-bottom: 1rem;
    overflow: hidden;
}
.focus-ring::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(59,130,246,0.15), transparent 60%);
    pointer-events: none;
}
.focus-ring:hover {
    border-color: rgba(59,130,246,0.45);
    box-shadow: 0 0 0 1px rgba(59,130,246,0.2),
                0 0 24px rgba(59,130,246,0.1),
                0 0 60px rgba(59,130,246,0.05);
}
.focus-ring-danger {
    border-color: rgba(239,68,68,0.35) !important;
    background: linear-gradient(135deg, var(--danger-soft) 0%, var(--surface) 60%);
}
.focus-ring-warn {
    border-color: rgba(245,158,11,0.35) !important;
    background: linear-gradient(135deg, var(--warn-soft) 0%, var(--surface) 60%);
}
.focus-ring-blue {
    border-color: rgba(59,130,246,0.35) !important;
    background: linear-gradient(135deg, #0f1a35 0%, var(--surface) 60%);
}

/* Scan animation */
@keyframes pulse-ring {
    0%   { transform: scale(0.85); opacity: 1; }
    70%  { transform: scale(1.4);  opacity: 0; }
    100% { transform: scale(0.85); opacity: 0; }
}
@keyframes pulse-core {
    0%, 100% { transform: scale(1);    box-shadow: 0 0 0 0 rgba(59,130,246,0.6); }
    50%       { transform: scale(1.12); box-shadow: 0 0 0 12px rgba(59,130,246,0); }
}
@keyframes scan-line {
    0%   { top: 0%; opacity: 0.9; }
    100% { top: 100%; opacity: 0; }
}

.scan-wrapper {
    display: flex;
    align-items: center;
    gap: 1.2rem;
    padding: 1.2rem 1.6rem;
    background: var(--surface);
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 12px;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}
.scan-wrapper::after {
    content: '';
    position: absolute;
    left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(59,130,246,0.6), transparent);
    animation: scan-line 1.8s linear infinite;
}
.pulse-dot {
    position: relative;
    width: 18px; height: 18px; flex-shrink: 0;
}
.pulse-dot::before {
    content: '';
    position: absolute; inset: 0;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse-core 1.4s ease-in-out infinite;
}
.pulse-dot::after {
    content: '';
    position: absolute; inset: 0;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse-ring 1.4s ease-out infinite;
}
.scan-text  { font-family: var(--mono); font-size: 0.8rem; color: #93c5fd; letter-spacing: 0.06em; }
.scan-label { font-family: var(--mono); font-size: 0.65rem; color: var(--muted); text-transform: uppercase;
              letter-spacing: 0.12em; margin-top: 0.15rem; }

/* Stat chips */
.stat-row { display: flex; gap: 0.8rem; flex-wrap: wrap; margin-bottom: 1.2rem; }
.stat-chip {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 0.04em;
}
.stat-chip span { display: block; font-size: 1.3rem; font-weight: 600; color: var(--text); margin-bottom: 0.1rem; }

/* Keyword tags */
.tag-row { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.6rem; }
.tag { font-family: var(--mono); font-size: 0.65rem; letter-spacing: 0.06em;
       padding: 0.2rem 0.6rem; border-radius: 999px; border: 1px solid; }
.tag-low  { background: var(--danger-soft); border-color: rgba(239,68,68,0.4); color: #fca5a5; }
.tag-high { background: var(--success-soft); border-color: rgba(34,197,94,0.4); color: #86efac; }

/* Section label */
.section-label {
    font-family: var(--mono); font-size: 0.6rem; text-transform: uppercase;
    letter-spacing: 0.2em; color: var(--muted);
    margin: 1.8rem 0 0.8rem 0;
    display: flex; align-items: center; gap: 0.8rem;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* Copy box */
.copy-box {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.2rem 1.4rem;
    font-family: var(--mono); font-size: 0.75rem; color: var(--muted);
    white-space: pre-wrap; word-break: break-word; line-height: 1.7;
    max-height: 280px; overflow-y: auto;
}

/* Recommendation */
.rec-box {
    background: linear-gradient(135deg, #0f1f0f, var(--surface));
    border: 1px solid rgba(34,197,94,0.25); border-radius: 10px;
    padding: 1rem 1.3rem; font-family: var(--mono); font-size: 0.8rem;
    color: #86efac; line-height: 1.65; margin-top: 0.8rem;
}

/* Bar track */
.bar-track { height: 6px; background: var(--surface2); border-radius: 3px; overflow: hidden; border: 1px solid var(--border); }
.bar-fill  { height: 100%; border-radius: 3px; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("analysis_done", False),
    ("analysis_data", None),
    ("slack_text", ""),
    ("copy_success", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 Review Delta")
    st.markdown(
        "<span style='font-family:\"IBM Plex Mono\",monospace;font-size:0.72rem;color:#64748b;'>"
        "Contribution Analysis Engine · v1.0</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    # API key is loaded from .streamlit/secrets.toml — no user input needed
    try:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]
        st.markdown(
            "<div style='font-family:\"IBM Plex Mono\",monospace;font-size:0.68rem;"
            "color:#22c55e;line-height:1.6;'>"
            "🔑 Gemini API key loaded<br>"
            "<span style='color:#475569;'>from Streamlit secrets</span></div>",
            unsafe_allow_html=True,
        )
    except KeyError:
        gemini_api_key = None
        st.markdown(
            "<div style='font-family:\"IBM Plex Mono\",monospace;font-size:0.68rem;"
            "color:#ef4444;line-height:1.7;'>"
            "⚠ <code>GEMINI_API_KEY</code> not found.<br><br>"
            "Add it to <code>.streamlit/secrets.toml</code>:<br><br>"
            "<code style='color:#f59e0b;'>GEMINI_API_KEY = \"AIza...\"</code>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        "<div style='font-family:\"IBM Plex Mono\",monospace;font-size:0.68rem;color:#475569;line-height:1.9;'>"
        "LOW RATINGS &nbsp;→ &nbsp;1–2 ★<br>"
        "HIGH RATINGS → 3–5 ★<br><br>"
        "Upload any CSV/Excel with a<br>"
        "<code style='color:#60a5fa;'>rating</code> column to begin.<br><br>"
        "Gemini 2.5 Flash identifies the<br>"
        "top 3 factors driving the delta.</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
#  HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:2rem;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;letter-spacing:0.2em;
                color:#334155;text-transform:uppercase;margin-bottom:0.5rem;">
        Diagnostic · Sentiment Intelligence
    </div>
    <h1 style="font-family:'DM Serif Display',serif;font-size:2.6rem;margin:0;
               line-height:1.1;color:#e2e8f0;">
        Review Delta<br>
        <em style="color:#3b82f6;">Contribution Analysis</em>
    </h1>
    <p style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#475569;
              margin-top:0.7rem;max-width:540px;line-height:1.6;">
        Pinpoints the exact factors separating 1–2★ reviews from 3–5★ reviews,
        quantified by impact percentage and surfaced for immediate action.
    </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1 — UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">01 · Upload Dataset</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop a CSV or Excel file with a **rating** column (values 1–5)",
    type=["csv", "xlsx", "xls"],
    label_visibility="collapsed",
)

df = None
low_df = high_df = None

if uploaded_file:
    try:
        if uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        if "rating" not in df.columns:
            st.error("❌ No `rating` column found. Please upload a file that contains a column named **rating**.")
            df = None
        else:
            df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
            df.dropna(subset=["rating"], inplace=True)
            df["rating"] = df["rating"].astype(int)

            low_df  = df[df["rating"].isin([1, 2])]
            high_df = df[df["rating"].isin([3, 4, 5])]

            total   = len(df)
            low_n   = len(low_df)
            high_n  = len(high_df)
            avg_r   = df["rating"].mean()
            low_pct = low_n / total * 100 if total else 0

            st.markdown(f"""
            <div class="stat-row">
                <div class="stat-chip"><span>{total:,}</span>Total Reviews</div>
                <div class="stat-chip"><span style="color:#ef4444;">{low_n:,}</span>Low (1–2 ★)</div>
                <div class="stat-chip"><span style="color:#22c55e;">{high_n:,}</span>High (3–5 ★)</div>
                <div class="stat-chip"><span style="color:#f59e0b;">{avg_r:.2f}</span>Avg Rating</div>
                <div class="stat-chip"><span style="color:#ef4444;">{low_pct:.1f}%</span>Low Share</div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Could not read file: {e}")
        df = None

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 2 — CONFIGURE
# ─────────────────────────────────────────────────────────────────────────────
text_col  = None
extra_cols = []

if df is not None:
    st.markdown('<div class="section-label">02 · Configure Analysis</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.dataframe(df.head(6), use_container_width=True, height=190)

    with col_right:
        text_candidates = [
            c for c in df.columns
            if df[c].dtype == object and c.lower() != "rating"
        ]
        if text_candidates:
            text_col = st.selectbox(
                "Primary text column for AI analysis",
                options=text_candidates,
                help="Column containing review text",
            )
        else:
            st.info("No text columns detected — analysis will use numeric patterns only.")

        other_cols = [c for c in df.columns if c.lower() != "rating" and c != text_col]
        extra_cols = st.multiselect(
            "Extra context columns (optional)",
            options=other_cols,
            max_selections=4,
        )

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 3 — RUN
# ─────────────────────────────────────────────────────────────────────────────
if df is not None:
    st.markdown('<div class="section-label">03 · Run Diagnostic</div>', unsafe_allow_html=True)

    run_col, _ = st.columns([1, 3])
    with run_col:
        run_btn = st.button("⚡  Run Contribution Analysis", use_container_width=True)

    if run_btn:
        if not gemini_api_key:
            st.error(
                "Gemini API key not found. "
                "Add `GEMINI_API_KEY = \"AIza...\"` to your `.streamlit/secrets.toml` file."
            )
            st.stop()
        if low_df is None or len(low_df) == 0 or high_df is None or len(high_df) == 0:
            st.error("Need at least one review in each group (1–2★ and 3–5★).")
            st.stop()

        # ── Medical scan animation ──────────────────────────────────────────
        scan_ph = st.empty()
        prog_ph = st.empty()

        scan_ph.markdown("""
        <div class="scan-wrapper">
            <div class="pulse-dot"></div>
            <div>
                <div class="scan-text">Running diagnostic scan · analysing sentiment vectors…</div>
                <div class="scan-label">Gemini 2.5 Flash · contribution engine active</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        progress_bar = prog_ph.progress(0)
        for pct in range(0, 82, 3):
            time.sleep(0.045)
            progress_bar.progress(pct)

        # ── Build prompt context ────────────────────────────────────────────
        def sample_texts(sub_df, col, n=50):
            if col and col in sub_df.columns:
                return sub_df[col].dropna().sample(min(n, len(sub_df)), random_state=42).tolist()
            return []

        low_samples  = sample_texts(low_df,  text_col)
        high_samples = sample_texts(high_df, text_col)

        numeric_cols = [c for c in df.select_dtypes(include=np.number).columns if c.lower() != "rating"]
        num_lines = []
        for nc in numeric_cols[:6]:
            lm = low_df[nc].mean()
            hm = high_df[nc].mean()
            num_lines.append(f"  {nc}: low_avg={lm:.2f}, high_avg={hm:.2f}, delta={lm-hm:+.2f}")

        extra_lines = []
        for ec in extra_cols:
            if df[ec].dtype == object:
                lt = low_df[ec].value_counts().head(3).to_dict()
                ht = high_df[ec].value_counts().head(3).to_dict()
                extra_lines.append(f"  {ec} — low top: {lt} | high top: {ht}")

        low_block  = "\n".join(f'  [{i+1}] "{t}"' for i, t in enumerate(low_samples[:30]))
        high_block = "\n".join(f'  [{i+1}] "{t}"' for i, t in enumerate(high_samples[:30]))

        prompt = textwrap.dedent(f"""
        You are a senior product analyst performing a contribution analysis on customer reviews.

        GROUP A — Low Ratings (1–2 stars): {len(low_df)} reviews
        GROUP B — High Ratings (3–5 stars): {len(high_df)} reviews

        {"SAMPLE LOW-RATING REVIEWS:" + chr(10) + low_block if low_samples else ""}
        {"SAMPLE HIGH-RATING REVIEWS:" + chr(10) + high_block if high_samples else ""}
        {"NUMERIC FEATURE DELTAS:" + chr(10) + chr(10).join(num_lines) if num_lines else ""}
        {"EXTRA CONTEXT:" + chr(10) + chr(10).join(extra_lines) if extra_lines else ""}

        TASK: Identify the top 3 contributing factors that most explain the delta between low and high ratings.
        Format them as a bulleted list with percentage impacts.

        Return ONLY valid JSON (no markdown fences, no text outside JSON):

        {{
          "executive_summary": "2-3 sentence summary of the key delta",
          "factors": [
            {{
              "rank": 1,
              "name": "Factor name (2-5 words)",
              "impact_pct": 45,
              "explanation": "One sentence explaining how this drives the rating difference.",
              "low_signal": "Pattern seen in low-rating reviews",
              "high_signal": "Pattern seen in high-rating reviews",
              "keywords_low": ["word1", "word2", "word3"],
              "keywords_high": ["word1", "word2", "word3"]
            }},
            {{
              "rank": 2,
              "name": "...",
              "impact_pct": 33,
              "explanation": "...",
              "low_signal": "...",
              "high_signal": "...",
              "keywords_low": ["word1", "word2"],
              "keywords_high": ["word1", "word2"]
            }},
            {{
              "rank": 3,
              "name": "...",
              "impact_pct": 22,
              "explanation": "...",
              "low_signal": "...",
              "high_signal": "...",
              "keywords_low": ["word1"],
              "keywords_high": ["word1"]
            }}
          ],
          "recommendation": "One specific, actionable recommendation to close the gap.",
          "confidence": "high"
        }}

        Ensure impact_pct values sum to exactly 100. Be analytical and specific.
        """).strip()

        # ── Call Gemini ─────────────────────────────────────────────────────
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1500,
                    response_mime_type="application/json"
                ),
            )

            raw_text = response.text.strip()
            raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text)
            raw_text = re.sub(r"\n?```$", "", raw_text).strip()

            result = json.loads(raw_text)

            for pct in range(82, 101, 3):
                time.sleep(0.02)
                progress_bar.progress(min(pct, 100))

            scan_ph.empty()
            prog_ph.empty()

            st.session_state.analysis_done = True
            st.session_state.analysis_data = result
            st.session_state.copy_success  = False

            # Build Slack-ready text
            facs = result.get("factors", [])
            slack_lines = [
                "📊 *Review Delta · Contribution Analysis*",
                f"Dataset: `{uploaded_file.name}` — {len(df):,} reviews",
                f"Low (1–2★): {len(low_df):,}  |  High (3–5★): {len(high_df):,}",
                "",
                f"*Summary:* {result.get('executive_summary', '')}",
                "",
                "*Top 3 Contributing Factors:*",
            ]
            for f in facs:
                slack_lines.append(
                    f"• *{f['name']}* — {f['impact_pct']}% impact\n"
                    f"  ↳ {f['explanation']}"
                )
            slack_lines += [
                "",
                f"*Recommendation:* {result.get('recommendation', '')}",
                "",
                f"_Confidence: {result.get('confidence','n/a').upper()} · Powered by Gemini 2.5 Flash_",
            ]
            st.session_state.slack_text = "\n".join(slack_lines)

        except json.JSONDecodeError as e:
            scan_ph.empty()
            prog_ph.empty()
            st.error(f"JSON parse error: {e}\n\nRaw:\n{raw_text[:600]}")
        except Exception as e:
            scan_ph.empty()
            prog_ph.empty()
            st.error(f"Gemini API error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 4 — DISPLAY RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.analysis_done and st.session_state.analysis_data:
    result  = st.session_state.analysis_data
    factors = result.get("factors", [])

    st.markdown('<div class="section-label">04 · Findings</div>', unsafe_allow_html=True)

    # Executive summary
    st.markdown(f"""
    <div class="focus-ring">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;text-transform:uppercase;
                    letter-spacing:0.18em;color:#475569;margin-bottom:0.6rem;">◈ Executive Summary</div>
        <p style="font-family:'IBM Plex Mono',monospace;font-size:0.85rem;color:#cbd5e1;
                  line-height:1.75;margin:0;">
            {result.get("executive_summary","")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Factor heading
    st.markdown(
        "<div style='font-family:\"IBM Plex Mono\",monospace;font-size:0.6rem;text-transform:uppercase;"
        "letter-spacing:0.18em;color:#475569;margin:1.4rem 0 0.8rem 0;'>◈ Top 3 Contributing Factors</div>",
        unsafe_allow_html=True,
    )

    color_map = {0: "#ef4444", 1: "#f59e0b", 2: "#3b82f6"}
    ring_map  = {0: "focus-ring focus-ring-danger", 1: "focus-ring focus-ring-warn", 2: "focus-ring focus-ring-blue"}

    for i, f in enumerate(factors[:3]):
        pct   = min(int(f.get("impact_pct", 0)), 100)
        color = color_map.get(i, "#94a3b8")
        ring  = ring_map.get(i, "focus-ring")

        kw_low  = "".join(f'<span class="tag tag-low">{kw}</span>'  for kw in f.get("keywords_low",  []))
        kw_high = "".join(f'<span class="tag tag-high">{kw}</span>' for kw in f.get("keywords_high", []))

        st.markdown(f"""
        <div class="{ring}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;">
                <div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;text-transform:uppercase;
                                letter-spacing:0.15em;color:#475569;margin-bottom:0.25rem;">
                        Factor #{f.get("rank","?")}
                    </div>
                    <div style="font-family:'DM Serif Display',serif;font-size:1.35rem;color:{color};">
                        {f.get("name","")}
                    </div>
                </div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:1.6rem;font-weight:600;
                            color:{color};letter-spacing:-0.02em;">
                    {pct}%
                </div>
            </div>

            <div style="margin-bottom:0.9rem;">
                <div class="bar-track">
                    <div class="bar-fill" style="width:{pct}%;background:{color};opacity:0.85;"></div>
                </div>
            </div>

            <p style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#94a3b8;
                      line-height:1.7;margin:0.7rem 0 0.9rem 0;">
                {f.get("explanation","")}
            </p>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;margin-top:0.8rem;">
                <div style="background:var(--danger-soft);border:1px solid rgba(239,68,68,0.2);
                            border-radius:8px;padding:0.7rem 0.9rem;">
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#ef4444;
                                text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.35rem;">
                        ↓ Low signal
                    </div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#fca5a5;line-height:1.5;">
                        {f.get("low_signal","")}
                    </div>
                    <div class="tag-row">{kw_low}</div>
                </div>
                <div style="background:var(--success-soft);border:1px solid rgba(34,197,94,0.2);
                            border-radius:8px;padding:0.7rem 0.9rem;">
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#22c55e;
                                text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.35rem;">
                        ↑ High signal
                    </div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#86efac;line-height:1.5;">
                        {f.get("high_signal","")}
                    </div>
                    <div class="tag-row">{kw_high}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Recommendation
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;text-transform:uppercase;
                letter-spacing:0.18em;color:#475569;margin:1.4rem 0 0.5rem 0;">◈ Recommended Action</div>
    <div class="rec-box">⚡ {result.get("recommendation","")}</div>
    """, unsafe_allow_html=True)

    # ── Slack Section ───────────────────────────────────────────────────────
    st.markdown('<div class="section-label">05 · Share Results</div>', unsafe_allow_html=True)

    slack_text = st.session_state.slack_text
    st.markdown(f'<div class="copy-box">{slack_text}</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

    copy_col, _ = st.columns([1, 4])
    with copy_col:
        if st.button("📋  Copy for Slack", use_container_width=True):
            escaped = (
                slack_text
                .replace("\\", "\\\\")
                .replace("`", "\\`")
                .replace("$", "\\$")
                .replace("\n", "\\n")
            )
            st.markdown(f"""
            <script>
            (function(){{
                const text = `{escaped}`.replace(/\\\\n/g, '\\n');
                navigator.clipboard.writeText(text).catch(function(e){{
                    console.error('Clipboard write failed:', e);
                }});
            }})();
            </script>
            """, unsafe_allow_html=True)
            st.success("✅  Copied — paste straight into Slack!")

# ─────────────────────────────────────────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
if df is None and not uploaded_file:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;">
        <div style="font-size:3.5rem;margin-bottom:1rem;opacity:0.25;">🔬</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;
                    color:#334155;line-height:2.1;">
            Upload a CSV or Excel file with a
            <code style="color:#3b82f6;">rating</code> column<br>
            and enter your Gemini API key in the sidebar to begin.
        </div>
    </div>
    """, unsafe_allow_html=True)
