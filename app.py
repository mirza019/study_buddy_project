import streamlit as st
import base64
import re
import os

# ============================================================
# CONFIG — LOCAL BUDDY IMAGE
# ============================================================
BUDDY_PATH = "Buddy.png"

def get_buddy_image_html(size=70):
    if not os.path.exists(BUDDY_PATH):
        return ""
    with open(BUDDY_PATH, "rb") as f:
        img64 = base64.b64encode(f.read()).decode()
    return f"""
        <img src="data:image/png;base64,{img64}"
             style="width:{size}px; border-radius:50%; margin-bottom:10px;">
    """


# ============================================================
# IMPORT BACKEND PDF FUNCTIONS
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
# SMART MATH RENDERER
# ============================================================
def render_text(text: str):
    inline = re.findall(r"\$(.+?)\$", text)
    display = re.findall(r"\$\$(.+?)\$\$", text)
    if inline or display:
        st.markdown(text, unsafe_allow_html=True)
    else:
        st.write(text)


# ============================================================
# MOBILE-FRIENDLY TEXT INPUT (ENTER = SUBMIT)
# ============================================================
def mobile_text_input(label, key):
    """
    - Textbox
    - Button below
    - ENTER also triggers submit
    """
    value = st.text_input(label, key=key)

    enter_pressed = False
    if value and st.session_state.get(key) == value:
        enter_pressed = True

    submit = st.button("Next ➜", key=f"{key}_btn", use_container_width=True)

    return value, (submit or enter_pressed)


# ============================================================
# CHAT INPUT — CHATGPT STYLE
# ============================================================
def chat_with_send_icon(key="chat_msg", placeholder="Type…"):
    """
    Custom chat box with:
    - Enter to send
    - Send icon ➤ inside the input
    """

    html = f"""
    <style>
    .chatbox {{
        display:flex;
        align-items:center;
        gap:10px;
        margin-top:10px;
    }}
    .chatbox input {{
        flex:1;
        padding:12px;
        border-radius:12px;
        background:#111;
        border:1px solid #555;
        color:white;
    }}
    .chatbox button {{
        background:#4a8df6;
        color:white;
        border:none;
        padding:10px 14px;
        border-radius:12px;
        cursor:pointer;
        font-size:18px;
    }}
    </style>

    <div class="chatbox">
        <input id="{key}" placeholder="{placeholder}">
        <button onclick="send_{key}()">➤</button>
    </div>

    <script>
    function send_{key}() {{
        const input = document.getElementById("{key}");
        const pyInput = window.parent.document
            .getElementById("hidden_{key}");
        pyInput.value = input.value;
        pyInput.dispatchEvent(new Event("input", {{ bubbles: true }}));
    }}

    document.getElementById("{key}").addEventListener("keydown", function(e) {{
        if(e.key === "Enter") {{
            send_{key}();
        }}
    }});
    </script>
    """

    st.markdown(html, unsafe_allow_html=True)

    hidden = st.text_input("hidden", key=f"hidden_{key}", label_visibility="collapsed")

    return hidden if hidden else None


# ============================================================
# SESSION INIT
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
        "dynamic_feedback": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# PAGE 1 — NAME
# ============================================================
def page_setup():
    st.markdown(get_buddy_image_html(100), unsafe_allow_html=True)
    st.header("Buddy — Your Study Partner ❤️")

    name, ok = mobile_text_input("What should I call you? 💕", key="name")
    if ok:
        st.session_state.user_info["name"] = name.strip() or "Sweetheart"
        st.session_state.page = "setup_gender"
        st.rerun()


# ============================================================
# PAGE 2 — GENDER
# ============================================================
def page_setup_gender():
    st.markdown(get_buddy_image_html(90), unsafe_allow_html=True)
    st.header("How should Buddy treat you? 💞")

    gender = st.radio(
        "",
        ["Pinacle of Creation/Ashraful Makhlukat 😍 (female)", "2nd class creation 😒 (male)"]
    )

    if st.button("Next ➜"):
        st.session_state.user_info["gender"] = (
            "female" if "female" in gender else "male"
        )
        st.session_state.page = "setup_country"
        st.rerun()


# ============================================================
# PAGE 3 — COUNTRY
# ============================================================
def page_setup_country():
    st.markdown(get_buddy_image_html(90), unsafe_allow_html=True)
    st.header("Where were you born and raised, Buddy? 🌍")

    val, ok = mobile_text_input("Country:", key="country")
    if ok:
        st.session_state.user_info["country"] = val.strip() or "Unknown"
        st.session_state.page = "setup_mood"
        st.rerun()


