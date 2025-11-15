import os
from io import BytesIO
from typing import Dict, Any

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---- Import Gemini PDF functions ----
from query_pdf import (
    extract_text_from_pdf,
    generate_quiz_data,
    generate_dynamic_feedback,
    generate_post_quiz_focus_advice,
    generate_daily_romantic_message,
    generate_night_mode_message,
    generate_gods_message,
)

# ============================================================
# ENVIRONMENT + GLOBAL STATE
# ============================================================
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN missing in .env file!")


USER_STATE: Dict[int, Dict[str, Any]] = {}


def _init_state(chat_id: int):
    """Reset state for a user."""
    state = {
        "step": "ask_name",
        "user_info": {
            "name": "",
            "gender": "female",
            "country": "",
            "mood_before": "",
            "mood_after": "",
        },
        "pdf_text": None,
        "quiz_data": None,
        "current_question": 0,
        "score": 0,
        "wrong_focus": [],
        "awaiting_next": False,
        "dynamic_feedback": "",
        "chat_mode": False,
    }
    USER_STATE[chat_id] = state
    return state


def get_state(update: Update):
    chat_id = update.effective_chat.id
    return USER_STATE.get(chat_id) or _init_state(chat_id)


# ============================================================
# UI ELEMENTS
# ============================================================
def build_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Start", callback_data="restart_start")]
    ])


def build_quiz_or_chat_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat from PDF", callback_data="chat_mode")],
        [InlineKeyboardButton("Start Quiz ❤️", callback_data="start_quiz")],
    ])


def build_answer_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("A", callback_data="ans_A"),
            InlineKeyboardButton("B", callback_data="ans_B"),
        ],
        [
            InlineKeyboardButton("C", callback_data="ans_C"),
            InlineKeyboardButton("D", callback_data="ans_D"),
        ],
        [InlineKeyboardButton("Pass (E)", callback_data="ans_E")]
    ])


