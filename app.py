import streamlit as st
import re
from utils import ask_gemini_via_api, apply_custom_css, store_user_data

# UI Setup
st.set_page_config(page_title="TalentScout - Hiring Assistant", layout="centered")
apply_custom_css()
st.markdown("""
    <style>
        .block-container{
            background-color: #E7F2E4;
        }
        .chat-container {
            background-color: #B6B09F;
            padding: 1rem;
            border-radius: 1rem;
            max-width: 700px;
            margin: auto;
            margin-bottom: 2rem;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .user-msg {
            background-color: #8DD8FF;
            color:black;
            padding: 0.6rem 1rem;
            border-radius: 1rem;
            margin-bottom: 0.5rem;
            align-self: flex-end;
            max-width: 70%;
            float:right;
        }
        .bot-msg {
            background-color: #FFE1E0;
            color: black;
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

# Questions for user info
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

# Render Chat History
def render_chat():
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for role, msg in st.session_state.chat:
        css_class = "bot-msg" if role == "assistant" else "user-msg"
        st.markdown(f"<div class='{css_class}'>{msg}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

render_chat()

# Input questions
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

# After collecting user info
if st.session_state.step == len(questions):
    tech_stack = st.session_state.responses["Tech Stack"]

    if "generated_questions" not in st.session_state:
        with st.chat_message("assistant"):
            st.markdown("Thank you for sharing your details!")
            st.markdown("Generating technical questions based on your tech stack...")

        prompt = f"""You're a technical interviewer. Generate 5 technical questions (1-2 sentences) to evaluate a candidate skilled in: {tech_stack}. Number each question."""
        questions_output = ask_gemini_via_api(prompt)
        st.session_state.generated_questions = questions_output
        st.session_state.chat.append(("assistant", questions_output))
        st.rerun()

    else:
        with st.chat_message("assistant"):
            st.markdown("Here are your technical questions:")
            st.markdown(st.session_state.generated_questions)

        user_input = st.chat_input("Reply to questions, type 'more' for advanced ones, or continue...")

        if user_input:
            st.session_state.chat.append(("user", user_input))

            if user_input.lower().strip() == "more":
                more_prompt = f"""Generate 5 more advanced technical questions for a candidate skilled in {tech_stack}. Avoid repeating earlier ones."""
                new_questions = ask_gemini_via_api(more_prompt)
                st.session_state.generated_questions += "\n" + new_questions
                st.session_state.chat.append(("assistant", new_questions))
                st.rerun()
            else:
                reply_prompt = f"""The candidate was asked:\n{st.session_state.generated_questions}\nThey responded with:\n{user_input}\nGive a friendly, helpful follow-up."""
                response = ask_gemini_via_api(reply_prompt)
                st.session_state.chat.append(("assistant", response))
                st.rerun()

        # Final feedback once chat ends (optional trigger)
        if not st.chat_input("Type anything..."):  # Or trigger another way
            if "feedback_given" not in st.session_state:
                feedback_prompt = f"""Here are the candidate's answers and responses:\n{st.session_state.chat}
Provide final technical feedback including strengths, weaknesses, and overall suitability."""
                final_feedback = ask_gemini_via_api(feedback_prompt)
                st.session_state.chat.append(("assistant", f"Final Feedback:\n\n{final_feedback}"))
                st.session_state.feedback_given = True

                # Save to MongoDB
                mongo_data = {
                    "user_info": st.session_state.responses,
                    "tech_stack": tech_stack,
                    "generated_questions": st.session_state.generated_questions,
                    "conversation": st.session_state.chat,
                    "final_feedback": final_feedback
                }

                store_user_data(mongo_data)
                st.rerun()
