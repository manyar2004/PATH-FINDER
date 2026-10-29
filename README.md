# Path Finder: A Smart Placement Guidance Assistant

A dedicated placement guidance and preparation platform for MCA students powered by a statistical placement prediction model and a multi-agent guidance pipeline.

Lookup any MCA student by their **University Seat Number (USN)** to predict which campus recruiters they can get into based on 344 historical company profiles, evaluate readiness for upcoming drives, prioritize deadlines, and receive a customized day-by-day interview preparation roadmap.

---

## 🔮 Placement Prediction Model
[`agents/placement_prediction_model.py`](file:///c:/Users/Manya%20R/Downloads/MINI_PROJECT/pathfinder-resumne-versions/pathfinder-resumne-versions/agents/placement_prediction_model.py)

Predicts which historical company a student has the highest chance of getting an offer from by evaluating:
1. **Academic Clearance & Margin:** Checks PG CGPA, 10th, 12th, and UG percentages against historical company cutoffs.
2. **Role-Specific Skill Fit:** Maps student technical skills against domain-specific role requirements (e.g. Backend, Data Analytics, QA Automation, Full Stack, Embedded).
3. **Campus Hiring Track Record:** Rewards frequent campus recruiters with higher conversion probabilities.
4. **Competitiveness Tier:** Modulates probability based on compensation tier (Dream/Tier-1 vs Primary Recruiters).
5. **AI Skill Booster:** Recommends the top 3 high-impact skills that would unlock the highest number of additional campus recruiters.

---

## 🤖 The Multi-Agent Pipeline

| Agent | Module | Role |
|---|---|---|
| **1. Readiness Agent** | [`agents/readiness_agent.py`](file:///c:/Users/Manya%20R/Downloads/MINI_PROJECT/pathfinder-resumne-versions/pathfinder-resumne-versions/agents/readiness_agent.py) | Calculates skill match % against active drive job descriptions, adjusted for past interview performance at similar company types. |
| **2. Prioritization Agent** | [`agents/prioritization_agent.py`](file:///c:/Users/Manya%20R/Downloads/MINI_PROJECT/pathfinder-resumne-versions/pathfinder-resumne-versions/agents/prioritization_agent.py) | Ranks target companies balancing readiness score and remaining prep days before the deadline. |
| **3. Interview-Prep Agent** | [`agents/interview_prep_agent.py`](file:///c:/Users/Manya%20R/Downloads/MINI_PROJECT/pathfinder-resumne-versions/pathfinder-resumne-versions/agents/interview_prep_agent.py) | Generates a structured day-by-day study roadmap and practice questions targeting missing skills and previous drop-off rounds. |

---

## 🧮 Decision Logic
- **Selection Probability:** $\text{clamp}\left(5, 95, (0.45 \times S_{\text{skill}} + 0.35 \times S_{\text{academic}} + 0.20 \times S_{\text{hiring}}) \times S_{\text{tier}}\right)$
- **Readiness Score:** $\text{Skill Match \%} + 5 \times (\text{Past Selections}) - 5 \times (\text{Past Drop-offs, max } 15)$ for similar company types.
- **Priority Score:** $\text{Readiness} + \frac{30}{\text{Days Left}}$.

---

## 📁 Project Structure
```
Paychex (1).xlsx          College MCA student records (USN, Academics, Skills)
DOC-20260801-WA0002..pdf  Historical company placement records and criteria
data/
  companies.json          Active target companies and required JD skills
  interview_history.json  Past interview history
agents/
  placement_prediction_model.py  Model: predicts which company a student can get into
  readiness_agent.py             Agent 1: Readiness evaluation
  prioritization_agent.py        Agent 2: Urgent drive ranking
  interview_prep_agent.py        Agent 3: Actionable preparation roadmap
pipeline/
  run_pipeline.py         Executes agents sequentially
utils/
  placement_data.py       Parses Excel student records & PDF drive history
.streamlit/
  config.toml             Light theme configuration
app.py                    Streamlit UI (Dedicated USN Search & Guidance)
```

---

## 🚀 Running the Project
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
streamlit run app.py
```
App will be accessible at: **http://localhost:8501**
