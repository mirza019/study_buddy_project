import streamlit as st
from query_pdf import (
    extract_text_from_pdf,
    generate_quiz_data,
    generate_post_quiz_focus_advice,
    generate_daily_romantic_message,
    generate_night_mode_message
)

# ==============================
# SMART MATH-RENDERER
# ==============================
def render_text(text: str):
    """
    Renders text normally, BUT detects math expressions and renders them in KaTeX.
    Supports inline $...$ and display $$...$$.
    Leaves romance text untouched.
    """

    import re

    # Detect math patterns safely
    inline_math = re.findall(r"\$(.+?)\$", text)
    display_math = re.findall(r"\$\$(.+?)\$\$", text)

    if display_math or inline_math:
        st.markdown(text, unsafe_allow_html=True)
    else:
        st.write(text)


# ==============================
# INITIAL STATE
# ==============================
def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "setup"

    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "name": "",
            "gender": "female",
            "country": "",
            "mood_before": "",
            "mood_after": ""
        }

    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None

    if "current_question" not in st.session_state:
        st.session_state.current_question = 0

    if "score" not in st.session_state:
        st.session_state.score = 0

    if "wrong_focus" not in st.session_state:
        st.session_state.wrong_focus = []

    if "dynamic_feedback" not in st.session_state:
        st.session_state.dynamic_feedback = ""


# ==============================
# PAGE 1 — USER SETUP
# ==============================
def page_setup():
    st.header("📚 Your Study Buddy AI")

    with st.form("setup"):
        st.markdown("Tell me a few details so I can tune myself for you ✨")

        name = st.text_input("What should I call you? ", "")
        gender = st.radio(
            "Choose how I should treat you:",
            ["Pinacle of creation/ Ashraful Makhlukat 😍 (female)", "2nd class creation 😒 (male)"]
        )
        country = st.text_input("Where were you born and raised? 🌍", "")
        mood_before = st.text_input("How’s are you feeling right now? It's Important for me to know", "")

        uploaded_file = st.file_uploader("Upload your study PDF 📄", type=["pdf"])

        btn = st.form_submit_button("Start Study Session ")

        if btn:
            if not uploaded_file:
                st.error("Upload a PDF first, sweetheart!")
                return

            st.session_state.user_info["name"] = name if name else "Sweetheart"
            st.session_state.user_info["country"] = country.strip() or "Unknown"
            st.session_state.user_info["mood_before"] = mood_before.strip()

            st.session_state.user_info["gender"] = (
                "female" if "female" in gender else "male"
            )

            st.session_state.uploaded_file = uploaded_file
            st.session_state.page = "preprocess"
            st.rerun()


# ==============================
# PAGE 2 — STUDY GUIDE
# ==============================
def page_preprocess():
    st.header("📘 Generating Study Guide…")
    st.markdown("Buddy, I'm reading your file carefully… einen moment bitte!!❤️")

    pdf_text = extract_text_from_pdf(st.session_state.uploaded_file)

    quiz_data = generate_quiz_data(pdf_text, st.session_state.user_info)
    st.session_state.quiz_data = quiz_data

    st.success("✨ Personalized Study Guide Ready!")

    st.markdown("## 💖 Soft Summary")
    render_text(quiz_data["sweet_summary"])

    sg = quiz_data["study_guide"]

    st.markdown("## 📚 What This PDF Is Mainly About")
    render_text(sg["overall_advice"])

    st.warning("📝 **Exam Strategy:**")
    render_text(sg["exam_strategy"])

    st.markdown("## 🔥 Key Topics")
    for topic in sg["key_topics"]:
        st.markdown(f"- {topic}")

    st.markdown("## ✨ Nuance Notes")
    for t in sg["topic_notes"]:
        st.markdown(f"### **{t['topic']}**")
        render_text(f"- 💡 {t['nuance_note']}")
        render_text(f"- 🎯 {t['why_important']}")

    if st.button("Start Quiz ❤️"):
        st.session_state.page = "quiz"
        st.rerun()


