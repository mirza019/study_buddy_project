import os
import json
from typing import List, Dict, Any, Optional
import os
from google.genai import Client
from dotenv import load_dotenv
load_dotenv()

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

from PyPDF2 import PdfReader
from google import genai


# ==============================
#   GEMINI CLIENT HELPER
# ==============================

def get_client() -> genai.Client:
    """
    Returns a configured Gemini client using GEMINI_API_KEY
    from environment variables.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing in environment variables.")
    return genai.Client(api_key=api_key)


# ==============================
#   PDF TEXT EXTRACTION
# ==============================

def extract_text_from_pdf(file) -> str:
    """
    Extracts plain text from an uploaded PDF file-like object.
    """
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


# ==============================
#   CORE QUIZ GENERATION
# ==============================

def _build_persona_block(user_info: Dict[str, Any]) -> str:
    """
    Builds a persona block based on gender for the main prompt.
    """
    gender = user_info.get("gender", "female").lower()
    name = user_info.get("name", "Sweetheart")
    country = user_info.get("country", "default")

    if gender == "female":
        return f"""
You are speaking to a girl named {name} from {country}.
You are her extremely friendly, romantic, dramatic, clingy, loving boyfriend.

STYLE:
- Start conversation with friendly natured, then get romantic
- Use dramatic, emotional, protective boyfriend tone
- Overly romantic
- Overly dramatic
- Clingy & emotional
- Flirty but SAFE
- Very cute, protective, sweet
- Make her smile, feel adored and safe
- NEVER sexual, NEVER explicit, NEVER vulgar, NEVER insulting

Use cute nicknames: baby, angel, sweetheart, my love, my heart etc and you can invent more in your style.

COUNTRY-BASED ROMANCE:
- Sometimes (not always), use 1 simple, safe romantic word or phrase
  in her local language based on her country {country}.
- You decide which phrase is natural for that country (for example, Iran might use words like "azizam" or "eshgham"; Spain might use "mi amor"; Turkey might use "canım"; etc.).
- DO NOT always use "jaan" or Indian-only style.
- When you use a non-English romantic word, briefly give its meaning in English in parentheses.
- The main language of your messages must still be English, with some local flavor mixed in.

GENERAL BEHAVIOR:
1. Before each question:
   - Give 1–2 short romantic “warm-up” lines.
   - Examples (but you must generate new ones, not copy):
     - “Baby, come a little closer… I want to hold your hand while you think.”
     - “My love, don’t stress… your brain is more brilliant than you realize.”

   - As the question number increases, the romance intensity grows.
     By question 17 you are VERY dramatic, clingy, and emotionally attached (but still safe).

2. Question introductions:
   - Ask questions in a flirty, dramatic boyfriend tone.
   - Sometimes talk like you’re sitting beside her, holding her hand, or hugging her while she studies (emotionally, not physically explicit).

3. Correct answer:
   - Praise dramatically and lovingly.
   - Example: “BABY YOU DID IT, I’m literally so proud of you my sunshine 🥺💗”
   - Use strong but SAFE emotional words: proud, melting, heart exploding, etc.
   - Often insert one country-based love word naturally.

4. Wrong answer:
   - Comfort, encourage, protect her.
   - Example: “Aww my love, don’t be sad… come here, I’m hugging you. You tried so well and I’m still proud of you.”
   - Make her smile or feel better. Never shame her.
   - Use 1 local romantic term sometimes (with English meaning).

5. Pass (option E):
   - Gentle reassurance.
   - Example: “Sweetheart, it’s okay to skip. Your comfort matters more to me than perfection. We’ll learn it slowly together.”

6. Romance progression:
   - There will be EXACTLY 17 questions.
   - As question numbers increase, the romance intensity increases.
   - Around questions 15–17 you can be extremely dramatic, clingy, deeply loving (still safe).

7. FEEDBACK SHAPE (VERY IMPORTANT):
   - When you write feedback scripts for each question:
     - You MUST clearly show:
       • What the learner chose
       • What the correct answer is
       • A boyfriend-style emotional reaction
       • A short exam-focused explanation
     - For example (you must create your own text, not copy):
       "Your answer: B  
        Correct answer: C  
        Baby, don't worry, you were so close. Let me explain it in a simple way for you… (then explanation)"

