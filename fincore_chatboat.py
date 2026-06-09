import streamlit as st
import requests
from bs4 import BeautifulSoup
import base64
import html as html_lib
import streamlit.components.v1 as components
import plotly.graph_objects as go
import numpy as np
from google import genai
from google.genai import types
import re
import io 
from pathlib import Path
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------- 1. PAGE CONFIGURATION ----------
st.set_page_config(page_title="FinCore : ", page_icon="💰", layout="wide")

# Neutral Theme Styling for both Light and Dark modes
st.markdown(
    """
    <style>
        :root {
            color-scheme: light dark;
            --app-bg: #f8fafc;
            --page-bg: rgba(45, 55, 75, 0.95);
            --panel-bg: #ffffff;
            --card-bg: #ffffff;
            --text-primary: #e5e7eb;
            --text-secondary: #cbd5e1;
            --border: #475569;
            --button-bg: #1f2937;
            --button-text: #e5e7eb;
            --button-border: #0ea5e9;
            --input-bg: #111827;
            --input-border: #334155;
            --accent: #0ea5e9;
            --shadow: 0 0 30px rgba(14, 165, 233, 0.4), 0 0 60px rgba(14, 165, 233, 0.2);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --app-bg: #020617;
                --page-bg: rgba(15, 23, 42, 0.92);
                --panel-bg: rgba(15, 23, 42, 0.96);
                --card-bg: rgba(15, 23, 42, 0.88);
                --text-primary: #e5e7eb;
                --text-secondary: #cbd5e1;
                --border: #334155;
                --button-bg: #1f2937;
                --button-text: #e5e7eb;
                --button-border: #475569;
                --input-bg: #111827;
                --input-border: #334155;
                --accent: #22d3ee;
                --shadow: 0 0 25px rgba(34, 211, 238, 0.12);
            }
        }

        html, body {
            zoom: 1.0;
            width: 100% !important;
            min-height: 100% !important;
            max-width: 100% !important;
            height: auto !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
        }

        .stApp, .main, .block-container {
            background-color: var(--app-bg) !important;
            color: var(--text-primary) !important;
        }

        .main .block-container, .block-container {
            max-width: 1400px;
            width: calc(100% - 24px) !important;
            padding: 16px 20px !important;
            margin: 0 auto !important;
            margin-top: 0px !important;
            background: var(--page-bg) !important;
            border: 1px solid var(--border) !important;
            border-radius: 24px !important;
            box-shadow: var(--shadow) !important;
        }

        section[data-testid="stSidebar"] {
            background-color: var(--panel-bg) !important;
            color: var(--text-primary) !important;
        }

        div.stButton > button, div[data-testid="stDownloadButton"] > button {
            background-color: var(--button-bg) !important;
            color: var(--button-text) !important;
            border: 1px solid var(--button-border) !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.2s ease-in-out !important;
        }

        div.stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover {
            background-color: var(--page-bg) !important;
            color: var(--button-text) !important;
            border-color: var(--accent) !important;
        }

        div.stButton > button:active, div[data-testid="stDownloadButton"] > button:active {
            background-color: var(--accent) !important;
            color: #ffffff !important;
        }

        div[data-baseweb="input"], div[data-baseweb="select"], input, textarea,
        .stTextInput input, .stNumberInput input, [data-baseweb="input"] input {
            background-color: var(--input-bg) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--input-border) !important;
        }

        input::placeholder, textarea::placeholder,
        .stTextInput input::placeholder, .stNumberInput input::placeholder,
        [data-baseweb="input"] input::placeholder {
            color: var(--text-secondary) !important;
            opacity: 1 !important;
        }

        h1, h2, h3, h4, h5, h6, p, span, label, strong {
            color: inherit !important;
        }

        div[data-testid="stMetric"] {
            background-color: var(--card-bg) !important;
            color: var(--text-primary) !important;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid var(--border) !important;
        }

        div[data-testid="stChatInput"] textarea {
            background-color: var(--input-bg) !important;
            color: var(--text-primary) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- 2. FINANCIAL GLOSSARY DICTIONARY ----------
FINANCIAL_GLOSSARY = {
    "SIP": "Systematic Investment Plan (SIP) is a method of investing a fixed sum regularly in a mutual fund, helping you benefit from rupee cost averaging and compounding over time.",
    "MUTUAL FUND": "A pool of money managed by a professional fund manager that invests in diversified portfolios of stocks, bonds, or other securities.",
    "BLUE CHIP STOCKS": "Shares of very large, financially sound, and nationally recognized companies with a history of stable growth and reliable dividend payouts (e.g., Reliance, TCS).",
    "SURPLUS": "The investable pool of cash left over after subtracting your total expenses (Essentials + Wants) from your net monthly income.",
    "CASH RESERVES": "An emergency safety buffer of highly liquid money (savings accounts, liquid funds) meant to cover 3 to 6 months of living expenses.",
    "FIXED INCOME": "Investment assets like Fixed Deposits (FDs) or Government Bonds that pay a fixed interest rate until maturity, offering high capital safety.",
    "GOLD HEDGE": "Investing in gold (Sovereign Gold Bonds or Gold ETFs) acting as a shield against inflation and stock market volatility, balancing portfolio risk.",
    "COMPOUND INTEREST": "The process of earning interest on your initial principal asset plus the accumulated interest from previous periods—essentially 'money making money'.",
    "ASSET ALLOCATION": "The strategic practice of distributing your investments across different asset classes (Equities, Debt, Gold, Cash) based on your risk tolerance.",
    "INFLATION": "The gradual rate at which the general prices of goods and services rise, subsequently reducing the purchasing power of your money over time."
}

# ---------- 3. SECURE INTERACTIVE API CONFIGURATION ----------
# Read GEMINI API key from environment first, then fall back to Streamlit secrets safely.
api_key_to_use = os.environ.get("GEMINI_API_KEY", "")
if not api_key_to_use:
    try:
        api_key_to_use = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key_to_use = ""

try:
    client = genai.Client(api_key=api_key_to_use) if api_key_to_use else None
except Exception:
    client = None

# ---------- 4. SESSION STATE INITIALIZATION ----------
if "show_home" not in st.session_state:
    st.session_state.show_home = True

if "step" not in st.session_state:
    st.session_state.step = "HOME"

if "home_tab" not in st.session_state:
    st.session_state.home_tab = "HOME"

if "user_name" not in st.session_state:
    st.session_state.user_name = "Guest User"

if "salary" not in st.session_state:
    st.session_state.salary = 50000.0

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I am your interactive AI Assistant. Ask me absolutely anything about finance."}]

if "essential_expenses" not in st.session_state:
    st.session_state.essential_expenses = 20000.0

if "lifestyle_expenses" not in st.session_state:
    st.session_state.lifestyle_expenses = 15000.0

if "existing_emi" not in st.session_state:
    st.session_state.existing_emi = 0.0

if "cibil_score" not in st.session_state:
    st.session_state.cibil_score = 750

if "deduction_80c" not in st.session_state:
    st.session_state.deduction_80c = 0.0

if "sf_name" not in st.session_state:
    st.session_state.sf_name = "Goal"

if "sf_target" not in st.session_state:
    st.session_state.sf_target = 120000.0

if "sf_months" not in st.session_state:
    st.session_state.sf_months = 12

if "ppf_annual" not in st.session_state:
    st.session_state.ppf_annual = 50000.0

if "dashboard_ready" not in st.session_state:
    st.session_state.dashboard_ready = False

if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

if "risk_profile" not in st.session_state: 
    st.session_state.risk_profile = "Moderate Growth"
    
if "expected_return" not in st.session_state: 
    st.session_state.expected_return = 0.122

# ---------- 5. HELPER FUNCTIONS ----------
def get_base64_image(image_path):
    try:
        image_file = Path(__file__).resolve().parent / image_path
        if not image_file.exists():
            image_file = Path(image_path)
        with open(image_file, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

logo_base64 = get_base64_image("fincore.jpeg")

def fallback_finance_news():
    news = [
        "Indian stock market updates are being tracked live",
        "SIP investing remains popular among young professionals",
        "Banks are focusing on digital finance and AI services",
        "CIBIL score and EMI management are important for loan approval",
        "Emergency fund planning is important for salaried people",
        "Tax planning helps compare old and new tax regimes"
    ]
    return " 🚨 ".join(news)

@st.cache_data(ttl=600)
def fetch_finance_news():
    try:
        url = "https://news.google.com/rss/search?q=India+finance+stock+market+personal+finance&hl=en-IN&gl=IN&ceid=IN:en"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")
        headlines = []
        for item in items[:10]:
            headlines.append(item.title.text.replace("&amp;", "&"))
        return " 💜 ".join(headlines) if headlines else fallback_finance_news()
    except:
        return fallback_finance_news()

@st.cache_data(ttl=1800)
def fetch_live_market_movers():
    try:
        url = "https://www.moneycontrol.com/news/business/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        scraped_tickers = []
        links = soup.find_all("a")
        watchlist = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "AXISBANK", "LT", "BHARTIARTL"]
        for link in links:
            text = link.get_text(strip=True).upper()
            if text in watchlist and text not in scraped_tickers:
                scraped_tickers.append(text)
        return scraped_tickers if scraped_tickers else ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    except Exception:
        return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    
@st.cache_data(ttl=600)
def fetch_top_20_nse_stocks():
    return [
        {"name": "RELIANCE", "price": 2945, "change": "+1.25%"},
        {"name": "TCS", "price": 3890, "change": "+0.85%"},
        {"name": "INFY", "price": 1640, "change": "-0.45%"},
        {"name": "HDFCBANK", "price": 1775, "change": "+2.10%"},
        {"name": "ICICIBANK", "price": 1240, "change": "+1.15%"},
        {"name": "SBIN", "price": 890, "change": "-1.05%"},
        {"name": "ITC", "price": 430, "change": "+0.30%"},
        {"name": "LT", "price": 3750, "change": "+1.90%"},
        {"name": "AXISBANK", "price": 1195, "change": "-0.80%"},
        {"name": "BHARTIARTL", "price": 1680, "change": "+2.40%"}
    ]

def generate_pdf_report():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=24, leading=28, textColor=colors.HexColor('#0f172a'), spaceAfter=15)
    subtitle_style = ParagraphStyle(name='SubTitleStyle', parent=styles['Normal'], fontSize=11, leading=14, textColor=colors.HexColor('#475569'), spaceAfter=25)
    h2_style = ParagraphStyle(name='H2Style', parent=styles['Heading2'], fontSize=16, leading=20, textColor=colors.HexColor('#1e3a8a'), spaceBefore=15, spaceAfter=10, keepWithNext=True)
    body_style = ParagraphStyle(name='BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#334155'))

    story.append(Paragraph("💰 FinCore Financial Portfolio Report", title_style))
    story.append(Paragraph(f"Prepared for: <b>{st.session_state.user_name}</b> | Generated Securely via FinCore Engine", subtitle_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Executive Capital Architecture Summary", h2_style))
    salary = st.session_state.salary
    total_ess = st.session_state.essential_expenses
    total_life = st.session_state.lifestyle_expenses
    total_burn = total_ess + total_life
    surplus = max(0.0, salary - total_burn)
    
    overview_data = [
        [Paragraph("<b>Financial Metric</b>", body_style), Paragraph("<b>Value Allocation</b>", body_style)],
        [Paragraph("Net Monthly Take-Home Income", body_style), Paragraph(f"₹{salary:,.2f}", body_style)],
        [Paragraph("Essential Dynamic Commitments", body_style), Paragraph(f"₹{total_ess:,.2f}", body_style)],
        [Paragraph("Lifestyle / Want Discretionary", body_style), Paragraph(f"₹{total_life:,.2f}", body_style)],
        [Paragraph("Monthly Operational Outflow Burn Rate", body_style), Paragraph(f"₹{total_burn:,.2f}", body_style)],
        [Paragraph("<b>Net Monthly Investable Surplus Pool</b>", body_style), Paragraph(f"<b>₹{surplus:,.2f}</b>", body_style)]
    ]
    
    t1 = Table(overview_data, colWidths=[300, 200])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("2. Credit Frameworks & Leverage Metrics", h2_style))
    dti_ratio = (st.session_state.existing_emi / salary * 100 if salary > 0 else 0)
    if st.session_state.cibil_score >= 750:
        cibil_tier, base_roi, max_dti_allowed = "Excellent", 0.085, 50
    elif st.session_state.cibil_score >= 650:
        cibil_tier, base_roi, max_dti_allowed = "Moderate", 0.098, 40
    else:
        cibil_tier, base_roi, max_dti_allowed = "High Risk", 0.12, 25
    available_emi_buffer = max(0, (salary * max_dti_allowed / 100) - st.session_state.existing_emi)
    r_monthly = base_roi / 12
    theoretical_max_loan = (available_emi_buffer * ((1 - (1 + r_monthly) ** (-240)) / r_monthly) if available_emi_buffer > 0 else 0)
    
    credit_data = [
        [Paragraph("<b>Metric Parameters</b>", body_style), Paragraph("<b>Analytics Assessment</b>", body_style)],
        [Paragraph("Bureau Credit Score (CIBIL Profile)", body_style), Paragraph(f"{st.session_state.cibil_score} ({cibil_tier})", body_style)],
        [Paragraph("Calculated Debt-to-Income (DTI) Ratio", body_style), Paragraph(f"{dti_ratio:.1f}%", body_style)],
        [Paragraph("System Baseline Rate of Interest (ROI)", body_style), Paragraph(f"{base_roi*100:.2f}%", body_style)],
        [Paragraph("Theoretical 20-Yr Maximum Home Loan Capacity", body_style), Paragraph(f"₹{theoretical_max_loan:,.2f}", body_style)]
    ]
    t2 = Table(credit_data, colWidths=[300, 200])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(t2)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("3. Luxurias Target Capital Allocation Target", h2_style))
    sf_needed = (st.session_state.sf_target / st.session_state.sf_months) if st.session_state.sf_months > 0 else 0
    sf_status = "ACHIEVABLE VECTOR" if surplus >= sf_needed else "DEFICIT VECTOR"
    
    sf_data = [
        [Paragraph("<b>Luxurias Target Parameter</b>", body_style), Paragraph("<b>Target Assessment Metrics</b>", body_style)],
        [Paragraph("Designated Sinking Asset Goal Name", body_style), Paragraph(f"{st.session_state.sf_name}", body_style)],
        [Paragraph("Target Valuation Threshold", body_style), Paragraph(f"₹{st.session_state.sf_target:,.2f}", body_style)],
        [Paragraph("Temporal Schedule Allocation (Months)", body_style), Paragraph(f"{st.session_state.sf_months} Months", body_style)],
        [Paragraph("Required Monthly Inflow Matrix", body_style), Paragraph(f"₹{sf_needed:,.2f} / mo", body_style)],
        [Paragraph("Feasibility Strategy Status", body_style), Paragraph(f"<b>{sf_status}</b>", body_style)]
    ]
    t3 = Table(sf_data, colWidths=[300, 200])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------- 6. GLOBAL CSS STYLE WITH SOFT GLOW EXTENSION ----------
bg_base64 = get_base64_image(r"new img.jpeg")

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image:
        linear-gradient(rgba(2,6,23,0.10), rgba(2,6,23,0.20)),
        url("data:image/png;base64,{bg_base64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

.main .block-container {{
    max-width: 1250px;
    padding-top: 12px !important;
    margin-top: 0px !important;
}}

.block-container {{
    padding-top: 12px !important;
    margin-top: 0px !important;
}}

section.main > div {{
    padding-top: 0rem !important;
}}

[data-testid="stAppViewContainer"] .main .block-container {{
    padding-top: 12px !important;
    margin-top: 0px !important;
}}

div.main:has(.home-wrap) .block-container {{
    padding-top: 12px !important;
    margin-top: 0px !important;
}}

div[data-testid="stHorizontalBlock"] {{
    margin-top: 0px !important;
    padding-top: 0px !important;
}}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ visibility: hidden; }}

div[data-testid="column"] button {{
    font-weight: 600 !important;
}}

/* --- THE GLOBAL SOFT GLOW COMPONENT INJECTIONS --- */
div[data-testid="stForm"], div.stForm {{
    border: 1px solid rgba(0, 245, 212, 0.4) !important;
    box-shadow: 0 0 15px rgba(0, 245, 212, 0.25) !important;
    background: rgba(15, 23, 42, 0.65) !important;
    border-radius: 20px !important;
}}

/* Glowing box container alignment styling */
div.stVerticalBlockBorderWrapper {{
    border: 1px solid rgba(0, 245, 212, 0.5) !important;
    box-shadow: 0 0 20px rgba(0, 245, 212, 0.3) !important;
    background: rgba(15, 23, 42, 0.45) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    margin-bottom: 20px !important;
}}

/* --- PREMIUM CHUNKY GLOWING METRIC CARDS --- */
div[data-testid="stMetric"] {{
    border: 1px solid rgba(148, 163, 184, 0.4) !important;
    box-shadow: 0 0 18px rgba(148, 163, 184, 0.22) !important;
    background: rgba(51, 65, 85, 0.92) !important;
    border-radius: 18px !important;
    padding: 25px 20px !important;
    min-height: 140px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    transition: all 0.3s ease;
}}
div[data-testid="stMetric"]:hover {{
    box-shadow: 0 0 28px rgba(148, 163, 184, 0.38) !important;
    border-color: rgba(148, 163, 184, 0.7) !important;
    transform: translateY(-4px);
}}
.budget-arrow {{
    margin-top: 12px;
    font-size: 18px;
    font-weight: 700;
    text-shadow: 0 0 16px rgba(0, 0, 0, 0.18);
}}
.budget-arrow.green {{
    color: #4ade80 !important;
    text-shadow: 0 0 12px rgba(74, 222, 128, 0.6);
}}
.budget-arrow.red {{
    color: #f87171 !important;
    text-shadow: 0 0 12px rgba(248, 113, 113, 0.6);
}}

/* Center labels and numbers inside metrics properly */
div[data-testid="stMetricLabel"] {{
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}}
div[data-testid="stMetricValue"] {{
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}}

.stSelectbox div[data-baseweb="select"] {{
    border: 1px solid rgba(251, 191, 36, 0.4) !important;
    box-shadow: 0 0 10px rgba(251, 191, 36, 0.15) !important;
    background: rgba(15, 23, 42, 0.8) !important;
    border-radius: 10px !important;
}}

div.element-container:has(div.stButton > button) button, button {{
    background: linear-gradient(145deg, #8b2eb5 0%, #d43aff 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.35) !important;
    box-shadow: 0 12px 25px rgba(139, 46, 181, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.35), inset 0 -2px 5px rgba(0, 0, 0, 0.12) !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.03em !important;
    border-radius: 18px !important;
    padding: 0.95rem 1.3rem !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25) !important;
    transition: all 0.2s ease-in-out !important;
    transform: translateY(0) !important;
}}
div.element-container:has(div.stButton > button) button:hover, button:hover {{
    background: linear-gradient(145deg, #c23cff 0%, #9b1ddb 100%) !important;
    box-shadow: 0 18px 30px rgba(139, 46, 181, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35), inset 0 -3px 6px rgba(0, 0, 0, 0.16) !important;
    border-color: rgba(255, 255, 255, 0.55) !important;
    transform: translateY(-2px) !important;
}}

button[title="Open Fin-Core Assistant"], button[aria-label="Open Fin-Core Assistant"] {{
    background: linear-gradient(145deg, #0474ff 0%, #02d1ff 100%) !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
    box-shadow: 0 14px 28px rgba(4, 116, 255, 0.35), inset 0 1px 0 rgba(255,255,255,0.28) !important;
    color: #ffffff !important;
    width: 90px !important;
    height: 90px !important;
    min-width: 90px !important;
    border-radius: 50% !important;
    transition: all 0.2s ease-in-out !important;
    transform: translateY(0) !important;
}}
button[title="Open Fin-Core Assistant"] span, button[aria-label="Open Fin-Core Assistant"] span {{
    font-size: 0 !important;
    color: transparent !important;
    line-height: 0 !important;
}}
button[title="Open Fin-Core Assistant"]:hover, button[aria-label="Open Fin-Core Assistant"]:hover {{
    background: linear-gradient(145deg, #00c2ff 0%, #0284ff 100%) !important;
    border-color: rgba(255,255,255,0.6) !important;
    box-shadow: 0 20px 35px rgba(4, 116, 255, 0.45), inset 0 1px 0 rgba(255,255,255,0.35) !important;
    transform: translateY(-3px) !important;
}}

div[style*="border: 1px solid"], div[style*="border:1px solid"] {{
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.2) !important;
}}

/* --- DYNAMIC TARGETED TEXT SIZE OVERRIDES FOR INNER PAGES --- */
html:not(:has(.home-wrap)) body, 
html:not(:has(.home-wrap)) div[data-testid="stAppViewContainer"] {{
    font-size: 19px !important;
}}

html:not(:has(.home-wrap)) p, 
html:not(:has(.home-wrap)) span, 
html:not(:has(.home-wrap)) label {{
    font-size: 19px !important;
}}

html:not(:has(.home-wrap)) h1 {{
    font-size: 42px !important;
}}

html:not(:has(.home-wrap)) h2 {{
    font-size: 34px !important;
}}

html:not(:has(.home-wrap)) h3 {{
    font-size: 28px !important;
}}

html:not(:has(.home-wrap)) input {{
    font-size: 19px !important;
    height: auto !important;
}}

html:not(:has(.home-wrap)) div[data-testid="stMetricValue"] {{
    font-size: 34px !important;
    font-weight: 800 !important;
    color: #00f5d4 !important;
}}

html:not(:has(.home-wrap)) div[data-testid="stMetricLabel"] p {{
    font-size: 18px !important;
    color: #f8fafc !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em !important;
    opacity: 1 !important;
    text-shadow: 0 0 3px rgba(0,0,0,0.25) !important;
}}

html:not(:has(.home-wrap)) button div p {{
    font-size: 18px !important;
}}
</style>
""", unsafe_allow_html=True)


