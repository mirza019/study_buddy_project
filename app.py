import streamlit as st
import base64
import re
import os
import streamlit.components.v1 as components

# ============================================================
# CONFIG — IMAGES
# ============================================================
BUDDY_IMG = "Buddy.png"
Ask_Buddy_IMG = "Ask_Buddy.png"
USER_MALE = "male_user.png"
USER_FEMALE = "female_user.png"



# ============================================================
# BACKEND FUNCTIONS FROM query_pdf
# ============================================================
from query_pdf import (
    extract_text_from_pdf,
    generate_quiz_data,
    generate_dynamic_feedback,
    generate_post_quiz_focus_advice,
    generate_daily_romantic_message,
    generate_night_mode_message,
    generate_gods_message,
    run_chat_from_pdf,
)


# ============================================================
# MATH RENDER
# ============================================================
def render_text(text):
    inline = re.findall(r"\$(.+?)\$", text)
    block = re.findall(r"\$\$(.+?)\$\$", text)
    if inline or block:
        st.markdown(text, unsafe_allow_html=True)
    else:
        st.write(text)


# ============================================================
# CHAT BUBBLE (Buddy Left)
# ============================================================
def bubble_buddy(message):
    st.markdown(
        f"""
        <div style="display:flex; align-items:flex-start; margin:10px 0;">
            <img src="data:image/png;base64,{BUDDY_IMG}"
                 style="width:40px; height:40px; border-radius:50%; margin-right:10px;">
            <div style="
                background:#2d2d2d;
                padding:12px 16px;
                border-radius:14px;
                color:#fff;
                max-width:70%;
                font-size:16px;
            ">
                <b>Buddy</b><br>
                {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# CHAT BUBBLE (User Right)
# ============================================================
def bubble_user(username, message, gender):
    if gender == "female":
        avatar = USER_FEMALE
    else:
        avatar = USER_MALE

    st.markdown(
        f"""
        <div style="display:flex; justify-content:flex-end; margin:10px 0;">
            <div style="
                background:#1e1e1e;
                padding:12px 16px;
                border-radius:14px;
                color:#fff;
                max-width:70%;
                font-size:16px;
                text-align:right;
                margin-right:10px;
            ">
                <b>{username}</b><br>
                {message}
            </div>
            <img src="data:image/png;base64,{avatar}"
                 style="width:40px; height:40px; border-radius:50%;">
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# TEXT INPUT (Ask Buddy) — Native Streamlit
# ============================================================
def ask_input():
    col1, col2 = st.columns([9, 1])
    with col1:
        user_text = st.text_input("", placeholder="Ask Buddy anything…", key="ask_field")
    with col2:
        submitted = st.button("Ask")
    enter_pressed = False

    if st.session_state.get("ask_field_submit"):
        enter_pressed = True
        st.session_state.ask_field_submit = False

    return user_text, (submitted or enter_pressed)


# Hack to detect ENTER
st.session_state.setdefault("ask_field_submit", False)
st.markdown("""
<script>
const input = window.parent.document.querySelector('input[id="ask_field"]');
if (input){
  input.addEventListener("keydown", function(e){
    if(e.key==="Enter"){
      window.parent.postMessage(
        {isStreamlitMessage: true, type:"streamlit:setComponentValue",
         key:"ask_field_submit", value:true},
        "*"
      );
    }
  });
}
</script>
""", unsafe_allow_html=True)


# ============================================================
# FLOATING MENU BUTTON
# ============================================================
def floating_menu():
    st.markdown("""
        <style>
        .menu-btn {
            position: fixed;
            top: 15px;
            left: 15px;
            z-index: 999999;
            background:#444;
            padding:8px 14px;
            border-radius:10px;
            color:white;
            font-size:18px;
            cursor:pointer;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.button("☰ Menu", key="floating_menu_button"):
        st.session_state.menu_open = not st.session_state.get("menu_open", False)
        st.rerun()

    if st.session_state.get("menu_open"):
        with st.container():
            st.markdown(
                """
                <div style='
                    position:fixed;
                    top:60px;
                    left:15px;
                    background:#222;
                    padding:15px;
                    width:240px;
                    border-radius:12px;
                    border:1px solid #555;
                    z-index:999999;
                '>
                """,
                unsafe_allow_html=True,
            )

            if st.button("📘 Study Guidance"):
                st.session_state.page = "guide"
                st.session_state.menu_open = False
                st.rerun()

            if st.button("💬 Ask Buddy"):
                st.session_state.page = "chat"
                st.session_state.menu_open = False
                st.rerun()

            if st.button("📝 Quiz Mode"):
                st.session_state.page = "quiz"
                st.session_state.menu_open = False
                st.rerun()

            if st.button("📤 Upload PDF Again"):
                st.session_state.page = "setup_pdf"
                st.session_state.menu_open = False
                st.rerun()

            if st.button("🔄 Restart Session"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                init_state()
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# SHOW MENU ONLY AFTER GUIDE
# ============================================================
def maybe_show_menu():
    """
    Show menu ONLY after the PDF is processed.
    Never show during setup flow.
    """

    pages_without_menu = {
        "setup",
        "setup_gender",
        "setup_country",
        "setup_mood",
        "setup_pdf",
        "preprocess",
    }

    # If current page is NOT in the setup flow → show menu
    if st.session_state.page not in pages_without_menu:
        floating_menu()


# ============================================================
# INIT SESSION
# ============================================================
def init_state():
    defaults = {
        "page": "setup",
        "user_info": {
            "name": "",
            "gender": "female",
            "country": "",
            "mood_before": "",
            "mood_after": "",
        },
        "uploaded_file": None,
        "pdf_text": None,
        "quiz_data": None,
        "chat_history": [],
        "current_question": 0,
        "score": 0,
        "wrong_focus": [],
        "menu_open": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
# ============================================================
# SINGLE PAGE — NAME + GENDER + COUNTRY + MOOD
# ============================================================
def page_setup():
    st.image(BUDDY_IMG, width=120)
    st.header("Buddy — Your Personal Study Partner ❤️")

    st.markdown("Tell Buddy a few things, so I can treat you perfectly 😘")

    # -------------------------------
    # NAME
    # -------------------------------
    name = st.text_input(
        "💖 Buddy, what should I call you?",
        key="input_name"
    )

    # -------------------------------
    # GENDER
    # -------------------------------
    gender = st.radio(
        "💞 How should Buddy treat you?",
        [
            "Pinnacle of Creation / Ashraful Makhlukat 😍 (female)",
            "Men 😒"
        ],
        key="radio_gender"
    )

    # -------------------------------
    # COUNTRY
    # -------------------------------
    country = st.text_input(
        "🌍 Where were you born and raised?",
        key="input_country"
    )

    # -------------------------------
    # MOOD
    # -------------------------------
    mood = st.text_input(
        "❤️ How do you feel right now?",
        key="input_mood_before"
    )

    # -------------------------------
    # NEXT BUTTON
    # -------------------------------
    if st.button("Next ➜", use_container_width=True):
        if not name.strip():
            st.error("Tell me your beautiful name first, sweetheart 😘")
            return

        # Save all details
        st.session_state.user_info["name"] = name.strip()
        st.session_state.user_info["country"] = country.strip() or "Unknown"
        st.session_state.user_info["mood_before"] = mood.strip()

        if "female" in gender.lower():
            st.session_state.user_info["gender"] = "female"
        else:
            st.session_state.user_info["gender"] = "male"

        # Move to PDF upload
        st.session_state.page = "setup_pdf"
        st.rerun()


# ============================================================
# PAGE 5 — PDF UPLOAD
# ============================================================
def page_setup_pdf():
    st.image(BUDDY_IMG, width=120)
    st.header("Upload your study PDF 📘")

    uploaded = st.file_uploader("Be Kind and Choose Only One PDF", type=["pdf"], key="pdf_uploader")

    if uploaded and st.button("Process PDF ❤️", use_container_width=True):
        st.session_state.uploaded_file = uploaded
        st.session_state.page = "preprocess"
        st.rerun()


# ============================================================
# PAGE 6 — PROCESS PDF
# ============================================================
def page_preprocess():
    st.image(BUDDY_IMG, width=120)
    st.header("📘 Buddy I am reading your PDF… Einen Moment bitte. ❤️")

    pdf_file = st.session_state.uploaded_file
    text = extract_text_from_pdf(pdf_file)
    st.session_state.pdf_text = text

    # Generate quiz + study guide
    st.session_state.quiz_data = generate_quiz_data(
        text,
        st.session_state.user_info
    )

    st.session_state.page = "guide"
    st.rerun()
# ============================================================
# PAGE — STUDY GUIDANCE (MAIN PAGE AFTER PDF PROCESS)
# ============================================================
def page_study_guidance():
    maybe_show_menu()

    qz = st.session_state.quiz_data
    sg = qz["study_guide"]

    st.image(BUDDY_IMG, width=120)
    st.header("📘 Study Guidance")

    # ----------------------------------------
    # Soft Romantic Summary
    # ----------------------------------------
    st.subheader("💖 Soft Summary")
    render_text(qz["sweet_summary"])

    # ----------------------------------------
    # About the Document
    # ----------------------------------------
    st.subheader("📚 What This PDF Is About")
    render_text(sg["overall_advice"])

    # ----------------------------------------
    # Exam Strategy
    # ----------------------------------------
    st.subheader("📝 Exam Strategy")
    render_text(sg["exam_strategy"])

    # ----------------------------------------
    # Key Topics
    # ----------------------------------------
    st.subheader("🔥 Key Topics")
    for t in sg["key_topics"]:
        st.write("• " + t)

    # ----------------------------------------
    # Nuance Notes
    # ----------------------------------------
    st.subheader("✨ Nuance Notes")
    for t in sg["topic_notes"]:
        st.markdown(f"### {t['topic']}")
        render_text(f"💡 {t['nuance_note']}")
        render_text(f"🎯 {t['why_important']}")

    st.markdown("---")

    # ----------------------------------------
    # Navigation Buttons
    # ----------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💬 Ask Buddy", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()

    with col2:
        if st.button("📝 Start Quiz", use_container_width=True):
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.wrong_focus = []
            st.session_state.page = "quiz"
            st.rerun()

    with col3:
        if st.button("⬅️ Back (Upload Again)", use_container_width=True):
            st.session_state.page = "setup_pdf"
            st.rerun()
# ============================================================
# PAGE — CHAT (ASK BUDDY)
# ============================================================
def page_chat():
    maybe_show_menu()
    user = st.session_state.user_info

    # ============================
    # Header + Buddy Avatar
    # ============================
    st.image(BUDDY_IMG, width=80)

    st.header("💬 Chat with Buddy")

    # ============================
    # Load correct user avatar
    # ============================
    if user["gender"] == "male":
        user_avatar = "male_user.png"
    else:
        user_avatar = "female_user.png"

    buddy_avatar = Ask_Buddy_IMG

    # ============================
    # SHOW CHAT HISTORY
    # ============================
    for role, msg in st.session_state.chat_history:
        if role == "assistant":
            st.chat_message("assistant", avatar=buddy_avatar).write(msg)
        else:
            st.chat_message("user", avatar=user_avatar).write(msg)

    # ============================
    # SINGLE CHAT INPUT — CLEAN
    # ============================
    question = st.chat_input(f"Ask Buddy something, {user['name']}…")

    if question:
        # Save user message
        st.session_state.chat_history.append(("user", question))

        # Generate answer
        raw_ans = run_chat_from_pdf(
            question,
            st.session_state.pdf_text,
            st.session_state.user_info
        )

        # Remove HTML tags — Gemini sometimes adds <div> <p>
        import re
        clean_ans = re.sub(r"<[^>]+>", "", raw_ans)

        # Save assistant message
        st.session_state.chat_history.append(("assistant", clean_ans))

        st.rerun()

    # ============================
    # MENU NAVIGATION
    # ============================
    if st.button("⬅ Back to Menu"):
        st.session_state.page = "guide"
        st.rerun()

# ============================================================
# PAGE — QUIZ QUESTION
# ============================================================
def page_quiz():
    maybe_show_menu()

    quiz = st.session_state.quiz_data
    i = st.session_state.current_question

    # End of quiz → go to result page
    if i >= len(quiz["questions"]):
        st.session_state.page = "results"
        st.rerun()

    q = quiz["questions"][i]

    st.image(BUDDY_IMG, width=80)
    st.header(f"📖 Question {i+1} / {len(quiz['questions'])}")

    render_text(q["introduction"])
    render_text(q["question_text"])

    # ============================
    # OPTIONS RENDER
    # ============================
    options = q["options"]
    labels = [f"[{k}] {v}" for k, v in options.items()]

    # Always define selected_key = None initially
    selected_key = None

    selected_label = st.radio("Choose one:", labels, index=None)

    # Extract key safely
    if selected_label:
        selected_key = selected_label.split("]")[0].strip("[")

    # ============================
    # SUBMIT BUTTON
    # ============================
    if st.button("Submit 💌", disabled=(selected_key is None)):

        # ❗ SAVE THE USER'S CHOICE HERE ❗
        q["user_selected"] = selected_key

        # Create payload for feedback generation
        payload = {
            "user_info": st.session_state.user_info,
            "selected_key": selected_key,
            "selected_text": options[selected_key],
            "correct_key": q["correct_answer_key"],
            "correct_text": options[q["correct_answer_key"]],
            "base_correct": q["correct_feedback_script"],
            "base_incorrect": q["incorrect_feedback_script"],
            "base_pass": q["pass_feedback_script"],
        }

        st.session_state.dynamic_feedback = generate_dynamic_feedback(payload)

        # Score
        if selected_key == q["correct_answer_key"]:
            st.session_state.score += 1
        else:
            if selected_key != "E":
                st.session_state.wrong_focus.append(q["focus_if_wrong"])

        st.session_state.page = "quiz_feedback"
        st.rerun()



# ============================================================
# PAGE — QUIZ FEEDBACK
# ============================================================
def page_quiz_feedback():
    maybe_show_menu()

    st.image(BUDDY_IMG, width=90)
    st.header("💝 Your Feedback")

    render_text(st.session_state.dynamic_feedback)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Next Question ➜"):
            st.session_state.current_question += 1
            st.session_state.page = "quiz"
            st.rerun()

    with col2:
        if st.button("Finish Quiz ❤️"):
            st.session_state.page = "results"
            st.rerun()


# ============================================================
# PAGE — QUIZ RESULTS (Summary Only)
# ============================================================
def page_results():
    maybe_show_menu()

    user = st.session_state.user_info
    quiz = st.session_state.quiz_data

    score = st.session_state.score
    total = len(quiz["questions"])
    pct = (score / total) * 100

    st.image(BUDDY_IMG, width=90)
    st.header("🎉 Quiz Completed!")

    # =============================
    # MAIN RESULT MESSAGE
    # =============================
    if user["gender"] == "female":
        st.success(
            f"My love {user['name']}… you scored **{score}/{total} ({pct:.1f}%)** 🥺💗"
        )
    else:
        st.error(
            f"{user['name']}… {score}/{total} ({pct:.1f}%)**. "
            f"Honestly… expected worse 🙄."
        )

    st.markdown("---")

    # =============================
    # FULL REVIEW (Combined Page)
    # =============================
    st.subheader("📝 Full Review")

    for i, q in enumerate(quiz["questions"], start=1):
        st.markdown(f"### ❓ Question {i}")

        # Question text
        render_text(q["question_text"])

        options = q.get("options", {})
        correct_key = q.get("correct_answer_key")
        user_key = q.get("user_selected", None)

        correct_text = options.get(correct_key, "Unknown")
        user_text = options.get(user_key, "No answer selected")

        # --- correct answer
        if user_key == correct_key:
            st.markdown(
                f"""
                <div style="background:#113d1a;
                            padding:12px;
                            border-radius:10px;
                            margin-top:10px;
                            color:#a6ffb3;
                            font-size:16px;">
                    ✔ <b>Your Answer (Correct):</b> {correct_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # --- wrong answer
        else:
            # User selected something
            if user_key:
                st.markdown(
                    f"""
                    <div style="background:#4a1717;
                                padding:12px;
                                border-radius:10px;
                                margin-top:10px;
                                color:#ffb3b3;
                                font-size:16px;">
                        ❌ <b>Your Answer (Wrong):</b> {user_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                # User selected nothing
                st.markdown(
                    f"""
                    <div style="background:#4a1717;
                                padding:12px;
                                border-radius:10px;
                                margin-top:10px;
                                color:#ffb3b3;
                                font-size:16px;">
                        ❌ <b>You did not select an answer.</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Always show correct answer below
            st.markdown(
                f"""
                <div style="background:#113d1a;
                            padding:12px;
                            border-radius:10px;
                            margin-top:10px;
                            color:#a6ffb3;
                            font-size:16px;">
                    ✔ <b>Correct Answer:</b> {correct_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<hr style='opacity:0.3;'>", unsafe_allow_html=True)

    # =============================
    # BUTTON — now OUTSIDE loop
    # =============================
    if st.button("Your Weak Spots (Let’s Fix Them) ➜", use_container_width=True):
        st.session_state.page = "focus_page"
        st.rerun()  


    st.markdown("---")

    if st.button("❤️ Start New Session"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_state()
        st.rerun()


      
# ============================================================
# PAGE — FULL QUIZ REVIEW (17 QUESTIONS)
# ============================================================


# ============================================================
# PAGE — FOCUS & MESSAGES PAGE
# ============================================================
def page_focus():
    maybe_show_menu()

    user = st.session_state.user_info

    st.image(BUDDY_IMG, width=100)
    st.header("🔍 Topics That Need More Attention")

    # ================================================
    # MAIN FOCUS ADVICE
    # ================================================
    advice = generate_post_quiz_focus_advice(
        user,
        st.session_state.wrong_focus
    )
    render_text(advice)

    st.markdown("---")

    # ================================================
    # INTERACTIVE MESSAGE POP-UPS
    # ================================================

    # Store toggle states safely
    if "show_romantic" not in st.session_state:
        st.session_state.show_romantic = False

    if "show_night" not in st.session_state:
        st.session_state.show_night = False

    if "show_god" not in st.session_state:
        st.session_state.show_god = False

    # --- Romantic Message Button ---
    if st.button("💌 Buddy’s Message For you"):
        st.session_state.show_romantic = not st.session_state.show_romantic

    if st.session_state.show_romantic:
        with st.expander("Your Buddy is missing you", expanded=True):
            msg = generate_daily_romantic_message(user, st.session_state.quiz_data)
            render_text(msg)

    st.markdown("---")

    # --- Night Whisper Button ---
    if st.button("🌙 Night Whisper"):
        st.session_state.show_night = not st.session_state.show_night

    if st.session_state.show_night:
        with st.expander("🌙 Soft Night Whisper", expanded=True):
            msg = generate_night_mode_message(user, st.session_state.quiz_data)
            render_text(msg)

    st.markdown("---")

    # --- God’s Message Button ---
    if st.button("🕊 God’s Message"):
        st.session_state.show_god = not st.session_state.show_god

    if st.session_state.show_god:
        with st.expander("🕊 A Message from God", expanded=True):
            msg = generate_gods_message(user)
            render_text(msg)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Back to Menu"):
            st.session_state.page = "guide"
            st.rerun()

    with col2:
        if st.button("Restart Session ❤️"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            init_state()
            st.rerun()

# ============================================================
# MAIN APP ROUTER
# ============================================================
def main():
    st.set_page_config(
        page_title="Study Buddy AI",
        page_icon=BUDDY_IMG,
        layout="wide"
    )

    init_state()  # Ensure everything exists

    page = st.session_state.page

    # ROUTES
    if page == "setup":
        page_setup()

    elif page == "setup_gender":
        page_setup_gender()

    elif page == "setup_country":
        page_setup_country()

    elif page == "setup_mood":
        page_setup_mood()

    elif page == "setup_pdf":
        page_setup_pdf()

    elif page == "preprocess":
        page_preprocess()

    elif page == "guide":
        page_study_guidance()

    elif page == "chat":
        page_chat()

    elif page == "quiz":
        page_quiz()

    elif page == "quiz_feedback":
        page_quiz_feedback()

    elif page == "results":
        page_results()


    elif page == "focus_page":
        page_focus()


# ============================================================
# RUN THE APP
# ============================================================
if __name__ == "__main__":
    main()