# ============================================================
# PAGE 4 — MOOD
# ============================================================
def page_setup_mood():
    st.markdown(get_buddy_image_html(90), unsafe_allow_html=True)
    st.header("How do you feel right now? ❤️")

    mood, ok = mobile_text_input("Your mood:", key="mood_before")
    if ok:
        st.session_state.user_info["mood_before"] = mood.strip()
        st.session_state.page = "setup_pdf"
        st.rerun()


# ============================================================
# PAGE 5 — PDF UPLOAD
# ============================================================
def page_setup_pdf():
    st.markdown(get_buddy_image_html(90), unsafe_allow_html=True)
    st.header("Upload your study PDF 📘")

    f = st.file_uploader("Choose PDF", type=["pdf"])

    if f and st.button("Process PDF ❤️", use_container_width=True):
        st.session_state.uploaded_file = f
        st.session_state.page = "preprocess"
        st.rerun()


# ============================================================
# PAGE 6 — STUDY GUIDE
# ============================================================
def page_preprocess():
    st.markdown(get_buddy_image_html(90), unsafe_allow_html=True)
    st.header("📘 Reading your PDF… einen moment bitte ❤️")

    text = extract_text_from_pdf(st.session_state.uploaded_file)
    st.session_state.pdf_text = text

    quiz_data = generate_quiz_data(text, st.session_state.user_info)
    st.session_state.quiz_data = quiz_data

    st.success("✨ Study Guide Ready!")

    sg = quiz_data["study_guide"]

    st.subheader("💖 Soft Summary")
    render_text(quiz_data["sweet_summary"])

    st.subheader("📚 What It's About")
    render_text(sg["overall_advice"])

    st.subheader("📝 Exam Strategy")
    render_text(sg["exam_strategy"])

    st.subheader("🔥 Key Topics")
    for t in sg["key_topics"]:
        st.write("- " + t)

    st.subheader("✨ Nuance Notes")
    for t in sg["topic_notes"]:
        st.markdown(f"### {t['topic']}")
        render_text(f"- 💡 {t['nuance_note']}")
        render_text(f"- 🎯 {t['why_important']}")

    if st.button("Go to Menu ➜", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()


# ============================================================
# PAGE — MENU
# ============================================================
def page_menu():
    st.markdown(get_buddy_image_html(100), unsafe_allow_html=True)
    st.header("📚 Buddy Menu")

    if st.button("📘 Study Guidance"):
        st.session_state.page = "guide"
        st.rerun()
    if st.button("💬 Chat from PDF"):
        st.session_state.page = "chat"
        st.rerun()
    if st.button("📝 Quiz Mode"):
        st.session_state.page = "quiz"
        st.rerun()


# ============================================================
# PAGE — GUIDANCE VIEW
# ============================================================
def page_study_guidance():
    qz = st.session_state.quiz_data
    sg = qz["study_guide"]

    st.markdown(get_buddy_image_html(90), unsafe_allow_html=True)
    st.header("📘 Study Guidance")

    st.subheader("💖 Soft Summary")
    render_text(qz["sweet_summary"])

    st.subheader("📚 About")
    render_text(sg["overall_advice"])

    st.subheader("📝 Exam Strategy")
    render_text(sg["exam_strategy"])

    st.subheader("🔥 Key Topics")
    for t in sg["key_topics"]:
        st.write("- " + t)

    st.subheader("✨ Nuance Notes")
    for t in sg["topic_notes"]:
        st.markdown(f"### {t['topic']}")
        render_text(f"💡 {t['nuance_note']}")
        render_text(f"🎯 {t['why_important']}")

    if st.button("Back to Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()


# ============================================================
# PAGE — CHAT GPT-LIKE CHAT
# ============================================================
def page_chat():
    st.markdown(get_buddy_image_html(80), unsafe_allow_html=True)
    st.header("💬 Chat with Buddy")

    # Print chat history
    for role, msg in st.session_state.chat_history:
        if role == "assistant":
            st.chat_message("assistant").markdown(
                get_buddy_image_html(40) + "<br>" + msg,
                unsafe_allow_html=True
            )
        else:
            st.chat_message("user").write(msg)

    # ChatGPT-style input
    q = chat_with_send_icon("docchat", "Ask Buddy anything…")

    if q:
        st.session_state.chat_history.append(("user", q))
        ans = run_chat_from_pdf(q, st.session_state.pdf_text, st.session_state.user_info)
        st.session_state.chat_history.append(("assistant", ans))
        st.rerun()

    if st.button("Back to Menu"):
        st.session_state.page = "menu"
        st.rerun()


# ============================================================
# PAGE — QUIZ
# ============================================================
def page_quiz():
    quiz = st.session_state.quiz_data
    i = st.session_state.current_question

    if i >= len(quiz["questions"]):
        st.session_state.page = "results"
        st.rerun()

    q = quiz["questions"][i]

    st.markdown(get_buddy_image_html(80), unsafe_allow_html=True)
    st.header(f"📖 Question {i+1} / {len(quiz['questions'])}")

    render_text(q["introduction"])
    render_text(q["question_text"])

    opts = q["options"]
    labels = [f"[{k}] {v}" for k, v in opts.items()]

    sel = st.radio("Choose:", labels, index=None)

    if sel:
        key = sel.split("]")[0].strip("[")
    else:
        key = None

    if st.button("Submit 💌", disabled=(key is None)):
        payload = {
            "user_info": st.session_state.user_info,
            "selected_key": key,
            "selected_text": opts[key],
            "correct_key": q["correct_answer_key"],
            "correct_text": opts[q["correct_answer_key"]],
            "base_correct": q["correct_feedback_script"],
            "base_incorrect": q["incorrect_feedback_script"],
            "base_pass": q["pass_feedback_script"],
        }

        st.session_state.dynamic_feedback = generate_dynamic_feedback(payload)

        if key == q["correct_answer_key"]:
            st.session_state.score += 1
        else:
            if key != "E":
                st.session_state.wrong_focus.append(q["focus_if_wrong"])

        st.session_state.page = "quiz_feedback"
        st.rerun()


# ============================================================
# PAGE — QUIZ FEEDBACK
# ============================================================
def page_quiz_feedback():
    st.markdown(get_buddy_image_html(80), unsafe_allow_html=True)
    st.header("💝 Your Feedback")

    render_text(st.session_state.dynamic_feedback)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Next ➜"):
            st.session_state.current_question += 1
            st.session_state.page = "quiz"
            st.rerun()

    with col2:
        if st.button("Finish Now ❤️"):
            st.session_state.page = "results"
            st.rerun()


# ============================================================
# PAGE — RESULTS + FOOTER
# ============================================================
def page_results():
    user = st.session_state.user_info

    sc = st.session_state.score
    total = len(st.session_state.quiz_data["questions"])
    pct = (sc / total) * 100

    st.markdown(get_buddy_image_html(100), unsafe_allow_html=True)
    st.header("🎉 Quiz Completed!")

    if user["gender"] == "female":
        st.success(f"My love {user['name']}… you scored **{sc}/{total} ({pct:.1f}%)** 🥺💗")
    else:
        st.error(f"{user['name']}… {sc}/{total} ({pct:.1f}%). Expected worse 😒")

    mood, ok = mobile_text_input("How do you feel now? 💗", key="mood_after")
    if ok:
        st.session_state.user_info["mood_after"] = mood

    st.subheader("📚 What To Focus More On")
    render_text(generate_post_quiz_focus_advice(user, st.session_state.wrong_focus))

    st.markdown("---")

    if st.button("💌 Buddy’s Message"):
        render_text(generate_daily_romantic_message(user, st.session_state.quiz_data))

    if st.button("🌙 Night Whisper"):
        render_text(generate_night_mode_message(user, st.session_state.quiz_data))

    if st.button("🕊 A Message from God"):
        render_text(generate_gods_message(user))

    st.markdown("---")

    if st.button("Start New Session ❤️"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_state()
        st.rerun()

    if st.button("Back to Menu"):
        st.session_state.page = "menu"
        st.rerun()

    # FOOTER
    st.markdown(
        """
        <div style="text-align:center; margin-top:40px; color:#aaa; font-size:15px;">
            Developed with ❤️ by <b>Mirza Shaheen Iqubal</b>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# MAIN APP
# ============================================================
def main():
    st.set_page_config(
        page_title="Study Buddy AI",
        page_icon=BUDDY_PATH,
        layout="wide"
    )

    init_state()

    page = st.session_state.page

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
    elif page == "menu":
        page_menu()
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


if __name__ == "__main__":
    main()
