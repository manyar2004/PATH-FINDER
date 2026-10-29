import os
import streamlit as st
import pandas as pd
from pipeline.run_pipeline import load, run_pipeline
from utils.placement_data import load_students, load_company_history, recommend_companies
from agents.placement_prediction_model import aggregate_company_profiles, predict_placement_chances

st.set_page_config(
    page_title="Path Finder - MCA Placement Guidance",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Light Theme and User-Friendly Styling
st.markdown("""
<style>
    /* Global Light Theme Font & Background */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Main container spacing */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    
    /* Card Container */
    .pf-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Header styling */
    .pf-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.25rem;
    }
    .pf-sub {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    
    /* Pill Badges for Skills */
    .skill-pill {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
        border-radius: 9999px;
        padding: 0.25rem 0.75rem;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 0.2rem 0.25rem;
    }
    
    /* Hero Banner for Top Recommendation */
    .focus-banner {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 1px solid #93C5FD;
        border-left: 6px solid #2563EB;
        border-radius: 10px;
        padding: 1.1rem 1.4rem;
        margin: 1rem 0;
    }
    .focus-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.3rem;
    }
    .focus-desc {
        font-size: 0.92rem;
        color: #1E40AF;
        line-height: 1.4;
    }
    
    /* Day-by-Day Prep Step */
    .prep-step {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        border-left: 4px solid #3B82F6;
    }
    .prep-day {
        font-weight: 700;
        font-size: 0.88rem;
        color: #2563EB;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.2rem;
    }
    .prep-focus {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1E293B;
    }
    .prep-q {
        font-size: 0.88rem;
        color: #475569;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# File Paths
project_root = os.path.dirname(os.path.abspath(__file__))
student_workbook = os.path.join(project_root, "Paychex (1).xlsx")
company_history_pdf = os.path.join(project_root, "DOC-20260801-WA0002..pdf")


@st.cache_data(show_spinner=False)
def load_placement_inputs(student_path, history_path, student_mtime, history_mtime):
    return load_students(student_path), load_company_history(history_path)


try:
    placement_students, company_history = load_placement_inputs(
        student_workbook,
        company_history_pdf,
        os.path.getmtime(student_workbook),
        os.path.getmtime(company_history_pdf),
    )
    cached_company_profiles = aggregate_company_profiles(company_history)
except (OSError, ValueError) as error:
    st.error("Unable to load the student workbook or company-history PDF: " + str(error))
    st.stop()

# Load active placement drives and default history
companies = load("companies.json")
base_history = load("interview_history.json")
STAGES = ["HR", "Technical", "Aptitude", "None (Selected)"]

# App Title & Navigation
st.markdown('<div class="pf-header">🎓 Path Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="pf-sub">Smart Placement Guidance & Preparation Assistant for MCA Students</div>', unsafe_allow_html=True)

# --- Sidebar: Search by USN ---
st.sidebar.header("🔍 Search Student")
if "active_usn" not in st.session_state:
    st.session_state["active_usn"] = ""


def set_demo_student(usn):
    st.session_state["active_usn"] = usn


st.sidebar.write("Lookup any MCA student by USN or select from the college roster.")

student_options = [f"{p['usn']} — {p['name']}" for p in placement_students]
default_dropdown_idx = 0
if st.session_state["active_usn"]:
    for opt_idx, opt in enumerate(student_options, start=1):
        if opt.startswith(st.session_state["active_usn"]):
            default_dropdown_idx = opt_idx
            break

selected_from_dropdown = st.sidebar.selectbox(
    "Choose from MCA roster (110 students)",
    ["-- Select student --"] + student_options,
    index=default_dropdown_idx,
    key="student_dropdown"
)

direct_usn_input = st.sidebar.text_input(
    "Or type USN directly",
    value=st.session_state["active_usn"] if default_dropdown_idx == 0 else "",
    placeholder="e.g. 1BM25MC002",
    key="usn_text_box"
)

# Determine queried USN
if direct_usn_input.strip():
    query_usn = direct_usn_input.strip()
elif selected_from_dropdown != "-- Select student --":
    query_usn = selected_from_dropdown.split(" — ")[0].strip()
else:
    query_usn = ""

# Optional: Past Interview history in sidebar
with st.sidebar.expander("📝 Past Interview History (Optional)", expanded=False):
    st.caption("Add past interviews if you attended previous rounds at service/product companies.")
    past_count = st.number_input("Past interview count", 0, 5, 0)
    user_past_records = []
    for i in range(int(past_count)):
        col1, col2 = st.columns(2)
        ctype = col1.selectbox("Company type", ["Service-based", "Product-based"], key=f"t_{i}")
        stage = col2.selectbox("Result / Exit round", STAGES, key=f"r_{i}")
        user_past_records.append({
            "company_id": f"P{i}",
            "company_name": f"Past company {i+1}",
            "company_type": ctype,
            "rounds_cleared": 0,
            "total_rounds": 0,
            "drop_off_stage": stage
        })

st.sidebar.divider()
st.sidebar.info(
    f"📊 **Database Summary**\n\n"
    f"• **Registered Students:** {len(placement_students)}\n\n"
    f"• **Active Target Companies:** {len(companies)}\n\n"
    f"• **Historical Recruitment Drives:** {len(company_history)}"
)

# --- Main Content Area ---
if not query_usn:
    # Welcome & Quick Demo State
    st.markdown("""
    <div class="pf-card">
        <h3 style="margin-top:0; color:#1E293B;">👋 Welcome to Path Finder</h3>
        <p style="color:#475569;">
            Select a student from the sidebar dropdown or enter their University Seat Number (USN) to generate:
        </p>
        <ul style="color:#475569; line-height: 1.6;">
            <li><strong>Student Academic & Skill Profile:</strong> Verified PG CGPA, 10th, 12th, and UG scores alongside technical skills.</li>
            <li><strong>1. Readiness Agent:</strong> Evaluates skill alignment against active campus placement recruiters.</li>
            <li><strong>2. Prioritization Agent:</strong> Ranks upcoming placement drives by readiness and preparation urgency.</li>
            <li><strong>3. Interview-Prep Agent:</strong> Builds a tailored, day-by-day study roadmap and practice questions for your top target.</li>
            <li><strong>Historical Drive Analysis:</strong> Compares academic eligibility against past recruitment drives.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("#### ⚡ Quick demo selections:")
    demo_cols = st.columns(3)
    demo_cols[0].button("👤 1BM25MC002 (Adith Kushal B A)", on_click=set_demo_student, args=("1BM25MC002",), use_container_width=True)
    demo_cols[1].button("👤 1BM24MC116 (Zabi Ulla)", on_click=set_demo_student, args=("1BM24MC116",), use_container_width=True)
    demo_cols[2].button("👤 1BM25MC003 (Akhil M Jain)", on_click=set_demo_student, args=("1BM25MC003",), use_container_width=True)

else:
    # Look up student
    found = next(
        (profile for profile in placement_students if profile["usn"].casefold() == query_usn.casefold()),
        None
    )
    
    if found is None:
        st.warning(f"⚠️ No student was found with USN: **{query_usn}**. Please check the seat number and try again.")
    else:
        # Build student payload for multi-agent pipeline
        user_history = base_history
        if user_past_records:
            user_history = base_history + [dict(r, student_id=found["usn"]) for r in user_past_records]
            
        student_obj = {
            "student_id": found["usn"],
            "name": found["name"],
            "resume_skills": found["skills"],
            "academics": found["academics"],
        }
        
        # --- 1. Student Profile Card ---
        st.markdown(f"""
        <div class="pf-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap;">
                <div>
                    <h2 style="margin:0 0 0.25rem 0; color:#0F172A;">{found['name']}</h2>
                    <span style="font-size:0.95rem; font-weight:600; color:#475569; background:#F1F5F9; padding:3px 10px; border-radius:6px;">
                        USN: {found['usn']}
                    </span>
                    <span style="margin-left:8px; font-size:0.85rem; font-weight:500; color:#0369A1; background:#E0F2FE; padding:3px 8px; border-radius:6px;">
                        MCA Department
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Academic KPI Metrics
        m1, m2, m3, m4 = st.columns(4)
        pg_val = found["academics"].get("PG CGPA")
        ug_val = found["academics"].get("UG percentage")
        xii_val = found["academics"].get("12th percentage")
        x_val = found["academics"].get("10th percentage")
        
        m1.metric("PG CGPA", f"{pg_val:.2f}" if pg_val is not None else "N/A")
        m2.metric("UG Percentage", f"{ug_val:.1f}%" if ug_val is not None else "N/A")
        m3.metric("12th Percentage", f"{xii_val:.1f}%" if xii_val is not None else "N/A")
        m4.metric("10th Percentage", f"{x_val:.1f}%" if x_val is not None else "N/A")
        
        # Skills on record
        st.markdown("**Technical Skills on Record:**")
        if found["skills"]:
            skills_html = " ".join([f'<span class="skill-pill">{s}</span>' for s in found["skills"]])
            st.markdown(f"<div>{skills_html}</div>", unsafe_allow_html=True)
        else:
            st.caption("No technical skills explicitly recorded in the workbook.")
        
        st.write("")
        
        # --- Predictive Placement Fit Model ---
        st.markdown("### 🔮 Placement Predictor: Which Company Can You Get Into?")
        st.caption(
            "Statistical fit model predicting selection chances across "
            f"{len(cached_company_profiles)} historical campus recruiters based on your academic marks and technical skills."
        )

        predictions, top_boosters = predict_placement_chances(student_obj, cached_company_profiles)
        top_3 = predictions[:3]

        p_cols = st.columns(3)
        for p_idx, p_data in enumerate(top_3):
            with p_cols[p_idx]:
                prob_val = p_data["probability"]
                border_col = "#22C55E" if prob_val >= 70 else ("#EAB308" if prob_val >= 50 else "#3B82F6")
                bg_col = "#F0FDF4" if prob_val >= 70 else ("#FEFCE8" if prob_val >= 50 else "#EFF6FF")
                text_col = "#15803D" if prob_val >= 70 else ("#854D0E" if prob_val >= 50 else "#1E40AF")
                badge_bg = "#DCFCE7" if prob_val >= 70 else ("#FEF08A" if prob_val >= 50 else "#DBEAFE")

                st.markdown(f"""
                <div style="background:{bg_col}; border:1px solid {border_col}; border-radius:10px; padding:1.1rem; height:100%;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                        <span style="font-size:0.75rem; font-weight:700; color:{text_col}; background:{badge_bg}; padding:3px 8px; border-radius:9999px;">
                            #{p_idx + 1} TOP MATCH
                        </span>
                        <span style="font-size:1.05rem; font-weight:800; color:{text_col};">
                            {prob_val}% Chance
                        </span>
                    </div>
                    <h4 style="margin:0 0 0.25rem 0; color:#0F172A; font-size:1.1rem;">{p_data['company_name']}</h4>
                    <div style="font-size:0.88rem; color:#334155; margin-bottom:0.25rem;">
                        <strong>Best Role:</strong> {p_data['best_role']}
                    </div>
                    <div style="font-size:0.82rem; color:#64748B;">
                        <strong>Package:</strong> {p_data['package']} &nbsp;|&nbsp; <strong>Drives:</strong> {p_data['total_drives']}
                    </div>
                    <div style="font-size:0.82rem; color:{text_col}; margin-top:0.4rem;">
                        <strong>Matched:</strong> {', '.join(p_data['matched_skills']) if p_data['matched_skills'] else 'General Foundational Fit'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if top_boosters:
            st.info(f"⚡ **AI Skill Booster:** Adding **{', '.join(top_boosters[:3])}** to your resume would increase your qualification probability across 40+ additional campus recruiters!")

        pred_tab1, pred_tab2, pred_tab3, pred_tab4 = st.tabs([
            "🟢 High Likelihood (≥ 70%)",
            "🟡 Competitive Target (50% - 69%)",
            "🔵 Ambitious Reach (< 50%)",
            "📋 All Predicted Recruiters"
        ])

        def format_pred_df(items):
            rows = []
            for rank_no, p in enumerate(items, start=1):
                rows.append({
                    "Rank": f"#{rank_no}",
                    "Company": p["company_name"],
                    "Best-Suited Role": p["best_role"],
                    "Selection Chance": f"{p['probability']}%",
                    "Recruiter Tier": p["tier"],
                    "Academic Clearance": p["acad_reason"],
                    "Matched Skills": ", ".join(p["matched_skills"]) if p["matched_skills"] else "None",
                    "Missing Skills to Learn": ", ".join(p["missing_skills"]) if p["missing_skills"] else "None (Full Fit)",
                    "Historical Package": p["package"],
                    "Past Drives": p["total_drives"]
                })
            return pd.DataFrame(rows)

        with pred_tab1:
            high_items = [p for p in predictions if p["probability"] >= 70]
            if high_items:
                st.dataframe(format_pred_df(high_items), width="stretch", hide_index=True)
            else:
                st.caption("No companies in the ≥70% bracket. Review 'Competitive Target' or learn the recommended booster skills.")

        with pred_tab2:
            med_items = [p for p in predictions if 50 <= p["probability"] < 70]
            st.dataframe(format_pred_df(med_items), width="stretch", hide_index=True)

        with pred_tab3:
            reach_items = [p for p in predictions if p["probability"] < 50]
            st.dataframe(format_pred_df(reach_items), width="stretch", hide_index=True)

        with pred_tab4:
            st.dataframe(format_pred_df(predictions), width="stretch", hide_index=True)

        st.divider()

        # Run Multi-Agent Pipeline
        results, ranked, plan = run_pipeline(student_obj, companies, user_history)
        top_company = ranked[0]
        
        # --- 2. Agent 1: Readiness Agent ---
        st.markdown("### 1. Readiness Agent")
        st.caption("Evaluates student technical skill match against active recruitment job descriptions, adjusted for past interview performance.")
        
        readiness_rows = []
        for r in results:
            score = r["readiness"]
            if score >= 70:
                status_badge = "🟢 High Match"
            elif score >= 40:
                status_badge = "🟡 Moderate Match"
            else:
                status_badge = "🔴 Skill Gap"
                
            readiness_rows.append({
                "Company": r["company_name"],
                "Readiness %": f"{score}%",
                "Match Level": status_badge,
                "Missing Skills": ", ".join(r["missing"]) if r["missing"] else "None (Full Match)",
                "Agent Assessment": r["reason"]
            })
            
        st.dataframe(
            pd.DataFrame(readiness_rows),
            width="stretch",
            hide_index=True
        )
        
        # --- 3. Agent 2: Prioritization Agent ---
        st.markdown("### 2. Prioritization Agent")
        st.caption("Ranks upcoming companies by balancing readiness score and days remaining before the interview deadline.")
        
        # Highlight Top Target
        st.markdown(f"""
        <div class="focus-banner">
            <div class="focus-title">🎯 Top Priority Recommendation: {top_company['company_name']}</div>
            <div class="focus-desc">
                <strong>Readiness:</strong> {top_company['readiness']}% &nbsp;|&nbsp; 
                <strong>Days Left:</strong> {top_company['days_left']} days &nbsp;|&nbsp; 
                <strong>Priority Score:</strong> {top_company['priority']}<br/>
                <em>{top_company['reason']}</em>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        prioritization_rows = []
        for i, r in enumerate(ranked):
            prioritization_rows.append({
                "Rank": f"#{i + 1}",
                "Company": r["company_name"],
                "Readiness": f"{r['readiness']}%",
                "Days Left": f"{r['days_left']} days",
                "Priority Score": r["priority"],
                "Strategic Guidance": r["reason"]
            })
            
        st.dataframe(
            pd.DataFrame(prioritization_rows),
            width="stretch",
            hide_index=True
        )
        
        # --- 4. Agent 3: Interview-Prep Agent ---
        st.markdown(f"### 3. Interview-Prep Agent — Action Plan for {top_company['company_name']}")
        st.caption(f"Day-by-day roadmap addressing missing skills and technical competencies required for {top_company['company_name']}.")
        
        prep_cols = st.columns(min(len(plan), 4))
        for idx, step in enumerate(plan):
            col_target = prep_cols[idx % len(prep_cols)]
            with col_target:
                st.markdown(f"""
                <div class="prep-step">
                    <div class="prep-day">Day {step['day']}</div>
                    <div class="prep-focus">{step['focus']}</div>
                    <div class="prep-q"><strong>Practice:</strong> {step['practice_question']}</div>
                </div>
                """, unsafe_allow_html=True)
                
        with st.expander("📋 View Full Prep Plan Table", expanded=False):
            st.dataframe(
                pd.DataFrame([{"Day": p["day"], "Topic / Focus": p["focus"], "Practice Question": p["practice_question"]} for p in plan]),
                width="stretch",
                hide_index=True
            )
            
        # --- 5. Historical Campus Drives ---
        with st.expander("📚 Historical Campus Recruitment Drives (College PDF Records)", expanded=False):
            st.caption(
                f"Evaluated across {len(company_history)} historical records from the college placement archive. "
                "Higher-ranked records meet academic cutoffs and/or match skills explicitly specified in past roles."
            )
            
            all_known_skills = sorted({skill for p in placement_students for skill in p["skills"]})
            ranked_history = recommend_companies(found, company_history, all_known_skills)
            
            history_rows = []
            for rank_idx, rec in enumerate(ranked_history[:25], start=1):
                if rec["role_skills"]:
                    skill_match_desc = ", ".join(rec["matched_skills"]) if rec["matched_skills"] else "No role skills matched"
                else:
                    skill_match_desc = "Not specified in historical role"
                    
                history_rows.append({
                    "Rank": rank_idx,
                    "Company": rec["company"],
                    "Historical Role": rec["role"],
                    "Year": rec["year"] or "N/A",
                    "Academic Cutoff Check": rec["eligibility"],
                    "Role Skill Match": skill_match_desc,
                    "Historical Drives": rec["historical_drives"],
                    "Criteria": rec["criteria"],
                    "Historical Package": rec["compensation"],
                })
                
            st.dataframe(
                pd.DataFrame(history_rows),
                width="stretch",
                hide_index=True
            )
            st.caption(
                "Note: Academic criteria is checked against available PG CGPA, 10th, 12th, and UG percentages. "
                "Backlog status is not recorded in the workbook."
            )