
import streamlit as st
import pandas as pd
import gspread
import uuid
import json
import hashlib
from datetime import datetime, timezone
from google.oauth2.service_account import Credentials


def save_response_to_google_sheets(row_values):
    """Append one validated survey response to the configured spreadsheet."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes,
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = spreadsheet.worksheet("Responses")
    worksheet.append_row(row_values, value_input_option="RAW")

st.set_page_config(
    page_title="Digital Productivity Index",
    page_icon="📊",
    layout="centered",
)

st.title("Digital Productivity Index (DPI)")
st.write(
    "This questionnaire explores digital work habits across work "
    "environments. It takes a few minutes to complete."
)

st.info(
    "Think about your typical work experience during the past "
    "four weeks. Participation is voluntary. Please do not enter "
    "your name, email address, or other identifying information. "
    "Your score is a self-reported measure of digital work habits, "
    "not a direct measure of job performance."
)

st.subheader("Eligibility")

working_status = st.radio(
    "Are you currently working in a paid role or self-employed?",
    ["Select an answer", "Yes", "No"],
    index=0,
)

if working_status == "No":
    st.warning(
        "Thank you for your interest. This survey is intended "
        "for people currently in paid employment or self-employment."
    )
    st.stop()

if working_status == "Select an answer":
    st.warning("Please answer the eligibility question to continue.")
    st.stop()

st.divider()

st.subheader("Section 1: Background Information")

age_group = st.selectbox(
    "Age group",
    [
        "Select an answer",
        "Below 21",
        "21–25",
        "26–30",
        "31–40",
        "41–50",
        "Above 50",
        "Prefer not to say",
    ],
)

experience = st.selectbox(
    "Total work experience",
    [
        "Select an answer",
        "Less than 1 year",
        "1–3 years",
        "4–6 years",
        "7–10 years",
        "More than 10 years",
    ],
)

role = st.selectbox(
    "Current role",
    [
        "Select an answer",
        "Developer",
        "Data Engineer / Data Analyst",
        "Tester",
        "Product Management",
        "Other",
    ],
)
role_other = ""
if role == "Other":
    role_other = st.text_input("Please specify your role")

organization = st.selectbox(
    "Organization type",
    [
        "Select an answer",
        "Product-based",
        "Service-based",
        "Manufacturing",
        "Self-employed",
        "Other",
    ],
)
organization_other = ""
if organization == "Other":
    organization_other = st.text_input(
        "Please specify your organization type"
    )

work_arrangement = st.selectbox(
    "Work arrangement",
    [
        "Select an answer",
        "Office-based",
        "Hybrid",
        "Remote",
        "Field-based",
        "Other",
    ],
)
work_arrangement_other = ""
if work_arrangement == "Other":
    work_arrangement_other = st.text_input(
        "Please specify your work arrangement"
    )

ai_access = st.selectbox(
    "Which statement best describes your access to AI tools at work?",
    [
        "Select an answer",
        "Use regularly",
        "Use occasionally",
        "Use rarely",
        "Never use",
        "No access or not permitted by organization",
    ],
)

st.divider()
st.subheader("Section 2: Digital Work Habits")

st.write(
    "For each statement, select how often it describes your "
    "usual work experience during the past four weeks."
)

scale = [
    "Select an answer",
    "1 — Never",
    "2 — Rarely",
    "3 — Sometimes",
    "4 — Often",
    "5 — Almost always",
]

dimensions = {
    "Planning & Prioritization": [
        (
            "PP1",
            "At the start of a workday, how often do you identify "
            "the tasks that need your attention first?",
        ),
        (
            "PP2",
            "When you have several tasks with different deadlines, "
            "how often do you organize them according to their "
            "importance and urgency?",
        ),
        (
            "PP3",
            "When your priorities change during the day, how often "
            "do you review and adjust your task plan?",
        ),
    ],
    "Focus Management": [
        (
            "FM1",
            "How often do you set aside time to work on an important "
            "task without switching to unrelated activities?",
        ),
        (
            "FM2",
            "After an interruption, how often are you able to return "
            "to the task you were working on?",
        ),
        (
            "FM3",
            "When working on a demanding task, how often do you avoid "
            "switching between multiple tasks unnecessarily?",
        ),
    ],
    "Notification Management": [
        (
            "NM1",
            "When you need to concentrate, how often do you silence "
            "or limit non-essential notifications?",
        ),
        (
            "NM2",
            "How often do you check messages and notifications at a "
            "time that suits your work, rather than immediately "
            "when they arrive?",
        ),
        (
            "NM3",
            "How often do you decide which alerts need immediate "
            "attention and which can wait?",
        ),
    ],
    "Meeting Effectiveness": [
        (
            "ME1",
            "How often do you attend meetings that have a clear "
            "purpose relevant to your work?",
        ),
        (
            "ME2",
            "How often do meetings you attend finish within their "
            "scheduled time, allowing you to continue your planned work?",
        ),
        (
            "ME3",
            "After a meeting, how often do you record or follow up "
            "on the actions assigned to you?",
        ),
    ],
    "AI Awareness and Responsible Use": [
        (
            "AI1",
            "How often do you identify work tasks where AI tools "
            "could help save time or effort, when their use is "
            "available and permitted?",
        ),
        (
            "AI2",
            "How often do you consider that AI-generated information "
            "may be inaccurate and need checking before being relied on?",
        ),
        (
            "AI3",
            "How often do you consider workplace rules and "
            "confidentiality requirements before deciding whether "
            "AI is appropriate for a work task?",
        ),
    ],
    "Information Management": [
        (
            "IM1",
            "How often do you save work files using a consistent "
            "naming or folder system?",
        ),
        (
            "IM2",
            "When you need information from a previous task, how "
            "often can you find it without spending excessive time searching?",
        ),
        (
            "IM3",
            "How often do you capture important work notes, tasks, "
            "or follow-ups in a reliable place instead of relying "
            "only on memory?",
        ),
    ],
    "Digital Wellbeing": [
        (
            "DW1",
            "During a typical workday, how often do you take short "
            "breaks from continuous screen-based work when your "
            "workload allows?",
        ),
        (
            "DW2",
            "How often do you avoid checking work messages outside "
            "your working hours unless genuinely necessary?",
        ),
        (
            "DW3",
            "How often do you stop or step away from digital work "
            "when you notice fatigue affecting your concentration?",
        ),
    ],
}

answers = {}

for dimension, questions in dimensions.items():
    st.markdown(f"### {dimension}")

    for question_id, question_text in questions:
        answers[question_id] = st.selectbox(
            f"{question_id}. {question_text}",
            scale,
            key=question_id,
        )

st.divider()
st.subheader("Section 3: Overall Self-Rated Productivity")

productivity = st.selectbox(
    "During the past four weeks, how would you rate your "
    "overall productivity at work?",
    [
        "Select an answer",
        "1 — Very low",
        "2 — Low",
        "3 — Moderate",
        "4 — High",
        "5 — Very high",
    ],
)

st.caption(
    "Your productivity rating is collected separately and is "
    "not included in the DPI score."
)

if st.button("Calculate My DPI", type="primary", use_container_width=True):
    errors = []

    background = {
        "Age group": age_group,
        "Work experience": experience,
        "Current role": role,
        "Organization type": organization,
        "Work arrangement": work_arrangement,
        "AI access/use": ai_access,
    }

    for label, value in background.items():
        if value == "Select an answer":
            errors.append(f"Please answer: {label}.")

    if role == "Other" and not role_other.strip():
        errors.append("Please specify your current role.")

    if organization == "Other" and not organization_other.strip():
        errors.append("Please specify your organization type.")

    if work_arrangement == "Other" and not work_arrangement_other.strip():
        errors.append("Please specify your work arrangement.")

    for question_id, answer in answers.items():
        if answer == "Select an answer":
            errors.append(f"Please answer question {question_id}.")

    if productivity == "Select an answer":
        errors.append("Please answer the overall productivity question.")

    if errors:
        st.error(
            "Please complete the missing responses before calculating "
            "your score."
        )
        for error in errors:
            st.write(f"- {error}")

    else:
        numeric_answers = {
            question_id: int(answer[0])
            for question_id, answer in answers.items()
        }

        dimension_scores = {}

        for dimension, questions in dimensions.items():
            item_values = [
                numeric_answers[question_id]
                for question_id, _ in questions
            ]
            mean_value = sum(item_values) / len(item_values)
            dimension_scores[dimension] = (
                (mean_value - 1) / 4
            ) * 100

        dpi_score = sum(dimension_scores.values()) / len(
            dimension_scores
        )

        # Save the validated raw response before showing a successful result.
        response_fields = {
            "age_group": age_group,
            "work_experience": experience,
            "current_role": role,
            "role_other": role_other.strip(),
            "organization_type": organization,
            "organization_other": organization_other.strip(),
            "work_arrangement": work_arrangement,
            "work_arrangement_other": work_arrangement_other.strip(),
            "ai_access": ai_access,
            **numeric_answers,
            "self_rated_productivity": int(productivity[0]),
        }

        # Prevent a repeated click from saving the exact same response twice
        # during this browser session. Editing an answer creates a new signature.
        response_signature = hashlib.sha256(
            json.dumps(response_fields, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

        if st.session_state.get("dpi_saved_signature") == response_signature:
            st.info("This exact response has already been saved in this session.")
        else:
            response_id = str(uuid.uuid4())
            submitted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            scoring_version = "DPI_v1.0"

            # Must match the 34 headers in the Responses worksheet exactly.
            row_values = [
                response_id,
                submitted_at,
                scoring_version,
                age_group,
                experience,
                role,
                role_other.strip(),
                organization,
                organization_other.strip(),
                work_arrangement,
                work_arrangement_other.strip(),
                ai_access,
                numeric_answers["PP1"],
                numeric_answers["PP2"],
                numeric_answers["PP3"],
                numeric_answers["FM1"],
                numeric_answers["FM2"],
                numeric_answers["FM3"],
                numeric_answers["NM1"],
                numeric_answers["NM2"],
                numeric_answers["NM3"],
                numeric_answers["ME1"],
                numeric_answers["ME2"],
                numeric_answers["ME3"],
                numeric_answers["AI1"],
                numeric_answers["AI2"],
                numeric_answers["AI3"],
                numeric_answers["IM1"],
                numeric_answers["IM2"],
                numeric_answers["IM3"],
                numeric_answers["DW1"],
                numeric_answers["DW2"],
                numeric_answers["DW3"],
                int(productivity[0]),
            ]

            try:
                save_response_to_google_sheets(row_values)
            except Exception as exc:
                st.error(
                    "Your response could not be saved. Your DPI result has not "
                    "been confirmed as submitted. Please try again later or contact "
                    "the project administrator."
                )
                # Keep technical details available for the developer, without
                # displaying credentials or secret values.
                st.caption(f"Technical error: {type(exc).__name__}: {exc}")
            else:
                st.session_state["dpi_saved_signature"] = response_signature
                st.session_state["dpi_result"] = {
                    "overall": dpi_score,
                    "dimensions": dimension_scores,
                    "productivity": int(productivity[0]),
                    "response_id": response_id,
                }
                st.success("Your response has been saved successfully.")

if "dpi_result" in st.session_state:
    result = st.session_state["dpi_result"]
    dpi_score = result["overall"]

    st.divider()
    st.header("Your Digital Productivity Index")

    st.metric("Overall DPI Score", f"{dpi_score:.1f} / 100")

    if dpi_score < 40:
        interpretation = "Habits to strengthen"
    elif dpi_score < 60:
        interpretation = "Developing habits"
    elif dpi_score < 80:
        interpretation = "Generally established habits"
    else:
        interpretation = "Strong reported habits"

    st.subheader(interpretation)
    st.write(
        "This is a preliminary, self-reported index score. "
        "It is not a percentage of your productivity and is not "
        "a validated measure of job performance."
    )

    score_df = pd.DataFrame(
        [
            {
                "Dimension": dimension,
                "Score (0–100)": round(score, 1),
            }
            for dimension, score in result["dimensions"].items()
        ]
    )

    st.subheader("Your Dimension Scores")
    st.dataframe(score_df, hide_index=True, use_container_width=True)

    suggestions = {
        "Planning & Prioritization": (
            "Identify your top three priorities at the start of the "
            "day and review them when deadlines change."
        ),
        "Focus Management": (
            "Reserve a focused work block for an important task and "
            "use a simple routine to resume work after interruptions."
        ),
        "Notification Management": (
            "Silence non-essential alerts during focus time and check "
            "non-urgent messages at planned intervals."
        ),
        "Meeting Effectiveness": (
            "Clarify the purpose of meetings and record action items "
            "and responsibilities before moving on."
        ),
        "AI Awareness and Responsible Use": (
            "Consider whether AI is suitable and permitted for a task, "
            "verify its output, and protect confidential information."
        ),
        "Information Management": (
            "Use consistent file names and folders, and keep task notes "
            "and follow-ups in a reliable place."
        ),
        "Digital Wellbeing": (
            "Take short breaks when workload allows and maintain "
            "reasonable boundaries around after-hours messages."
        ),
    }

    st.subheader("Suggested Areas for Improvement")
    lowest_dimensions = sorted(
        result["dimensions"].items(),
        key=lambda item: item[1],
    )[:2]

    for dimension, score in lowest_dimensions:
        st.markdown(f"**{dimension} — {score:.1f}/100**")
        st.write(suggestions[dimension])

    st.caption(
        "Score interpretation bands and suggestions are provisional "
        "and intended for reflection. They are not diagnostic or "
        "employment assessment tools."
    )
