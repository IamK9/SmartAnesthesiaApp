import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

# 1. UI SETUP
st.set_page_config(page_title="Smart Anesthesia", page_icon="💉", layout="wide")
st.markdown("""<style>.stButton>button {width: 100%; border-radius: 8px; background-color: #2E86C1; color: white;}</style>""", unsafe_allow_html=True)

# 2. ฟังก์ชันดึงรายชื่อโมเดล
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

# 3. SIDEBAR: เลือกโมเดล (จัดย่อหน้าใหม่ให้ถูกต้อง)
with st.sidebar:
    st.header("⚙️ Settings")
    
    # รายชื่อสำรอง (เรียงตามความเก่ง)
    backup_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    # พยายามดึงของจริง
    real_models = get_available_models()
    all_options = sorted(list(set(real_models + backup_models)))
    
    # *** ตั้งค่าเริ่มต้นเป็น gemini-2.0-flash (ถ้ามี) ***
    default_ix = 0
    target_model = "gemini-2.0-flash"
    
    if target_model in all_options:
        default_ix = all_options.index(target_model)
    elif "gemini-1.5-flash" in all_options:
        default_ix = all_options.index("gemini-1.5-flash")
    
    selected_model_name = st.selectbox("เลือก AI Model:", all_options, index=default_ix)
    st.info(f"Using: {selected_model_name}")

# 4. AI FUNCTION (เพิ่มความฉลาดเรื่อง Critical Event)
def process_command(cmd):
    if "GEMINI_API_KEY" not in st.secrets: return {"error": "API Key Missing"}
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(selected_model_name)
        
        # Prompt สั่งงาน (เพิ่ม Rule พิเศษ)
        prompt = f"""
        Act as an Anesthesiologist Assistant.
        Analyze input: "{cmd}"
        
        Rules:
        1. Extract Item, Qty, Unit.
        2. IF input is a Critical Event (e.g., BP Drop, Desat, Cardiac Arrest):
           - Set Category = "Critical Event"
           - Set Qty = 1
           - Set Unit = "event"
           - Item = The event name (e.g., "Hypotension", "Desaturation")
        3. IF input is Drug/Equipment:
           - Classify Category: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Antibiotic, Equipment].
        
        Output JSON ONLY. 
        Example 1: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "cat": "Narcotic"}}
        Example 2: {{"item": "Hypotension", "qty": 1, "unit": "event", "cat": "Critical Event"}}
        """
        
        response = model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        return {"error": str(e)}

# 5. MAIN UI
c1, c2 = st.columns([1, 5])
with c1: st.image("https://img.icons8.com/color/96/anesthetist.png", width=60)
with c2: st.title("Smart Anesthesia Logger")

cmd = st.text_input("ป้อนคำสั่ง (Voice/Text):", key="cmd")

if st.button("🚀 ส่งคำสั่ง (Submit)"):
    if cmd:
        with st.spinner(f"AI ({selected_model_name}) Processing..."):
            res = process_command(cmd)
            if "error" in res:
                st.error(f"❌ Error: {res['error']}")
            else:
                # โชว์ผลลัพธ์สวยๆ
                item_show = res.get('item')
                qty_show = res.get('qty')
                unit_show = res.get('unit')
                cat_show = res.get('cat') # แก้ให้ตรงกับ JSON key
                
                st.success(f"✅ Saved: {item_show} ({qty_show} {unit_show}) - [{cat_show}]")
                
                # Save Data
                if 'logs' not in st.session_state: 
                    st.session_state.logs = pd.DataFrame(columns=['Time','Item','Qty','Unit','Category'])
                
                new_row = {
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'Item': item_show, 
                    'Qty': qty_show, 
                    'Unit': unit_show, 
                    'Category': cat_show
                }
                st.session_state.logs = pd.concat([pd.DataFrame([new_row]), st.session_state.logs], ignore_index=True)

# Dashboard
if 'logs' in st.session_state and not st.session_state.logs.empty:
    st.divider()
    st.subheader("📊 Dashboard")
    
    # Metrics
    try:
        narc_sum = st.session_state.logs[st.session_state.logs['Category'] == 'Narcotic']['Qty'].sum()
        crit_count = len(st.session_state.logs[st.session_state.logs['Category'] == 'Critical Event'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Narcotics (Total)", f"{narc_sum}")
        m2.metric("Critical Events", f"{crit_count}", delta_color="inverse")
        m3.metric("Total Logs", len(st.session_state.logs))
    except:
        pass

    st.dataframe(st.session_state.logs, use_container_width=True, hide_index=True)
