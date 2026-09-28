"""
SkillSprint AI – Main Streamlit Application
Complete dual-pipeline demo with working validation flow
Includes authentication, RBAC, manual review, consistency check (SRS-compliant)
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings
from src.document_processing.uploader import validate_file, save_upload
from src.document_processing.parser import parse_document
from src.python_validation.validator import validate_plan
from src.comparison_engine.compare import compare_and_report
from src.security.prompt_injection import scan_for_injection, build_safe_system_instruction
from src.database.mongo_queries import (
    save_plan_to_mongo,
    get_admin_stats_from_mongo,
    get_recent_plans_from_mongo,
    get_plans_by_role_from_mongo,
)
from src.manual_review.review_queue import (
    flag_items_from_report, apply_decision, build_audit_record
)
from src.python_validation.consistency import compare_consistency
from src.python_validation.contradictions import detect_all_contradictions

st.set_page_config(
    page_title="SkillSprint AI | OnboardVerse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AI & Machinery Custom Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap');

    :root {
        --void-black: #03060c;
        --machinery-bg: #070d18;
        --panel-steel: rgba(13, 22, 38, 0.75);
        --panel-glass: rgba(18, 30, 50, 0.45);
        --neon-cyan: #00f0ff;
        --neon-blue: #3b82f6;
        --neon-purple: #8b5cf6;
        --laser-green: #10b981;
        --warning-amber: #f59e0b;
        --border-cyber: rgba(0, 240, 255, 0.25);
        --border-glow: rgba(0, 240, 255, 0.65);
        --text-main: #e2e8f0;
        --text-muted: #64748b;
        --grad-hud: linear-gradient(135deg, #00f0ff 0%, #3b82f6 50%, #8b5cf6 100%);
    }

    /* Machine Background Grid Overlay */
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Rajdhani', sans-serif;
        color: var(--text-main);
        background-color: var(--void-black) !important;
    }

    [data-testid="stAppViewContainer"] {
        background: 
            radial-gradient(circle at 50% 0%, rgba(0, 240, 255, 0.08) 0%, transparent 60%),
            linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px),
            var(--void-black) !important;
        background-size: 100% 100%, 40px 40px, 40px 40px !important;
        background-attachment: fixed !important;
    }

    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.5rem; max-width: 1280px; }

    /* AI / Machine Headers */
    .machinery-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        background: var(--grad-hud);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(0, 240, 255, 0.4);
        margin-bottom: 0.1rem;
    }

    .machinery-subtitle {
        font-family: 'Share Tech Mono', monospace;
        color: var(--neon-cyan);
        font-size: 0.95rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .machinery-subtitle::before {
        content: '';
        display: inline-block;
        width: 8px;
        height: 8px;
        background: var(--neon-cyan);
        box-shadow: 0 0 10px var(--neon-cyan);
        border-radius: 50%;
        animation: pulseDots 1.5s infinite alternate;
    }

    @keyframes pulseDots {
        0% { opacity: 0.3; transform: scale(0.8); }
        100% { opacity: 1; transform: scale(1.2); }
    }

    /* Cyber Card Panels & Machinery Metrics */
    [data-testid="stMetric"] {
        background: var(--panel-steel) !important;
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-cyber) !important;
        border-radius: 8px !important;
        padding: 1rem 1.2rem !important;
        position: relative;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.8), inset 0 0 15px rgba(0, 240, 255, 0.05);
        transition: all 0.3s ease;
        overflow: hidden;
    }

    /* Cybernetic Corner Brackets */
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 12px; height: 12px;
        border-top: 2px solid var(--neon-cyan);
        border-right: 2px solid var(--neon-cyan);
    }

    [data-testid="stMetric"]::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0;
        width: 12px; height: 12px;
        border-bottom: 2px solid var(--neon-cyan);
        border-left: 2px solid var(--neon-cyan);
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--border-glow) !important;
        transform: translateY(-3px);
        box-shadow: 0 15px 35px -10px rgba(0, 240, 255, 0.3), inset 0 0 20px rgba(0, 240, 255, 0.1);
    }

    div[data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #ffffff !important;
        text-shadow: 0 0 12px rgba(0, 240, 255, 0.5);
    }

    [data-testid="stMetricLabel"] {
        font-family: 'Share Tech Mono', monospace;
        color: var(--text-muted) !important;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* CUSTOM MACHINERY HIGH-TECH SLIDER */
    .stSlider {
        padding: 1rem 0;
    }

    .stSlider label {
        font-family: 'Share Tech Mono', monospace ! grand;
        color: var(--neon-cyan) !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.9rem !important;
    }

    /* Slider Track */
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: var(--void-black) !important;
        border: 2px solid var(--neon-cyan) !important;
        box-shadow: 0 0 12px var(--neon-cyan), inset 0 0 8px var(--neon-cyan) !important;
        height: 22px !important;
        width: 22px !important;
        border-radius: 4px !important; /* Industrial square/hex aesthetic */
    }

    .stSlider [data-baseweb="slider"] div[role="slider"]::after {
        content: '';
        display: block;
        width: 6px;
        height: 6px;
        background: #fff;
        margin: 6px auto;
        border-radius: 1px;
    }

    /* Inner bar filled */
    .stSlider [data-baseweb="slider"] div > div:nth-child(1) {
        background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple)) !important;
        height: 8px !important;
        border-radius: 4px !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
    }

    /* Inner bar track background */
    .stSlider [data-baseweb="slider"] div > div {
        background: rgba(255, 255, 255, 0.08);
        height: 8px !important;
        border-radius: 4px;
    }

    /* Industrial Action Buttons */
    .stButton > button {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        border-radius: 4px !important;
        color: var(--void-black) !important;
        background: var(--neon-cyan) !important;
        border: 1px solid var(--neon-cyan) !important;
        padding: 0.65rem 1.6rem !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.4) !important;
        transition: all 0.25s ease-in-out !important;
    }

    .stButton > button:hover {
        background: #ffffff !important;
        border-color: #ffffff !important;
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.8) !important;
        transform: scale(1.02) translateY(-2px) !important;
    }

    /* Download Buttons Secondary */
    .stDownloadButton > button {
        font-family: 'Share Tech Mono', monospace !important;
        border-radius: 4px !important;
        background: rgba(0, 240, 255, 0.05) !important;
        border: 1px solid var(--border-cyber) !important;
        color: var(--neon-cyan) !important;
        transition: all 0.25s ease !important;
    }

    .stDownloadButton > button:hover {
        background: rgba(0, 240, 255, 0.2) !important;
        border-color: var(--neon-cyan) !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.3) !important;
    }

    /* Sidebar Mechanical Dashboard */
    [data-testid="stSidebar"] {
        background: var(--machinery-bg) !important;
        border-right: 1px solid var(--border-cyber) !important;
        box-shadow: 5px 0 25px rgba(0, 0, 0, 0.8);
    }

    [data-testid="stSidebar"] h1 {
        font-family: 'Orbitron', sans-serif;
        color: var(--neon-cyan);
        font-size: 1.3rem;
        letter-spacing: 0.05em;
    }

    /* Form Inputs and UI Elements */
    .stTextInput input, .stTextArea textarea, .stNumberInput input, [data-baseweb="select"] > div {
        background: var(--machinery-bg) !important;
        border: 1px solid var(--border-cyber) !important;
        border-radius: 4px !important;
        color: var(--text-main) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.05rem !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus, [data-baseweb="select"] > div:focus-within {
        border-color: var(--neon-cyan) !important;
        box-shadow: 0 0 12px rgba(0, 240, 255, 0.4) !important;
    }

    /* Cyber Drag & Drop Area */
    [data-testid="stFileUploader"] section {
        background: rgba(7, 13, 24, 0.6) !important;
        border: 2px dashed var(--border-cyber) !important;
        border-radius: 8px !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stFileUploader"] section:hover {
        border-color: var(--neon-cyan) !important;
        box-shadow: inset 0 0 20px rgba(0, 240, 255, 0.15);
    }

    /* Futuristic Tabs UI */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--machinery-bg);
        padding: 4px;
        border-radius: 6px;
        border: 1px solid var(--border-cyber);
    }

    [data-testid="stTabs"] [data-baseweb="tab"] {
        border-radius: 4px !important;
        color: var(--text-muted);
        font-family: 'Share Tech Mono', monospace;
        padding: 0.4rem 1.2rem;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        background: var(--border-cyber) !important;
        color: var(--neon-cyan) !important;
        border: 1px solid var(--neon-cyan);
    }

    /* Tables & Data frames */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border-radius: 6px !important;
        border: 1px solid var(--border-cyber) !important;
        background: var(--machinery-bg);
    }

    /* Expanders Panel */
    [data-testid="stExpander"] {
        border: 1px solid var(--border-cyber) !important;
        border-radius: 6px !important;
        background: var(--panel-glass) !important;
    }

    /* Login Cyber-Vault Box */
    .login-vault {
        padding: 2.5rem 2rem;
        border-radius: 8px;
        background: var(--machinery-bg);
        border: 1px solid var(--border-cyber);
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.15), inset 0 0 15px rgba(0, 240, 255, 0.05);
        position: relative;
    }

    .login-vault::before {
        content: 'SECURE_ACCESS_TERMINAL';
        position: absolute;
        top: -10px; left: 20px;
        background: var(--void-black);
        padding: 0 8px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.75rem;
        color: var(--neon-cyan);
        border: 1px solid var(--border-cyber);
    }
</style>
""", unsafe_allow_html=True)