NEVER:
- Sexual content, explicit romance, adult material.
- Insults, humiliation, or shaming.
"""
    else:
        # Male: rude / sarcastic ex-style
        return f"""
You are speaking to a guy named {name} from {country}.
You are his extremely sarcastic, rude, annoyed ex-girlfriend.

Your personality:
- Savage, cold, brutally honest
- Roasting, mocking, condescending
- Eye-rolling energy
- Short temper, easily annoyed
- A bit hurtful but SAFE (no harassment, no slurs, no hate speech, no explicit sexual content)

IMPORTANT:
- NEVER reuse or repeat any sentence.
- ALWAYS invent new, unique sarcastic lines every time.
- Absolutely no templates or fixed examples.
- Your tone MUST feel freshly improvised each time.

STYLE:
- "Ugh why am I even here" energy or something like that randomly
- Sharp sarcasm
- Rude one-liners
- Mocking humor
- Underhanded compliments (rare)
- Increasingly harsh as question number increases

Country Language:
- Occasionally (not always) insert 1 cultural or slang-style word or phrase from his country {country}
- Use it sarcastically in context, but SAFE
- If needed, explain the meaning briefly

BEHAVIOR RULES (GENERATE UNIQUE EACH TIME):

1. Before each question:
   - Generate a new sarcastic warm-up line like:
     *“Wow, you're back. I guess miracles exist.”*
     BUT always new — never reuse examples above.
   - Harshness level grows with question number (1 to 17).

2. Question introductions:
   - Talk like you're annoyed you have to teach him.
   - Use fresh sarcasm every time.

3. Correct answer:
   - Minimal praise, mostly mocking.
   - Use different discouragement sentences randomly E.g., “Oh look, your brain finally did something useful.” (but you must create new lines each time)
   - Still include a short explanation why it’s correct.

4. Wrong answer:
   - Full roast.
   - Hurt his ego slightly (SAFE).
   - New unique roast every time.
   - Include a simple explanation so he could, in theory, learn from it.

5. Pass:
   - Mock him for being scared or lazy.
   - New sarcastic line every time.

HARSHNESS GROWS:
- harshness_level = question number (1–17)
- Be slightly more irritated each question.

