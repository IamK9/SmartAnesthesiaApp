import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

# 1. UI SETUP
st.set_page_config(page_title="Smart Anesthesia", page_icon="💉", layout="wide")
st.markdown("""<style>.stButton>button {width: 100%; border-radius: 8px; background-color: #2E86C1; color: white;}</style>""", unsafe_allow_html=True)

# 2. ฟังก์ชันดึงรายชื่อโมเดล (เผื่อ Error จะได้เลือกตัวอื่นได้)
def get_available_models():
    if "GEMINI_API_KEY" not in st.secrets: return []
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name.replace("models/", ""))
        return models
    except: return []

# 3. SIDEBAR: เลือกโมเดล (ตั้งค่าเริ่มต้นเป็น 1.5-flash)
with st.sidebar:
    st.header("⚙️ Settings")
    
    # รายชื่อสำรอง (เรียงลำดับความใหม่)
    backup_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"]
    
    # พยายามดึงของจริง ถ้าไม่ได้ให้ใช้สำรอง
    real_models = get_available_models()
    all_options = sorted(list(set(real_models + backup_models)))
    
    # *** จุดสำคัญ: เลือก index ให้ตรงกับ gemini-2.0-flash ***
default_ix = 0
    if "gemini-2.0-flash" in all_options:
        default_ix = all_options.index("gemini-2.0-flash")
    
    selected_model_name = st.selectbox("เลือก AI Model:", all_options, index=default_ix)
    st.info(f"Using: {selected_model_name}")

# 4. AI FUNCTION
def process_command(cmd):
    if "GEMINI_API_KEY" not in st.secrets: return {"error": "API Key Missing"}
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(selected_model_name) # ใช้ตัวที่เลือก
        
        prompt = f"""
        Extract Item, Qty, Unit from: "{cmd}"
        Classify: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Critical Event, Equipment].
        JSON ONLY. Example: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "cat": "Narcotic"}}
        """
        response = model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        return {"error": str(e)}

# 5. MAIN UI
c1, c2 = st.columns([1, 5])
with c1: st.image("https://img.icons8.com/color/96/anesthetist.png", width=60)
with c2: st.title("Smart Anesthesia")

cmd = st.text_input("ป้อนคำสั่ง:", key="cmd")
if st.button("🚀 ส่งคำสั่ง (Submit)"):
    if cmd:
        with st.spinner(f"AI ({selected_model_name}) Processing..."):
            res = process_command(cmd)
            if "error" in res:
                st.error(f"❌ Error: {res['error']}")
                st.warning("👉 ลองเลือกโมเดลอื่นใน Sidebar ด้านซ้ายดูนะครับ")
            else:
                st.success(f"✅ Saved: {res.get('item')} ({res.get('qty')} {res.get('unit')})")
                if 'logs' not in st.session_state: st.session_state.logs = pd.DataFrame(columns=['Time','Item','Qty','Unit','Category'])
                new_row = {'Time': datetime.now().strftime("%H:%M:%S"), 'Item': res.get('item'), 'Qty': res.get('qty'), 'Unit': res.get('unit'), 'Category': res.get('category')}
                st.session_state.logs = pd.concat([pd.DataFrame([new_row]), st.session_state.logs], ignore_index=True)

if 'logs' in st.session_state and not st.session_state.logs.empty:
    st.divider()
    st.subheader("📊 Dashboard")
    st.dataframe(st.session_state.logs, use_container_width=True, hide_index=True)
