import hashlib
import json
import random
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


# ---------------------------------------------------------------------
# Google Sheets storage
# ---------------------------------------------------------------------
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


# ---------------------------------------------------------------------
# Page configuration and restrained visual styling
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Digital Productivity Index (DPI)",
    page_icon="📊",
    layout="centered",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 900px;
    }
    .dpi-eyebrow {
        color: #16877B;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .dpi-intro {
        padding: 1.2rem 1.3rem;
        border-radius: 14px;
        border: 1px solid rgba(22, 135, 123, 0.25);
        background: linear-gradient(120deg, rgba(22, 135, 123, 0.08), rgba(35, 91, 130, 0.06));
        margin: 0.6rem 0 1rem 0;
    }
    .dpi-small {
        color: #64748b;
        font-size: 0.9rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
    }
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        border-radius: 10px;
        font-weight: 650;
    }

    /* Subtle styling for survey answer controls */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        border: 1px solid #C7D5E2;
        border-radius: 8px;
        background-color: #F8FAFC;
    }

    /* Clear keyboard-focus indicator */
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div {
        border-color: #2B6F91;
        box-shadow: 0 0 0 1px #2B6F91;
    }

    /* DPI results heading colours */
    .dpi-interpretation {
        color: #173B57 !important;
        font-weight: 700;
    }

    .dpi-strong-heading {
        color: #168A83 !important;
        font-weight: 700;
    }

    .dpi-suggestions-heading {
        color: #B96C18 !important;
        font-weight: 700;
    }
    
    </style>
    """,
    unsafe_allow_html=True,
)

if "dpi_show_success_dialog" not in st.session_state:
    st.session_state["dpi_show_success_dialog"] = False

@st.dialog("Response saved successfully")
def show_success_dialog():
    st.success(
        "Your response has been saved successfully to the test spreadsheet."
    )
    st.write(
        "Your Digital Productivity Index score and suggestions are ready."
    )

    if st.button(
        "View my DPI results",
        type="primary",
        use_container_width=True,
    ):
        st.session_state["dpi_show_success_dialog"] = False
        st.session_state["dpi_scroll_to_results"] = True
        st.rerun()

    if st.button("Close", use_container_width=True):
        st.session_state["dpi_show_success_dialog"] = False
        st.rerun()

if st.session_state["dpi_show_success_dialog"]:
    show_success_dialog()

st.title("Digital Productivity Index (DPI)")
st.write("Understand your reported digital work habits and identify practical ways to strengthen them.")

with st.container(border=True):
    st.markdown("### Before you begin")
    intro_cols = st.columns(3)
    with intro_cols[0]:
        st.markdown("**🧭 Reflect**")
        st.caption("Think about your usual work experience during the past four weeks.")
    with intro_cols[1]:
        st.markdown("**📝 Answer honestly**")
        st.caption("There are no right or wrong answers. Accuracy matters more than a high score.")
    with intro_cols[2]:
        st.markdown("**📊 Learn from your results**")
        st.caption("Review your dimension scores and practical suggestions after submission.")

st.info(
    "Participation is voluntary. Please do not enter your name, email address, "
    "or other identifying or confidential information. Your score is a preliminary, "
    "self-reported measure of digital work habits—not a direct measure of job performance."
)

st.markdown(
    "**How to answer:** Choose the option that best reflects your usual work habits, "
    "rather than what you think the ideal answer should be. Thoughtful, genuine responses "
    "help make the study findings more meaningful."
)

# ---------------------------------------------------------------------
# Eligibility and staged background form
# ---------------------------------------------------------------------
if "dpi_stage" not in st.session_state:
    st.session_state["dpi_stage"] = "background"
if "dpi_run_id" not in st.session_state:
    st.session_state["dpi_run_id"] = 0

if "dpi_background" not in st.session_state:
    st.session_state["dpi_background"] = None

st.subheader("Step 1 of 3 · Eligibility and background")

working_status = st.radio(
    "Are you currently working in a paid role or self-employed?",
    ["Select an answer", "Yes", "No"],
    index=0,
    horizontal=True,
    key="dpi_working_status",
)

if working_status == "No":
    st.warning(
        "Thank you for your interest. This survey is intended for people currently "
        "in paid employment or self-employment."
    )
    st.stop()

if working_status == "Select an answer":
    st.info("Please confirm your eligibility to continue.")
    st.stop()

if st.session_state["dpi_stage"] == "background":
    st.write(
        "Complete the background details below. After you continue, these details "
        "will be locked for this survey session."
    )

    with st.container(border=True):
        age_group = st.selectbox(
            "Age group",
            [
                "Select an answer", "Below 21", "21–25", "26–30",
                "31–40", "41–50", "Above 50", "Prefer not to say",
            ],
            key=f"{st.session_state['dpi_run_id']}_dpi_age_group",
        )
        experience = st.selectbox(
            "Total work experience",
            [
                "Select an answer", "Less than 1 year", "1–3 years",
                "4–6 years", "7–10 years", "More than 10 years",
            ],
            key=f"{st.session_state['dpi_run_id']}_dpi_experience",
        )
        role = st.selectbox(
            "Current role",
            [
                "Select an answer", "Developer", "Data Engineer / Data Analyst",
                "Tester", "Product Management", "Other",
            ],
            key=f"{st.session_state['dpi_run_id']}_dpi_role",
        )
        role_other = ""
        if role == "Other":
            role_other = st.text_input(
                "Please specify your role",
                key=f"{st.session_state['dpi_run_id']}_dpi_role_other",
                help="Please do not include names or other identifying details.",
            )

        organization = st.selectbox(
            "Organization type",
            [
                "Select an answer", "Product-based", "Service-based",
                "Manufacturing", "Self-employed", "Other",
            ],
            key=f"{st.session_state['dpi_run_id']}_dpi_organization",
        )
        organization_other = ""
        if organization == "Other":
            organization_other = st.text_input(
                "Please specify your organization type",
                key=f"{st.session_state['dpi_run_id']}_dpi_organization_other",
                help="Please do not include confidential or identifying information.",
            )

        work_arrangement = st.selectbox(
            "Work arrangement",
            [
                "Select an answer", "Office-based", "Hybrid",
                "Remote", "Field-based", "Other",
            ],
            key=f"{st.session_state['dpi_run_id']}_dpi_work_arrangement",
        )
        work_arrangement_other = ""
        if work_arrangement == "Other":
            work_arrangement_other = st.text_input(
                "Please specify your work arrangement",
                key=f"{st.session_state['dpi_run_id']}_dpi_work_arrangement_other",
                help="Please do not include names or other identifying details.",
            )

        ai_access = st.selectbox(
            "Which statement best describes your access to AI tools at work?",
            [
                "Select an answer", "Use regularly", "Use occasionally",
                "Use rarely", "Never use",
                "No access or not permitted by organization",
            ],
            key=f"{st.session_state['dpi_run_id']}_dpi_ai_access",
        )

        continue_background = st.button(
            "Continue to questionnaire",
            type="primary",
            use_container_width=True,
        )

    if continue_background:
        errors = []
        background_values = {
            "Age group": age_group,
            "Work experience": experience,
            "Current role": role,
            "Organization type": organization,
            "Work arrangement": work_arrangement,
            "AI access/use": ai_access,
        }
        for label, value in background_values.items():
            if value == "Select an answer":
                errors.append(f"Please answer: {label}.")
        if role == "Other" and not role_other.strip():
            errors.append("Please specify your current role.")
        if organization == "Other" and not organization_other.strip():
            errors.append("Please specify your organization type.")
        if work_arrangement == "Other" and not work_arrangement_other.strip():
            errors.append("Please specify your work arrangement.")

        if errors:
            st.error("Please complete the missing background details.")
            for error in errors:
                st.write(f"- {error}")
        else:
            st.session_state["dpi_background"] = {
                "age_group": age_group,
                "work_experience": experience,
                "current_role": role,
                "role_other": role_other.strip(),
                "organization_type": organization,
                "organization_other": organization_other.strip(),
                "work_arrangement": work_arrangement,
                "work_arrangement_other": work_arrangement_other.strip(),
                "ai_access": ai_access,
            }
            st.session_state["dpi_stage"] = "questionnaire"
            st.rerun()

    st.stop()

# Background details are read-only after the respondent has continued.
background = st.session_state.get("dpi_background")
if not background:
    st.session_state["dpi_stage"] = "background"
    st.rerun()

with st.container(border=True):
    st.markdown("**Background details saved for this session**")
    summary_cols = st.columns(2)
    with summary_cols[0]:
        st.caption(f"Age group: {background['age_group']}")
        st.caption(f"Work experience: {background['work_experience']}")
        st.caption(f"Current role: {background['current_role']}")
        if background["role_other"]:
            st.caption(f"Role details: {background['role_other']}")
    with summary_cols[1]:
        st.caption(f"Organization: {background['organization_type']}")
        if background["organization_other"]:
            st.caption(f"Organization details: {background['organization_other']}")
        st.caption(f"Work arrangement: {background['work_arrangement']}")
        if background["work_arrangement_other"]:
            st.caption(f"Arrangement details: {background['work_arrangement_other']}")
        st.caption(f"AI access/use: {background['ai_access']}")

st.subheader("Step 2 of 3 · Digital work habits")
st.write(
    "For each statement, select how often it describes your usual work experience "
    "during the past four weeks."
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

st.progress(0.67, text="Step 2 of 3 · Complete the questionnaire")

with st.form(f"dpi_questionnaire_form_{st.session_state['dpi_run_id']}"):
    answers = {}
    for dimension, questions in dimensions.items():
        st.markdown(f"### {dimension}")
        for question_id, question_text in questions:
            with st.container(border=True):
                answers[question_id] = st.selectbox(
                    f"{question_id}. {question_text}",
                    scale,
                    key=f"dpi_answer_{st.session_state['dpi_run_id']}_{question_id}" ,
                )

    st.markdown("### Overall self-rated productivity")
    productivity = st.selectbox(
        "During the past four weeks, how would you rate your overall productivity at work?",
        [
            "Select an answer", "1 — Very low", "2 — Low",
            "3 — Moderate", "4 — High", "5 — Very high",
        ],
        key="dpi_self_rated_productivity",
    )
    st.caption(
        "Your productivity rating is collected separately and is not included in the DPI score."
    )
    submitted = st.form_submit_button(
        "Submit responses and calculate my DPI",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------------------
# Scoring, validation, and response storage
# ---------------------------------------------------------------------
if submitted:
    errors = []
    for question_id, answer in answers.items():
        if answer == "Select an answer":
            errors.append(f"Please answer question {question_id}.")
    if productivity == "Select an answer":
        errors.append("Please answer the overall productivity question.")

    if errors:
        st.error("Please complete the missing responses before submitting.")
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
            dimension_scores[dimension] = ((mean_value - 1) / 4) * 100

        dpi_score = sum(dimension_scores.values()) / len(dimension_scores)

        response_fields = {
            **background,
            **numeric_answers,
            "self_rated_productivity": int(productivity[0]),
        }
        response_signature = hashlib.sha256(
            json.dumps(
                response_fields, sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()

        if st.session_state.get("dpi_saved_signature") == response_signature:
            st.session_state["dpi_save_error"] = False
            st.info("This exact response has already been saved in this session.")
        else:
            response_id = str(uuid.uuid4())
            submitted_at = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds")
            scoring_version = "DPI_v1.1"

            # Preserve the exact order of the existing 34 Responses headers.
            row_values = [
                response_id,
                submitted_at,
                scoring_version,
                background["age_group"],
                background["work_experience"],
                background["current_role"],
                background["role_other"],
                background["organization_type"],
                background["organization_other"],
                background["work_arrangement"],
                background["work_arrangement_other"],
                background["ai_access"],
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
                st.session_state["dpi_save_error"] = True
                st.error(
                    "Your response could not be saved. Your submission has not been "
                    "confirmed. Please try again later or contact the project administrator."
                )
                st.caption(f"Technical error: {type(exc).__name__}: {exc}")
            else:
                # Choose suggestions once and keep them stable for this result.
                st.session_state["dpi_save_error"] = False
                st.session_state["dpi_saved_signature"] = response_signature
                st.session_state["dpi_recommendations"] = {}
                st.session_state["dpi_result"] = {
                    "overall": dpi_score,
                    "dimensions": dimension_scores,
                    "productivity": int(productivity[0]),
                    "response_id": response_id,
                }
                st.session_state["dpi_stage"] = "results"
                st.session_state["dpi_show_success_dialog"] = True
                st.rerun()

# ---------------------------------------------------------------------
# Scenario-based recommendation library: four scenarios per dimension
# ---------------------------------------------------------------------
recommendation_library = {
    "Planning & Prioritization": [
        {
            "why": "Making priorities visible can help you direct attention toward the work that matters most.",
            "scenario": "You begin the day with several requests, two deadlines, and a message asking for an urgent update.",
            "action": "Write down your top three priorities, identify their deadlines, and revisit the list when genuinely urgent work arrives.",
        },
        {
            "why": "A clear plan can make competing tasks easier to manage.",
            "scenario": "You move between small requests all morning and discover that an important deliverable has barely progressed.",
            "action": "Reserve a specific time block for the deliverable and group smaller tasks into a separate period.",
        },
        {
            "why": "Reviewing plans helps you respond to changes without losing track of existing commitments.",
            "scenario": "A new task arrives midway through the day and changes what your manager needs first.",
            "action": "Reorder your task list, note what will be delayed, and communicate the revised priority when needed.",
        },
        {
            "why": "Breaking large tasks into smaller steps can make progress easier to track.",
            "scenario": "A large assignment feels difficult to start because the final outcome involves several separate activities.",
            "action": "Define the next two or three concrete steps and choose the first one you can complete today.",
        },
    ],
    "Focus Management": [
        {
            "why": "Protected focus time can reduce unnecessary task switching on work that needs sustained attention.",
            "scenario": "You start writing a report but repeatedly switch to email, chat, and unrelated requests.",
            "action": "Try a 25-minute focus block, silence non-essential alerts where possible, and check messages afterward.",
        },
        {
            "why": "A simple restart routine can help you return to work after an interruption.",
            "scenario": "A colleague asks a question while you are analysing data, and you return unsure which step you were on.",
            "action": "Before switching tasks, leave a short note about the next action; use it to resume when you return.",
        },
        {
            "why": "Reducing unnecessary switching can make demanding tasks easier to complete.",
            "scenario": "You alternate between a presentation, a spreadsheet, and messages, making slow progress on all three.",
            "action": "Choose one task for a defined period, keep only its required tools open, and switch at a planned stopping point.",
        },
        {
            "why": "Matching difficult work to a suitable time can support concentration.",
            "scenario": "You try to complete a complex task at the end of a day filled with meetings and interruptions.",
            "action": "When your schedule allows, place the demanding task in a quieter period when you usually feel more alert.",
        },
    ],
    "Notification Management": [
        {
            "why": "Not every alert requires an immediate response, and separating urgent from non-urgent messages can protect attention.",
            "scenario": "Several app notifications appear while you are completing a time-sensitive task.",
            "action": "Use available notification settings to quiet non-essential alerts and agree on a channel for genuinely urgent issues.",
        },
        {
            "why": "Planned message checks can reduce the pull of repeatedly checking incoming notifications.",
            "scenario": "You open your inbox every few minutes even when no task requires a response.",
            "action": "Where your role permits, check messages at planned intervals and keep alerts enabled for essential contacts.",
        },
        {
            "why": "A clear priority rule helps you decide which notifications deserve attention first.",
            "scenario": "A team chat, a calendar reminder, and an urgent request arrive close together.",
            "action": "Define simple rules for urgency, deadlines, and impact so you can respond in a deliberate order.",
        },
        {
            "why": "Notification boundaries can help protect focused work without making you unreachable.",
            "scenario": "You need uninterrupted time to prepare a deliverable but still need to remain available for critical matters.",
            "action": "Use a focus mode or status message if appropriate, while keeping an agreed route open for urgent requests.",
        },
    ],
    "Meeting Effectiveness": [
        {
            "why": "A clear purpose helps participants prepare and understand why their attendance matters.",
            "scenario": "You join a meeting and spend the first several minutes trying to understand what decision is needed.",
            "action": "Before the meeting, check the agenda and expected outcome; ask for clarification if the purpose is unclear.",
        },
        {
            "why": "Capturing decisions and owners helps turn discussion into follow-through.",
            "scenario": "A meeting ends with several ideas, but nobody is certain who will complete each next step.",
            "action": "Record the decision, action owner, and due date before leaving or immediately afterward.",
        },
        {
            "why": "Protecting meeting time leaves more room for planned work.",
            "scenario": "A recurring meeting routinely runs over because the discussion drifts away from its main topic.",
            "action": "Use the agenda to bring the conversation back to its purpose and identify topics that can be handled separately.",
        },
        {
            "why": "Choosing the right form of communication can avoid unnecessary meetings.",
            "scenario": "You are invited to a meeting that appears to be a straightforward status update.",
            "action": "When appropriate, ask whether a short written update or asynchronous message could achieve the same outcome.",
        },
    ],
    "AI Awareness and Responsible Use": [
        {
            "why": "Choosing suitable tasks for AI can help you use it intentionally rather than automatically.",
            "scenario": "You have a repetitive drafting or summarizing task and are unsure whether an approved AI tool would help.",
            "action": "Check workplace rules, assess whether the task is suitable, and compare the result with your usual process.",
        },
        {
            "why": "AI-generated content can sound confident while still containing errors or missing context.",
            "scenario": "An AI tool provides a polished summary that includes a figure or statement you do not recognize.",
            "action": "Verify important claims against reliable source material before using or sharing the output.",
        },
        {
            "why": "Protecting confidential information helps prevent accidental disclosure through digital tools.",
            "scenario": "You want AI help with a document that contains customer, employee, or commercially sensitive details.",
            "action": "Review your organization's approved-tool and data-handling rules; do not enter restricted information into an unapproved tool.",
        },
        {
            "why": "Human review keeps responsibility for decisions and final work with the appropriate person.",
            "scenario": "An AI-generated recommendation looks useful but could affect a customer, colleague, or business decision.",
            "action": "Check the reasoning, context, and possible limitations, and apply your own judgment before relying on it.",
        },
    ],
    "Information Management": [
        {
            "why": "Consistent file names and locations make important work easier to retrieve later.",
            "scenario": "You have several similarly named versions of a presentation saved across different folders.",
            "action": "Use a consistent naming convention, keep the current version in an agreed location, and archive outdated copies when appropriate.",
        },
        {
            "why": "A reliable place for notes and follow-ups reduces the need to rely on memory.",
            "scenario": "After a call, you remember that you promised to do something but cannot recall the exact next step.",
            "action": "Capture the action, owner, and due date in a trusted task list or work notes system.",
        },
        {
            "why": "A simple shared structure can reduce time spent searching for team information.",
            "scenario": "A colleague needs a project file, but each team member stores documents in a different way.",
            "action": "Agree on a common folder structure and naming approach that suits the team's workflow.",
        },
        {
            "why": "Keeping useful information close to the task can make repeated work more efficient.",
            "scenario": "You regularly repeat a process but have to search through old chats to find the instructions.",
            "action": "Create or update a short reference note in an approved, easy-to-find location.",
        },
    ],
    "Digital Wellbeing": [
        {
            "why": "Short breaks can offer a pause from continuous screen work when workload permits.",
            "scenario": "You have worked on a screen for a long stretch and notice your concentration beginning to fade.",
            "action": "When practical, step away briefly, stretch, or look away from the screen before returning to the task.",
        },
        {
            "why": "Reasonable after-hours boundaries can help separate work time from personal time.",
            "scenario": "You keep checking routine work messages after your working day has ended.",
            "action": "Where your role permits, mute non-urgent work notifications outside working hours and agree how genuine emergencies are handled.",
        },
        {
            "why": "Noticing fatigue early can help you choose a sensible pause or adjust your workload.",
            "scenario": "You reread the same information several times and make avoidable mistakes late in the day.",
            "action": "Take a short pause if possible, then review priorities and decide what can reasonably wait.",
        },
        {
            "why": "A manageable digital routine can make it easier to maintain healthy work patterns over time.",
            "scenario": "Your day fills with back-to-back calls, leaving little time for focused tasks or breaks.",
            "action": "Where possible, protect small gaps between meetings and reserve realistic time for focused work and recovery.",
        },
    ],
}

# ---------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------
if "dpi_result" in st.session_state and not st.session_state.get("dpi_save_error", False):

    # Add a target for the browser to scroll to.
    st.markdown(
        '<div id="dpi-results-anchor"></div>',
        unsafe_allow_html=True,
    )

    # Scroll here after the respondent clicks "View my DPI results".
    if st.session_state.get("dpi_scroll_to_results", False):
        import streamlit.components.v1 as components

        components.html(
            """
            <script>
            const scrollToResults = () => {
                const target = window.parent.document.getElementById(
                    "dpi-results-anchor"
                );
                if (target) {
                    target.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });
                }
            };
            scrollToResults();
            </script>
            """,
            height=0,
        )

        st.session_state["dpi_scroll_to_results"] = False

    result = st.session_state["dpi_result"]
    dpi_score = result["overall"]
    dimension_scores = result["dimensions"]

    st.divider()
    st.progress(1.0, text="Step 3 of 3 · Your results")
    st.header("Your Digital Productivity Index")
    st.caption("Your DPI score and suggestions are based on the responses you submitted.")

    st.metric("Overall DPI Score", f"{dpi_score:.1f} / 100")

    if dpi_score < 40:
        interpretation = "Habits to strengthen"
    elif dpi_score < 60:
        interpretation = "Developing habits"
    elif dpi_score < 80:
        interpretation = "Generally established habits"
    elif dpi_score < 85:
        interpretation = "Established habits with room to strengthen"
    else:
        interpretation = "Strong reported habits"

    st.markdown(
        f'<h3 class="dpi-interpretation">{interpretation}</h3>',
        unsafe_allow_html=True,
    )
    
    st.write(
        "The overall interpretation bands are provisional. The DPI is a preliminary, "
        "self-reported index; it is not a percentage of productivity or a validated "
        "measure of job performance."
    )

    st.subheader("Your Dimension Scores")
    score_df = pd.DataFrame(
        [
            {
                "Dimension": dimension,
                "Score (0–100)": round(score, 1),
                "Reported habit": "Strong" if score >= 85 else "Opportunity to strengthen",
            }
            for dimension, score in dimension_scores.items()
        ]
    )
    with st.container(border=True):
        st.dataframe(
            score_df,
            hide_index=True,
            use_container_width=True,
        )
        
    strong_dimensions = [
        (dimension, score)
        for dimension, score in dimension_scores.items()
        if score >= 85
    ]
    if strong_dimensions:
        with st.container(border=True):
            st.markdown(
                '<h3 class="dpi-strong-heading">✨ Strong reported habits</h3>',
                unsafe_allow_html=True,
            )
            st.caption("Dimensions scoring 85 or above are highlighted here.")
            for dimension, score in strong_dimensions:
                st.markdown(f"**{dimension} · {score:.1f}/100**")
                st.write("This is a relative strength in your self-reported results. Consider how you can maintain this habit in your usual work routine.")
    else:
        with st.container(border=True):
            st.markdown("### 🌱 Building stronger habits")
            st.write(
                "No dimension reached the provisional strong-habit threshold of 85 in this result. "
                "You can start with one manageable change and build from there."
            )

    if all(score == 100 for score in dimension_scores.values()):
        st.subheader("🏆 Excellent consistency across all seven dimensions!")
        st.write(
            "Your responses indicate consistently strong reported habits across all dimensions. "
            "Keep practising the routines that work for you, adapt them as your work changes, "
            "and periodically reflect on whether they continue to support your goals."
        )
    else:
        improvement_dimensions = sorted(
            [
                (dimension, score)
                for dimension, score in dimension_scores.items()
                if score < 85
            ],
            key=lambda item: item[1],
        )[:2]

        if improvement_dimensions:
            st.markdown(
                '<h3 class="dpi-suggestions-heading">Suggestions to explore</h3>',
                unsafe_allow_html=True,
            )
            st.write(
                "These suggestions focus on up to two dimensions below the provisional "
                "strong-habit threshold. They are prompts for reflection, not judgments "
                "about your work performance."
            )
            selected_recommendations = st.session_state.setdefault(
                "dpi_recommendations", {}
            )
            for dimension, score in improvement_dimensions:
                if dimension not in selected_recommendations:
                    selected_recommendations[dimension] = random.choice(
                        recommendation_library[dimension]
                    )
                recommendation = selected_recommendations[dimension]
                with st.container(border=True):
                    st.markdown(f"### {dimension} · {score:.1f}/100")
                    st.markdown("**Why it matters**")
                    st.write(recommendation["why"])
                    st.markdown("**A workday scenario**")
                    st.write(recommendation["scenario"])
                    st.markdown("**Action to try**")
                    st.write(recommendation["action"])
        else:
            st.subheader("Keep building on your strengths")
            st.write(
                "All seven dimensions are at or above the provisional strong-habit threshold. "
                "Continue practising the habits that work for you and review them as your work changes."
            )

    st.markdown("---")
    st.caption(
        "Score interpretation bands and recommendations are provisional and intended for reflection. "
        "The DPI is not a diagnostic instrument or an employment assessment tool."
    )
