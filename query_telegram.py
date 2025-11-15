import os
import json
from typing import List, Dict, Any, Optional
from io import BytesIO
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from huggingface_hub import InferenceClient

# ======================================================
# LOAD ENV
# ======================================================
load_dotenv()
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not HF_API_KEY:
    raise RuntimeError("HUGGINGFACE_API_KEY missing in environment")

# ======================================================
# MULTIMODAL CLIENT: Qwen2-VL-2B-Instruct
# ======================================================
hf_client = InferenceClient(
    "Qwen/Qwen2-VL-2B-Instruct",
    token=HF_API_KEY
)

# ======================================================
# IMAGE + TEXT EXTRACTION
# ======================================================
def extract_pdf_text_and_images(file_bytes: bytes):
    """
    Extract:
      ✔ Text via PyPDF2
      ✔ Page-rendered images via pdf2image (PIL Images)
    """
    # TEXT
    buffer = BytesIO(file_bytes)
    reader = PdfReader(buffer)

    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    # IMAGES (PIL)
    images = convert_from_bytes(file_bytes)

    return text.strip(), images


# ======================================================
# HF MULTIMODAL GENERATE
# ======================================================
def hf_generate(prompt: str, images=None, max_tokens=4096, temperature=0.7):
    """
    Sends multimodal messages to Qwen2-VL:
      - images: list of PIL Images or None
      - text prompt
    """
    messages = []

    if images:
        for img in images:
            buf = BytesIO()
            img.save(buf, format="JPEG")
            messages.append({"type": "image", "image": buf.getvalue()})

    messages.append({"type": "text", "text": prompt})

    response = hf_client.chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )

    return response.choices[0].message["content"]


# ======================================================
# PERSONA BLOCK (ROMANTIC BF / SARCASTIC EX)
# ======================================================
def _build_persona_block(user_info: Dict[str, Any]) -> str:
    gender = user_info.get("gender", "female").lower()
    name = user_info.get("name", "Sweetheart")
    country = user_info.get("country", "default")

    if gender == "female":
        return f"""
You are speaking to a girl named {name} from {country}.
You are her extremely romantic, dramatic, clingy, loving boyfriend.

STYLE:
- Overly romantic
- Dramatic, clingy, emotional
- Cute, protective, affectionate
- NEVER sexual or explicit

Use cute nicknames (baby, angel, sweetheart, my love).

COUNTRY-BASED ROMANCE:
- Sometimes use small romantic phrases from her language ({country})
  with English meaning in parentheses.
"""

    return f"""
You are speaking to a guy named {name} from {country}.
You are his extremely sarcastic, annoyed ex-girlfriend.

STYLE:
- Savage, cold, sarcastic
- Eye-rolling, rude but SAFE
- No romance ever
- Increasing irritation as question number increases
"""


# ======================================================
# QUIZ GENERATION
# ======================================================
def generate_quiz_data(pdf_text: str, pdf_images, user_info: Dict[str, Any]):
    print("🚀 ENTER generate_quiz_data")
    print("PDF TEXT LENGTH:", len(pdf_text))
    print("NUM IMAGES:", len(pdf_images))

    persona_block = _build_persona_block(user_info)

    prompt = f"""
{persona_block}

You are helping them study for an exam using the PDF content.

PDF CONTENT:
--- START PDF ---
{pdf_text}
--- END PDF ---

You MUST output STRICT JSON with the following structure ONLY:

{{
  "sweet_summary": "...",
  "study_guide": {{
    "overall_advice": "...",
    "exam_strategy": "...",
    "key_topics": ["...", "...", "..."],
    "topic_notes": [
      {{
        "topic": "...",
        "nuance_note": "...",
        "why_important": "..."
      }}
    ]
  }},
  "questions": [
    {{
      "introduction": "...",
      "question_text": "...",
      "options": {{
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "...",
        "E": "Pass"
      }},
      "correct_answer_key": "A",
      "correct_feedback_script": "...",
      "incorrect_feedback_script": "...",
      "pass_feedback_script": "...",
      "focus_if_wrong": "...",
      "romance_level": 1
    }}
  ],
  "daily_romantic_message_seed": "...",
  "night_mode_message_seed": "..."
}}

RULES:
- Generate EXACTLY 17 questions.
- Valid JSON ONLY.
- Romance_level increases from 1 → 17 for girls (more romantic).
- Harshness increases 1 → 17 for boys.
- Feedback scripts MUST mention what the learner chose + correct answer.
"""

    print("🚀 Sending to HF multimodal...")
    raw = hf_generate(prompt, images=pdf_images)

    print("RAW LEN:", len(raw))

    # Clean accidental ```json wrappers
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        data = json.loads(raw)
    except Exception as e:
        print("❌ JSON ERROR:", e)
        print("RAW OUTPUT:", raw)
        raise e

    print("✅ JSON parsed successfully")
    return data


# ======================================================
# POST QUIZ ADVICE
# ======================================================
def generate_post_quiz_focus_advice(user_info, wrong_focus_list):
    if not wrong_focus_list:
        wrong_focus_list = ["No major weak areas – amazing performance."]

    persona = _build_persona_block(user_info)
    topics = "\n".join(f"- {t}" for t in wrong_focus_list)

    prompt = f"""
{persona}

These were the weak topics:
{topics}

Generate one short motivating paragraph:
- Girl: romantic, gentle, emotional, motivating.
- Boy: sarcastic roast but useful.
"""

    return hf_generate(prompt, max_tokens=700)


# ======================================================
# DAILY MESSAGE
# ======================================================
def generate_daily_romantic_message(user_info, quiz_data=None):
    seed = quiz_data.get("daily_romantic_message_seed") if quiz_data else ""
    persona = _build_persona_block(user_info)

    prompt = f"""
{persona}

Create a short DAILY message based on seed: "{seed}".
"""

    return hf_generate(prompt, max_tokens=512)


# ======================================================
# NIGHT MESSAGE
# ======================================================
def generate_night_mode_message(user_info, quiz_data=None):
    seed = quiz_data.get("night_mode_message_seed") if quiz_data else ""
    persona = _build_persona_block(user_info)

    prompt = f"""
{persona}

Create a NIGHT MODE message based on: "{seed}".
"""

    return hf_generate(prompt, max_tokens=512)


# ======================================================
# FEEDBACK GENERATION
# ======================================================
def generate_dynamic_feedback(payload):
    user = payload["user_info"]
    persona = _build_persona_block(user)

    selected_key = payload["selected_key"]
    selected_text = payload["selected_text"]
    correct_key = payload["correct_key"]
    correct_text = payload["correct_text"]

    base = payload["base_correct"] if selected_key == correct_key else (
        payload["base_pass"] if selected_key == "E" else payload["base_incorrect"]
    )

    prompt = f"""
{persona}

You MUST start EXACTLY with:

"You selected: [{selected_key}] {selected_text}"
"Correct answer: [{correct_key}] {correct_text}"

THEN:
- Explain WHY the correct answer is correct.
- If wrong: explain WHY their answer was wrong.
- THEN apply persona tone.
- Output ONLY final message.

BASE TONE REFERENCE:
"{base}"
"""

    return hf_generate(prompt, max_tokens=700, temperature=0.85)
