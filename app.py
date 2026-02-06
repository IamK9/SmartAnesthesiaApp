import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

# 1. SETUP
st.set_page_config(page_title="Smart Anesthesia", page_icon="💉", layout="wide")
st.markdown("""<style>.stButton>button {width: 100%; border-radius: 8px; background-color: #2E86C1; color: white;}</style>""", unsafe_allow_html=True)

# 2. AI FUNCTION (ระบบค้นหาโมเดลอัตโนมัติ)
def get_best_model():
    """ฟังก์ชันหาชื่อโมเดลที่ใช้ได้จริงในขณะนั้น"""
    try:
        # ลองหาชื่อโมเดลที่มีคำว่า pro หรือ flash
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name: return 'gemini-1.5-flash'
                if 'gemini-pro' in m.name: return 'gemini-pro'
    except:
        pass
    return 'gemini-pro' # ถ้าหาไม่เจอเลย ให้ใช้ตัวนี้เป็นค่า Default

def process_command(cmd):
    if "GEMINI_API_KEY" not in st.secrets:
        return {"error": "API Key Missing"}
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # --- ใช้ฟังก์ชันเลือกโมเดลอัตโนมัติ ---
        model_name = get_best_model() 
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        Extract Item, Qty, Unit from: "{cmd}"
        Classify: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Critical Event, Equipment].
        JSON ONLY. Example: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "cat": "Narcotic"}}
        """
        response = model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        return {"error": str(e) + f" (Model used: {model_name})"}

# 3. UI
c1, c2 = st.columns([1, 5])
with c1: st.image("https://img.icons8.com/color/96/anesthetist.png", width=60)
with c2: st.title("Smart Anesthesia")

# --- MAIN APP ---
cmd = st.text_input("ป้อนคำสั่ง:", key="cmd")
if st.button("🚀 ส่งคำสั่ง (Submit)"):
    if cmd:
        with st.spinner("Processing..."):
            res = process_command(cmd)
            if "error" in res:
                st.error(res['error'])
            else:
                st.success(f"Saved: {res.get('item')} ({res.get('qty')} {res.get('unit')})")
                
                # Update Data
                if 'logs' not in st.session_state: 
                    st.session_state.logs = pd.DataFrame(columns=['Time','Item','Qty','Unit','Category'])
                
                new_row = {
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'Item': res.get('item'), 'Qty': res.get('qty'), 
                    'Unit': res.get('unit'), 'Category': res.get('category')
                }
                st.session_state.logs = pd.concat([pd.DataFrame([new_row]), st.session_state.logs], ignore_index=True)

# Dashboard
if 'logs' in st.session_state and not st.session_state.logs.empty:
    st.divider()
    st.subheader("📊 Dashboard")
    st.dataframe(st.session_state.logs, use_container_width=True, hide_index=True)
