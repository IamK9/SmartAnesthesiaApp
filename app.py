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
    
    default_ix = 0
    target_model = "gemini-2.0-flash"
    if target_model in all_options:
        default_ix = all_options.index(target_model)
    elif "gemini-1.5-flash" in all_options:
        default_ix = all_options.index("gemini-1.5-flash")
    
    selected_model_name = st.selectbox("เลือก AI Model:", all_options, index=default_ix)
    st.info(f"Using: {selected_model_name}")

# 4. AI FUNCTION (รองรับ Multiple Items)
def process_command(cmd):
    if "GEMINI_API_KEY" not in st.secrets: return {"error": "API Key Missing"}
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(selected_model_name)
        
        # Prompt สั่งให้ตอบเป็น List เสมอ เพื่อความชัวร์
        prompt = f"""
        Act as an Expert Anesthesia Assistant.
        Analyze input: "{cmd}"
        
        Task: Extract ALL medical items/events from the text.
        
        Rules:
        1. Return a JSON ARRAY of objects (even if there is only one item).
        2. Keys: "item", "qty", "unit", "category".
        3. If multiple items (e.g., "Drug A and Drug B"), separate them into objects.
        4. Category list: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Antibiotic, Equipment, Critical Event, General].
        
        Example Input: "Give Cefazolin 2 g and Fentanyl 100 mcg"
        Example Output: 
        [
            {{"item": "Cefazolin", "qty": 2, "unit": "g", "category": "Antibiotic"}},
            {{"item": "Fentanyl", "qty": 100, "unit": "mcg", "category": "Narcotic"}}
        ]
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        
        # แปลงเป็น JSON (จะได้ List กลับมา)
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
            
            # --- จัดการผลลัพธ์ (แก้ Error ตรงนี้) ---
            
            # 1. เช็คว่า Error ตั้งแต่ AI หรือไม่
            if isinstance(res, dict) and "error" in res:
                st.error(f"❌ Error: {res['error']}")
            
            else:
                # 2. แปลงทุกอย่างให้เป็น List (เพื่อวนลูปบันทึกทีละตัว)
                items_to_save = []
                if isinstance(res, list):
                    items_to_save = res
                elif isinstance(res, dict):
                    items_to_save = [res]
                
                # 3. วนลูปบันทึกข้อมูล
                saved_count = 0
                for entry in items_to_save:
                    # ดึงค่าแบบปลอดภัย (Case Insensitive)
                    item = entry.get('item') or entry.get('Item') or "Unknown"
                    qty = entry.get('qty') or entry.get('Qty') or 1
                    unit = entry.get('unit') or entry.get('Unit') or "-"
                    cat = entry.get('category') or entry.get('Category') or "General"
                    
                    # บันทึกลงตาราง
                    thai_time = (datetime.now() + timedelta(hours=7)).strftime("%H:%M:%S")
                    
                    if 'logs' not in st.session_state: 
                        st.session_state.logs = pd.DataFrame(columns=['Time','Item','Qty','Unit','Category'])

                    new_row = {
                        'Time': thai_time,
                        'Item': item, 'Qty': qty, 'Unit': unit, 'Category': cat
                    }
                    st.session_state.logs = pd.concat([pd.DataFrame([new_row]), st.session_state.logs], ignore_index=True)
                    saved_count += 1
                
                if saved_count > 0:
                    st.success(f"✅ Saved {saved_count} items successfully!")

# Dashboard
if 'logs' in st.session_state and not st.session_state.logs.empty:
    st.divider()
    st.subheader("📊 Dashboard")
    
    try:
        # คำนวณยอดรวม
        narc_sum = pd.to_numeric(st.session_state.logs[st.session_state.logs['Category'] == 'Narcotic']['Qty'], errors='coerce').fillna(0).sum()
        crit_count = len(st.session_state.logs[st.session_state.logs['Category'] == 'Critical Event'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Narcotics (Total)", f"{int(narc_sum)}")
        m2.metric("Critical Events", f"{crit_count}", delta_color="inverse")
        m3.metric("Total Logs", len(st.session_state.logs))
    except Exception as e:
        pass

    st.dataframe(st.session_state.logs, use_container_width=True, hide_index=True)
