# app.py

import streamlit as st
import re
from utils import ask_gemini_via_api

# UI Setup
st.set_page_config(page_title="TalentScout - Hiring Assistant", layout="centered")
st.markdown("""
    <style>
        .chat-container {
            background-color: #f9f9f9;
            padding: 1rem;
            border-radius: 1rem;
            max-width: 700px;
            margin: auto;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .user-msg {
            background-color: #DCF8C6;
            padding: 0.6rem 1rem;
            border-radius: 1rem;
            margin-bottom: 0.5rem;
            align-self: flex-end;
            max-width: 70%;
        }
        .bot-msg {
            background-color: #FFFFFF;
            padding: 0.6rem 1rem;
            border-radius: 1rem;
            margin-bottom: 0.5rem;
            align-self: flex-start;
            max-width: 70%;
        }
        .msg-wrapper {
            display: flex;
            flex-direction: column;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'> TalentScout - AI Hiring Assistant</h2>", unsafe_allow_html=True)

# Define questions
questions = [
    ("Full Name", "What's your full name?"),
    ("Email", "Your email address? (Only Gmail is accepted)"),
    ("Phone", "Your phone number? (10 digits only)"),
    ("Years of Experience", "How many years of experience do you have?"),
    ("Desired Position", "Which position are you applying for?"),
    ("Location", "Where are you currently located?"),
    ("Tech Stack", "Mention your tech stack (languages, tools, frameworks):")
]

# Validation functions
def is_valid_email(email):
    return re.fullmatch(r"^[\w\.-]+@gmail\.com$", email)

def is_valid_phone(phone):
    return re.fullmatch(r"[6-9]\d{9}", phone)

def is_valid_name(name):
    return re.fullmatch(r"[A-Za-z ]+$", name.strip())

def is_non_empty(text):
    return bool(text.strip())

# Streamlit session state
if "step" not in st.session_state:
    st.session_state.step = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "chat" not in st.session_state:
    st.session_state.chat = []

# Chat UI rendering
def render_chat():
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for role, msg in st.session_state.chat:
        if role == "assistant":
            st.markdown(f"<div class='bot-msg'>{msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='user-msg'>{msg}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

render_chat()

# Questioning logic
if st.session_state.step < len(questions):
    key, question = questions[st.session_state.step]

    with st.form(key="input_form", clear_on_submit=True):
        user_input = st.text_input(question)
        submitted = st.form_submit_button("Submit")

        if submitted:
            user_input = user_input.strip()

            if user_input.lower() in ["exit", "quit", "bye"]:
                st.session_state.chat.append(("assistant", "👋 Thank you for your time. Goodbye!"))
                st.rerun()

            error = None
            if key == "Email" and not is_valid_email(user_input):
                error = "❌ Please enter a valid Gmail address."
            elif key == "Phone" and not is_valid_phone(user_input):
                error = "❌ Please enter a valid 10-digit Indian phone number."
            elif key == "Full Name" and not is_valid_name(user_input):
                error = "❌ Name should contain only letters and spaces."
            elif not is_non_empty(user_input):
                error = "❌ This field cannot be empty."

            if error:
                st.session_state.chat.append(("assistant", error))
            else:
                st.session_state.chat.append(("assistant", question))
                st.session_state.chat.append(("user", user_input))
                st.session_state.responses[key] = user_input
                st.session_state.step += 1
            st.rerun()

# Generate tech questions
if st.session_state.step == len(questions):
    tech_stack = st.session_state.responses.get("Tech Stack", "")
    prompt = f"""
        You're an expert interviewer. Generate 3 to 5 technical interview questions for a candidate skilled in: {tech_stack}.
    """
    response = ask_gemini_via_api(prompt)
    st.session_state.chat.append(("assistant", "Here are your technical questions:"))
    st.session_state.chat.append(("assistant", response))
    st.session_state.step += 1
    st.rerun()

# End
if st.session_state.step > len(questions):
    st.markdown("<div style='text-align:center;'>🎉 Thank you for using TalentScout!</div>", unsafe_allow_html=True)
