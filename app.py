import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Smart Anesthesia", page_icon="💉", layout="wide")

# ใส่ CSS ตรงนี้เลย ไม่ต้องแยกไฟล์
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    h1 { color: #2E86C1; }
    .stButton>button { background-color: #2E86C1; color: white; border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 2rem; color: #E74C3C; }
</style>
""", unsafe_allow_html=True)

# --- 2. AI FUNCTION (รวมไว้ที่นี่) ---
def get_gemini_response(command_text):
    try:
        # ดึง Key จาก Streamlit Cloud Secrets
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        else:
            return {"error": "Key Missing. Please set GEMINI_API_KEY in Secrets."}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an anesthesia assistant. Analyze: "{command_text}"
        Extract Item, Quantity (number), Unit.
        Classify into: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Antibiotic, Equipment, Critical Event].
        Return ONLY JSON. Example: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "cat": "Narcotic"}}
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return {"error": str(e)}

# --- 3. MAIN APP UI ---
if 'logs' not in st.session_state:
    st.session_state.logs = pd.DataFrame(columns=['Time', 'Item', 'Qty', 'Unit', 'Category'])

col1, col2 = st.columns([1, 2])

with col1:
    st.image("https://img.icons8.com/color/96/anesthetist.png", width=80) # ใช้รูปออนไลน์แทน
    st.title("Smart Anesthesia")
    st.info("Try: 'Give Fentanyl 50 mcg' or 'BP Drop'")
    
    # Input
    text_val = st.text_input("Type Command:", key="txt_input")
    # ปุ่มกดส่ง
    if st.button("Submit Command", type="primary"):
        if text_val:
            with st.spinner("AI Processing..."):
                data = get_gemini_response(text_val)
                
                if "error" in data:
                    st.error(data["error"])
                else:
                    new_row = {
                        'Time': datetime.now().strftime("%H:%M:%S"),
                        'Item': data.get('item', 'Unknown'),
                        'Qty': data.get('qty', 0),
                        'Unit': data.get('unit', '-'),
                        'Category': data.get('cat', 'General')
                    }
                    st.session_state.logs = pd.concat([pd.DataFrame([new_row]), st.session_state.logs], ignore_index=True)
                    st.success(f"Recorded: {new_row['Item']}")

with col2:
    st.subheader("Real-time Dashboard")
    
    if not st.session_state.logs.empty:
        # Metrics
        narc_sum = st.session_state.logs[st.session_state.logs['Category'] == 'Narcotic']['Qty'].sum()
        crit_count = len(st.session_state.logs[st.session_state.logs['Category'] == 'Critical Event'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Narcotics", f"{narc_sum}", "mcg/mg")
        m2.metric("Critical Events", f"{crit_count}", "Times")
        m3.metric("Total Logs", len(st.session_state.logs))
        
        # Table
        st.dataframe(st.session_state.logs, use_container_width=True, hide_index=True)
    else:
        st.write("Waiting for data...")