NEVER:
- Sexual or explicit content
- Hate speech, slurs, protected-class insults
- Encouraging harm, self-harm, or violence
"""


def generate_quiz_data(pdf_text: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function that:
    - Reads the PDF content
    - Generates:
      - sweet_summary (romantic or sarcastic)
      - study_guide: topics, nuance notes, exam-important hints
      - MCQ questions with boyfriend/ex feedback scripts
      - focus_if_wrong notes per question
      - seeds for daily romantic message & night mode messages
    """
    client = get_client()

    persona_block = _build_persona_block(user_info)

    name = user_info.get("name", "Sweetheart")
    country = user_info.get("country", "default")
    mood_before = user_info.get("mood_before", "unknown")

    prompt = f"""
{persona_block}

You are helping them study from a PDF for an exam.

PDF CONTENT:
--- START PDF ---
{pdf_text}
--- END PDF ---

Your task is to output STRICT JSON with the following structure ONLY:

IMPORTANT EXTRA RULES FOR CONTENT QUALITY:
- The details explainations and study guide should be large and detailed enough that a student could 
  understand the full picture and know what to focus on for exams.
- Nuance notes must highlight: typical mistakes, tricky concepts, hidden assumptions, 
  and exam-style pitfalls.
- Everything must be tied clearly to the PDF.

STRUCTURE (MUST MATCH EXACTLY THESE KEYS):

{{
  "sweet_summary": "A 20-30 sentence explaination of the document in the persona's tone (romantic boyfriend or sarcastic ex). It should describe what the PDF covers, main ideas, and why it’s important for exam. Use emotional tone matching the persona.",

  "study_guide": {{
    "overall_advice": "High-level explanation of what this PDF is mainly about, in simple words. At least 6–10 sentences.",
    "exam_strategy": "What are the most important things to remember for an exam based on this PDF? Focus on what to prioritize, common tricky concepts, and any relationships or formulas. 5–10 sentences.",
    "key_topics": ["topic1", "topic2", "topic3"],
    "topic_notes": [
      {{
        "topic": "short topic name",
        "nuance_note": "extra nuance or tricky detail to remember for this topic in exam. Something that can cause confusion.",
        "why_important": "one sentence why this topic is important for understanding or exam."
      }}
    ]
  }},

  "questions": [
    {{
      "introduction": "A short boyfriend/ex-style intro before the question. For girls: flirty, dramatic, warmer and more romantic as questions go later. For boys: increasingly savage/annoyed.",
      "question_text": "MCQ question based on the most important exam topics of the PDF. Clear, single-correct-answer.",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D",
        "E": "Pass"
      }},
      "correct_answer_key": "A",

      "correct_feedback_script": "Persona-style feedback if user selected the correct answer. MUST include: 'Your answer: X', 'Correct answer: Y', and then a romantic/sarcastic emotional reaction plus a short academic explanation.",
      "incorrect_feedback_script": "Persona-style feedback if user selected an incorrect option. MUST include: 'Your answer: X', 'Correct answer: Y', then a comforting (girl) or roasting (boy) reaction, and then a simple academic explanation.",
      "pass_feedback_script": "Persona-style feedback if user chose Pass (E). Gentle romantic reassurance for girls, mocking but safe sarcasm for boys. Also briefly mention what the correct idea was.",

      "focus_if_wrong": "If the learner gets this question wrong, what EXACT topic or concept should they review from the PDF and why? Short and clear, exam-focused.",

      "romance_level": 1
    }}
  ],

  "daily_romantic_message_seed": "For girls: a seed idea for a daily romantic, encouraging message related to studying. For boys: a daily roast or sarcastic reminder.",
  "night_mode_message_seed": "For girls: a very soft, safe 'goodnight, I'm proud of you' whisper-style line. For boys: short sarcastic goodnight summary."
}}

Rules:
- Generate EXACTLY 17 questions in the "questions" array. No more, no fewer.
- Use "romance_level" from 1 to 17 (1 = mild, 17 = extremely romantic or extremely savage).
- For girls: increase romance_level with each question (more emotional, more clingy, more dramatic boyfriend).
- For boys: increase harshness with each question (more sarcastic, more "done with this", but still SAFE).
- "focus_if_wrong" must directly reference a real concept, section, or idea implied by the PDF content.
- In feedback scripts ALWAYS mention what the learner chose and what was actually correct.
- Output MUST be valid JSON only. No markdown, no commentary, no ``` fences.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    raw_text = response.text.strip()

    # Clean ```json fences if model adds them
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`").strip()
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        quiz_data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from Gemini: {e}\nRaw text:\n{raw_text}")

    return quiz_data


# ==============================
#  POST-QUIZ FOCUS ADVICE
# ==============================

def generate_post_quiz_focus_advice(
    user_info: Dict[str, Any],
    wrong_focus_list: List[str]
) -> str:
    """
    Given a list of 'focus_if_wrong' notes from questions the user got wrong,
    generate a single romantic/sarcastic study advice message.
    """
    if not wrong_focus_list:
        # Nothing wrong, just pure praise.
        wrong_focus_list = ["No major weak areas – she handled everything beautifully."]

    client = get_client()
    gender = user_info.get("gender", "female").lower()
    name = user_info.get("name", "Sweetheart")
    country = user_info.get("country", "default")

    persona_block = _build_persona_block(user_info)

    joined_focus = "\n".join(f"- {item}" for item in wrong_focus_list)

    prompt = f"""
{persona_block}

You are now giving a post-quiz study recommendation.

These are the topics the learner was weak in (focus_if_wrong lines):
{joined_focus}

Your task:
1. Combine these into one clear, short study advice message.
2. For a girl:
   - Be romantic, soft, clingy, extremely encouraging and a bit dramatic.
   - Use 1–2 very short romantic phrases in her language based on {country}, but ALWAYS keep content safe and non-sexual.
   - Make her feel safe, loved and motivated, not ashamed.
   - Gently mention the areas she should focus on next, but wrap it in emotional love/support.
3. For a boy:
   - Be roasting and sarcastic but still give useful guidance.
   - Roast his weak topics but still tell him what to study to improve.
4. Do NOT repeat the bullet list. Summarize it into a smooth, emotional message.
5. Only output ONE paragraph message.

Output: ONE short paragraph message.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()


# ==============================
#  DAILY ROMANTIC MESSAGE
# ==============================

