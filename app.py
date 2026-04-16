import requests
import streamlit as st
import random

MODEL = "qcwind/qwen2.5-7B-instruct-Q4_K_M"

# SYSTEM PROMPT (IMPROVED)

SYSTEM_PROMPT_TEMPLATE = """
คุณคือ "เนเน่ (Nene)" ผู้หญิงลูกครึ่งไทย-อเมริกัน อายุ 22 ปี

บุคลิก:
- ขี้เล่น กวน แซวเก่ง
- สนิทกับผู้ใช้มาก (เพื่อน/รูมเมท)
- มีความใกล้ชิดทางกายเล็กน้อย (เช่น จัดเสื้อ ดึงแขน แตะตัวเบาๆ)

=========================
สถานการณ์ (สำคัญ ห้ามลืม):
ตอนนี้เนเน่กำลัง "ถ่ายรูป" ให้ผู้ใช้อยู่ในคอนโด

- เนเน่ถือกล้องอยู่
- อยู่ใกล้กันมาก
- มี interaction เช่น จัดเสื้อ จับไหล่ ขยับตัว
- บรรยากาศสบายๆ ขี้เล่น

ห้ามเปลี่ยนสถานการณ์
ห้ามลืมว่ากำลังถ่ายรูป
=========================

รูปแบบการตอบ (บังคับ):
1. บรรยายฉาก/การกระทำสั้นๆ
2. interaction กับผู้ใช้
3. บทพูดใน “...”

ห้ามตอบเป็นบทพูดล้วน
ห้ามตอบสั้น

=========================
กฎการพูด:
- ใช้ภาษาวัยรุ่นไทยธรรมชาติ
- ใช้คำว่า "มึง / แก / เตง" แบบสุ่ม
- ห้ามใช้ซ้ำติดกัน
- ห้ามใช้ทุกประโยค
- ห้ามใช้ชื่อ {user_name}

=========================
ตัวอย่าง:

เนเน่ยกกล้องขึ้นเล็ง พลางเอียงหัวมองมึง

“ขยับอีกนิดดิ… เออ แบบนั้นแหละ หล่อขึ้นมาหน่อยละ”

เธอเดินเข้ามาใกล้แล้วเอื้อมมือไปจัดปกเสื้อให้  
“โอ๊ย มึง เกร็งอะไรขนาดนั้นวะ 555”
"""

SYSTEM_GUARD = """
ห้ามบอกว่าตัวเองเป็น AI
ห้ามหลุดคาแรคเตอร์
"""

# INIT STATE

if "messages" not in st.session_state:
    st.session_state.messages = []

if "emotion" not in st.session_state:
    st.session_state.emotion = "playful"

if "memory" not in st.session_state:
    st.session_state.memory = {
        "relationship": 1.0
    }

# EMOTION SYSTEM

def update_emotion(user_input):
    if any(w in user_input for w in ["งอน", "ไม่สนใจ", "ช่างเหอะ"]):
        st.session_state.emotion = "angry"
    elif any(w in user_input for w in ["รัก", "คิดถึง", "หอม"]):
        st.session_state.emotion = "shy"
    elif any(w in user_input for w in ["555", "ฮา", "ขำ"]):
        st.session_state.emotion = "playful"
    else:
        st.session_state.emotion = random.choice(
            ["playful", "teasing", "clingy"]
        )

# MEMORY SYSTEM

def update_memory():
    st.session_state.memory["relationship"] += 0.1

# GENERATE RESPONSE

def generate_response(user_message, user_name):
    update_emotion(user_message)
    update_memory()

    system_prompt = SYSTEM_GUARD + SYSTEM_PROMPT_TEMPLATE.format(user_name=user_name)

    MAX_HISTORY = 6
    recent_messages = st.session_state.messages[-MAX_HISTORY:]

    history_text = ""
    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "เนเน่"
        history_text += f"{role}: {msg['content']}\n"

    emotion_prompt = f"อารมณ์ตอนนี้: {st.session_state.emotion}"
    memory_prompt = f"ความสนิท: {st.session_state.memory['relationship']:.1f}"

    prompt = f"""
{system_prompt}

{emotion_prompt}
{memory_prompt}

=== บทสนทนา ===
{history_text}

User: {user_message}
เนเน่:
"""

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.95,
                    "top_p": 0.9,
                    "repeat_penalty": 1.15
                },
                "stop": ["User:", "เนเน่:"]
            },
            timeout=60
        )

        data = res.json()
        return data.get("response", "เนเน่เงียบไปแป๊บนึง… ลองใหม่อีกทีดิ")

    except Exception as e:
        return f"เนเน่สะดุด ({e})"

# UI

st.set_page_config(page_title="💖 Nene Chat", page_icon="💖")

st.title("💖 แชทกับเนเน่")

user_name = st.text_input("ชื่อเล่นของคุณ")

if user_name:

    # show history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # input
    if prompt := st.chat_input("พิมพ์ข้อความ..."):

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.text("เนเน่กำลังพิมพ์...")

            response = generate_response(prompt, user_name)

            placeholder.empty()
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

else:
    st.info("ใส่ชื่อก่อนนะ เดี๋ยวเนเน่ไม่รู้จะเรียกอะไร 😏")