# ---------- 7. RENDER HOMEPAGE SCREEN ----------
if st.session_state.show_home:
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([4, 1, 1, 1])
    with nav_col1:
        st.markdown("<h2 style='margin:0; padding:0; color:#00f5d4; font-family:sans-serif;'></h2>", unsafe_allow_html=True)
    with nav_col2:
        if st.button("🏠 Home", use_container_width=True, key="nav_home_btn"):
            st.session_state.home_tab = "HOME"
            st.rerun()
    with nav_col3:
        if st.button("👥 About Us", use_container_width=True, key="nav_about_btn"):
            st.session_state.home_tab = "ABOUT"
            st.rerun()
    with nav_col4:
        if st.button("📞 Contact Us", use_container_width=True, key="nav_contact_btn"):
            st.session_state.home_tab = "CONTACT"
            st.rerun()
            
    st.markdown("<hr style='margin-top:0px; margin-bottom:10px; border-color:rgba(0,245,212,0.25);'>", unsafe_allow_html=True)

    if st.session_state.home_tab == "ABOUT":
        about_html = """
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-start; text-align: center; font-family: Arial, sans-serif; padding: 20px 0;">
            <div style="width: 88%; background: rgba(3,7,18,0.78); border: 1px solid rgba(56,189,248,0.5); border-radius: 35px; padding: 45px; color: #dbeafe; box-shadow: 0 0 25px rgba(56,189,248,0.35);">
                <h1 style="font-size: 50px; background: linear-gradient(90deg, #38bdf8, #00f5d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900; margin-bottom: 10px;">About FinCore</h1>
                <p style="font-size: 20px; line-height: 1.7; margin-top: 10px; max-width: 800px; margin-left: auto; margin-right: auto;">
                    FinCore was built with a clear vision: to democratize financial literacy and simplify complex personal wealth tracking.
                </p>
                <p style="font-size: 18px; color: #38bdf8; margin-top: 15px; font-weight: 600;">
                    📈 Automated Architecture • 🔒 Data Security Primary • ⚡ Interactive Engineering
                </p>
                
                <!-- --- MISSION & VISION SECTION --- -->
                <hr style="margin:30px 0; border:0; height:1px; background:rgba(56,189,248,0.2);">
                <div style="display: flex; gap: 25px; justify-content: center; flex-wrap: wrap; margin-bottom: 15px;">
                    <div style="background: rgba(15,23,42,0.6); border: 1px solid rgba(0, 245, 212, 0.4); box-shadow: 0 0 15px rgba(0, 245, 212, 0.15); border-radius: 20px; padding: 25px; width: 45%; min-width: 280px; text-align: left;">
                        <h3 style="margin: 0 0 10px 0; color: #00f5d4; font-size: 22px;">🎯 Our Mission</h3>
                        <p style="margin: 0; font-size: 15px; line-height: 1.6; color: #cbd5e1;">Empowering individuals with intelligent financial tools to make informed decisions, build wealth, and achieve long-term financial security.</p>
                    </div>
                    <div style="background: rgba(15,23,42,0.6); border: 1px solid rgba(251, 191, 36, 0.4); box-shadow: 0 0 15px rgba(251, 191, 36, 0.15); border-radius: 20px; padding: 25px; width: 45%; min-width: 280px; text-align: left;">
                        <h3 style="margin: 0 0 10px 0; color: #fbbf24; font-size: 22px;">🚀 Our Vision</h3>
                        <p style="margin: 0; font-size: 15px; line-height: 1.6; color: #cbd5e1;">To become a trusted AI-powered financial companion for every household.</p>
                    </div>
                </div>

                <!-- --- WEALTH ANALYTICS FEATURES --- -->
                <hr style="margin:30px 0; border:0; height:1px; background:rgba(56,189,248,0.2);">
                <h2 style="font-size:28px; color:#38bdf8; margin-bottom:20px; font-weight: 800;">🛠️ Core Analytics Ecosystem</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 15px;">
                    <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(56,189,248,0.3); border-radius: 16px; padding: 20px; transition: transform 0.3s;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 30px; margin-bottom: 8px;">📊</div>
                        <h4 style="margin: 0 0 5px 0; color: #38bdf8; font-size: 16px;">Wealth Analytics</h4>
                        <p style="margin: 0; font-size: 13px; color: #94a3b8;">AI-powered portfolio insights</p>
                    </div>
                    <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(56,189,248,0.3); border-radius: 16px; padding: 20px; transition: transform 0.3s;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 30px; margin-bottom: 8px;">💰</div>
                        <h4 style="margin: 0 0 5px 0; color: #38bdf8; font-size: 16px;">Investment Planning</h4>
                        <p style="margin: 0; font-size: 13px; color: #94a3b8;">Personalized asset strategies</p>
                    </div>
                    <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(56,189,248,0.3); border-radius: 16px; padding: 20px; transition: transform 0.3s;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 30px; margin-bottom: 8px;">🏦</div>
                        <h4 style="margin: 0 0 5px 0; color: #38bdf8; font-size: 16px;">Loan Intelligence</h4>
                        <p style="margin: 0; font-size: 13px; color: #94a3b8;">Eligibility & EMI tuning</p>
                    </div>
                    <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(56,189,248,0.3); border-radius: 16px; padding: 20px; transition: transform 0.3s;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 30px; margin-bottom: 8px;">🔒</div>
                        <h4 style="margin: 0 0 5px 0; color: #38bdf8; font-size: 16px;">Secure Platform</h4>
                        <p style="margin: 0; font-size: 13px; color: #94a3b8;">Privacy-first metric safe</p>
                    </div>
                </div>

                <!-- --- PLATFORM STATISTICS --- -->
                <hr style="margin:30px 0; border:0; height:1px; background:rgba(56,189,248,0.2);">
                <h2 style="font-size:28px; color:#ff4ecd; margin-bottom:20px; font-weight: 800;">⚡ Network Pulse & Metrics</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 15px;">
                    <div style="background: rgba(15,23,42,0.9); border: 1px solid rgba(255, 78, 205, 0.5); box-shadow: 0 0 15px rgba(255, 78, 205, 0.2); border-radius: 18px; padding: 20px;">
                        <h3 style="margin: 0; font-size: 28px; color: #ff4ecd; font-weight: 900;">₹10M+</h3>
                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #cbd5e1;">Simulated Investments</p>
                    </div>
                    <div style="background: rgba(15,23,42,0.9); border: 1px solid rgba(255, 78, 205, 0.5); box-shadow: 0 0 15px rgba(255, 78, 205, 0.2); border-radius: 18px; padding: 20px;">
                        <h3 style="margin: 0; font-size: 28px; color: #ff4ecd; font-weight: 900;">95%</h3>
                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #cbd5e1;">Planning Accuracy</p>
                    </div>
                    <div style="background: rgba(15,23,42,0.9); border: 1px solid rgba(255, 78, 205, 0.5); box-shadow: 0 0 15px rgba(255, 78, 205, 0.2); border-radius: 18px; padding: 20px;">
                        <h3 style="margin: 0; font-size: 28px; color: #ff4ecd; font-weight: 900;">10+</h3>
                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #cbd5e1;">Financial Tools</p>
                    </div>
                    <div style="background: rgba(15,23,42,0.9); border: 1px solid rgba(255, 78, 205, 0.5); box-shadow: 0 0 15px rgba(255, 78, 205, 0.2); border-radius: 18px; padding: 20px;">
                        <h3 style="margin: 0; font-size: 28px; color: #ff4ecd; font-weight: 900;">100%</h3>
                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #cbd5e1;">Secure Analytics</p>
                    </div>
                </div>

                <!-- --- TEAM MEMBERS --- -->
                <hr style="margin:30px 0; border:0; height:1px; background:rgba(56,189,248,0.3);">
                <h2 style="font-size:28px; color:#00f5d4; margin-bottom:25px; font-weight: 800;">👨‍💻 Engineering Guild</h2>
                <div style="display:flex; justify-content:center; gap:25px; flex-wrap:wrap; margin-bottom: 15px;">
                    <div style="background:rgba(15,23,42,0.85); padding:20px; border-radius:20px; width:260px; border:1px solid rgba(56,189,248,0.3);">
                        <h3 style="margin: 0 0 10px 0; color:#38bdf8; font-size: 18px;">Priyanka Kumari Sharma</h3>
                        <p style="margin:0; font-size: 13px; color: #94a3b8;">📧 priyanka.sharma@fincorelabs.com</p>
                    </div>
                    <div style="background:rgba(15,23,42,0.85); padding:20px; border-radius:20px; width:260px; border:1px solid rgba(56,189,248,0.3);">
                        <h3 style="margin: 0 0 10px 0; color:#38bdf8; font-size: 18px;">Himali Parveen</h3>
                        <p style="margin:0; font-size: 13px; color: #94a3b8;">📧 himali.parveen@fincorelabs.com</p>
                    </div>
                    <div style="background:rgba(15,23,42,0.85); padding:20px; border-radius:20px; width:260px; border:1px solid rgba(56,189,248,0.3);">
                        <h3 style="margin: 0 0 10px 0; color:#38bdf8; font-size: 18px;">Nandita Das</h3>
                        <p style="margin:0; font-size: 13px; color: #94a3b8;">📧 nandita.das@fincorelabs.com</p>
                    </div>
                </div>

                <!-- --- TECHNOLOGY STACK BADGES --- -->
                <hr style="margin:30px 0; border:0; height:1px; background:rgba(56,189,248,0.2);">
                <h2 style="font-size:24px; color:#fbbf24; margin-bottom:20px; font-weight: 800;">⚙️ Core System Core Technology Stack</h2>
                <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                    <span style="background: rgba(255, 75, 75, 0.15); border: 1px solid rgba(255, 75, 75, 0.4); color: #ff4b4b; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; box-shadow: 0 0 8px rgba(255, 75, 75, 0.2);">⚡ Streamlit</span>
                    <span style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; box-shadow: 0 0 8px rgba(56, 189, 248, 0.2);">🤖 Gemini AI</span>
                    <span style="background: rgba(251, 191, 36, 0.15); border: 1px solid rgba(251, 191, 36, 0.4); color: #fbbf24; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; box-shadow: 0 0 8px rgba(251, 191, 36, 0.2);">📈 Plotly</span>
                    <span style="background: rgba(0, 245, 212, 0.15); border: 1px solid rgba(0, 245, 212, 0.4); color: #00f5d4; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; box-shadow: 0 0 8px rgba(0, 245, 212, 0.2);">🐍 Python</span>
                    <span style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.4); color: #a855f7; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; box-shadow: 0 0 8px rgba(168, 85, 247, 0.2);">☁️ Cloud Ready</span>
                </div>
            </div>
        </div>
        """
        components.html(about_html, height=1350, scrolling=True)

    elif st.session_state.home_tab == "CONTACT":
        contact_html = """
        <div style="display: flex; align-items: center; justify-content: center; text-align: center; font-family: Arial, sans-serif; min-height: 480px;">
            <div style="width: 82%; background: rgba(3,7,18,0.78); border: 1px solid rgba(251,191,36,0.5); border-radius: 35px; padding: 45px; color: #dbeafe; box-shadow: 0 0 25px rgba(251,191,36,0.3);">
                <h1 style="font-size: 50px; background: linear-gradient(90deg, #fbbf24, #ff4ecd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900;">Contact Support</h1>
                <p style="font-size: 21px; margin-top: 20px; line-height:1.6;">Have inquiries regarding data metrics or advanced features? Get in touch with our engineering team.</p>
                <div style="margin-top: 30px; font-size: 19px; line-height: 2;">
                    <div>📧 <b>Support Email:</b> operations@fincore-hub.io</div>
                    <div>📍 <b>Corporate Lab:</b> Salt Lake, Sector 5, Kolkata ,India</div>
                    <div>🕒 <b>Operational Hours:</b> Monday - Friday (09:00 AM – 06:00 PM IST)</div>
                    <div>🕒 <b>Phone number:</b> 963258741</div>
                </div>
            </div>
        </div>
        """
        components.html(contact_html, height=540, scrolling=False)

    else:
        news_text = html_lib.escape(fetch_finance_news())
        if logo_base64:
            logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" class="home-logo">'
        else:
            logo_html = '<div class="money-logo">💰</div>'

        # Expanded stock listings for widget columns
        stocks_html_block = "".join([
            f"<div style='display:flex; justify-content:space-between; margin-bottom: 8px; font-size:14px;'> "
            f"<span style='color:#cbd5e1; font-weight:600;'>{s['name']}</span>"
            f"<span style='color:{'#22c55e' if '+' in s['change'] else '#ef4444'}; font-weight:700;'>₹{s['price']:,} ({s['change']})</span></div>" 
            for s in fetch_top_20_nse_stocks()
        ])

        gainers_losers_html_block = """
        <div style='color:#22c55e; font-weight:700; font-size:13px; margin-bottom:4px;'>▲ TOP GAINERS</div>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:12px; color:#cbd5e1;'><span>TATAMOTORS</span><span style='color:#22c55e;'>+4.2%</span></div>
        <div style='display:flex; justify-content:space-between; margin-bottom:12px; font-size:12px; color:#cbd5e1;'><span>BHARTIARTL</span><span style='color:#22c55e;'>+2.4%</span></div>
        <div style='color:#ef4444; font-weight:700; font-size:13px; margin-bottom:4px;'>▼ TOP LOSERS</div>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:12px; color:#cbd5e1;'><span>SBIN</span><span style='color:#ef4444;'>-1.05%</span></div>
        <div style='display:flex; justify-content:space-between; font-size:12px; color:#cbd5e1;'><span>AXISBANK</span><span style='color:#ef4444;'>-0.80%</span></div>
        """

        fd_rates = [
            {"bank": "SBI", "general": "7.10%", "senior": "7.60%"},
            {"bank": "HDFC Bank", "general": "7.25%", "senior": "7.75%"},
            {"bank": "ICICI Bank", "general": "7.25%", "senior": "7.75%"},
            {"bank": "Axis Bank", "general": "7.20%", "senior": "7.75%"},
            {"bank": "PNB", "general": "7.00%", "senior": "7.50%"}
        ]
        fd_html_block = "".join([
            f"<div style='display:flex; justify-content:space-between; padding: 6px 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:13px;'>"
            f"<span style='color:#cbd5e1; font-weight:600; width: 40%;'>{item['bank']}</span>"
            f"<span style='color:#38bdf8; font-weight:700; width: 30%; text-align:center;'>{item['general']}</span>"
            f"<span style='color:#fbbf24; font-weight:700; width: 30%; text-align:right;'>{item['senior']}</span></div>"
            for item in fd_rates
        ])

        home_html = f"""
        <style>
        @keyframes continuousNeonGlow {{
            0% {{ box-shadow: 0 0 20px rgba(0, 245, 212, 0.35), 0 0 40px rgba(56, 189, 248, 0.2); }}
            50% {{ box-shadow: 0 0 35px rgba(0, 245, 212, 0.7), 0 0 60px rgba(56, 189, 248, 0.45); }}
            100% {{ box-shadow: 0 0 20px rgba(0, 245, 212, 0.35), 0 0 40px rgba(56, 189, 248, 0.2); }}
        }}
        @keyframes microElasticPop {{
            0% {{ transform: translateY(35px) scale(0.96); opacity: 0; }}
            100% {{ transform: translateY(0) scale(1); opacity: 1; }}
        }}
        @keyframes polishedTitleShimmer {{
            0% {{ background-position: 0% 50%; opacity: 0.88; transform: translateY(8px) scale(0.98); }}
            50% {{ background-position: 100% 50%; opacity: 1; transform: translateY(0) scale(1); }}
            100% {{ background-position: 0% 50%; opacity: 0.92; transform: translateY(4px) scale(0.99); }}
        }}
        .home-wrap {{ display: flex; align-items: center; justify-content: center; text-align: center; font-family: Arial, sans-serif; }}
        .home-card {{ width: 92%; background: rgba(3,7,18,0.78); border: 1px solid rgba(0,245,212,0.5); box-shadow: 0 0 30px rgba(0,245,212,0.25); border-radius: 35px; padding: 45px; }}
        .home-logo {{ width: 260px; border-radius: 30px; margin-bottom: 20px; border: 1px solid rgba(0, 245, 212, 0.45); animation: continuousNeonGlow 4s ease-in-out infinite, microElasticPop 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards; }}
        .money-logo {{ font-size: 110px; }}
        .home-title {{ font-size: 60px; font-weight: 900; background: linear-gradient(120deg, #0ea5e9, #f472b6, #c084fc, #38bdf8); background-size: 240% 240%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 18px rgba(255, 255, 255, 0.12), 0 10px 30px rgba(20, 20, 60, 0.25); animation: polishedTitleShimmer 6s ease-in-out infinite, microElasticPop 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.15s backwards; }}
        .home-caption {{ font-size: 22px; color: #dbeafe; line-height: 1.6; margin-top: 18px; animation: microElasticPop 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.3s backwards; }}
        .news-bar {{ margin-top: 35px; background: linear-gradient(90deg, #e9d5ff, #d8b4fe, #c084fc); border-radius: 16px; overflow: hidden; white-space: nowrap; display: flex; align-items: center; box-sizing: border-box; height: 54px; padding: 0 20px; animation: microElasticPop 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.4s backwards; }}
        .news-text {{ display: inline-block; padding-left: 100%; animation: scrollNews 35s linear infinite; font-size: 16px; font-weight: 900; color: #581c87; line-height: 54px; margin: 0; }}
        @keyframes scrollNews {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
        
        /* Layout structures inspired by image_337333.jpg */
        .monitor-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; width: 92%; margin: 30px auto 0 auto; font-family: Arial, sans-serif; animation: microElasticPop 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.5s backwards; }}
        .monitor-card {{ background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(148, 163, 184, 0.35); box-shadow: 0 0 15px rgba(148, 163, 184, 0.15); border-radius: 20px; padding: 20px; text-align: left; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }}
        .monitor-card:hover {{ box-shadow: 0 0 25px rgba(0, 245, 212, 0.3); border-color: rgba(0, 245, 212, 0.5); }}
        .monitor-card-title {{ font-size: 17px; color: #00f5d4; font-weight: 700; margin-bottom: 15px; border-bottom: 1px solid rgba(148, 163, 184, 0.15); padding-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
        .snapshot-metric {{ display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.5); padding: 8px; border-radius: 10px; margin-bottom: 6px; }}
        .snapshot-val {{ font-weight: 700; color: #f8fafc; font-size: 13px; }}
        .snapshot-delta {{ color: #22c55e; font-size: 12px; font-weight: 700; }}
        .snapshot-delta.negative {{ color: #ef4444; }}

        /* How FinCore Works Flowchart Pipeline Styling */
        .flowchart-container {{ width: 92%; margin: 40px auto; font-family: Arial, sans-serif; text-align: center; color: white; }}
        .flowchart-title {{ font-size: 32px; font-weight: 800; margin-bottom: 25px; background: linear-gradient(90deg, #00f5d4, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .flowchart-pipeline {{ display: flex; align-items: center; justify-content: space-around; background: rgba(3, 7, 18, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); padding: 30px; border-radius: 24px; box-shadow: 0 0 20px rgba(56, 189, 248, 0.15); }}
        .flowchart-node {{ width: 260px; background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(0, 245, 212, 0.4); box-shadow: 0 0 15px rgba(0, 245, 212, 0.2); border-radius: 16px; padding: 20px; transition: all 0.3s ease; }}
        .flowchart-node:hover {{ transform: translateY(-5px); box-shadow: 0 0 25px rgba(0, 245, 212, 0.5); border-color: rgba(0, 245, 212, 0.8); }}
        .node-icon {{ font-size: 36px; margin-bottom: 10px; }}
        .node-heading {{ font-size: 18px; color: #00f5d4; font-weight: 700; margin-bottom: 8px; }}
        .node-desc {{ font-size: 13px; color: #cbd5e1; line-height: 1.4; }}
        .flowchart-arrow {{ font-size: 32px; color: #38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.6); animation: pulseArrow 1.5s infinite alternate; }}
        @keyframes pulseArrow {{ 0% {{ opacity: 0.4; transform: scale(0.9); }} 100% {{ opacity: 1; transform: scale(1.1); }} }}
        </style>

        <div class="home-wrap">
            <div class="home-card">
                {logo_html}
                <div class="home-title">Welcome to FinCore</div>
                <div class="home-caption">
                    FinCore is an AI-powered personal finance chatbot that helps users manage salary,
                    expenses, savings, investments, tax planning, loan eligibility, future wealth,
                    and dream goals in one smart dashboard.
                </div>
                <div class="news-bar">
                    <p class="news-text">📈 LIVE MARKET NEWS • {news_text}</p>
                </div>
            </div>
        </div>

        <!-- --- UPGRADED WIDGET CHANNELS FROM IMAGE_337333.JPG --- -->
        <div class="monitor-grid">
            <div class="monitor-card">
                <div class="monitor-card-title">📊 Equities Monitor</div>
                <div style="max-height: 200px; overflow-y: auto; padding-right: 4px;">{stocks_html_block}</div>
            </div>
            <div class="monitor-card">
                <div class="monitor-card-title">⚡ Market Momentum</div>
                <div style="max-height: 200px; overflow-y: auto; padding-right: 4px;">{gainers_losers_html_block}</div>
            </div>
            <div class="monitor-card">
                <div class="monitor-card-title">📈 Trends & Commodities</div>
                <div class="snapshot-metric">
                    <div><span style="color:#cbd5e1; font-weight:600; font-size:11px;">NIFTY 50</span><br><span class="snapshot-val">24,850</span></div>
                    <div class="snapshot-delta">+0.85%</div>
                </div>
                <div class="snapshot-metric">
                    <div><span style="color:#cbd5e1; font-weight:600; font-size:11px;">SENSEX</span><br><span class="snapshot-val">81,350</span></div>
                    <div class="snapshot-delta">+0.72%</div>
                </div>
                <div class="snapshot-metric">
                    <div><span style="color:#cbd5e1; font-weight:600; font-size:11px;">🪙 GOLD RATE (10g)</span><br><span class="snapshot-val">₹72,450</span></div>
                    <div class="snapshot-delta">+0.45%</div>
                </div>
                <div class="snapshot-metric">
                    <div><span style="color:#cbd5e1; font-weight:600; font-size:11px;">💵 USD / INR</span><br><span class="snapshot-val">₹83.42</span></div>
                    <div class="snapshot-delta negative">-0.12%</div>
                </div>
                <div class="snapshot-metric">
                    <div><span style="color:#cbd5e1; font-weight:600; font-size:11px;">🌱 NIFTY MUTUAL FUND INDEX</span><br><span class="snapshot-val">1.12% Growth</span></div>
                    <div class="snapshot-delta">+1.08%</div>
                </div>
            </div>
            <div class="monitor-card">
                <div class="monitor-card-title">🏦 Top Bank FD Rates</div>
                <div style="display:flex; justify-content:space-between; font-size:11px; color:#94a3b8; font-weight:700; margin-bottom:5px; border-bottom:1px solid rgba(148,163,184,0.15); padding-bottom:3px;">
                    <span style="width: 40%;">BANK</span><span style="width: 30%; text-align:center; color:#38bdf8;">NORMAL</span><span style="width: 30%; text-align:right; color:#fbbf24;">SR. CITIZEN</span>
                </div>
                <div style="max-height: 180px; overflow-y: auto;">{fd_html_block}</div>
                <div style="text-align: center; color: #94a3b8; font-size: 10px; margin-top: 10px;">ℹ️ Rates are for >1 year tenure</div>
            </div>
        </div>

        <!-- --- NEW INTERACTIVE PIPELINE FLOWCHART --- -->
        <div class="flowchart-container">
            <div class="flowchart-title">⚡ How FinCore Works</div>
            <div class="flowchart-pipeline">
                <div class="flowchart-node">
                    <div class="node-icon">🔌</div>
                    <div class="node-heading">1. Connect Financial Data</div>
                    <div class="node-desc">Safely initialize income allocations, essential expenditures, tax records, and target custom goals.</div>
                </div>
                <div class="flowchart-arrow">➔</div>
                <div class="flowchart-node">
                    <div class="node-icon">🧠</div>
                    <div class="node-heading">2. AI Analyzes Spending</div>
                    <div class="node-desc">The predictive analytical engine parses structural margins, assessing credit matrices and micro burn limits.</div>
                </div>
                <div class="flowchart-arrow">➔</div>
                <div class="flowchart-node">
                    <div class="node-icon">📊</div>
                    <div class="node-heading">3. Get Personalized Advice</div>
                    <div class="node-desc">Receive dynamic investment architectures, wealth simulation charting models, and automated reporting.</div>
                </div>
            </div>
        </div>
        """
        components.html(home_html, height=880, scrolling=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Enter Dashboard", use_container_width=True, key="enter_dashboard_btn"):
                st.session_state.show_home = False
                st.session_state.step = "GET_NAME"
                st.rerun()
    st.stop()


# ---------- 8. PORTFOLIO SETUP PAGE ----------
if st.session_state.step == "GET_NAME":
    st.markdown(
        """
        <div style="padding: 10px 0px 20px 0px;">
            <h1 style="font-size: 54px !important; font-weight: 900; background: linear-gradient(90deg, #00f5d4, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0px;">
                💰 Fin-Core Personal Assistant
            </h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown("---")

    with st.container(border=True):
        name_input = st.text_input("Please enter your name to initialize your portfolio:", key="portfolio_name_input")
        salary_input = st.number_input("Net Monthly Take-Home Salary (₹):", min_value=0.0, step=5000.0, value=float(st.session_state.salary), key="portfolio_salary_input")
        if st.button("Initialize", key="initialize_btn"):
            if name_input.strip() and salary_input > 0:
                st.session_state.user_name = name_input.strip()
                st.session_state.salary = salary_input
                st.session_state.step = "GET_EXPENSES"
                st.rerun()
            else:
                st.warning("Please enter both name and salary.")


# ---------- 9. EXPENSE INPUT PAGE ----------
submit = False
if st.session_state.step == "GET_EXPENSES":
    st.title("💰 Financial Dashboard")
    with st.form("expense_tuner"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 💰 Income & Indian Tax Deductions")
            sal = st.number_input("Monthly Income (₹)", min_value=0.0, value=float(st.session_state.salary), step=5000.0, key="monthly_income")
            u_80c = st.number_input("Section 80C Deductions (₹/yr)", min_value=0.0, max_value=150000.0, key="deduction_80c")
            u_ppf = st.number_input("Annual PPF Contribution (₹/yr)", min_value=0.0, key="ppf_contribution")
        with col2:
            st.markdown("### 🛡️ Essential Expenses")
            u_rent = st.number_input("Rent / Home Loan EMI (₹)", min_value=0.0, key="rent")
            u_groc = st.number_input("Groceries & Food (₹)", min_value=0.0, key="groceries")
            u_bills = st.number_input("Bills (₹)", min_value=0.0, key="bills")
            u_ins = st.number_input("Insurance & Fixed EMIs (₹)", min_value=0.0, key="insurance")
            u_edu = st.number_input("Education Fees (₹)", min_value=0.0, key="education")
        with col3:
            st.markdown("### 🛡️ Non-essential Expenses")
            u_dining = st.number_input("Dining & Entertainment (₹)", min_value=0.0, key="dining")
            u_shop = st.number_input("Shopping & Apparel (₹)", min_value=0.0, key="shopping")
            u_subs = st.number_input("OTT / Gym (₹)", min_value=0.0, key="subscriptions")
            u_travel = st.number_input("Travel & Hobbies (₹)", min_value=0.0, key="travel")
            u_misc = st.number_input("Miscellaneous (₹)", min_value=0.0, key="miscellaneous")
            st.markdown("---")

        st.markdown("---")
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            st.markdown("### 🏦 Credit Profile")
            u_cibil = st.slider("Current CIBIL Score", 300, 900, 750, key="cibil_score")
            u_emi = st.number_input("Monthly EMI (₹)", min_value=0.0, key="monthly_emi")
        with subcol2:
            st.markdown("### Luxurias Target")
            u_sf_name = st.text_input("Goal Name", value="Luxury Goal", key="goal_name")
            u_sf_target = st.number_input("Target Amount (₹)", min_value=0.0, key="target_amount")
            u_sf_months = st.number_input("Months", min_value=1, value=12, key="goal_months")

        submit = st.form_submit_button("⚡ Sync & Recompute Dashboard")

    if submit:
        st.session_state.step = "DASHBOARD"
        st.session_state.salary = sal
        st.session_state.essential_expenses = (u_rent + u_groc + u_bills + u_ins + u_edu)
        st.session_state.lifestyle_expenses = (u_dining + u_shop + u_subs + u_travel + u_misc)
        st.session_state.existing_emi = u_emi
        st.session_state.sf_name = u_sf_name
        st.session_state.sf_target = u_sf_target
        st.session_state.sf_months = u_sf_months
        st.session_state.ppf_annual = u_ppf
        st.session_state.dashboard_ready = True
        st.rerun()

    if st.button("⬅ Back to Home", key="back_home_btn"):
        st.session_state.show_home = True
        st.session_state.step = "HOME"
        st.session_state.home_tab = "HOME" 
        st.rerun()


# ---------- 10. MAIN DASHBOARD TERMINAL HUB ----------
if st.session_state.step == "DASHBOARD" and st.session_state.dashboard_ready:
    salary = st.session_state.salary
    total_ess = st.session_state.essential_expenses
    total_life = st.session_state.lifestyle_expenses
    total_burn = total_ess + total_life
    surplus = max(0.0, salary - total_burn)

    if total_burn > salary:
        st.error(f"🚨 Outflow Overhead Warning: Expenses (₹{total_burn:,.2f}) exceed incoming capacity (₹{salary:,.2f}). Please re-adjust values.")
    else:
        dash_title_col, pdf_btn_col = st.columns([3, 1])
        with dash_title_col:
            st.markdown(f"### 📊 Live Financial Portfolio — Welcome, **{st.session_state.user_name}**")
        with pdf_btn_col:
            pdf_data = generate_pdf_report()
            st.download_button(
                label="📥 Download PDF Financial Report",
                data=pdf_data,
                file_name=f"FinCore_Report_{st.session_state.user_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dashboard_pdf_generation_btn"
            )

        ess_ratio = total_ess / salary if salary > 0 else 0
        wants_ratio = total_life / salary if salary > 0 else 0
        savings_ratio = surplus / salary if salary > 0 else 0

        def get_arrow_html(ratio, target, positive=True):
            if positive:
                if ratio >= target:
                    return f"<div class='budget-arrow green'>▲ {ratio*100:.1f}%</div>"
                return f"<div class='budget-arrow red'>▼ {ratio*100:.1f}%</div>"
            if ratio <= target:
                return f"<div class='budget-arrow green'>▲ {ratio*100:.1f}%</div>"
            return f"<div class='budget-arrow red'>▼ {ratio*100:.1f}%</div>"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Net Income", f"₹{salary:,.0f}")
        col2.markdown(f"<div style='text-align:center'>\n<h4>🏠 Essential Expenses</h4>\n<div style='font-size:24px; font-weight:800; color:#4ade80;'>₹{total_ess:,.0f}</div>\n{get_arrow_html(ess_ratio, 0.50, positive=False)}\n</div>", unsafe_allow_html=True)
        col3.markdown(f"<div style='text-align:center'>\n<h4>🎯 Lifestyle Expenses</h4>\n<div style='font-size:24px; font-weight:800; color:#4ade80;'>₹{total_life:,.0f}</div>\n{get_arrow_html(wants_ratio, 0.30, positive=False)}\n</div>", unsafe_allow_html=True)
        col4.markdown(f"<div style='text-align:center'>\n<h4>📈 Investable Surplus</h4>\n<div style='font-size:24px; font-weight:800; color:#4ade80;'>₹{surplus:,.0f}</div>\n{get_arrow_html(savings_ratio, 0.20, positive=True)}\n</div>", unsafe_allow_html=True)

    selected_module = st.selectbox(
        "Select Financial Analysis",
        ["Choose a module...", "🏦 CIBIL & Loan", "📊 Investment Strategy", "🎯 Luxurias Target", "📈 PPF Growth", "🎲 20-Year Wealth Simulation"]
    )

    if selected_module == "🏦 CIBIL & Loan":
        st.markdown("## 🏦 CIBIL Matrix & Loan Borrowing Capacity Estimator")
        dti_ratio = (st.session_state.existing_emi / salary * 100 if salary > 0 else 0)
        if st.session_state.cibil_score >= 750:
            cibil_tier, base_roi, max_dti_allowed = "Excellent", 0.085, 50
        elif st.session_state.cibil_score >= 650:
            cibil_tier, base_roi, max_dti_allowed = "Moderate", 0.098, 40
        else:
            cibil_tier, base_roi, max_dti_allowed = "High Risk", 0.12, 25
        available_emi_buffer = max(0, (salary * max_dti_allowed / 100) - st.session_state.existing_emi)
        r_monthly, n_months = base_roi / 12, 240
        theoretical_max_loan = (available_emi_buffer * ((1 - (1 + r_monthly) ** (-n_months)) / r_monthly) if available_emi_buffer > 0 else 0)

        c1, c2, c3 = st.columns(3)
        c1.metric("CIBIL Score", f"{st.session_state.cibil_score}")
        c2.metric("DTI Ratio", f"{dti_ratio:.1f}%")
        c3.metric("Max Loan Power", f"₹{theoretical_max_loan:,.0f}")

    elif selected_module == "📊 Investment Strategy":
        st.markdown("## 📊 Investment Strategy")
        risk_profile = st.select_slider("Select Risk Profile", ["Conservative Balanced", "Moderate Growth", "Aggressive Alpha Expansion"])
        if risk_profile == "Conservative Balanced":
            w_cash, w_fd, w_mf, w_eq, w_gold = 0.30, 0.35, 0.20, 0.05, 0.10
        elif risk_profile == "Moderate Growth":
            w_cash, w_fd, w_mf, w_eq, w_gold = 0.20, 0.20, 0.35, 0.15, 0.10
        else:
            w_cash, w_fd, w_mf, w_eq, w_gold = 0.10, 0.05, 0.40, 0.35, 0.10

        st.markdown("### Suggested Monthly Allocation")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Cash", f"₹{surplus*w_cash:,.0f}")
        c2.metric("FD", f"₹{surplus*w_fd:,.0f}")
        c3.metric("Mutual Funds", f"₹{surplus*w_mf:,.0f}")
        c4.metric("Equity", f"₹{surplus*w_eq:,.0f}")
        c5.metric("Gold", f"₹{surplus*w_gold:,.0f}")

    elif selected_module == "🎯 Luxurias Target":
        st.markdown("## Luxurias Target Planner")
        if st.session_state.sf_target > 0:
            monthly_required = (st.session_state.sf_target / st.session_state.sf_months)
            c1, c2 = st.columns(2)
            c1.metric("Monthly Required", f"₹{monthly_required:,.0f}")
            c2.metric("Available Surplus", f"₹{surplus:,.0f}")
            if surplus >= monthly_required:
                st.success("✅ Goal is achievable.")
            else:
                st.warning("⚠ Increase surplus or extend timeline.")
        else:
            st.info("Enter a Luxurias Target goal in the expense form.")

    elif selected_module == "📈 PPF Growth":
        st.markdown("## 📈 PPF Growth Projection")
        annual_ppf = st.session_state.ppf_annual
        if annual_ppf > 0:
            rate, years, corpus, value = 0.071, np.arange(1, 16), [], 0
            for y in years:
                value = (value + annual_ppf) * (1 + rate)
                corpus.append(value)
            st.line_chart(corpus)
            st.metric("15-Year Corpus", f"₹{corpus[-1]:,.0f}")
        else:
            st.info("No PPF contribution entered.")

    elif selected_module == "🎲 20-Year Wealth Simulation":
        st.markdown("## 🎲 20-Year Wealth Simulation")
        if surplus > 0:
            years, simulations = 20, 100
            sim = np.zeros((years + 1, simulations))
            for i in range(simulations):
                wealth = 0
                for y in range(1, years + 1):
                    wealth = ((wealth + surplus * 12) * (1 + np.random.normal(0.12, 0.15)))
                    sim[y, i] = wealth

            interval_points = [5, 10, 15, 20]
            median_values = [np.median(sim[year]) for year in interval_points]
            profit_changes = [median_values[i] - (median_values[i-1] if i > 0 else 0) for i in range(len(median_values))]
            profit_labels = [f"+₹{profit:,.0f}" for profit in profit_changes]
            norm_profit = np.array(profit_changes) / max(profit_changes) if max(profit_changes) > 0 else np.zeros_like(profit_changes)
            bar_colors = [
                f"rgba({int(239 - 69 * p)}, {int(68 + 187 * p)}, {int(68 + 41 * p)}, 0.9)"
                for p in norm_profit
            ]

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=[f"Year {year}" for year in interval_points],
                        y=median_values,
                        marker_color=bar_colors,
                        text=profit_labels,
                        textposition="outside",
                        textfont=dict(color="#02111b", size=12, family="Arial, sans-serif"),
                        hovertemplate="%{x}<br>Median Wealth: ₹%{y:,.0f}<extra></extra>"
                    )
                ]
            )
            fig.update_layout(
                title="Median Wealth Growth at 5-Year Intervals",
                xaxis_title="Interval",
                yaxis_title="Median Wealth (₹)",
                plot_bgcolor="rgba(236, 239, 241, 0.92)",
                paper_bgcolor="rgba(236, 239, 241, 0.95)",
                font=dict(color="#0f172a", family="Arial, sans-serif"),
                margin=dict(t=60, b=40, l=60, r=40),
                uniformtext_minsize=12,
                uniformtext_mode="show"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.success(f"Projected median wealth after 20 years can exceed ₹{median_values[-1]:,.0f}")
            st.markdown(
                "#### Absolute profit gain per 5-year interval:\n"
                f"- Year 5: {profit_labels[0]}\n"
                f"- Year 10: {profit_labels[1]}\n"
                f"- Year 15: {profit_labels[2]}\n"
                f"- Year 20: {profit_labels[3]}\n",
                unsafe_allow_html=True
            )
        else:
            st.warning("No investable surplus available.")


# ---------- 11. FLOATING CHATBOT ENGINE ----------
if not st.session_state.show_home:
    salary = st.session_state.salary
    total_ess = st.session_state.essential_expenses
    total_life = st.session_state.lifestyle_expenses
    total_burn = total_ess + total_life
    surplus = max(0.0, salary - total_burn)

    if not st.session_state.chat_open:
        st.markdown(
            f"""
            <style>
            @keyframes continuousRotation {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
            button[title="Open Fin-Core Assistant"], button[aria-label="Open Fin-Core Assistant"] {{
                position: fixed !important;
                bottom: 25px !important;
                right: 25px !important;
                z-index: 999999 !important;
                width: 90px !important;
                height: 90px !important;
                min-width: 90px !important;
                border-radius: 50% !important;
                border: 2px solid rgba(255,255,255,0.35) !important;
                box-shadow: 0 16px 32px rgba(124, 58, 237, 0.24), inset 0 1px 0 rgba(255,255,255,0.20) !important;
                animation: continuousRotation 12s linear infinite !important;
                background: radial-gradient(circle at top left, rgba(255,255,255,0.35), transparent 32%), linear-gradient(145deg, #7c3aed 20%, #d946ef 70%, #f43f5e 100%) !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                color: transparent !important;
                font-size: 0px !important;
                padding: 0px !important;
                overflow: hidden !important;
                transform: translateY(0) !important;
            }}
            button[title="Open Fin-Core Assistant"] span, button[aria-label="Open Fin-Core Assistant"] span {{
                font-size: 0 !important;
                color: transparent !important;
                line-height: 0 !important;
            }}
            button[title="Open Fin-Core Assistant"]:hover, button[aria-label="Open Fin-Core Assistant"]:hover {{
                border-color: rgba(255,255,255,0.75) !important;
                box-shadow: 0 20px 40px rgba(124, 58, 237, 0.32), inset 0 2px 0 rgba(255,255,255,0.25) !important;
                transform: translateY(-2px) scale(1.03) !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open Fin-Core Assistant", key="logo_popup_btn", help="Open Fin-Core Assistant"):
            st.session_state.chat_open = True
            st.rerun()

    if st.session_state.chat_open:
        st.markdown("---")
        col_header1, col_header2 = st.columns([5, 1])
        with col_header1:
            st.markdown("### 💬 Fin-Core Conversational Assistant")
        with col_header2:
            if st.button("❌ Close", key="close_chat_window_btn"):
                st.session_state.chat_open = False
                st.rerun()

        st.markdown(
            """
            <style>
            div.element-container:has(button[key="close_chat_window_btn"]) {
                position: fixed !important;
                bottom: 130px !important;
                right: 25px !important;
                z-index: 999998 !important;
                width: 430px !important;
                max-width: calc(100vw - 50px) !important;
                min-height: 520px !important;
                background: rgba(7, 18, 41, 0.96) !important;
                border-radius: 24px !important;
                box-shadow: 0 0 35px rgba(0, 245, 212, 0.22) !important;
                padding: 18px !important;
            }
            div.element-container:has(button[key="close_chat_window_btn"]) button {
                margin: 0 !important;
            }
            div.element-container:has(button[key="close_chat_window_btn"]) .stMarkdown { padding: 0 !important; }
            </style>
            """,
            unsafe_allow_html=True
        )

        chat_container = st.container(height=400, border=True)
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"<div style='display:flex;justify-content:flex-end;margin-bottom:8px'><div style='background:#2563eb;padding:10px 14px;border-radius:18px;max-width:70%;width:fit-content;color:white;box-shadow: 0 0 10px rgba(37,99,235,0.3); border:1px solid rgba(37,99,235,0.4); font-size:18px;'>{message['content']}</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='display:flex;justify-content:flex-start;margin-bottom:8px'><div style='background:#1e293b;padding:10px 14px;border-radius:18px;max-width:70%;width:fit-content;color:white;box-shadow: 0 0 10px rgba(30,41,59,0.4); border:1px solid rgba(148,163,184,0.2); font-size:18px;'>{message['content']}</div></div>", unsafe_allow_html=True)

        if prompt := st.chat_input("Ask anything...", key="fincore_chat_input_field"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            clean_prompt = prompt.strip().lower()
            calculator_reply = ""
            math_context = ""

            dti_ratio = (st.session_state.existing_emi / salary) * 100 if salary > 0 else 0
            if st.session_state.cibil_score >= 750:
                cibil_tier, base_roi, max_dti_allowed = "Excellent", 0.085, 50.0
            elif st.session_state.cibil_score >= 650:
                cibil_tier, base_roi, max_dti_allowed = "Moderate", 0.098, 40.0
            else:
                cibil_tier, base_roi, max_dti_allowed = "High Risk", 0.120, 25.0
                
            available_emi_buffer = max(0.0, (salary * (max_dti_allowed / 100)) - st.session_state.existing_emi)
            r_monthly = base_roi / 12
            theoretical_max_loan = available_emi_buffer * ((1 - (1 + r_monthly)**-240) / r_monthly) if available_emi_buffer > 0 else 0.0

            numbers = re.findall(r'\d+\.?\d*', clean_prompt)
            if "sip" in clean_prompt and len(numbers) >= 3:
                try:
                    monthly_investment = float(numbers[0])
                    annual_rate = float(numbers[1])
                    years = int(float(numbers[2]))
                    monthly_rate = (annual_rate / 100) / 12
                    months = years * 12
                    total_invested = monthly_investment * months
                    future_value = monthly_investment * (((1 + monthly_rate)**months - 1) / monthly_rate) * (1 + monthly_rate)
                    wealth_gained = future_value - total_invested
                    calculator_reply = (
                        f"📊 **NATIVE SIP CALCULATOR BREAKDOWN**\n"
                        f"- 🔹 **Monthly SIP Contribution:** ₹{monthly_investment:,.2f}\n"
                        f"- 🔹 **Expected Return Rate:** {annual_rate}%\n"
                        f"- 🔹 **Time Horizon:** {years} Years ({months} months)\n"
                        f"--- \n"
                        f"💰 **Total Amount Invested:** ₹{total_invested:,.2f}\n"
                        f"📈 **Estimated Wealth Gained:** ₹{wealth_gained:,.2f}\n"
                        f"🌟 **Total Projected Portfolio Value:** ₹{future_value:,.2f}\n\n"
                    )
                    math_context = f"The user calculated an SIP. Investment: ₹{monthly_investment}, Rate: {annual_rate}%, Years: {years}. Total Value: ₹{future_value:.2f}."
                except Exception:
                    pass

            elif "loan" in clean_prompt or "borrow" in clean_prompt or "cibil" in clean_prompt:
                calculator_reply = (
                    f"🏦 **CREDIT ACCELERATION REPORT**\n"
                    f"- CIBIL Score Model: {st.session_state.cibil_score} ({cibil_tier})\n"
                    f"- Active DTI Burden: {dti_ratio:.1f}%\n"
                    f"- Theoretical Max 20-Year Home Loan: ₹{theoretical_max_loan:,.2f}\n"
                    f"- System Pricing Tier (ROI): {base_roi*100:.2f}%\n\n"
                )
                math_context = f"The user is evaluating loan eligibility. CIBIL score: {st.session_state.cibil_score}, Tier: {cibil_tier}, Active DTI: {dti_ratio:.1f}%, Max calculated borrowing cap: ₹{theoretical_max_loan:.2f}."

            matched_definition = None
            clean_glossary_prompt = prompt.strip().upper()
            for key, def_text in FINANCIAL_GLOSSARY.items():
                if key in clean_glossary_prompt or clean_glossary_prompt in key:
                    matched_definition = def_text
                    break
            
            if matched_definition:
                reply = f"✨ **{prompt} Found in Dictionary:** {matched_definition}"
                if calculator_reply:
                    reply = calculator_reply + reply
            else:
                if client is not None and len(api_key_to_use) > 10:
                    try:
                        system_instruction = (
                            "You are 'Fin-Core AI', an expert personal finance companion specialized in the Indian market.\n"
                            f"Current User Profile: {st.session_state.user_name}\n"
                            f"=== INCOME & CAPACITY ===\n"
                            f"- Net Take-Home Salary: ₹{salary:,.2f}/month | Surplus Pool: ₹{surplus:,.2f}/month\n"
                            f"=== AUTOMATED CALCULATOR STATUS CONTEXT ===\n"
                            f"{math_context}\n"
                            "Explain frameworks clearly using real metrics provided."
                        )
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt,
                            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.3)
                        )
                        reply = calculator_reply + response.text
                    except Exception as e:
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            reply = calculator_reply + "⚠️ **Fin-Core AI Free Tier Quota Limit Reached.**"
                        else:
                            reply = calculator_reply + f"⚠️ Assistant temporarily unavailable: `{str(e)}`"
                else:
                    reply = calculator_reply + "🚨 **API Configuration Blocked: Invalid Key.**"

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

# --- FOOTER DISCLAIMER ---
st.markdown("<br>" * 3, unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);">
        <p style="font-size: 12px; color: #ffffff; font-style: italic; line-height: 1.6; opacity: 0.8; margin: 0;">
            This app and chatbot, created by Nandita Das, Priyanka Kumari Sharma, and Himali Parveen, are provided for informational purposes only and do not constitute financial advice. Users should consult qualified professionals before making financial decisions.
        </p>
    </div>
""", unsafe_allow_html=True)
