# 🏠 Hofakkers 44 Renovatie Dashboard

Een interactief Streamlit-dashboard voor de renovatie, begroting en het budgetbeheer van Hofakkers 44.

## 📋 Overzicht

Dit dashboard helpt bij het beheren van de financiële aspecten van de renovatie van Hofakkers 44. Het bestaat uit meerdere pagina's die elk een specifiek deel van het budget en de planning behandelen:

- **🏠 Dashboard**: Algemeen overzicht met KPI's, voortgang en financiële samenvattingen.
- **🔨 Verbouwing**: Bewerkbare verbouwingsbegroting met realtime totalen per categorie.
- **🛋️ Inboedel**: Bewerkbare inboedelbegroting per kamer.
- **💳 Cashflow**: Maandelijkse cashflow planner voor inkomsten en uitgaven.
- **💎 Vermogen**: Vermogensoverzicht voor Patrick & Willianne na de verbouwing.

Alle data wordt opgeslagen in een Excel-bestand en is volledig aanpasbaar via de interface.

## 🚀 Setup & Installatie

1. **Clone of download deze repository**
2. **Plaats het Excel-bestand in de data map:**
   Zorg dat `Begroting_Willianne_Patrick_PRO_v2.xlsx` zich in de map `/data/` bevindt.
3. **Installeer de benodigdheden:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start het dashboard:**
   ```bash
   streamlit run app.py
   ```

## 📊 Functies

### Dashboard (Hoofdpagina)
- **Project KPI's**: Overzicht van totale kosten, voortgang en budgetallocatie.
- **Maandelijkse Totalen**: Inkomsten, uitgaven en spaargeld per maand.
- **Grafieken**: Donut-charts voor verdeling van uitgaven, voortgangsbalken en meer.

### Verbouwing
- Bewerkbare lijst van verbouwingskosten per categorie (bijv. keuken, badkamer).
- Realtime berekening van totalen en voortgang.
- Mogelijkheid om items toe te voegen, bewerken of verwijderen.

### Inboedel
- Begroting per kamer voor meubels en inrichting.
- Bewerkbare tabellen met kosten per item.
- Totaaloverzicht per kamer en algemeen.

### Cashflow
- Maandelijkse planner voor inkomsten (vaste en variabele) en uitgaven.
- Bewerkbare tabellen voor elke maand.
- Berekening van netto cashflow en spaargeld.

### Vermogen
- Overzicht van het vermogen van Patrick en Willianne na de verbouwing.
- Aanpasbare bedragen voor spaargeld, investeringen, etc.
- Grafische weergave van de verdeling.

## 🛠️ Technologieën

- **Streamlit**: Voor de webinterface.
- **Pandas & Plotly**: Voor data manipulatie en visualisaties.
- **Excel**: Voor data opslag en import/export.

## 📝 Bijdragen

Voor vragen of verbeteringen, neem contact op met de ontwikkelaars.

## 📄 Licentie

Dit project is privé en bedoeld voor persoonlijk gebruik.