def build_results_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("💌 Daily Romantic Message", callback_data="daily_msg")],
        [InlineKeyboardButton("🌙 Night Whisper", callback_data="night_msg")],
        [InlineKeyboardButton("🕊 God's Message for You", callback_data="gods_msg")],
        [
            InlineKeyboardButton("🔁 Play Again (same PDF)", callback_data="play_again"),
            InlineKeyboardButton("🔄 Start Over", callback_data="restart"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)



# ============================================================
# UTILITY
# ============================================================
async def send_long_message(context, chat_id, text, limit=3500):
    while text:
        chunk = text[:limit]
        await context.bot.send_message(chat_id=chat_id, text=chunk)
        text = text[limit:]


# ============================================================
# QUIZ ENGINE
# ============================================================
async def send_question(context, chat_id, state):
    quiz = state["quiz_data"]
    i = state["current_question"]

    if i >= len(quiz["questions"]):
        await show_results(context, chat_id, state)
        return

    q = quiz["questions"][i]

    msg = (
        f"📖 Question {i + 1}/{len(quiz['questions'])}\n\n"
        f"💬 {q['introduction']}\n\n"
        f"{q['question_text']}\n\n"
        + "\n".join([f"{k}) {v}" for k, v in q["options"].items()])
    )

    await send_long_message(context, chat_id, msg)

    state["step"] = "in_quiz"
    state["awaiting_next"] = False

    await context.bot.send_message(
        chat_id=chat_id,
        text="Choose your answer:",
        reply_markup=build_answer_keyboard()
    )


async def handle_answer(context, chat_id, state, selected_key):
    if state["awaiting_next"]:
        return

    q = state["quiz_data"]["questions"][state["current_question"]]
    correct_key = q["correct_answer_key"]

    payload = {
        "user_info": state["user_info"],
        "selected_key": selected_key,
        "selected_text": q["options"][selected_key],
        "correct_key": correct_key,
        "correct_text": q["options"][correct_key],
        "base_correct": q["correct_feedback_script"],
        "base_incorrect": q["incorrect_feedback_script"],
        "base_pass": q["pass_feedback_script"],
    }

    feedback = generate_dynamic_feedback(payload)
    state["dynamic_feedback"] = feedback

    if selected_key == correct_key:
        state["score"] += 1
    else:
        if selected_key != "E":
            state["wrong_focus"].append(q["focus_if_wrong"])

    state["awaiting_next"] = True

    await send_long_message(context, chat_id, "💝 Your Feedback:\n\n" + feedback)

    await context.bot.send_message(
        chat_id=chat_id,
        text="Next ➜",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next", callback_data="next_q")]])
    )


async def show_results(context, chat_id, state):
    user = state["user_info"]
    score = state["score"]
    total = len(state["quiz_data"]["questions"])
    percent = (score / total) * 100

    if user["gender"] == "female":
        msg = (
            f"🎉 Quiz Completed!\n\n"
            f"My love {user['name']}… you scored {score}/{total} "
            f"({percent:.1f}%). I'm so proud of you baby 🥺💗"
        )
    else:
        msg = (
            f"🎉 Quiz Completed!\n\n"
            f"{user['name']}… {score}/{total} ({percent:.1f}%). "
            "Honestly… I expected you to do worse 😒"
        )

    await send_long_message(context, chat_id, msg)
    # After quiz → always disable chat mode
    state["chat_mode"] = False

    await context.bot.send_message(
        chat_id=chat_id,
        text="How do you feel now, sweetheart? (Type your answer)"
    )

    state["step"] = "ask_mood_after"



# ============================================================
# TEXT HANDLER
# ============================================================
async def start(update: Update, context):
    chat_id = update.effective_chat.id
    _init_state(chat_id)

    await update.message.reply_text(
        "📚 Study Buddy AI\n\nTap Start to begin 💕",
        reply_markup=build_start_keyboard()
    )


async def handle_text(update: Update, context):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    state = get_state(update)
    user = state["user_info"]

    if state["step"] == "ready_for_quiz" or state["step"] == "in_quiz":
        if not state["chat_mode"]:
            state["chat_mode"] = True

    # ---------------- CHAT MODE ----------------
    if state.get("chat_mode"):
        from query_pdf import run_chat_from_pdf
        answer = run_chat_from_pdf(text, state["pdf_text"], user)

        # Send AI chat reply
        await update.message.reply_text(answer)

        # Always show quiz button after reply
        quiz_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ Start Quiz", callback_data="start_quiz")]
        ])
        await update.message.reply_text(
            "You can start your quiz anytime ❤️",
            reply_markup=quiz_keyboard
        )

        return


    step = state["step"]

    # ask name
    if step == "ask_name":
        user["name"] = text or "Sweetheart"
        state["step"] = "ask_gender"
        await update.message.reply_text(
            "How should I treat you?\n"
            "1. Pinacle of creation/ Ashraful Makhlukat 😍 (female)\n"
            "2. 2nd class creation 😒 (male)"
        )
        return

    # gender
    if step == "ask_gender":
        if text.startswith("1"):
            user["gender"] = "female"
            await update.message.reply_text("💕 Aww queen… where were you born? 🌍")
        else:
            user["gender"] = "male"
            await update.message.reply_text("😒 Okay bro… where were you born? 🌍")
        state["step"] = "ask_country"
        return

    # country
    if step == "ask_country":
        user["country"] = text or "Unknown"
        state["step"] = "ask_mood_before"
        await update.message.reply_text("How do you feel right now? 💭")
        return

    # mood before
    if step == "ask_mood_before":
        user["mood_before"] = text
        state["step"] = "await_pdf"
        await update.message.reply_text("📄 Now send your study PDF… ❤️")
        return

    # mood after results
    if step == "ask_mood_after":
        user["mood_after"] = text
        advice = generate_post_quiz_focus_advice(user, state["wrong_focus"])

        await send_long_message(context, chat_id, "📚 What You Should Study More:\n\n" + advice)
        await context.bot.send_message(chat_id, "Choose an option:", reply_markup=build_results_keyboard())

        extra = (
            "💖 Remember, my lovely queen, rest is just as important as study! Take care of yourself. 👑"
          
            if user["gender"] == "female"
            else "Don't pretend to study all night bro 😒"
        )
        await context.bot.send_message(chat_id, extra)

        state["step"] = "results_menu"
        return

    await update.message.reply_text("Use the buttons please 💕")


