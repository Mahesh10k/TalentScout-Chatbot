import streamlit as st
import re
from utils import ask_gemini_via_api,  store_user_data

# Page Setup
st.set_page_config(page_title="TalentScout - Hiring Assistant", layout="wide")
# apply_custom_css()

# Custom CSS
st.markdown("""
    <style>
        
        .block-container {
            background-color: #F5F7FA;
        }
        .chat-container {
            background-color: #FFFFFF;
            padding: 1rem;
            border-radius: 1rem;
            max-width: 700px;
            margin: auto;
            margin-bottom: 2rem;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .user-msg, .bot-msg {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 1rem;
        }
        .user-msg {
            justify-content: flex-end;
        }
        .user-msg .msg-content, .bot-msg .msg-content {
            padding: 0.6rem 1rem;
            border-radius: 1rem;
            max-width: 70%;
            line-height: 1.5;
            font-size: 15px;
        }
        .user-msg .msg-content {
            background-color: #DCF8C6;
            color: #000;
        }
        .bot-msg .msg-content {
            background-color: #E4E6EB;
            color: #000;
        }
        .profile-pic {
            width: 35px;
            height: 35px;
            border-radius: 50%;
        }
        input[type="text"] {
            background-color: white;
            color: black;
            border: 1px solid #ccc;
            padding: 10px;
            font-size: 15px;
            border-radius: 5px;
            width: 80%;
        }
        div.stButton > button:first-child {
            background-color: #007BFF;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
        }
        @media only screen and (max-width: 768px) {
            *{
                color: black !important;
            }
            button {
                color: white;
            }
            div.stButton > button:first-child {
                background-color: blue;  
                color: black;
            }
            
        
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'> TalentScout - AI Hiring Assistant</h2>", unsafe_allow_html=True)

# Input questions
questions = [
    ("Full Name", "What's your full name?"),
    ("Email", "Your email address? (Only Gmail is accepted)"),
    ("Phone", "Your phone number? (10 digits only)"),
    ("Years of Experience", "How many years of experience do you have?"),
    ("Desired Position", "Which position are you applying for?"),
    ("Location", "Where are you currently located?"),
    ("Tech Stack", "Mention your tech stack (languages, tools, frameworks):")
]

# Validators
def is_valid_email(email): return re.fullmatch(r"^[\w\.-]+@gmail\.com$", email)
def is_valid_phone(phone): return re.fullmatch(r"[6-9]\d{9}", phone)
def is_valid_name(name): return re.fullmatch(r"[A-Za-z ]+$", name.strip())
def is_non_empty(text): return bool(text.strip())

# Session states
if "step" not in st.session_state:
    st.session_state.step = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "chat" not in st.session_state:
    st.session_state.chat = []
if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = []  
if "answer_index" not in st.session_state:
    st.session_state.answer_index = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = False

# Chat renderer
def render_chat():
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for role, msg in st.session_state.chat:
        if role == "assistant":
            st.markdown(f"""
                <div class='bot-msg'>
                    <img src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png' class='profile-pic'/>
                    <div class='msg-content'>{msg}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='user-msg'>
                    <div class='msg-content'>{msg}</div>
                    <img src='https://cdn-icons-png.flaticon.com/512/847/847969.png' class='profile-pic'/>
                </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

render_chat()

# Step 1: Collect user data
if st.session_state.step < len(questions):
    key, question = questions[st.session_state.step]
    with st.form(key="input_form", clear_on_submit=True):
        user_input = st.text_input(question)
        submitted = st.form_submit_button("Submit")

        if submitted:
            user_input = user_input.strip()
            error = None

            if user_input.lower() in ["exit", "quit", "bye"]:
                st.session_state.chat.append(("assistant", "👋 Thank you for your time. Goodbye!"))
                st.rerun()

            if key == "Email" and not is_valid_email(user_input):
                error = "Please enter a valid Gmail address."
            elif key == "Phone" and not is_valid_phone(user_input):
                error = "Please enter a valid 10-digit Indian phone number."
            elif key == "Full Name" and not is_valid_name(user_input):
                error = "Name should contain only letters and spaces."
            elif not is_non_empty(user_input):
                error = "This field cannot be empty."

            if error:
                st.session_state.chat.append(("assistant", error))
            else:
                st.session_state.chat.append(("assistant", question))
                st.session_state.chat.append(("user", user_input))
                st.session_state.responses[key] = user_input
                st.session_state.step += 1
            st.rerun()

# Step 2: Generate questions
elif not st.session_state.get("generated_questions"):
    tech_stack = st.session_state.responses["Tech Stack"]
    st.session_state.chat.append(("assistant", "Generating technical questions based on your tech stack..."))
    prompt = f"""You're a technical interviewer. Generate 5 technical questions to evaluate a candidate skilled in: {tech_stack}. Number each question."""
    questions_output = ask_gemini_via_api(prompt)
    questions_list = re.findall(r"\d+\.\s*(.*)", questions_output.strip())
    st.session_state.generated_questions = questions_list
    st.session_state.chat.append(("assistant", "Here are your technical questions:\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions_list)])))
    st.rerun()

# Step 3: Ask each question
elif st.session_state.answer_index < len(st.session_state.generated_questions):
    current_q = st.session_state.generated_questions[st.session_state.answer_index]
    st.markdown(f"**Question {st.session_state.answer_index + 1}:** {current_q}")
    user_input = st.chat_input("Your answer:")

    if user_input:
        st.session_state.chat.append(("assistant", current_q))
        st.session_state.chat.append(("user", user_input))
        st.session_state.user_answers.append((current_q, user_input))
        st.session_state.answer_index += 1
        st.rerun()

# Step 4: Give feedback after all answers
elif not st.session_state.feedback_given:
    answer_summary = "\n".join([f"Q: {q}\nA: {a}" for q, a in st.session_state.user_answers])
    feedback_prompt = f"""Evaluate the following technical interview responses:\n\n{answer_summary}\n\nGive a summary of strengths, weaknesses, and whether the candidate is suitable for the role."""
    final_feedback = ask_gemini_via_api(feedback_prompt)
    st.session_state.chat.append(("assistant", f"📊 Final Feedback:\n\n{final_feedback}"))
    st.session_state.feedback_given = True

    mongo_data = {
        "user_info": st.session_state.responses,
        "tech_stack": st.session_state.responses["Tech Stack"],
        "generated_questions": st.session_state.generated_questions,
        "user_answers": st.session_state.user_answers,
        "conversation": st.session_state.chat,
        "final_feedback": final_feedback
    }
    store_user_data(mongo_data)
    st.rerun()

else:
    st.success("✅ Interview process completed.")
    st.info("Thank you for using TalentScout.")
