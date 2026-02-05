import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Smart Anesthesia Nurse", page_icon="💉", layout="wide")

# 2. เชื่อมต่อ Gemini (Secret Key จะไปใส่ใน Setting ของ Cloud ทีหลัง)
# ถ้าลองในเครื่องให้แก้เป็น api_key="YOUR_KEY_HERE"
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.warning("Please setup GEMINI_API_KEY in Streamlit Secrets")

# 3. เตรียม Database จำลอง (ใช้ DataFrame แทน Excel ชั่วคราว)
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Timestamp', 'Item', 'Quantity', 'Category', 'Raw_Text'])

# --- ส่วนหน้าจอ UI ---

st.title("🎙️ Smart Anesthesia Voice Logger")
st.caption("Powered by Gemini 1.5 Flash")

# แบ่งหน้าจอเป็น 2 คอลัมน์ (ซ้าย: สั่งงาน / ขวา: Dashboard)
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Voice Command")
    st.info("Try saying: 'Fentanyl 50 micrograms' or 'BP drop give Ephedrine 6 mg'")
    
    # ปุ่มอัดเสียง (Built-in ของ Streamlit)
    audio_value = st.audio_input("Record your voice")

    if audio_value:
        st.success("Processing audio...")
        
        # --- ส่วน AI Processing ---
        # 1. แปลงเสียงเป็น Text (ถ้า Gemini รับ Audio โดยตรงได้ก็ส่งเลย แต่ในที่นี้ขอสมมติว่าแปลง Text มาแล้วหรือใช้โมเดลเสียง)
        # *หมายเหตุ: เพื่อความง่ายในการ Demo ใน 2 วัน อาจจะใช้ st.text_input คู่กันกันเหนียว
        
        # สมมติ Logic การเรียก Gemini (Prompt เดิมที่เราเคยคุยกัน)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        You are an anesthesia assistant. Analyze this command/audio context.
        Extract: Item Name, Quantity (number only), and Category (Narcotic, Vasoactive, Induction, Event).
        Return JSON string only. Example: {"item": "Fentanyl", "qty": 50, "cat": "Narcotic"}
        """
        
        # ส่งเสียงให้ Gemini (ต้องแปลง Audio เป็น Blob ก่อน - ขั้นตอนนี้อาจซับซ้อนหน้างาน)
        # ** ทางลัดสำหรับ Demo: ** ให้ Gemini ฟังเสียงโดยตรง (Multimodal)
        response = model.generate_content([prompt, "Please analyze the audio file provided in the context (mockup for code structure)"]) 
        # *ในโค้ดจริงต้องมีการจัดการไฟล์เสียงเล็กน้อย*
        
        # จำลองผลลัพธ์เพื่อไม่ให้โค้ด Error ตอนอาจารย์เอาไปแปะ
        mock_response = """{"item": "Fentanyl", "qty": 50, "cat": "Narcotic"}""" 
        
        # แปลง JSON
        result = json.loads(mock_response) 
        
        # บันทึกลงตาราง
        new_row = {
            'Timestamp': datetime.now().strftime("%H:%M:%S"),
            'Item': result['item'],
            'Quantity': result['qty'],
            'Category': result['cat'],
            'Raw_Text': "Voice Input Demo"
        }
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
        st.success("Saved!")

with col2:
    st.header("Real-time Dashboard")
    
    # แสดง Metric
    if not st.session_state.data.empty:
        narc_count = st.session_state.data[st.session_state.data['Category'] == 'Narcotic']['Quantity'].sum()
        st.metric("Total Narcotics Usage", f"{narc_count} units", delta="Updated just now")
    
    # แสดงตารางล่าสุด
    st.subheader("Recent Logs")
    st.dataframe(st.session_state.data.tail(5), use_container_width=True)
    
    # แสดงกราฟ
    if not st.session_state.data.empty:
        st.subheader("Usage by Category")
        chart_data = st.session_state.data.groupby("Category")["Quantity"].sum()
        st.bar_chart(chart_data)

# --- จบโค้ด ---