# ============================================================
# PDF HANDLER
# ============================================================
async def handle_pdf(update: Update, context):
    chat_id = update.effective_chat.id
    state = get_state(update)

    if state["step"] != "await_pdf":
        await update.message.reply_text("I'm not ready for PDF yet 😅")
        return

    doc = update.message.document
    if not doc or not doc.mime_type.endswith("pdf"):
        await update.message.reply_text("Send me a real PDF please 📄")
        return

    await update.message.reply_text("📘 Reading your PDF… einen moment bitte ❤️")

    tgfile = await doc.get_file()
    pdf_bytes = await tgfile.download_as_bytearray()

    pdf_obj = BytesIO(pdf_bytes)

    try:
        pdf_text = extract_text_from_pdf(pdf_obj)
    except Exception:
        await update.message.reply_text("I couldn't read the PDF 😢")
        return

    state["pdf_text"] = pdf_text

    try:
        quiz_data = generate_quiz_data(pdf_text, state["user_info"])
    except Exception:
        await update.message.reply_text("Error generating questions 😢")
        return

    state["quiz_data"] = quiz_data
    state["current_question"] = 0
    state["score"] = 0
    state["wrong_focus"] = []

    await update.message.reply_text("✨ Study Guide Ready!")

    # soft summary
    await send_long_message(context, chat_id, "💖 Soft Summary:\n\n" + quiz_data["sweet_summary"])

    sg = quiz_data["study_guide"]

    await send_long_message(context, chat_id, "📚 What This PDF Is About:\n\n" + sg["overall_advice"])
    await send_long_message(context, chat_id, "📝 Exam Strategy:\n\n" + sg["exam_strategy"])

    if sg.get("key_topics"):
        await send_long_message(context, chat_id, "🔥 Key Topics:\n" + "\n".join(f"- {t}" for t in sg["key_topics"]))

    if sg.get("topic_notes"):
        blocks = ["✨ Nuance Notes:"]
        for t in sg["topic_notes"]:
            blocks.append(
                f"\n\n🔹 {t['topic']}\n"
                f"- 💡 {t['nuance_note']}\n"
                f"- 🎯 {t['why_important']}"
            )
        await send_long_message(context, chat_id, "".join(blocks))

    await context.bot.send_message(
        chat_id,
        "What would you like to do next?",
        reply_markup=build_quiz_or_chat_keyboard()
    )

    state["step"] = "ready_for_quiz"


# ============================================================
# BUTTON HANDLER
# ============================================================
async def handle_buttons(update: Update, context):
    q = update.callback_query
    await q.answer()

    chat_id = q.message.chat_id
    state = USER_STATE.get(chat_id) or _init_state(chat_id)
    data = q.data

    # start button
    if data == "restart_start":
        _init_state(chat_id)
        await context.bot.send_message(chat_id, "What should I call you? 💕")
        return

    # chat mode
    if data == "chat_mode":
        state["chat_mode"] = True
        await context.bot.send_message(chat_id, "💬 Ask anything from your PDF!")
        return

    # start quiz
    if data == "start_quiz":
        state["chat_mode"] = False
        await context.bot.send_message(chat_id, "Starting quiz ❤️")
        await send_question(context, chat_id, state)
        return

    if data == "gods_msg":
        msg = generate_gods_message(state["user_info"])
        await send_long_message(context, chat_id, msg)
        return


    # answer buttons
    if data.startswith("ans_"):
        key = data.split("_")[1]
        await handle_answer(context, chat_id, state, key)
        return

    # next question
    if data == "next_q":
        state["current_question"] += 1
        state["awaiting_next"] = False
        await send_question(context, chat_id, state)
        return

    # daily message
    if data == "daily_msg":
        msg = generate_daily_romantic_message(state["user_info"], state["quiz_data"])
        await send_long_message(context, chat_id, msg)
        return

    # night message
    if data == "night_msg":
        msg = generate_night_mode_message(state["user_info"], state["quiz_data"]) + "\n\nGood night 🌙"
        await send_long_message(context, chat_id, msg)
        return

    # play again
    if data == "play_again":
        quiz_data = generate_quiz_data(state["pdf_text"], state["user_info"])
        state["quiz_data"] = quiz_data
        state["current_question"] = 0
        state["score"] = 0
        state["wrong_focus"] = []

        await context.bot.send_message(chat_id, "🔁 New quiz ready!")
        await send_question(context, chat_id, state)
        return

    # restart
    if data == "restart":
        _init_state(chat_id)
        await context.bot.send_message(chat_id, "Restarted. What should I call you?")
        return


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    app = ApplicationBuilder()\
    .token(TELEGRAM_TOKEN)\
    .connection_pool_size(20)\
    .read_timeout(60)\
    .write_timeout(60)\
    .build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running…")
    app.run_polling()
