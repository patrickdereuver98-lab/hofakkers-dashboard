import streamlit as st
import json
from PIL import Image
import google.generativeai as genai
from data.storage import save_bon_to_excel
import os

# Configureer Gemini model voor bon extractie
systeem_prompt = """
Je bent een expert in het extraheren van financiële data uit bonnetjes en facturen.
Analyseer de geüploade afbeelding en retourneer ALLEEN een geldige JSON object met deze exacte structuur:
{
  "Bedrag": float (het totale bedrag inclusief BTW),
  "Leverancier": "string" (naam van de winkel/bedrijf),
  "Kamer": "string" (suggestie voor welke ruimte dit hoort, gebaseerd op de aankoop, bijv. "Keuken", "Badkamer", etc.),
  "Omschrijving": "string" (korte beschrijving van de aankoop)
}
Gebruik Nederlandse taal voor de velden. Als iets niet duidelijk is, maak een redelijke inschatting.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # Gebruikt beschikbare versie
    system_instruction=systeem_prompt
)

st.title("🧾 AI Bonnenstraat")

st.markdown("Upload een bonnetje of factuur. De AI extraheert direct de data. Na controle slaan we dit netjes op in de Excel.")

# Laad API key
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("GEMINI_API_KEY niet gevonden in secrets.")
    st.stop()

uploaded_file = st.file_uploader("Upload je bon (PNG/JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Toon afbeelding
    image = Image.open(uploaded_file)
    st.image(image, caption="Geüploade bon", use_column_width=True)
    
    # Extract data met AI
    if st.button("🤖 Extraheer Data met AI"):
        with st.spinner("AI analyseert de bon..."):
            try:
                # Converteer image naar bytes
                from io import BytesIO
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_bytes = img_byte_arr.getvalue()
                
                # Genereer response
                response = model.generate_content([
                    {"mime_type": "image/jpeg", "data": img_bytes}
                ])
                
                # Parse JSON
                ai_data = json.loads(response.text.strip())
                
                # Toon geëxtraheerde data
                st.subheader("📋 Geëxtraheerde Data")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Bedrag:** € {ai_data['Bedrag']:.2f}")
                    st.write(f"**Leverancier:** {ai_data['Leverancier']}")
                with col2:
                    st.write(f"**Kamer:** {ai_data['Kamer']}")
                    st.write(f"**Omschrijving:** {ai_data['Omschrijving']}")
                
                # Opslaan optie
                if st.button("✅ Opslaan naar Excel"):
                    bon_data = {
                        "Datum": st.date_input("Datum", value=None).strftime("%Y-%m-%d") if st.date_input("Datum", value=None) else "",
                        "Leverancier": ai_data['Leverancier'],
                        "Bedrag": ai_data['Bedrag'],
                        "Categorie": st.selectbox("Categorie", ["Materialen", "Arbeid", "Overig"]),
                        "Kamer": ai_data['Kamer'],
                        "Omschrijving": ai_data['Omschrijving']
                    }
                    
                    if save_bon_to_excel(bon_data):
                        st.success("✅ Bon opgeslagen in Excel!")
                        # Reset uploader
                        st.rerun()
                    else:
                        st.error("❌ Opslaan mislukt.")
            
            except Exception as e:
                st.error(f"AI extractie mislukt: {e}")