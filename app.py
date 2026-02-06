import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าจอ (UI CONFIGURATION)
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Anesthesia Voice Logger", page_icon="🩺", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    h1, h2, h3 { color: #2E86C1; }
    .stButton>button {
        background-color: #2E86C1;
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        font-size: 16px;
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #1B4F72; color: white; }
    [data-testid="stMetricValue"] { font-size: 2.5rem; color: #E74C3C; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ฟังก์ชันสมอง AI (ใช้รุ่น gemini-pro ที่เสถียรที่สุด)
# ---------------------------------------------------------
def process_command_with_ai(command_text):
    if "GEMINI_API_KEY" not in st.secrets:
        return {"error": "ไม่พบ API Key! กรุณาตั้งค่าใน Secrets"}

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # 🟢 แก้ไข: ใช้ 'gemini-pro' แทน flash เพื่อความเสถียรสูงสุด
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        You are a smart assistant for an Anesthesiologist.
        Analyze this command: "{command_text}"
        
        Rules:
        1. Extract Item Name, Quantity (number only), Unit.
        2. Classify into ONE Category: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Antibiotic, Equipment, Critical Event, General].
        3. Output JSON ONLY.
        
        Example: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "category": "Narcotic"}}
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
        
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------
# 3. ส่วนแสดงผล (UI)
# ---------------------------------------------------------
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Time', 'Item', 'Qty', 'Unit', 'Category'])

c1, c2 = st.columns([1, 8])
with c1:
    st.image("https://img.icons8.com/color/96/anesthetist.png", width=80)
with c2:
    st.title("Smart Anesthesia Voice Logger")

st.divider()

col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.subheader("🎤 Voice / Text Command")
    st.info("ตัวอย่าง: 'ให้ Fentanyl 50 ไมโครกรัม' หรือ 'BP Drop'")
    
    command = st.text_input("พิมพ์คำสั่งที่นี่:", key="cmd_input")
    
    if st.button("🚀 บันทึกข้อมูล (Submit)", use_container_width=True):
        if command:
            with st.spinner("🤖 AI กำลังประมวลผล..."):
                result = process_command_with_ai(command)
                
                if "error" in result:
                    st.error(f"เกิดข้อผิดพลาด: {result['error']}")
                else:
                    new_record = {
                        'Time': datetime.now().strftime("%H:%M:%S"),
                        'Item': result.get('item', 'Unknown'),
                        'Qty': result.get('qty', 0),
                        'Unit': result.get('unit', '-'),
                        'Category': result.get('category', 'General')
                    }
                    st.session_state.data = pd.concat([pd.DataFrame([new_record]), st.session_state.data], ignore_index=True)
                    st.success(f"✅ บันทึกแล้ว: {new_record['Item']}")

with col_right:
    st.subheader("📊 Real-time Dashboard")
    
    if not st.session_state.data.empty:
        narc_df = st.session_state.data[st.session_state.data['Category'] == 'Narcotic']
        narc_sum = narc_df['Qty'].sum()
        crit_count = len(st.session_state.data[st.session_state.data['Category'] == 'Critical Event'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Narcotics", f"{narc_sum}")
        m2.metric("Critical Events", f"{crit_count}", delta_color="inverse")
        m3.metric("Total Logs", f"{len(st.session_state.data)}")
        
        st.dataframe(st.session_state.data, use_container_width=True, hide_index=True)
        
        # กราฟแท่ง (ใช้ Built-in ไม่ต้องพึ่ง Matplotlib)
        st.bar_chart(st.session_state.data.groupby("Category")["Qty"].sum())
        
    else:
        st.info("รอรับคำสั่งแรก...")
