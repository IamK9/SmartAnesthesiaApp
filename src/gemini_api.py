import google.generativeai as genai
import json
import streamlit as st

def process_voice_command(text_command):
    """
    ฟังก์ชันสำหรับส่งข้อความไปหา Gemini และรับค่ากลับมาเป็น JSON
    """
    try:
        # ดึง Key จาก secrets
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are a smart assistant for Anesthesia Nurses.
        Analyze this command: "{text_command}"
        
        Rules:
        1. Extract the Item Name, Quantity (number), and Unit.
        2. Classify into ONE Category: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Antibiotic, Equipment, General].
        3. If it is a critical event (e.g., BP drop), set Category to "Critical Event".
        4. Return ONLY a JSON string. No markdown.
        
        Example Output:
        {{"item": "Fentanyl", "quantity": 50, "unit": "mcg", "category": "Narcotic"}}
        """
        
        response = model.generate_content(prompt)
        
        # Clean text (บางที AI เผลอใส่ ```json มาด้วย)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
        
    except Exception as e:
        return {"error": str(e)}
