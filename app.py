import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าจอ (UI CONFIGURATION)
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Anesthesia Voice Logger", page_icon="🩺", layout="wide")

# ปรับแต่ง CSS ให้สวยงาม สะอาดตา (Medical Theme)
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
    .stAlert { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ฟังก์ชันสมอง AI (AI ENGINE - GEMINI)
# ---------------------------------------------------------
def process_command_with_ai(command_text):
    # ตรวจสอบ API Key
    if "GEMINI_API_KEY" not in st.secrets:
        return {"error": "ไม่พบ API Key! กรุณาตั้งค่าใน Secrets"}

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # ใช้ Model Flash เพื่อความเร็ว
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # คำสั่งที่ส่งให้ AI (Prompt) - ปรับให้รองรับภาษาไทยและศัพท์แพทย์
        prompt = f"""
        You are a smart assistant for an Anesthesiologist.
        Analyze the following voice command (which may be in Thai or English): "{command_text}"
        
        Your Task:
        1. Extract the **Item Name** (Drug name or Equipment name).
        2. Extract the **Quantity** (Number only). If not specified, default to 1.
        3. Extract the **Unit** (e.g., mg, mcg, amp, piece).
        4. Classify into ONE **Category**:
           - 'Narcotic' (High alert drugs: Fentanyl, Morphine, Pethidine)
           - 'Vasoactive' (BP/Heart drugs: Ephedrine, Norepinephrine, Nicardipine)
           - 'Induction' (Propofol, Ketamine, Etomidate)
           - 'Muscle Relaxant' (Rocuronium, Cisatracurium)
           - 'Antibiotic'
           - 'Equipment' (Syringe, Needle, Gauze, Airway)
           - 'Critical Event' (BP Drop, Desat, Bradycardia, Cardiac Arrest)
           - 'General' (Others)
        
        Output Format: Return ONLY a valid JSON string.
        Example: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "category": "Narcotic"}}
        """
        
        response = model.generate_content(prompt)
        # ล้างข้อความขยะที่อาจติดมา
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
        
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------
# 3. เตรียมข้อมูล (SESSION STATE)
# ---------------------------------------------------------
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Time', 'Item', 'Qty', 'Unit', 'Category'])

# ---------------------------------------------------------
# 4. ส่วนแสดงผลหน้าจอ (USER INTERFACE)
# ---------------------------------------------------------

# ส่วนหัว (Header)
c1, c2 = st.columns([1, 8])
with c1:
    st.image("https://img.icons8.com/color/96/anesthetist.png", width=80)
with c2:
    st.title("Smart Anesthesia Voice Logger")
    st.markdown("ระบบบันทึกข้อมูลและยาทางวิสัญญีด้วยเสียง (AI-Powered)")

st.divider()

# แบ่งหน้าจอเป็น 2 ส่วน: ซ้าย(Input) ขวา(Dashboard)
col_left, col_right = st.columns([1, 2], gap="large")

# --- PANEL ซ้าย: รับคำสั่ง ---
with col_left:
    st.subheader("🎤 Voice / Text Command")
    st.info("พูดหรือพิมพ์คำสั่ง เช่น: 'ให้ Fentanyl 50 ไมโครกรัม' หรือ 'BP Drop'")
    
    # 1. ช่องรับข้อมูล (ใช้ Text Input เพื่อความเสถียรสูงสุดบนเวที)
    # หมายเหตุ: ถ้าใช้ st.audio_input() ต้องเป็น Streamlit เวอร์ชันใหม่ล่าสุด
    command = st.text_input("พิมพ์คำสั่งที่นี่:", key="cmd_input", placeholder="Ex. Propofol 100 mg")
    
    # 2. ปุ่มส่งข้อมูล
    if st.button("🚀 บันทึกข้อมูล (Submit)", use_container_width=True):
        if command:
            with st.spinner("🤖 AI กำลังประมวลผล..."):
                result = process_command_with_ai(command)
                
                if "error" in result:
                    st.error(f"เกิดข้อผิดพลาด: {result['error']}")
                else:
                    # บันทึกข้อมูลลงตาราง
                    new_record = {
                        'Time': datetime.now().strftime("%H:%M:%S"),
                        'Item': result.get('item', 'Unknown'),
                        'Qty': result.get('qty', 0),
                        'Unit': result.get('unit', '-'),
                        'Category': result.get('category', 'General')
                    }
                    st.session_state.data = pd.concat([pd.DataFrame([new_record]), st.session_state.data], ignore_index=True)
                    st.success(f"✅ บันทึกแล้ว: {new_record['Item']} ({new_record['Qty']} {new_record['Unit']})")

    st.markdown("---")
    st.caption("Tips: ระบบรองรับทั้งภาษาไทยและอังกฤษ AI จะแยกหมวดหมู่ให้อัตโนมัติ")

# --- PANEL ขวา: Dashboard ---
with col_right:
    st.subheader("📊 Real-time Dashboard")
    
    if not st.session_state.data.empty:
        # 1. ส่วนแสดงตัวเลขสำคัญ (Metrics)
        # คำนวณยอดรวม Narcotics
        narc_df = st.session_state.data[st.session_state.data['Category'] == 'Narcotic']
        narc_sum = narc_df['Qty'].sum()
        
        # นับจำนวนเหตุการณ์วิกฤต
        crit_count = len(st.session_state.data[st.session_state.data['Category'] == 'Critical Event'])
        
        # นับจำนวนรายการทั้งหมด
        total_logs = len(st.session_state.data)

        m1, m2, m3 = st.columns(3)
        m1.metric("Narcotics Used", f"{narc_sum}", "units")
        m2.metric("Critical Events", f"{crit_count}", "times", delta_color="inverse")
        m3.metric("Total Logs", f"{total_logs}", "records")
        
        st.markdown("#### 📝 Transaction Logs (ล่าสุด)")
        
        # 2. ตารางข้อมูล (Dataframe)
        st.dataframe(
            st.session_state.data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Category": st.column_config.TextColumn("Category", width="medium"),
                "Time": st.column_config.TextColumn("Time", width="small"),
            }
        )
        
        # 3. กราฟสรุป (Chart)
        st.markdown("#### 📈 Usage by Category")
        chart_data = st.session_state.data.groupby("Category")["Qty"].sum()
        st.bar_chart(chart_data, color="#2E86C1")
        
    else:
        # แสดงหน้าว่างๆ สวยๆ ตอนยังไม่มีข้อมูล
        st.warning("ยังไม่มีข้อมูล... กรุณาลองป้อนคำสั่งแรก")
        st.image("https://cdn.dribbble.com/users/2063378/screenshots/14206263/media/4c5520c017d84f09d84f63c473136209.png?resize=400x300", width=400)
