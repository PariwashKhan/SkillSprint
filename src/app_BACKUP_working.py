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
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root{
        --void:#05070d;
        --surface:#0d1220;
        --surface-raised:#121a2e;
        --border:rgba(148,163,255,0.14);
        --border-strong:rgba(148,163,255,0.28);
        --blue:#5b7cfa;
        --violet:#9b6bff;
        --magenta:#ff5fa8;
        --mint:#34e0a1;
        --amber:#ffb86b;
        --coral:#ff5c72;
        --text:#eef1fb;
        --text-dim:#8b93b8;
        --grad-signal: linear-gradient(115deg,var(--blue),var(--violet) 55%,var(--magenta));
    }

    html, body, [class*="css"], [data-testid="stAppViewContainer"]{
        font-family:'Inter',sans-serif;
        color:var(--text);
    }
    [data-testid="stAppViewContainer"]{
        background:
            radial-gradient(1100px 500px at 12% -10%, rgba(91,124,250,0.16), transparent 60%),
            radial-gradient(900px 500px at 100% 0%, rgba(255,95,168,0.10), transparent 55%),
            var(--void);
    }
    [data-testid="stHeader"]{ background:transparent; }

    .main-header{
        font-family:'Outfit',sans-serif;
        font-size:2.6rem;
        font-weight:800;
        letter-spacing:-0.01em;
        background:var(--grad-signal);
        background-size:200% 200%;
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
        animation:auroraShift 14s ease-in-out infinite;
        margin-bottom:0.25rem;
    }
    @keyframes auroraShift{
        0%,100%{background-position:0% 50%;}
        50%{background-position:100% 50%;}
    }
    @media (prefers-reduced-motion: reduce){
        .main-header{ animation:none; }
    }

    h1,h2,h3{ font-family:'Outfit',sans-serif; font-weight:700; letter-spacing:-0.01em; }

    .glass-card{
        background:linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border:1px solid var(--border);
        border-radius:16px;
        padding:1.25rem 1.4rem;
        transition:transform .25s ease, border-color .25s ease, box-shadow .25s ease;
    }
    .glass-card:hover{
        transform:translateY(-3px);
        border-color:var(--border-strong);
        box-shadow:0 16px 40px -20px rgba(91,124,250,0.45);
    }

    [data-testid="stMetric"]{
        background:linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.015));
        backdrop-filter: blur(14px);
        border:1px solid var(--border);
        border-radius:14px;
        padding:1rem 1.1rem 0.9rem;
        transition:transform .2s ease, border-color .2s ease, box-shadow .2s ease;
    }
    [data-testid="stMetric"]:hover{
        transform:translateY(-2px);
        border-color:rgba(155,107,255,0.45);
        box-shadow:0 14px 34px -18px rgba(155,107,255,0.5);
    }
    div[data-testid="stMetricValue"]{
        font-family:'Outfit',sans-serif;
        font-size:1.9rem;
        font-weight:700;
        background:var(--grad-signal);
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
    }
    [data-testid="stMetricLabel"]{
        color:var(--text-dim);
        font-size:0.82rem;
        font-weight:500;
    }
    [data-testid="stMetricDelta"] svg{ vertical-align:middle; }

    .stButton>button{
        border-radius:10px;
        font-weight:600;
        font-family:'Inter',sans-serif;
        color:#fff;
        background:var(--grad-signal);
        background-size:160% 160%;
        border:none;
        padding:0.55rem 1.3rem;
        box-shadow:0 8px 24px -10px rgba(91,124,250,0.55);
        transition:transform .18s ease, box-shadow .18s ease, background-position .4s ease;
    }
    .stButton>button:hover{
        transform:translateY(-2px);
        background-position:100% 0%;
        box-shadow:0 12px 30px -10px rgba(155,107,255,0.65);
    }
    .stButton>button:active{ transform:translateY(0); }
    .stButton>button:focus-visible{
        outline:2px solid var(--blue);
        outline-offset:2px;
    }
    .stDownloadButton>button{
        border-radius:10px;
        font-weight:600;
        background:rgba(255,255,255,0.05);
        border:1px solid var(--border-strong);
        color:var(--text);
        transition:border-color .2s ease, transform .18s ease;
    }
    .stDownloadButton>button:hover{
        border-color:var(--blue);
        transform:translateY(-2px);
    }

    [data-testid="stSidebar"]{
        background:linear-gradient(180deg, #0a0f1e 0%, #0d1428 60%, #0a0f1e 100%);
        border-right:1px solid var(--border);
    }
    [data-testid="stSidebar"] .stRadio label, [data-testid="stSidebar"] p{
        color:var(--text-dim);
    }
    [data-testid="stSidebarNav"] a{
        border-radius:8px;
        transition:background .18s ease, color .18s ease;
    }
    [data-testid="stSidebarNav"] a:hover{
        background:rgba(91,124,250,0.12);
        color:var(--text);
    }
    [data-testid="stSidebarNav"] a[aria-current="page"]{
        background:rgba(91,124,250,0.16);
        border-left:2px solid var(--blue);
        box-shadow:inset 0 0 14px rgba(91,124,250,0.18);
    }

    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stNumberInput input,
    .stDateInput input{
        background:rgba(255,255,255,0.04) !important;
        border:1px solid var(--border) !important;
        border-radius:10px !important;
        color:var(--text) !important;
        transition:border-color .2s ease, box-shadow .2s ease;
    }
    .stTextInput>div>div>input:focus,
    .stTextArea textarea:focus{
        border-color:var(--blue) !important;
        box-shadow:0 0 0 3px rgba(91,124,250,0.22) !important;
    }
    [data-baseweb="select"]>div{
        background:rgba(255,255,255,0.04) !important;
        border-radius:10px !important;
        border-color:var(--border) !important;
    }

    [data-testid="stFileUploader"] section{
        background:rgba(255,255,255,0.03);
        border:1.5px dashed var(--border-strong);
        border-radius:14px;
        padding:1.4rem;
        transition:border-color .2s ease, background .2s ease;
    }
    [data-testid="stFileUploader"] section:hover{
        border-color:var(--blue);
        background:rgba(91,124,250,0.06);
    }

    [data-testid="stExpander"]{
        border:1px solid var(--border);
        border-radius:12px;
        background:rgba(255,255,255,0.02);
        overflow:hidden;
    }
    [data-testid="stExpander"] summary{
        font-weight:600;
        transition:color .18s ease;
    }
    [data-testid="stExpander"] summary:hover{ color:var(--blue); }
    [data-testid="stExpander"] summary svg{ transition:transform .25s ease; }

    [data-testid="stTabs"] [data-baseweb="tab-list"]{
        gap:6px;
        background:rgba(255,255,255,0.03);
        padding:5px;
        border-radius:999px;
        border:1px solid var(--border);
    }
    [data-testid="stTabs"] [data-baseweb="tab"]{
        border-radius:999px !important;
        color:var(--text-dim);
        font-weight:600;
        padding:0.4rem 1rem;
        transition:color .18s ease, background .18s ease;
    }
    [data-testid="stTabs"] [aria-selected="true"]{
        background:var(--grad-signal) !important;
        color:#fff !important;
    }

    [data-testid="stDataFrame"], [data-testid="stTable"]{
        border-radius:12px;
        overflow:hidden;
        border:1px solid var(--border);
    }
    [data-testid="stDataFrame"] thead tr th{
        background:rgba(91,124,250,0.10) !important;
        color:var(--text) !important;
        font-weight:600 !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover{
        background:rgba(91,124,250,0.06) !important;
    }

    ::-webkit-scrollbar{ width:9px; height:9px; }
    ::-webkit-scrollbar-track{ background:var(--void); }
    ::-webkit-scrollbar-thumb{
        background:var(--grad-signal);
        border-radius:999px;
    }

    [data-testid="stAlert"]{
        border-radius:12px;
        backdrop-filter: blur(10px);
        border:1px solid transparent;
    }

    .login-box{
        padding:2.2rem 2rem;
        border-radius:22px;
        max-width:420px;
        margin:3rem auto 0;
        background:linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border:1px solid transparent;
        background-clip:padding-box;
        position:relative;
        box-shadow:0 30px 60px -30px rgba(91,124,250,0.35);
    }
    .login-box::before{
        content:"";
        position:absolute;
        inset:-1px;
        border-radius:22px;
        padding:1px;
        background:var(--grad-signal);
        -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite:xor;
        mask-composite:exclude;
        opacity:0.55;
        pointer-events:none;
    }
    .login-box .stButton>button{ width:100%; margin-top:0.5rem; }
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
    st.markdown('<p class="main-header" style="text-align:center;">🚀 SkillSprint AI</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#94a3b8; margin-top:-10px;">OnboardVerse • Dual Pipeline • Secure Access</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader("🔐 Sign In")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

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
                st.error("❌ Invalid username or password")

        st.markdown("---")
        st.caption("**Demo credentials:**")
        st.caption("🔴 Administrator: `admin` / `admin123`")
        st.caption("🟡 Reviewer: `reviewer` / `review123`")
        st.caption("🟢 Employee: `emp001` / `emp123`")


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
    st.title("🚀 SkillSprint AI")
    st.caption("OnboardVerse • Dual Pipeline")
    st.markdown("---")
    st.markdown(f"**👤 {user['name']}**")
    st.caption(f"Role: **{user['role']}**")
    st.divider()

    page = st.radio("Go to", user["pages"], label_visibility="collapsed")

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["last_plan"] = None
        st.session_state["last_report"] = None
        st.rerun()
    st.caption(f"Provider: {settings.GENAI_PROVIDER}")

# ========== PAGES ==========

if page == "🏠 Home":
    st.markdown('<p class="main-header">SkillSprint AI</p>', unsafe_allow_html=True)
    st.subheader("Personalized Onboarding with Dual-Pipeline Verification")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Roles Supported", "10")
    c2.metric("Matrix Requirements", len(MATRIX))
    c3.metric("Mandatory Items", sum(1 for r in MATRIX if r["mandatory"]))
    c4.metric("Target Coverage", "100%")

    st.markdown("---")
    st.markdown("""
    ### Architecture
    | Pipeline | Responsibility | Technology |
    |----------|----------------|------------|
    | **Pipeline 1** | Generate structured onboarding plan | GenAI (Gemini / OpenAI) + Pydantic schema |
    | **Pipeline 2** | Independent validation | Pure Python (no GenAI) |

    **Key guarantees**
    - Every mandatory learning item must have source_document_id + source_section_id
    - Coverage Score = Covered Mandatory / Total Mandatory × 100
    - Free-form GenAI text is never accepted as final output
    - Uploaded documents are treated as DATA only (prompt-injection protected)
    """)
    st.success("Company: **NexusFintech Pvt. Ltd.** (unique fictional fintech)")

elif page == "📄 Document Upload":
    st.header("Document Upload & Processing")
    st.caption("Mandatory formats: PDF and DOCX.")

    uploaded = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"], accept_multiple_files=True)

    if uploaded:
        for file in uploaded:
            valid, msg = validate_file(file.name, file.getvalue())
            if not valid:
                st.error(f"{file.name}: {msg}")
                continue
            path = save_upload(file.name, file.getvalue())
            st.success(f"Saved → {path}")

            try:
                text_preview = file.getvalue().decode("utf-8", errors="ignore")[:3000]
            except Exception:
                text_preview = ""
            suspicious, patterns = scan_for_injection(text_preview)
            if suspicious:
                st.warning(f"Possible prompt injection detected in {file.name}: {patterns}")

            with st.spinner("Parsing..."):
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
                    with st.expander("First chunks"):
                        st.write(result["chunks"][:2])
                except Exception as e:
                    st.error(str(e))

    st.markdown("### Sample text documents available")
    st.code("data/sample_documents/text_versions/")

elif page == "👥 Role Matrix":
    st.header("Role Requirement Matrix (Ground Truth)")
    st.info("This matrix is the independent source of truth for Pipeline 2. It is never generated by GenAI.")

    roles = sorted(set(r["role"] for r in MATRIX))
    selected = st.multiselect("Filter by role", roles, default=roles[:3])

    filtered = [r for r in MATRIX if r["role"] in selected]
    st.dataframe(filtered, use_container_width=True)
    st.caption(f"Showing {len(filtered)} of {len(MATRIX)} requirements")

elif page == "🧠 Generate + Validate":
    st.header("Pipeline 1 → Pipeline 2 (Generate + Validate)")

    role = st.selectbox("Select Employee Role", sorted(set(r["role"] for r in MATRIX)))
    dept = st.selectbox("Department", ["Customer Experience", "Finance", "Sales", "HR", "Technology", "Operations", "Marketing", "Data"])
    exp = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced"])

    demo_mode = st.checkbox("Demo Mode (no API key required – uses realistic mock plan)", value=False)

    if st.button("Generate Plan & Run Validation", type="primary"):
        with st.spinner("Running dual pipelines..."):
            if not demo_mode:
                from src.genai_pipeline.generator import generate_onboarding_plan

                parsed_docs = st.session_state.get("parsed_docs", [])
                if not parsed_docs:
                    st.error("⚠️ Upload & parse at least one document first (Document Upload page).")
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
                    st.success(f"✅ Real GenAI generated plan • Status: **{report['final_status']}**")
                except Exception as e:
                    st.error(f"❌ GenAI failed: {e}")
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
                st.success(f"Plan generated (mock) • Status: **{report['final_status']}**")

            try:
                save_plan_to_mongo(st.session_state["last_plan"], report)
            except Exception as e:
                print(f"Warning: could not save plan to MongoDB: {e}")

            if "last_report" in st.session_state:
                report = st.session_state["last_report"]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Coverage Score", f"{report['coverage_score']}%")
                col2.metric("Traceability Score", f"{report['traceability_score']}%")
                col3.metric("Missing", report["missing_count"])
                col4.metric("Hallucinations", report["hallucination_count"])

                with st.expander("Full Comparison Report", expanded=True):
                    st.json(report)

                with st.expander("Generated Plan (structured JSON)"):
                    st.json(st.session_state["last_plan"])

elif page == "✅ Validation Results":
    st.header("Last Validation Results")
    if "last_report" in st.session_state:
        report = st.session_state["last_report"]
        st.metric("Final Status", report["final_status"])
        st.metric("Coverage", f"{report['coverage_score']}%")
        st.metric("Traceability", f"{report['traceability_score']}%")
        st.dataframe(report["detailed_comparison"], use_container_width=True)
    else:
        st.info("Run Generate + Validate first.")

elif page == "🔄 Policy Impact":
    st.header("Policy Update → Impact Analysis → Selective Regeneration")
    from src.python_validation.impact_analysis import find_affected, selective_regenerate_plan

    if "last_plan" not in st.session_state:
        st.warning("Generate a plan first (go to 🧠 Generate + Validate).")
    else:
        plan = st.session_state["last_plan"]
        docs = sorted({m["source_document_id"] for m in plan["modules"]})
        changed = st.selectbox("Which document was updated?", docs)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Run Impact Analysis"):
                impact = find_affected(plan, changed)
                st.json(impact)
                if impact["total_affected"]:
                    st.warning(f"{impact['total_affected']} items will be regenerated.")
                else:
                    st.success("No affected items. Full plan intact.")
        with col2:
            if st.button("Selective Regenerate"):
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
                st.success(f"Regenerated {len(new_plan['regenerated_module_ids'])} modules.")
                st.json({
                    "regenerated_module_ids": new_plan["regenerated_module_ids"],
                    "last_regenerated": new_plan["last_regenerated"],
                    "total_modules": len(new_plan["modules"]),
                })

elif page == "📊 Dashboards":
    st.header("Dashboards")

    stats = get_admin_stats_from_mongo()
    tab1, tab2 = st.tabs(["Administrator", "Employee"])

    with tab1:
        st.subheader("Administrator Dashboard")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Plans", stats["total_plans"])
        c2.metric("Verified", stats["verified_plans"])
        c3.metric("Avg Coverage", f"{stats['avg_coverage']}%")
        c4.metric("Avg Traceability", f"{stats['avg_traceability']}%")

        c5, c6, c7 = st.columns(3)
        c5.metric("With Warnings", stats.get("warned_plans", 0))
        c6.metric("Failed Validation", stats.get("failed_plans", 0))
        c7.metric("Employees", stats.get("employees", 0))

        st.markdown("---")
        st.subheader("Recent Onboarding Plans")
        recent = get_recent_plans_from_mongo(10)
        if recent:
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No plans generated yet. Go to 🧠 Generate + Validate to create one.")

        st.markdown("---")
        st.subheader("Coverage by Role")
        by_role = get_plans_by_role_from_mongo()
        if by_role:
            st.dataframe(by_role, use_container_width=True)
        else:
            st.info("No data yet.")

    with tab2:
        st.subheader("Employee Learning Dashboard")
        st.write("• Onboarding progress")
        st.write("• Assigned modules & tasks")
        st.write("• Quiz scores & milestones")
        st.info("Employee-specific progress tracking appears here once an employee ID is selected.")

elif page == "🔒 Security / Injection":
    st.header("Prompt Injection Protection")
    st.markdown(build_safe_system_instruction())

    test_text = st.text_area("Paste document text to scan", height=150)
    if st.button("Scan for Injection"):
        suspicious, patterns = scan_for_injection(test_text)
        if suspicious:
            st.error(f"Suspicious patterns found: {patterns}")
        else:
            st.success("No injection patterns detected.")

    st.markdown("### Built-in adversarial test file")
    st.code("data/adversarial/prompt_injection_test.txt")

elif page == "📈 Reports":
    st.header("Reports & Export")
    from src.reports.export import to_csv, to_excel, to_pdf

    if "last_report" not in st.session_state:
        st.info("Run Generate + Validate first to produce a report.")
    else:
        r = st.session_state["last_report"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Status", r.get("final_status", "N/A"))
        col2.metric("Coverage", f"{r.get('coverage_score', 0)}%")
        col3.metric("Traceability", f"{r.get('traceability_score', 0)}%")
        col4.metric("Missing", r.get("missing_count", 0))

        st.markdown("---")
        st.subheader("Download Report")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.download_button("📄 JSON",
                data=json.dumps(r, indent=2),
                file_name="report.json", mime="application/json",
                use_container_width=True)
        with c2:
            st.download_button("📊 CSV",
                data=to_csv(r), file_name="report.csv", mime="text/csv",
                use_container_width=True)
        with c3:
            st.download_button("📗 Excel",
                data=to_excel(r), file_name="report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        with c4:
            st.download_button("📕 PDF",
                data=to_pdf(r), file_name="report.pdf", mime="application/pdf",
                use_container_width=True)

        st.markdown("---")
        with st.expander("Preview detailed comparison", expanded=False):
            st.dataframe(r.get("detailed_comparison", []), use_container_width=True)

elif page == "📝 Manual Review":
    st.header("Manual Review Queue")
    st.caption("Review flagged content — approve, reject, edit, or regenerate (SRS §48-49)")

    if "review_queue" not in st.session_state:
        st.session_state["review_queue"] = []

    if "last_report" in st.session_state:
        if st.button("🔄 Refresh Queue from Last Report"):
            st.session_state["review_queue"] = flag_items_from_report(
                st.session_state["last_report"]
            )
            st.success(f"Added {len(st.session_state['review_queue'])} items to queue.")
    else:
        st.info("Generate a plan first (🧠 Generate + Validate).")

    if not st.session_state["review_queue"]:
        st.info("No items in review queue.")
    else:
        st.write(f"**{len(st.session_state['review_queue'])} items**")
        for i, item in enumerate(st.session_state["review_queue"]):
            with st.expander(f"[{item['status']}] {item['queue_id']} — {item['reason']}"):
                st.write(f"**Requirement:** {item['requirement_id']}")
                st.write(f"**Reason:** {item['reason']}")
                st.json(item.get("content", {}))

                if item["status"] == "Pending Review":
                    comment = st.text_input("Comment", key=f"cmt_{i}")
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

                    if st.button("💾 Save to Audit Trail", key=f"au_{i}"):
                        try:
                            from src.database.models import AuditLog, SessionLocal
                            db = SessionLocal()
                            db.add(AuditLog(**build_audit_record(item)))
                            db.commit()
                            db.close()
                            st.success("Audit trail saved.")
                        except Exception as e:
                            st.error(f"Audit save failed: {e}")

elif page == "🔍 Consistency Check":
    st.header("GenAI Consistency Check")
    st.caption("Runs the same generation task twice and compares structured output (SRS §44-45)")

    if "last_plan" not in st.session_state:
        st.warning("Generate a plan first (go to 🧠 Generate + Validate).")
    else:
        plan1 = st.session_state["last_plan"]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Plan A (existing)")
            st.json({
                "plan_id": plan1.get("plan_id"),
                "modules": len(plan1.get("modules", [])),
                "model_used": plan1.get("model_used"),
            })

        with col2:
            st.subheader("Plan B (fresh call)")
            if st.button("🚀 Run Second Generation"):
                from src.genai_pipeline.generator import generate_onboarding_plan
                parsed_docs = st.session_state.get("parsed_docs", [])
                if not parsed_docs:
                    st.error("Upload a document first.")
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
                        st.success("Second plan generated.")
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

        if "plan2" in st.session_state:
            st.markdown("---")
            st.subheader("Consistency Report")
            result = compare_consistency(plan1, st.session_state["plan2"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Overall Consistency", f"{result['overall_consistency_score']}%")
            c2.metric("Verdict", result["final_verdict"])
            c3.metric("Flagged Differences", len(result["flagged_differences"]))
            st.json(result)

            if result["overall_consistency_score"] >= 85:
                st.success("✅ Generations are highly consistent.")
            elif result["overall_consistency_score"] >= 70:
                st.warning("⚠️ Minor differences detected.")
            else:
                st.error("❌ Generations differ significantly.")

        st.markdown("---")
        st.subheader("Contradiction Detection")
        contradictions = detect_all_contradictions(plan1)
        if contradictions:
            for c in contradictions:
                st.error(f"⚠️ {c}")
        else:
            st.success("✅ No contradictions detected.")

st.markdown("---")
st.caption("SkillSprint AI • TechWiz 7 • Dual Pipeline • Source-Grounded • NexusFintech")