# ========== AUTHENTICATION ==========
USERS = {
    "admin":    {"password": "admin123",  "role": "Administrator",
                 "name": "Admin User",
                 "pages": ["🏠 Home", "📄 Document Upload", "👥 Role Matrix",
                          "🧠 Generate + Validate", "✅ Validation Results",
                          "🔄 Policy Impact", "📊 Dashboards",
                          "🔒 Security / Injection", "📈 Reports",
                          "📝 Manual Review", "🔍 Consistency Check"]},
    "reviewer": {"password": "review123", "role": "Reviewer",
                 "name": "Reviewer User",
                 "pages": ["🏠 Home", "👥 Role Matrix", "✅ Validation Results",
                          "🔄 Policy Impact", "📈 Reports",
                          "📝 Manual Review", "🔍 Consistency Check"]},
    "emp001":   {"password": "emp123",    "role": "Employee",
                 "name": "Employee One",
                 "pages": ["🏠 Home", "📄 Document Upload",
                          "🧠 Generate + Validate", "📊 Dashboards"]},
}

if "user" not in st.session_state:
    st.session_state["user"] = None


def show_login():
    st.markdown('<div style="text-align:center; padding-top: 1.5rem;">', unsafe_allow_html=True)
    st.markdown('<p class="machinery-title">⚡ SKILLSPRINT AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="machinery-subtitle">OnboardVerse Engine // Dual-Pipeline AI System</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-vault">', unsafe_allow_html=True)
        st.subheader("🔐 Authenticate Core")
        with st.form("login_form"):
            username = st.text_input("Operator Username", placeholder="e.g. admin")
            password = st.text_input("Security Clearance", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("INITIALIZE SESSION", use_container_width=True, type="primary")

        if submitted:
            user_rec = USERS.get(username.strip().lower())
            if user_rec and user_rec["password"] == password:
                st.session_state["user"] = {
                    "username": username.strip().lower(),
                    "role": user_rec["role"],
                    "name": user_rec["name"],
                    "pages": user_rec["pages"],
                }
                st.rerun()
            else:
                st.error("❌ Clearance Denied: Invalid Credentials")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("⚙️ **System Operator Profiles:**")
        st.caption("🔴 Administrator: `admin` / `admin123`")
        st.caption("🟡 Reviewer: `reviewer` / `review123`")
        st.caption("🟢 Employee: `emp001` / `emp123`")
        st.markdown('</div>', unsafe_allow_html=True)


if st.session_state["user"] is None:
    show_login()
    st.stop()

# ========== AUTHENTICATED APP ==========
user = st.session_state["user"]

# Load Role Matrix once
@st.cache_data
def load_matrix():
    path = ROOT / "data" / "role_matrix" / "nexusfintech_matrix.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)

MATRIX = load_matrix()
KNOWN_DOC_IDS = {r["source_document"] for r in MATRIX}

# Sidebar (RBAC-aware)
with st.sidebar:
    st.title("⚡ SKILLSPRINT AI")
    st.caption("SYSTEM OPERATIONAL // V2.4")
    st.markdown("---")
    st.markdown(f"**OPERATOR:** `{user['name']}`")
    st.caption(f"CLEARANCE: **{user['role']}**")
    st.divider()

    page = st.radio("System Control", user["pages"], label_visibility="collapsed")

    st.divider()
    if st.button("🚪 Terminate Session", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["last_plan"] = None
        st.session_state["last_report"] = None
        st.rerun()
    st.caption(f"ENGINE: {settings.GENAI_PROVIDER}")

# ========== PAGES ==========

if page == "🏠 Home":
    st.markdown('<p class="machinery-title">SKILLSPRINT AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="machinery-subtitle">Autonomous Onboarding Architecture // Dual-Pipeline Engine</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Roles In System", "10")
    c2.metric("Matrix Rules", len(MATRIX))
    c3.metric("Mandatory Requirements", sum(1 for r in MATRIX if r["mandatory"]))
    c4.metric("Target Fidelity", "100%")

    st.markdown("---")
    st.markdown("""
    ### System Architecture & Pipeline Operations
    | Pipeline Node | Core Functionality | Underlying Tech Stack |
    | :--- | :--- | :--- |
    | **Pipeline 1** | Generates tailored onboarding plan | GenAI (Gemini / OpenAI) + Pydantic |
    | **Pipeline 2** | Deterministic non-LLM validation | Pure Python Structural Engine |

    #### Machine Security & Execution Controls
    - Strict document mapping requirement (`source_document_id` + `source_section_id`).
    - Deterministic Coverage Metric = `Covered Mandatory / Total Mandatory × 100`.
    - Unstructured GenAI responses are instantly discarded by validator.
    - Input documents processed isolated as raw payloads to prevent prompt injections.
    """)
    st.success("Target Enterprise: **NexusFintech Pvt. Ltd.**")

elif page == "📄 Document Upload":
    st.header("Document Ingestion & Parsing Node")
    st.caption("Accepted File Types: PDF, DOCX")

    uploaded = st.file_uploader("Upload document sources for processing", type=["pdf", "docx"], accept_multiple_files=True)

    if uploaded:
        for file in uploaded:
            valid, msg = validate_file(file.name, file.getvalue())
            if not valid:
                st.error(f"{file.name}: {msg}")
                continue
            path = save_upload(file.name, file.getvalue())
            st.success(f"Ingested → {path}")

            try:
                text_preview = file.getvalue().decode("utf-8", errors="ignore")[:3000]
            except Exception:
                text_preview = ""
            suspicious, patterns = scan_for_injection(text_preview)
            if suspicious:
                st.warning(f"⚠️ Security Exception: Potential Prompt Injection found in {file.name}: {patterns}")

            with st.spinner("Processing & Segmenting Document..."):
                try:
                    result = parse_document(path)
                    st.json({
                        "document_id": result["document_id"],
                        "version": result["version"],
                        "chunks": result["chunk_count"],
                        "file_type": result["file_type"]
                    })
                    if "parsed_docs" not in st.session_state:
                        st.session_state["parsed_docs"] = []
                    st.session_state["parsed_docs"].append(result)
                    with st.expander("Inspect Chunk Segments"):
                        st.write(result["chunks"][:2])
                except Exception as e:
                    st.error(str(e))

    st.markdown("### Pre-Loaded Local Samples")
    st.code("data/sample_documents/text_versions/")

elif page == "👥 Role Matrix":
    st.header("Role Requirement Ground Truth Matrix")
    st.info("Pipeline 2 Reference Ruleset. Non-GenAI verified ground truth matrix.")

    roles = sorted(set(r["role"] for r in MATRIX))
    selected = st.multiselect("Filter matrix rules by operational role", roles, default=roles[:3])

    filtered = [r for r in MATRIX if r["role"] in selected]
    st.dataframe(filtered, use_container_width=True)
    st.caption(f"Displaying {len(filtered)} of {len(MATRIX)} matrix records")

elif page == "🧠 Generate + Validate":
    st.header("Dual-Pipeline Processing Console")

    col_a, col_b = st.columns(2)
    with col_a:
        role = st.selectbox("Select Target Employee Role", sorted(set(r["role"] for r in MATRIX)))
        dept = st.selectbox("Department", ["Customer Experience", "Finance", "Sales", "HR", "Technology", "Operations", "Marketing", "Data"])
    
    with col_b:
        exp = st.selectbox("Experience Tier", ["Beginner", "Intermediate", "Advanced"])
        # Custom Machinery Slider Added
        simulation_intensity = st.slider("Pipeline Execution Precision Level", min_value=1, max_value=10, value=8)

    demo_mode = st.checkbox("Enable Simulation / Offline Mock Mode", value=False)

    if st.button("⚡ EXECUTE DUAL PIPELINE", type="primary"):
        with st.spinner("Executing GenAI Pass & Deterministic Verification Pass..."):
            if not demo_mode:
                from src.genai_pipeline.generator import generate_onboarding_plan

                parsed_docs = st.session_state.get("parsed_docs", [])
                if not parsed_docs:
                    st.error("⚠️ Ingest document sources before execution.")
                    st.stop()

                source_chunks = "\n\n".join(
                    f"[{c['document_id']} §{c['section']}]\n{c['text']}"
                    for doc in parsed_docs
                    for c in doc.get("chunks", [])
                )
                role_reqs = [r for r in MATRIX if r["role"] == role]
                matrix_json = json.dumps(role_reqs, indent=2)

                try:
                    plan_dict = generate_onboarding_plan(
                        role=role, department=dept, experience_level=exp,
                        source_chunks=source_chunks, role_matrix=matrix_json,
                        prompt_version="v1",
                    )
                    report = compare_and_report(plan_dict, MATRIX, KNOWN_DOC_IDS, role)
                    st.session_state["last_plan"] = plan_dict
                    st.session_state["last_report"] = report
                    st.success(f"✅ Processing Complete • Status: **{report['final_status']}**")
                except Exception as e:
                    st.error(f"❌ Pipeline Execution Error: {e}")
                    st.stop()
            else:
                mock_plan = {
                    "plan_id": f"PLAN-{role[:3].upper()}-{datetime.now().strftime('%H%M%S')}",
                    "employee_id": "EMP001",
                    "role": role,
                    "department": dept,
                    "experience_level": exp,
                    "generated_at": datetime.now().isoformat(),
                    "prompt_version": "v1",
                    "model_used": "demo-mock",
                    "source_document_versions": list(KNOWN_DOC_IDS),
                    "stages": ["Day 1", "Week 1", "Week 2", "First 30 Days"],
                    "modules": []
                }
                role_reqs = [r for r in MATRIX if r["role"] == role]
                for i, req in enumerate(role_reqs[:8]):
                    mod = {
                        "module_id": req["requirement_id"],
                        "module_title": req["policy_requirement"] or req["process_requirement"] or f"Module {i+1}",
                        "purpose": f"Ensure compliance with {req['source_document']}",
                        "learning_objectives": [{"objective": f"Understand {req['competency']}", "measurable": True}],
                        "key_concepts": [req["competency"]],
                        "required_source_documents": [req["source_document"]],
                        "source_document_id": req["source_document"],
                        "source_section_id": req["source_section"],
                        "estimated_duration_minutes": 25,
                        "learning_activities": ["Read policy section", "Complete quiz"],
                        "tasks": [{
                            "task_id": f"T-{req['requirement_id']}",
                            "description": req["process_requirement"] or "Complete the required reading",
                            "expected_outcome": "Acknowledged and assessed",
                            "source_document_id": req["source_document"],
                            "source_section_id": req["source_section"],
                            "difficulty": "Beginner",
                            "due_stage": req["due_stage"],
                            "mandatory": req["mandatory"]
                        }],
                        "checklist": [],
                        "quiz": [],
                        "assessment_rubric": [],
                        "mandatory": req["mandatory"],
                        "priority": req["priority"],
                        "due_stage": req["due_stage"],
                        "prerequisites": []
                    }
                    mock_plan["modules"].append(mod)

                report = compare_and_report(mock_plan, MATRIX, KNOWN_DOC_IDS, role)
                st.session_state["last_plan"] = mock_plan
                st.session_state["last_report"] = report
                st.success(f"Simulation Complete • Status: **{report['final_status']}**")

            try:
                save_plan_to_mongo(st.session_state["last_plan"], report)
            except Exception as e:
                print(f"Warning: Mongo persistence failed: {e}")

            if "last_report" in st.session_state:
                report = st.session_state["last_report"]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Coverage Metric", f"{report['coverage_score']}%")
                col2.metric("Traceability Metric", f"{report['traceability_score']}%")
                col3.metric("Missing Count", report["missing_count"])
                col4.metric("Hallucinations", report["hallucination_count"])

                with st.expander("🔍 Detailed Comparison Diagnostics", expanded=True):
                    st.json(report)

                with st.expander("📑 Generated Plan JSON Structure"):
                    st.json(st.session_state["last_plan"])

elif page == "✅ Validation Results":
    st.header("Validation Engine Results")
    if "last_report" in st.session_state:
        report = st.session_state["last_report"]
        st.metric("Final Verification Status", report["final_status"])
        st.metric("Coverage Score", f"{report['coverage_score']}%")
        st.metric("Traceability Score", f"{report['traceability_score']}%")
        st.dataframe(report["detailed_comparison"], use_container_width=True)
    else:
        st.info("Execute pipeline pass first in 🧠 Generate + Validate.")

elif page == "🔄 Policy Impact":
    st.header("Selective Plan Regeneration")
    from src.python_validation.impact_analysis import find_affected, selective_regenerate_plan

    if "last_plan" not in st.session_state:
        st.warning("Generate plan first before performing impact analysis.")
    else:
        plan = st.session_state["last_plan"]
        docs = sorted({m["source_document_id"] for m in plan["modules"]})
        changed = st.selectbox("Select Modified Target Policy Document", docs)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Run Impact Analysis"):
                impact = find_affected(plan, changed)
                st.json(impact)
                if impact["total_affected"]:
                    st.warning(f"Impact Alert: {impact['total_affected']} module(s) require regeneration.")
                else:
                    st.success("Impact Scan Complete: No dependent modules affected.")
        with col2:
            if st.button("⚡ Regenerate Affected Modules"):
                role_reqs = [r for r in MATRIX if r["role"] == plan["role"]]
                replacements = []
                for r in role_reqs[:3]:
                    replacements.append({
                        "module_id": r["requirement_id"],
                        "module_title": f"[REGENERATED] {r['policy_requirement']}",
                        "purpose": f"Updated per new {changed}",
                        "learning_objectives": [{"objective": r["competency"], "measurable": True}],
                        "key_concepts": [r["competency"]],
                        "required_source_documents": [r["source_document"]],
                        "source_document_id": r["source_document"],
                        "source_section_id": r["source_section"],
                        "estimated_duration_minutes": 20,
                        "learning_activities": ["Review updated policy"],
                        "tasks": [],
                        "checklist": [],
                        "quiz": [],
                        "assessment_rubric": [],
                        "mandatory": r["mandatory"],
                        "priority": r["priority"],
                        "due_stage": r["due_stage"],
                        "prerequisites": [],
                    })
                new_plan = selective_regenerate_plan(plan, changed, replacements)
                st.session_state["last_plan"] = new_plan
                st.success(f"Regenerated {len(new_plan['regenerated_module_ids'])} affected modules.")
                st.json({
                    "regenerated_module_ids": new_plan["regenerated_module_ids"],
                    "last_regenerated": new_plan["last_regenerated"],
                    "total_modules": len(new_plan["modules"]),
                })

elif page == "📊 Dashboards":
    st.header("System Intelligence Dashboards")

    stats = get_admin_stats_from_mongo()
    tab1, tab2 = st.tabs(["📊 Administrative Metrics", "👤 Employee Telemetry"])

    with tab1:
        st.subheader("System Compliance Telemetry")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Generated Plans", stats["total_plans"])
        c2.metric("Verified Compliant", stats["verified_plans"])
        c3.metric("Avg Coverage Metric", f"{stats['avg_coverage']}%")
        c4.metric("Avg Traceability Metric", f"{stats['avg_traceability']}%")

        c5, c6, c7 = st.columns(3)
        c5.metric("Warnings Flagged", stats.get("warned_plans", 0))
        c6.metric("Failed Validations", stats.get("failed_plans", 0))
        c7.metric("Active Employee Accounts", stats.get("employees", 0))

        st.markdown("---")
        st.subheader("Recent Onboarding Plans")
        recent = get_recent_plans_from_mongo(10)
        if recent:
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No persisted plan telemetry available.")

        st.markdown("---")
        st.subheader("Role Coverage Distribution")
        by_role = get_plans_by_role_from_mongo()
        if by_role:
            st.dataframe(by_role, use_container_width=True)
        else:
            st.info("No distribution records logged.")

    with tab2:
        st.subheader("Individual Progress Dashboard")
        st.write("• Task milestones tracking")
        st.write("• Document learning verification")
        st.write("• Knowledge check score history")
        st.info("Select active employee record to view progression.")

elif page == "🔒 Security / Injection":
    st.header("Prompt Injection Threat Scanner")
    st.markdown(build_safe_system_instruction())

    test_text = st.text_area("Paste document text snippet to run threat scan", height=150)
    if st.button("🛡️ Execute Threat Diagnostic"):
        suspicious, patterns = scan_for_injection(test_text)
        if suspicious:
            st.error(f"🚨 Security Alert: Adversarial Injection detected: {patterns}")
        else:
            st.success("✅ Clean Scan: No malicious vectors found.")

    st.markdown("### Adversarial Sample Data")
    st.code("data/adversarial/prompt_injection_test.txt")

elif page == "📈 Reports":
    st.header("Report Exporter Console")
    from src.reports.export import to_csv, to_excel, to_pdf

    if "last_report" not in st.session_state:
        st.info("Generate an onboarding plan to output report files.")
    else:
        r = st.session_state["last_report"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Final Status", r.get("final_status", "N/A"))
        col2.metric("Coverage Score", f"{r.get('coverage_score', 0)}%")
        col3.metric("Traceability Score", f"{r.get('traceability_score', 0)}%")
        col4.metric("Missing Count", r.get("missing_count", 0))

        st.markdown("---")
        st.subheader("Download Formatted Reports")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.download_button("📄 JSON Report",
                data=json.dumps(r, indent=2),
                file_name="report.json", mime="application/json",
                use_container_width=True)
        with c2:
            st.download_button("📊 CSV Export",
                data=to_csv(r), file_name="report.csv", mime="text/csv",
                use_container_width=True)
        with c3:
            st.download_button("📗 Excel File",
                data=to_excel(r), file_name="report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        with c4:
            st.download_button("📕 PDF Document",
                data=to_pdf(r), file_name="report.pdf", mime="application/pdf",
                use_container_width=True)

        st.markdown("---")
        with st.expander("Detailed Audit Data", expanded=False):
            st.dataframe(r.get("detailed_comparison", []), use_container_width=True)

elif page == "📝 Manual Review":
    st.header("Human-in-the-Loop Governance Queue")
    st.caption("Review flagged items (SRS §48-49)")

    if "review_queue" not in st.session_state:
        st.session_state["review_queue"] = []

    if "last_report" in st.session_state:
        if st.button("🔄 Sync Review Queue"):
            st.session_state["review_queue"] = flag_items_from_report(
                st.session_state["last_report"]
            )
            st.success(f"Added {len(st.session_state['review_queue'])} items to review state.")
    else:
        st.info("Generate plan to process review items.")

    if not st.session_state["review_queue"]:
        st.info("No items in review queue.")
    else:
        st.write(f"**{len(st.session_state['review_queue'])} items in queue**")
        for i, item in enumerate(st.session_state["review_queue"]):
            with st.expander(f"[{item['status']}] {item['queue_id']} — {item['reason']}"):
                st.write(f"**Target Requirement:** {item['requirement_id']}")
                st.write(f"**Reason:** {item['reason']}")
                st.json(item.get("content", {}))

                if item["status"] == "Pending Review":
                    comment = st.text_input("Reviewer Comment", key=f"cmt_{i}")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        if st.button("✅ Approve", key=f"ap_{i}"):
                            st.session_state["review_queue"][i] = apply_decision(
                                item, "Approved", user["username"], comment)
                            st.rerun()
                    with c2:
                        if st.button("❌ Reject", key=f"rj_{i}"):
                            st.session_state["review_queue"][i] = apply_decision(
                                item, "Rejected", user["username"], comment)
                            st.rerun()
                    with c3:
                        if st.button("✏️ Edit", key=f"ed_{i}"):
                            st.session_state["review_queue"][i] = apply_decision(
                                item, "Edited", user["username"], comment)
                            st.rerun()
                    with c4:
                        if st.button("🔁 Regenerate", key=f"rg_{i}"):
                            st.session_state["review_queue"][i] = apply_decision(
                                item, "Regenerated", user["username"], comment)
                            st.rerun()
                else:
                    st.success(f"Decision: **{item['decision']}** by {item['reviewer']}")
                    if item.get("comment"):
                        st.write(f"Comment: {item['comment']}")

                    if st.button("💾 Persist Audit Trail", key=f"au_{i}"):
                        try:
                            from src.database.models import AuditLog, SessionLocal
                            db = SessionLocal()
                            db.add(AuditLog(**build_audit_record(item)))
                            db.commit()
                            db.close()
                            st.success("Audit Log Saved.")
                        except Exception as e:
                            st.error(f"Audit log write failed: {e}")

elif page == "🔍 Consistency Check":
    st.header("GenAI Nondeterminism Diagnostic Pass")
    st.caption("Dual Generation Structural Comparison Pass (SRS §44-45)")

    if "last_plan" not in st.session_state:
        st.warning("Generate baseline plan before executing comparison.")
    else:
        plan1 = st.session_state["last_plan"]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Baseline Pass A")
            st.json({
                "plan_id": plan1.get("plan_id"),
                "modules": len(plan1.get("modules", [])),
                "model_used": plan1.get("model_used"),
            })

        with col2:
            st.subheader("Comparative Pass B")
            if st.button("⚡ Run Secondary Generation Pass"):
                from src.genai_pipeline.generator import generate_onboarding_plan
                parsed_docs = st.session_state.get("parsed_docs", [])
                if not parsed_docs:
                    st.error("Upload documents first.")
                else:
                    source_chunks = "\n\n".join(
                        f"[{c['document_id']} §{c['section']}]\n{c['text']}"
                        for doc in parsed_docs
                        for c in doc.get("chunks", [])
                    )
                    role_reqs = [r for r in MATRIX if r["role"] == plan1.get("role")]
                    try:
                        plan2 = generate_onboarding_plan(
                            role=plan1.get("role"),
                            department=plan1.get("department"),
                            experience_level=plan1.get("experience_level"),
                            source_chunks=source_chunks,
                            role_matrix=json.dumps(role_reqs, indent=2),
                            prompt_version="v1",
                        )
                        st.session_state["plan2"] = plan2
                        st.success("Secondary generation pass complete.")
                    except Exception as e:
                        st.error(f"Generation error: {e}")

        if "plan2" in st.session_state:
            st.markdown("---")
            st.subheader("Consistency Diagnostic Analysis")
            result = compare_consistency(plan1, st.session_state["plan2"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Consistency Rating", f"{result['overall_consistency_score']}%")
            c2.metric("Verdict", result["final_verdict"])
            c3.metric("Flagged Differences", len(result["flagged_differences"]))
            st.json(result)

            if result["overall_consistency_score"] >= 85:
                st.success("✅ Output exhibits high structural consistency.")
            elif result["overall_consistency_score"] >= 70:
                st.warning("⚠️ Minor structural variance detected.")
            else:
                st.error("❌ High nondeterministic variance detected.")

        st.markdown("---")
        st.subheader("Internal Logical Contradictions Diagnostic")
        contradictions = detect_all_contradictions(plan1)
        if contradictions:
            for c in contradictions:
                st.error(f"⚠️ {c}")
        else:
            st.success("✅ No internal logical contradictions detected.")

st.markdown("---")
st.caption("SkillSprint AI • Cybernetic Industrial AI Architecture • NexusFintech Systems Engine")