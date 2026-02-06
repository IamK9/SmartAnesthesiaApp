import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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

# 3. SIDEBAR: เลือกโมเดล
with st.sidebar:
    st.header("⚙️ Settings")
    backup_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    real_models = get_available_models()
    all_options = sorted(list(set(real_models + backup_models)))
    
    # ตั้งค่าเริ่มต้น
    default_ix = 0
    target_model = "gemini-2.0-flash"
    if target_model in all_options:
        default_ix = all_options.index(target_model)
    elif "gemini-1.5-flash" in all_options:
        default_ix = all_options.index("gemini-1.5-flash")
    
    selected_model_name = st.selectbox("เลือก AI Model:", all_options, index=default_ix)
    st.info(f"Using: {selected_model_name}")

# 4. AI FUNCTION (ฉบับอัปเกรด: สั่งให้ชัดเจนขึ้น + ดักจับ Error)
def process_command(cmd):
    if "GEMINI_API_KEY" not in st.secrets: return {"error": "API Key Missing"}
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(selected_model_name)
        
        # Prompt ที่บังคับโครงสร้าง JSON ให้แม่นยำขึ้น
        prompt = f"""
        Act as an Expert Anesthesia Assistant.
        Analyze input: "{cmd}"
        
        Your Goal: Convert voice/text commands into structured data.
        
        Rules:
        1. Return strictly JSON with keys: "item", "qty", "unit", "category".
        2. Keys MUST be lowercase.
        3. If input is an action (e.g., "Intubate Tube 7.5"), map it to the Item (e.g., item="ET Tube No. 7.5", qty=1, unit="piece").
        4. If input is a Critical Event (e.g., "BP Drop"), set item="Hypotension", qty=1, unit="event", category="Critical Event".
        5. Category list: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Antibiotic, Equipment, Critical Event, General].
        
        Example Output: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "category": "Narcotic"}}
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
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
                # --- จุดแก้สำคัญ: ดักจับตัวพิมพ์เล็ก/ใหญ่ (Case Insensitive) ---
                # ไม่ว่า AI จะส่ง Item, item, ITEM เราจะจับได้หมด
                item = res.get('item') or res.get('Item') or res.get('ITEM') or cmd
                qty = res.get('qty') or res.get('Qty') or res.get('QTY') or 1
                unit = res.get('unit') or res.get('Unit') or res.get('UNIT') or "-"
                cat = res.get('category') or res.get('Category') or res.get('cat') or "General"
                
                # แสดงผลทันที
                st.success(f"✅ Saved: {item} ({qty} {unit}) - [{cat}]")
                
                # Save Data
                if 'logs' not in st.session_state: 
                    st.session_state.logs = pd.DataFrame(columns=['Time','Item','Qty','Unit','Category'])
                
                # เวลาไทย (UTC+7)
                thai_time = (datetime.now() + timedelta(hours=7)).strftime("%H:%M:%S")
                
                new_row = {
                    'Time': thai_time,
                    'Item': item, 
                    'Qty': qty, 
                    'Unit': unit, 
                    'Category': cat
                }
                st.session_state.logs = pd.concat([pd.DataFrame([new_row]), st.session_state.logs], ignore_index=True)

# Dashboard
if 'logs' in st.session_state and not st.session_state.logs.empty:
    st.divider()
    st.subheader("📊 Dashboard")
    
    try:
        # คำนวณยอดรวม (พยายามแปลงเป็นตัวเลขก่อนบวก)
        narc_sum = pd.to_numeric(st.session_state.logs[st.session_state.logs['Category'] == 'Narcotic']['Qty'], errors='coerce').fillna(0).sum()
        crit_count = len(st.session_state.logs[st.session_state.logs['Category'] == 'Critical Event'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Narcotics (Total)", f"{int(narc_sum)}")
        m2.metric("Critical Events", f"{crit_count}", delta_color="inverse")
        m3.metric("Total Logs", len(st.session_state.logs))
    except Exception as e:
        st.error(f"Calculation Error: {e}")

    st.dataframe(st.session_state.logs, use_container_width=True, hide_index=True)