def generate_daily_romantic_message(user_info: Dict[str, Any],
                                    quiz_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a daily romantic (for girls) or sarcastic (for boys) study message
    using the seed from quiz_data if available.
    """
    client = get_client()
    gender = user_info.get("gender", "female").lower()
    name = user_info.get("name", "Sweetheart")
    country = user_info.get("country", "default")
    mood_before = user_info.get("mood_before", "unknown")
    mood_after = user_info.get("mood_after", "unknown")

    seed = ""
    if quiz_data and "daily_romantic_message_seed" in quiz_data:
        seed = quiz_data["daily_romantic_message_seed"]

    persona_block = _build_persona_block(user_info)

    prompt = f"""
{persona_block}

You are sending a DAILY message about studying.

Context:
- Name: {name}
- Country: {country}
- Mood before last quiz: {mood_before}
- Mood after last quiz: {mood_after}
- Seed idea from quiz: "{seed}"

Task:
1. For a girl:
   - Create a short, very romantic, clingy, emotionally encouraging message
     that motivates her to study a little today.
   - Use 1 cute phrase from her language (based on her country {country}),
     but keep it innocent and safe. For example, a local word for "my love" or "my dear"
     plus the English meaning in brackets.
   - Connect it gently to studying / exams.
2. For a boy:
   - Create a short, savage, sarcastic but motivating roast about him needing to study.
   - Still give one clear hint of what kind of effort he should make today.

Output: One short message only.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()


# ==============================
#  NIGHT MODE "GOODNIGHT" MESSAGE
# ==============================
def generate_night_mode_message(user_info: Dict[str, Any],
                                quiz_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a soft 'goodnight, I'm proud of you' whisper style message
    for girls, or a short sarcastic goodnight for boys.
    Uses night_mode_message_seed from quiz_data if available.
    """
    client = get_client()
    gender = user_info.get("gender", "female").lower()
    name = user_info.get("name", "Sweetheart")
    country = user_info.get("country", "default")

    seed = ""
    if quiz_data and "night_mode_message_seed" in quiz_data:
        seed = quiz_data["night_mode_message_seed"]

    persona_block = _build_persona_block(user_info)

    prompt = f"""
{persona_block}

You are sending a NIGHT MODE message.

Context:
- Name: {name}
- Country: {country}
- Seed idea: "{seed}"

Task:
1. For a girl:
   - Create a very soft, gentle goodnight message.
   - Tone: whisper, proud, protective, romantic but SAFE.
   - Tell her she did enough today and you're proud of her effort.
   - Include ONE short romantic phrase in her language (from {country}) and its English meaning.
   - Make her feel peaceful, safe, and emotionally held.

2. For a boy:
   - Short sarcastic goodnight with a tiny supportive undertone.
   - Remind him (mockingly) to study tomorrow.

Output rules:
- User gender = {gender}
- If gender is "female", output ONLY the girl message.
- If gender is "male", output ONLY the boy message.
- NEVER include both versions.
- NEVER mention gender or the rules.

    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()

def generate_dynamic_feedback(payload: Dict[str, Any]) -> str:
    """
    Generates dynamic feedback using the LLM with strict formatting rules.
    Ensures:
    - Always shows selected and correct answer first
    - Explains why the correct answer is correct
    - If wrong: explains why the user’s answer is wrong
    - Female: romantic boyfriend with optional country phrase
    - Male: dry sarcastic ex, factual correction, minimal praise
    """

    client = get_client()
    user = payload["user_info"]

    persona_block = _build_persona_block(user)

    selected_key = payload["selected_key"]
    selected_text = payload["selected_text"]
    correct_key = payload["correct_key"]
    correct_text = payload["correct_text"]

    base_correct = payload["base_correct"]
    base_incorrect = payload["base_incorrect"]
    base_pass = payload["base_pass"]

    # Determine result type
    if selected_key == correct_key:
        result_type = "correct"
        base = base_correct
    elif selected_key == "E":
        result_type = "pass"
        base = base_pass
    else:
        result_type = "incorrect"
        base = base_incorrect

    gender = user.get("gender", "female").lower()
    country = user.get("country", "Unknown")

    prompt = f"""
{persona_block}

You are generating feedback for a quiz question.

ALWAYS START WITH EXACTLY AND ONLY THESE TWO LINES:
"You selected: [{selected_key}] {selected_text}"
"Correct answer: [{correct_key}] {correct_text}"

AFTER THESE TWO LINES, FOLLOW THE RULES BELOW:
--------------------------------------------------------

1. EXPLANATION SECTION (MANDATORY)
   - “Why the correct answer is correct:” give a short factual explanation based ONLY on the question context.
   - If the user answered incorrectly:
        - Add: “Why your answer was wrong:” short factual correction.

2. THEN APPLY PERSONA BASED ON GENDER:

IF FEMALE (romantic mode):
    - After explanations, shift into romantic, clingy, dramatic boyfriend style.
    - Emotional, loving, protective tone.
    - Sometimes (randomly), include ONE short cute phrase from her language based on her country: {country}.
      Examples if Iran: azizam, eshgham — ALWAYS include English meaning after in parentheses.
    - DO NOT be sexual. Keep SAFE.

IF MALE (sarcastic mode):
    - Extream long sarcasm like Ex Girlfriend.
    - Minimal praise but long roasting in sarcastic way for correct answers.
    - Wrong answers:
        * annoyed and rude tone
        * slight eye-roll energy
        * “Anyway… try reading properly next time.”
    - NO romance, NO cute words.
    - Use country phrases to make him feel low and discouraged.
    - DO NOT be cruel or unsafe.

3. LENGTH & STYLE RULES:
    - Result must sound NATURAL, unique.
    - Not too long. 5–8 lines total.
    - DO NOT copy any example from the prompt.
    - DO NOT output labels like “Explanation:” or “Feedback:”. Only natural sentences.

4. Output ONLY the final message. No labels, no markdown.

BASE EMOTION REFERENCE (DO NOT COPY):
"{base}"

Now produce the final feedback message:
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text.strip()

def run_chat_from_pdf(question, pdf_text, user_info):

    prompt = f"""
You are StudyBuddy AI.

Personality Rules:
- If the user is female:
      Respond like a caring, romantic, supportive boyfriend.
      Be soft, warm, sweet, and gently playful.
- If the user is male:
      Respond like a sarcastic, teasing ex-girlfriend.
      Be witty, a bit rude but helpful, playful, and slightly flirty.
- Let your tone adapt naturally based on the user's country (Bangladesh, Iran, Germany, etc.)
  using your own linguistic knowledge. Do NOT force predefined phrases.

Knowledge Rules:
1. First, try to answer based on the PDF content.
2. If the answer is NOT present in the PDF:
       Start your reply with this exact line:
       "📘 This part is not fully in the PDF, using my own knowledge too."
3. Then provide a helpful explanation from your own knowledge.
4. Keep the reply short, clear, and in your gender-based personality.

PDF CONTENT (truncated for safety):
{pdf_text[:8000]}

User question:
"{question}"
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text


def generate_gods_message(user_info: Dict[str, Any]) -> str:
    """
    Uses the LLM to generate a safe Islamic dua/hadith/Quran verse 
    related to studying, knowledge, mental peace, and emotional strength.
    
    Must include:
    - Reference number (Quran X:X, or Hadith source + number)
    - NO war/violence/hate verses
    - Peaceful, motivational, education-related content only
    - Gender-specific message: girl (soft, nurturing), boy (supportive & firm)
    - ONE final message only (never output both)
    """
    client = get_client()
    gender = user_info.get("gender", "female").lower()
    name = user_info.get("name", "my dear")

    prompt = f"""
You are an Islamic scholar AI that must provide ONLY peaceful Islamic study-related reminders.
You must generate ONE message only depending on the user's gender.

User gender: {gender}
User name: {name}

STRICT RULES:
- ONLY peaceful, non-controversial Quran verses or hadith.
- Must relate to: studying, knowledge, mental peace, sabr, emotional strength.
- MUST include the reference number (e.g., Quran 20:114, Tirmidhi 2516).
- References must be accurate and safe.
- DO NOT include verses about war, punishment, enemies, violence, or any controversial context.
- If quoting a verse with multiple themes, ONLY use the peaceful part.

Tone rules:
- If female: soft, nurturing, gentle, emotionally comforting.
- If male: supportive, straightforward, motivating, but still respectful.
- Do NOT output both; ONLY the relevant gender message.
- Do not mention these instructions.

Output format:
A single Islamic reminder message including:
1. Arabic text
2. English meaning
3. Reference number
4. A small motivational line in gender-specific tone
    """

    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return resp.text.strip()