# ==============================
# PAGE 3 — QUIZ LOOP
# ==============================
def page_quiz():
    quiz = st.session_state.quiz_data
    q_index = st.session_state.current_question
    total_q = len(quiz["questions"])

    if q_index >= total_q:
        st.session_state.page = "results"
        st.rerun()
        return

    question = quiz["questions"][q_index]

    st.header(f"📖 Question {q_index + 1} / {total_q}")

    render_text(f"### 💬 {question['introduction']}")
    render_text(question["question_text"])

    options = question["options"]
    opt_labels = [f"[{k}] {v}" for k, v in options.items()]
    selected = st.radio("Choose your answer:", opt_labels, index=None)

    selected_key = None
    if selected:
        selected_key = selected.split("]")[0].strip("[")

    # SUBMIT ANSWER
    if not st.session_state.get("awaiting_next", False):

        if st.button("Submit Answer 💌", disabled=(selected_key is None)):

            correct_key = question["correct_answer_key"]

            # NEW — generate dynamic feedback with explicit answer explanation
            from query_pdf import generate_dynamic_feedback

            payload = {
                "user_info": st.session_state.user_info,
                "selected_key": selected_key,
                "selected_text": options[selected_key],
                "correct_key": correct_key,
                "correct_text": options[correct_key],
                "base_correct": question["correct_feedback_script"],
                "base_incorrect": question["incorrect_feedback_script"],
                "base_pass": question["pass_feedback_script"],
            }

            # Get dynamically generated romantic/sarcastic feedback
            feedback = generate_dynamic_feedback(payload)
            st.session_state.dynamic_feedback = feedback


            if selected_key == correct_key:
                st.session_state.score += 1
            else:
                if selected_key != "E":
                    st.session_state.wrong_focus.append(question["focus_if_wrong"])

            st.session_state.awaiting_next = True
            st.rerun()

    else:
        st.markdown("### 💝 **Your Feedback**")
        render_text(st.session_state.dynamic_feedback)

        if st.button("Next ➜"):
            st.session_state.awaiting_next = False
            st.session_state.current_question += 1
            st.rerun()


# ==============================
# PAGE 4 — RESULTS
# ==============================
def page_results():
    user = st.session_state.user_info
    total = len(st.session_state.quiz_data["questions"])
    score = st.session_state.score
    percent = (score / total) * 100

    st.header("🎉 Quiz Completed!")

    if user["gender"] == "female":
        st.balloons()
        st.success(
            f"My love {user['name']}… you scored **{score}/{total} ({percent:.1f}%)**. "
            f"I'm so proud of you baby 🥺💗"
        )
    else:
        st.error(
            f"{user['name']}… {score}/{total} ({percent:.1f}%). "
            f"Honestly? I expected you to do worse. Miracles do happen 🙄"
        )

    user["mood_after"] = st.text_input("How do you feel now, sweetheart? ")

    st.markdown("---")
    st.subheader("📚 What You Should Study More")

    advice = generate_post_quiz_focus_advice(
        user,
        st.session_state.wrong_focus
    )
    render_text(advice)

    st.markdown("---")

    if st.button("💌 Daily Romantic Message"):
        msg = generate_daily_romantic_message(user, st.session_state.quiz_data)
        render_text(msg)

    if st.button("🌙 Night Whisper"):
        msg = generate_night_mode_message(user, st.session_state.quiz_data)
        render_text(msg)

    if st.button("Start New Quiz ❤️"):
        st.session_state.clear()
        init_state()
        st.rerun()


# ==============================
# MAIN APP
# ==============================
def main():
    st.set_page_config(
        page_title="Study Buddy AI",
        page_icon="📚",
        layout="centered"
    )
    init_state()

    if st.session_state.page == "setup":
        page_setup()
    elif st.session_state.page == "preprocess":
        page_preprocess()
    elif st.session_state.page == "quiz":
        page_quiz()
    elif st.session_state.page == "results":
        page_results()
            # --------------------------
    # FOOTER CREDIT
    # --------------------------
    st.markdown("""
        <hr style="margin-top:40px; margin-bottom:10px; border: 0.5px solid #555;">
        <div style="text-align: center; color: #bbb; font-size: 14px; padding-top: 10px;">
            Developed with ❤️ by <b>Mirza Shaheen Iqubal</b><br>
            Powered by <span style="color:#8ab4f8;"><b>Google Gemini</b></span>
        </div>
    """, unsafe_allow_html=True)



if __name__ == "__main__":
    
    main()
