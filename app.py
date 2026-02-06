import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

# 1. SETUP
st.set_page_config(page_title="Smart Anesthesia", page_icon="💉", layout="wide")
st.markdown("""<style>.stButton>button {width: 100%; border-radius: 8px;}</style>""", unsafe_allow_html=True)

# 2. AI FUNCTION
def process_command(cmd):
    if "GEMINI_API_KEY" not in st.secrets:
        return {"error": "API Key Missing"}
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # --- ส่วนสำคัญ: ใช้ชื่อโมเดลล่าสุด ---
        # ลองใช้ gemini-1.5-flash เพราะเป็นมาตรฐานปี 2025-2026
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        prompt = f"""
        Extract Item, Qty, Unit from: "{cmd}"
        Classify: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Critical Event, Equipment].
        JSON ONLY. Example: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "cat": "Narcotic"}}
        """
        response = model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        return {"error": str(e)}

# 3. UI
st.title("Smart Anesthesia 💉")

# --- 🛠️ ส่วนเช็คของ (DEBUGGER) ---
with st.sidebar:
    st.header("🔧 Debug Menu")
    if st.button("เช็คชื่อโมเดลที่ใช้ได้ (List Models)"):
        if "GEMINI_API_KEY" in st.secrets:
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                st.write("--- โมเดลที่ Server มองเห็น ---")
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        st.code(m.name) # มันจะโชว์ชื่อออกมา เช่น models/gemini-1.5-flash
            except Exception as e:
                st.error(f"เช็คไม่ได้: {e}")
        else:
            st.error("ยังไม่ใส่ API Key")

# --- MAIN APP ---
cmd = st.text_input("ป้อนคำสั่ง:", key="cmd")
if st.button("🚀 ส่งคำสั่ง (Submit)", type="primary"):
    if cmd:
        with st.spinner("Processing..."):
            res = process_command(cmd)
            if "error" in res:
                st.error(res['error'])
                st.warning("👈 ลองกดปุ่ม 'เช็คชื่อโมเดล' ด้านซ้ายดูครับ ว่ามีชื่ออะไรบ้าง")
            else:
                st.success(f"Saved: {res.get('item')}")
                # (แสดง JSON ดิบๆ เพื่อความชัวร์)
                st.json(res)
