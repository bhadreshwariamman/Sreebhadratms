# app.py - Complete Temple Management System (Fully working PDF & WhatsApp)
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import base64
import time
import hashlib
import io
import urllib.parse
import tempfile
import os
from supabase import create_client, Client

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🛕 Arulmigu Bhadreshwari Amman Temple",
    page_icon="🛕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SUPABASE INITIALIZATION
# ============================================================
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {str(e)}")
        return None

supabase = init_supabase()

# ============================================================
# TEMPLE CONSTANTS
# ============================================================
TEMPLE_NAME = "Arulmigu Bhadreshwari Amman Temple"
TEMPLE_TRUST = "Samrakshana Seva Trust 179/2004"
TEMPLE_ADDRESS = "Kanjampuram, Kanniyakumari Dist. - 629154"
TEMPLE_EMAIL = "bhadreshwariamman@gmail.com"
TEMPLE_PHONE = "+91 9876543210"
TEMPLE_TAMIL = "அம்மே நாராயணா ..தேவி நாராயணா"

TEMPLE_CONFIG = {
    "name": TEMPLE_NAME,
    "trust": TEMPLE_TRUST,
    "address": TEMPLE_ADDRESS,
    "phone": TEMPLE_PHONE,
    "email": TEMPLE_EMAIL,
    "tagline": TEMPLE_TAMIL,
    "currency": "₹"
}

# ============================================================
# NATCHATHIRAM LIST
# ============================================================
NATCHATHIRAM_LIST = [
    "Aswini", "Bharani", "Krithikai", "Rohini", "Mrigaseersham",
    "Thiruvathirai", "Punarpoosam", "Poosam", "Ayilyam", "Magam",
    "Pooram", "Uthiram", "Hastham", "Chithirai", "Swathi",
    "Visakham", "Anusham", "Kettai", "Moolam", "Pooradam",
    "Uthiradam", "Thiruvonam", "Avittam", "Sathayam",
    "Poorattathi", "Uthirattathi", "Revathi"
]

RELATION_TYPES = [
    "Self", "Spouse", "Son", "Daughter", "Father", "Mother",
    "Brother", "Sister", "Grandfather", "Grandmother",
    "Father-in-law", "Mother-in-law", "Son-in-law",
    "Daughter-in-law", "Uncle", "Aunt", "Nephew", "Niece", "Other"
]

MIN_DATE = date(1950, 1, 1)
MAX_DATE = date(2050, 12, 31)

# ============================================================
# DATE HANDLING (DD/MM/YYYY)
# ============================================================
def format_date_ddmmyyyy(date_obj):
    if date_obj:
        return date_obj.strftime('%d/%m/%Y')
    return ""

def parse_date_ddmmyyyy(date_str):
    if not date_str or date_str.strip() == "":
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
    except:
        return None

def date_to_db(date_obj):
    return date_obj.isoformat() if date_obj else None

# ============================================================
# BARCODE GENERATION
# ============================================================
BARCODE_AVAILABLE = False
try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except:
    pass

QRCODE_AVAILABLE = False
try:
    import qrcode
    QRCODE_AVAILABLE = True
except:
    pass

def generate_barcode_image(data_str):
    if BARCODE_AVAILABLE:
        try:
            barcode_class = barcode.get_barcode_class('code128')
            buffer = io.BytesIO()
            b = barcode_class(str(data_str), writer=ImageWriter())
            b.write(buffer, options={'module_width':0.4,'module_height':15,'font_size':10})
            buffer.seek(0)
            img_base64 = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            img_bytes = buffer.getvalue()
            return img_base64, img_bytes
        except:
            pass
    if QRCODE_AVAILABLE:
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(str(data_str))
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            img_bytes = buffer.getvalue()
            return img_base64, img_bytes
        except:
            pass
    fallback_svg = f'<svg width="200" height="60"><rect width="200" height="60" fill="white"/><text x="100" y="35" text-anchor="middle" font-family="monospace">{data_str}</text></svg>'
    img_base64 = "data:image/svg+xml;base64," + base64.b64encode(fallback_svg.encode()).decode()
    return img_base64, None

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hash_value: str) -> bool:
    return hash_password(password) == hash_value

def generate_unique_id(prefix: str = 'DEV') -> str:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_part = str(uuid.uuid4())[:8].upper()
    return f"{prefix}{timestamp}{unique_part}"

def create_default_admin():
    if not supabase: return
    try:
        existing = supabase.table('users').select('id').eq('username','admin').execute()
        if not existing.data:
            supabase.table('users').insert({
                'username':'admin',
                'password_hash':hash_password('admin123'),
                'role':'admin',
                'full_name':'Administrator',
                'email':'admin@temple.com'
            }).execute()
    except:
        pass

def get_temple_setting(key: str) -> str:
    if not supabase: return ''
    try:
        res = supabase.table('temple_settings').select('value').eq('key',key).execute()
        return res.data[0]['value'] if res.data else ''
    except:
        return ''

def set_temple_setting(key: str, value: str):
    if not supabase: return
    try:
        existing = supabase.table('temple_settings').select('id').eq('key',key).execute()
        if existing.data:
            supabase.table('temple_settings').update({'value':value}).eq('key',key).execute()
        else:
            supabase.table('temple_settings').insert({'key':key,'value':value}).execute()
    except:
        pass

def get_amman_image():
    img = get_temple_setting('amman_image')
    if img and img.startswith('data:image'):
        return img
    # Default PNG image as base64 (simple OM symbol – will work with FPDF)
    # You can replace this with your own default PNG base64 if needed.
    # For now, we'll use a small PNG of a lotus (data:image/png;base64,...)
    # But to keep it simple, we'll return None and let the PDF skip the image.
    # To make the PDF work without external image, we'll embed a simple text OM.
    # Actually, better: we'll use a local file if exists, else skip.
    # But since we can't guarantee cairosvg, we'll create a default PNG placeholder.
    default_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAABISURBVEhL7ZXRCcAgDEPV6gjdQBEcQdFhHMRBHMzEfFIotVYtCn2/B5eUkJY0P7Lcbtkz9owsM7LMVpaZZWaZWWaWWVWWmdUys8wsM8vM+gA1tLpXwVcR2AAAAABJRU5ErkJggg=="
    return "data:image/png;base64," + default_png_base64

def set_amman_image(base64_img):
    set_temple_setting('amman_image', base64_img)

def save_base64_image_to_temp(base64_str):
    if not base64_str: return None
    try:
        if ',' in base64_str:
            header, data = base64_str.split(',',1)
            if 'png' in header: ext='.png'
            elif 'jpeg' in header or 'jpg' in header: ext='.jpg'
            elif 'svg' in header: ext='.svg'
            else: ext='.png'
        else:
            data = base64_str
            ext='.png'
        img_data = base64.b64decode(data)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(img_data)
        tmp.close()
        return tmp.name
    except:
        return None

def convert_svg_to_png(svg_path):
    try:
        import cairosvg
        png_path = svg_path.replace('.svg','.png')
        cairosvg.svg2png(url=svg_path, write_to=png_path)
        return png_path
    except:
        return None

def get_todays_birthdays():
    if not supabase: return []
    today = date.today()
    birthdays = []
    try:
        res = supabase.table('devotees').select('name,dob').execute()
        for d in res.data:
            if d.get('dob'):
                try:
                    dob = datetime.strptime(d['dob'],'%Y-%m-%d').date()
                    if dob.month == today.month and dob.day == today.day:
                        birthdays.append(f"🎂 {d['name']} (Devotee)")
                except: pass
    except: pass
    return birthdays

def get_todays_anniversaries():
    if not supabase: return []
    today = date.today()
    anniversaries = []
    try:
        res = supabase.table('devotees').select('name,wedding_day').execute()
        for d in res.data:
            if d.get('wedding_day'):
                try:
                    wedding = datetime.strptime(d['wedding_day'],'%Y-%m-%d').date()
                    if wedding.month == today.month and wedding.day == today.day:
                        anniversaries.append(f"💒 {d['name']} (Wedding)")
                except: pass
    except: pass
    return anniversaries

def get_financial_summary(start_date, end_date):
    if not supabase: return {'income':0,'expenses':0,'donations':0,'balance':0}
    try:
        inc = supabase.table('bills').select('amount').gte('bill_date',start_date.isoformat()).lte('bill_date',end_date.isoformat()).execute()
        total_inc = sum(i['amount'] for i in inc.data) if inc.data else 0
        exp = supabase.table('expenses').select('amount').gte('expense_date',start_date.isoformat()).lte('expense_date',end_date.isoformat()).execute()
        total_exp = sum(e['amount'] for e in exp.data) if exp.data else 0
        don = supabase.table('donations').select('amount').gte('donation_date',start_date.isoformat()).lte('donation_date',end_date.isoformat()).execute()
        total_don = sum(d['amount'] for d in don.data) if don.data else 0
        return {'income':total_inc,'expenses':total_exp,'donations':total_don,'balance':total_inc+total_don-total_exp}
    except:
        return {'income':0,'expenses':0,'donations':0,'balance':0}

def make_whatsapp_link(phone, message):
    phone_clean = ''.join(filter(str.isdigit, str(phone)))
    if len(phone_clean) == 10:
        phone_clean = "91" + phone_clean
    return f"https://wa.me/{phone_clean}?text={urllib.parse.quote(message)}"

def build_bill_whatsapp_message(bill_no, bill_date, name, pooja, amount, manual_bill="", book_no=""):
    return (
        f"🛕 *{TEMPLE_NAME}*\n*{TEMPLE_TRUST}*\n📍 {TEMPLE_ADDRESS}\n🙏 {TEMPLE_TAMIL}\n\n"
        f"📋 *BILL / RECEIPT*\n━━━━━━━━━━━━━━━━━\n📄 Bill No: {bill_no}\n"
        f"{'📝 Manual: '+str(manual_bill)+'\n' if manual_bill else ''}"
        f"{'📖 Book: '+str(book_no)+'\n' if book_no else ''}"
        f"📅 Date: {bill_date}\n━━━━━━━━━━━━━━━━━\n👤 Name: {name}\n🙏 Pooja: {pooja}\n"
        f"💰 *Amount: Rs. {float(amount):,.2f}*\n━━━━━━━━━━━━━━━━━\n\n"
        f"🙏 Thank you! May Goddess Bhadreshwari bless you!\n✉ {TEMPLE_EMAIL}\n🪔 {TEMPLE_TAMIL} 🪔"
    )

# ============================================================
# PDF LIBRARY AND HELPER FUNCTIONS
# ============================================================
PDF_AVAILABLE = False
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    pass

def sanitize_text(text):
    """Convert text to ASCII, replacing non-ASCII chars and ₹ with Rs."""
    if not text:
        return ""
    text = str(text).replace("₹", "Rs.")
    text = text.replace("–", "-").replace("—", "-").replace("‘", "'").replace("’", "'")
    return ''.join(c if ord(c) < 128 else ' ' for c in text)

def save_base64_image_to_temp(base64_str):
    """Save base64 image to temporary file and return path."""
    if not base64_str:
        return None
    try:
        if ',' in base64_str:
            header, data = base64_str.split(',', 1)
            if 'png' in header:
                ext = '.png'
            elif 'jpeg' in header or 'jpg' in header:
                ext = '.jpg'
            elif 'svg' in header:
                ext = '.svg'
            else:
                ext = '.png'
        else:
            data = base64_str
            ext = '.png'
        img_data = base64.b64decode(data)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(img_data)
        tmp.close()
        return tmp.name
    except:
        return None

def convert_svg_to_png(svg_path):
    """Convert SVG to PNG using cairosvg if available."""
    try:
        import cairosvg
        png_path = svg_path.replace('.svg', '.png')
        cairosvg.svg2png(url=svg_path, write_to=png_path)
        return png_path
    except:
        return None

def generate_bill_pdf(bill_no, manual_bill, bill_book, bill_date, name, address, mobile, pooja_type, amount, amman_base64=None):
    if not PDF_AVAILABLE:
        return None
    
    # Sanitize all text inputs
    bill_no = sanitize_text(bill_no)
    manual_bill = sanitize_text(manual_bill)
    bill_book = sanitize_text(bill_book)
    bill_date = sanitize_text(bill_date)
    name = sanitize_text(name)
    address = sanitize_text(address)
    mobile = sanitize_text(mobile)
    pooja_type = sanitize_text(pooja_type)
    amount_str = sanitize_text(f"{amount:,.2f}")
    temple_name_safe = sanitize_text(TEMPLE_NAME)
    temple_trust_safe = sanitize_text(TEMPLE_TRUST)
    temple_address_safe = sanitize_text(TEMPLE_ADDRESS)
    temple_email_safe = sanitize_text(TEMPLE_EMAIL)
    temple_tamil_safe = sanitize_text(TEMPLE_TAMIL)
    
    amman_img_path = None
    if amman_base64:
        amman_img_path = save_base64_image_to_temp(amman_base64)
        if amman_img_path and amman_img_path.endswith('.svg'):
            png_path = convert_svg_to_png(amman_img_path)
            if png_path:
                amman_img_path = png_path
    
    pdf = FPDF()
    pdf.add_page()
    
    # Add Amman image centered
    if amman_img_path and os.path.exists(amman_img_path) and amman_img_path.lower().endswith(('.png','.jpg','.jpeg')):
        try:
            pdf.image(amman_img_path, x=90, y=10, w=30)
            pdf.ln(35)
        except:
            pdf.ln(10)
    else:
        pdf.ln(10)
    
    # Temple header
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, temple_name_safe, 0, 1, 'C')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, temple_trust_safe, 0, 1, 'C')
    pdf.cell(0, 6, temple_address_safe, 0, 1, 'C')
    pdf.cell(0, 6, f"Email: {temple_email_safe}", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "BILL / RECEIPT", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(50, 8, f"Bill No: {bill_no}", 0, 0)
    pdf.cell(0, 8, f"Date: {bill_date}", 0, 1)
    if manual_bill:
        pdf.cell(50, 8, f"Manual Bill: {manual_bill}", 0, 0)
    if bill_book:
        pdf.cell(0, 8, f"Book No: {bill_book}", 0, 1)
    pdf.ln(5)
    pdf.cell(50, 8, f"Name: {name}", 0, 1)
    if address:
        pdf.cell(50, 8, f"Address: {address}", 0, 1)
    if mobile:
        pdf.cell(50, 8, f"Mobile: {mobile}", 0, 1)
    pdf.ln(5)
    pdf.cell(50, 8, f"Pooja Type: {pooja_type}", 0, 1)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(50, 10, f"Amount: Rs. {amount_str}", 0, 1)
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.cell(0, 6, "Thank you for your contribution! May Goddess Bhadreshwari bless you!", 0, 1, 'C')
    pdf.cell(0, 6, temple_tamil_safe, 0, 1, 'C')
    
    # Clean up temp file
    if amman_img_path and os.path.exists(amman_img_path):
        try:
            os.unlink(amman_img_path)
        except:
            pass
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin1')
# ============================================================
# LOGIN PAGE
# ============================================================
def login_page():
    if not supabase:
        st.error("⚠️ Database connection failed. Check Supabase secrets.")
        return
    create_default_admin()
    amman_img = get_amman_image()
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #1a1a3e, #302b63, #4a1942); }
    .login-container {
        max-width: 480px;
        margin: 60px auto;
        padding: 40px;
        background: rgba(255,255,255,0.12);
        backdrop-filter: blur(15px);
        border-radius: 30px;
        text-align: center;
        animation: float 6s ease-in-out infinite;
    }
    @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
    .amman-img {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        border: 4px solid #ffd700;
        display: block;
        margin: 0 auto 20px auto;
        animation: glow 3s ease-in-out infinite;
    }
    @keyframes glow { 0%,100% { box-shadow: 0 0 20px rgba(255,215,0,0.4); } 50% { box-shadow: 0 0 50px rgba(255,215,0,0.8); } }
    .temple-name { color: #ffd700; font-size: 1.5em; font-weight: 700; margin: 10px 0 5px; text-shadow: 0 2px 10px rgba(0,0,0,0.3); text-align: center; }
    .temple-trust { color: #ffaa66; font-size: 0.9em; margin: 5px 0; text-align: center; }
    .temple-address { color: #ddd; font-size: 0.8em; margin: 5px 0; text-align: center; }
    .temple-email { color: #90caf9; font-size: 0.75em; margin: 5px 0; text-align: center; }
    .tamil-text { color: #ffd966; font-size: 1em; font-weight: 600; margin: 15px 0 10px; animation: pulse 2s infinite; text-align: center; }
    @keyframes pulse { 0%,100% { opacity: 0.7; } 50% { opacity: 1; } }
    .login-divider { height: 2px; background: linear-gradient(90deg, transparent, #ffd700, #ff6b35, #ffd700, transparent); margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        # Centered Amman image
        st.markdown(f'<img src="{amman_img}" class="amman-img">', unsafe_allow_html=True)
        # Centered text content
        st.markdown(f'<div class="temple-name">🛕 {TEMPLE_NAME}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="temple-trust">{TEMPLE_TRUST}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="temple-address">📍 {TEMPLE_ADDRESS}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="temple-email">✉ {TEMPLE_EMAIL} | 📞 {TEMPLE_PHONE}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tamil-text">🙏 {TEMPLE_TAMIL} 🙏</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-divider"></div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("🚀 Enter Temple Portal", use_container_width=True):
                if username and password:
                    try:
                        res = supabase.table('users').select('*').eq('username',username).execute()
                        if res.data and verify_password(password, res.data[0]['password_hash']):
                            st.session_state.logged_in = True
                            st.session_state.username = res.data[0]['username']
                            st.session_state.role = res.data[0]['role']
                            st.session_state.user_id = res.data[0]['id']
                            st.session_state.current_page = "Dashboard"
                            st.success("Login successful!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials")
                    except Exception as e:
                        st.error(f"Error: {e}")
        st.markdown('<div class="login-divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center; color:#aaa;">🔑 Default: admin / admin123<br>🪔 {TEMPLE_TAMIL} 🪔</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
# ============================================================
# HEADER & SIDEBAR
# ============================================================
def render_header():
    amman_img = get_amman_image()
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea, #764ba2, #f093fb, #f5576c); padding: 20px; border-radius: 15px; margin-bottom: 20px; position: relative;'>
        <div style='position: absolute; left: 20px; top: 50%; transform: translateY(-50%);'>
            <img src="{amman_img}" style='width: 60px; height: 60px; border-radius: 50%; border: 3px solid #ffd700;'>
        </div>
        <div style='text-align: center;'>
            <h1 style='color: white;'>🛕 {TEMPLE_NAME}</h1>
            <p style='color: #fff8e7;'>{TEMPLE_TRUST}</p>
            <p style='color: #fff0d0;'>📍 {TEMPLE_ADDRESS} | 📞 {TEMPLE_PHONE} | ✉ {TEMPLE_EMAIL}</p>
            <p style='color: #ffd700; font-style: italic;'>{TEMPLE_TAMIL}</p>
        </div>
        <div style='position: absolute; right: 20px; top: 50%; transform: translateY(-50%);'>
            <img src="{amman_img}" style='width: 60px; height: 60px; border-radius: 50%; border: 3px solid #ffd700;'>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("<div style='text-align:center; background: linear-gradient(135deg, #667eea, #764ba2); padding: 15px; border-radius: 15px;'><h2 style='color: white;'>🛕 Temple MS</h2></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #43e97b, #38f9d7); padding: 12px; border-radius: 10px; text-align: center; margin: 10px 0;'>
            <p style='color: #1a1a2e; font-weight: bold;'>👤 {st.session_state.get('username','Guest')}</p>
            <p style='color: #1a1a2e; font-size: 12px;'>{st.session_state.get('role','user')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        pages = {
            "Dashboard":"🏠","Devotee Management":"👥","Billing System":"🧾",
            "Pooja Management":"🙏","Expense Tracking":"💰","Donations":"🎁",
            "Samaya Vakuppu":"📚","Thirumana Mandapam":"💒",
            "Asset Management":"🏷️","Reports":"📊","Settings":"⚙️","User Management":"👥"
        }
        for page, icon in pages.items():
            if page=="User Management" and st.session_state.get('role')!='admin':
                continue
            if st.button(f"{icon} {page}", key=page, use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for k in ['logged_in','username','role','user_id','current_page']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

# ============================================================
# DASHBOARD
# ============================================================
def dashboard_page():
    render_header()
    col1, col2 = st.columns([1,2])
    with col1:
        period = st.selectbox("Period", ["Today","This Week","This Month","This Year"])
    today = date.today()
    if period=="Today": s=e=today
    elif period=="This Week": s=today-timedelta(days=today.weekday()); e=today
    elif period=="This Month": s=today.replace(day=1); e=today
    else: s=today.replace(month=1,day=1); e=today
    summary = get_financial_summary(s,e)
    st.markdown("""
    <style>.metric-card{ background: linear-gradient(135deg,#667eea,#764ba2); padding:15px; border-radius:15px; text-align:center; color:white; }</style>
    """, unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><h3>💰 Income</h3><h2>{TEMPLE_CONFIG["currency"]}{summary["income"]:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><h3>💸 Expenses</h3><h2>{TEMPLE_CONFIG["currency"]}{summary["expenses"]:,.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><h3>🎁 Donations</h3><h2>{TEMPLE_CONFIG["currency"]}{summary["donations"]:,.2f}</h2></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><h3>💎 Balance</h3><h2>{TEMPLE_CONFIG["currency"]}{summary["balance"]:,.2f}</h2></div>', unsafe_allow_html=True)
    st.markdown("---")
    try:
        news = supabase.table('news_ticker').select('message').eq('is_active',True).order('priority', desc=True).execute()
        if news.data:
            st.markdown(f"<div style='background: linear-gradient(90deg,#ffecd2,#fcb69f); padding:12px; border-radius:10px;'><marquee>{' | '.join([n['message'] for n in news.data])}</marquee></div>", unsafe_allow_html=True)
    except: pass
    colA, colB = st.columns(2)
    with colA:
        st.subheader("🎂 Today's Birthdays")
        for b in get_todays_birthdays(): st.info(b)
        st.subheader("💒 Anniversaries")
        for a in get_todays_anniversaries(): st.success(a)
    with colB:
        st.subheader("🙏 Today's Pooja")
        try:
            pooja_today = supabase.table('daily_pooja').select('*').eq('pooja_date', today.isoformat()).execute()
            if pooja_today.data:
                for p in pooja_today.data:
                    st.write(f"{'✅' if p['status']=='completed' else '⏳'} **{p['pooja_name']}** at {p.get('pooja_time','')}")
            else:
                st.info("No poojas scheduled")
        except: pass

# ============================================================
# DEVOTEE MANAGEMENT (Full)
# ============================================================
def devotee_management_page():
    render_header()
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Register","👨‍👩‍👧 Family Members","📋 View All","📤 Bulk Import"])
    with tab1:
        with st.form("reg_devotee"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *")
                dob_str = st.text_input("DOB (DD/MM/YYYY)", value=format_date_ddmmyyyy(date(1980,1,1)))
                gender = st.selectbox("Gender", ["Male","Female","Other"])
                mobile = st.text_input("Mobile")
                whatsapp = st.text_input("WhatsApp")
                email = st.text_input("Email")
            with col2:
                address = st.text_area("Address")
                natchathiram = st.selectbox("Natchathiram", ["--"]+NATCHATHIRAM_LIST)
                wedding_str = st.text_input("Wedding Day (DD/MM/YYYY)")
                occupation = st.text_input("Occupation")
                gothram = st.text_input("Gothram")
            photo = st.file_uploader("Photo", type=['jpg','png','jpeg'])
            if st.form_submit_button("Register"):
                if name:
                    dob = parse_date_ddmmyyyy(dob_str) if dob_str else None
                    wedding = parse_date_ddmmyyyy(wedding_str) if wedding_str else None
                    if dob_str and not dob:
                        st.error("Invalid DOB")
                    elif wedding_str and not wedding:
                        st.error("Invalid Wedding date")
                    else:
                        dev_id = generate_unique_id('DEV')
                        photo_b64 = base64.b64encode(photo.getvalue()).decode() if photo else None
                        data = {
                            'devotee_id':dev_id,'name':name,'dob':date_to_db(dob),'gender':gender,
                            'mobile_no':mobile,'whatsapp_no':whatsapp,'email':email,'address':address,
                            'natchathiram':natchathiram if natchathiram!="--" else None,
                            'wedding_day':date_to_db(wedding),'occupation':occupation,'gothram':gothram,
                            'photo_url':photo_b64
                        }
                        supabase.table('devotees').insert(data).execute()
                        st.success(f"✅ {name} registered! ID: {dev_id}")
                        st.balloons()
    with tab2:
        devotees = supabase.table('devotees').select('id,name,mobile_no').execute()
        if devotees.data:
            dev_opt = {f"{d['name']} - {d.get('mobile_no','')}": d['id'] for d in devotees.data}
            selected = st.selectbox("Select Devotee (Head)", list(dev_opt.keys()))
            dev_id = dev_opt[selected]
            family = supabase.table('family_members').select('*').eq('devotee_id',dev_id).execute()
            if family.data:
                st.write("**Existing Family Members:**")
                for fm in family.data:
                    col1, col2 = st.columns([3,1])
                    dob_str = format_date_ddmmyyyy(datetime.strptime(fm['dob'],'%Y-%m-%d').date()) if fm.get('dob') else ''
                    col1.write(f"👤 {fm['name']} ({fm['relation_type']}) - DOB: {dob_str}")
                    if col2.button("🗑️", key=f"del_fm_{fm['id']}"):
                        supabase.table('family_members').delete().eq('id',fm['id']).execute()
                        st.rerun()
            with st.form("add_family"):
                st.subheader("Add Family Member")
                col1, col2 = st.columns(2)
                with col1:
                    fm_name = st.text_input("Name")
                    fm_dob_str = st.text_input("DOB (DD/MM/YYYY)", value=format_date_ddmmyyyy(date(2000,1,1)))
                    fm_relation = st.selectbox("Relation", RELATION_TYPES)
                with col2:
                    fm_wedding_str = st.text_input("Wedding Day (DD/MM/YYYY)")
                    fm_natchathiram = st.selectbox("Natchathiram", ["--"]+NATCHATHIRAM_LIST)
                if st.form_submit_button("Add Member"):
                    fm_dob = parse_date_ddmmyyyy(fm_dob_str) if fm_dob_str else None
                    fm_wedding = parse_date_ddmmyyyy(fm_wedding_str) if fm_wedding_str else None
                    if fm_name and fm_dob:
                        supabase.table('family_members').insert({
                            'devotee_id':dev_id,'name':fm_name,'dob':date_to_db(fm_dob),
                            'relation_type':fm_relation,'wedding_day':date_to_db(fm_wedding),
                            'natchathiram':fm_natchathiram if fm_natchathiram!="--" else None
                        }).execute()
                        st.success("Family member added")
                        st.rerun()
                    else:
                        st.error("Name and valid DOB required")
        else:
            st.warning("No devotees found")
    with tab3:
        search = st.text_input("🔍 Search by name/mobile/address")
        query = supabase.table('devotees').select('*').order('created_at', desc=True)
        if search:
            query = query.or_(f"name.ilike.%{search}%,mobile_no.ilike.%{search}%,address.ilike.%{search}%")
        res = query.execute()
        devotees = res.data if res.data else []
        st.write(f"**Total: {len(devotees)}**")
        for d in devotees:
            with st.expander(f"👤 {d['name']} - {d['devotee_id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📱 Mobile: {d.get('mobile_no','N/A')}")
                    st.write(f"📲 WhatsApp: {d.get('whatsapp_no','N/A')}")
                    st.write(f"📧 Email: {d.get('email','N/A')}")
                    dob_obj = datetime.strptime(d['dob'],'%Y-%m-%d').date() if d.get('dob') else None
                    st.write(f"🎂 DOB: {format_date_ddmmyyyy(dob_obj) if dob_obj else 'N/A'}")
                with col2:
                    st.write(f"⭐ Star: {d.get('natchathiram','N/A')}")
                    wedding_obj = datetime.strptime(d['wedding_day'],'%Y-%m-%d').date() if d.get('wedding_day') else None
                    st.write(f"💒 Wedding: {format_date_ddmmyyyy(wedding_obj) if wedding_obj else 'N/A'}")
                    st.write(f"🏠 Address: {d.get('address','N/A')}")
                if d.get('photo_url'):
                    st.image(base64.b64decode(d['photo_url']), width=100)
                if st.button("🗑️ Delete", key=f"del_dev_{d['id']}"):
                    supabase.table('family_members').delete().eq('devotee_id',d['id']).execute()
                    supabase.table('devotee_yearly_pooja').delete().eq('devotee_id',d['id']).execute()
                    supabase.table('devotees').delete().eq('id',d['id']).execute()
                    st.rerun()
    with tab4:
        st.markdown("Download template, fill, and upload.")
        template = pd.DataFrame([["Sample","01/01/1980","Male","9876543210","email@ex.com","Address","Aswini","10/05/2005","Business","Vishwamitra"]],
                                columns=["Name","DOB","Gender","Mobile","Email","Address","Natchathiram","WeddingDay","Occupation","Gothram"])
        csv = template.to_csv(index=False).encode()
        st.download_button("📥 Template", csv, "devotee_template.csv")
        uploaded = st.file_uploader("Upload CSV/Excel", type=['csv','xlsx'])
        if uploaded:
            df = pd.read_csv(uploaded) if uploaded.name.endswith('.csv') else pd.read_excel(uploaded)
            if st.button("Import"):
                success=0
                for _, row in df.iterrows():
                    try:
                        dev_id = generate_unique_id('DEV')
                        dob = parse_date_ddmmyyyy(str(row['DOB'])) if pd.notna(row['DOB']) else None
                        wedding = parse_date_ddmmyyyy(str(row['WeddingDay'])) if pd.notna(row['WeddingDay']) else None
                        supabase.table('devotees').insert({
                            'devotee_id':dev_id,'name':str(row['Name']),'dob':date_to_db(dob),
                            'gender':str(row['Gender']),'mobile_no':str(row['Mobile']),'email':str(row['Email']),
                            'address':str(row['Address']),'natchathiram':str(row['Natchathiram']),
                            'wedding_day':date_to_db(wedding),'occupation':str(row['Occupation']),'gothram':str(row['Gothram'])
                        }).execute()
                        success+=1
                    except:
                        pass
                st.success(f"Imported {success} devotees")

# ============================================================
# BILLING SYSTEM (Full with PDF & WhatsApp)
# ============================================================
def billing_page():
    render_header()
    tab1, tab2 = st.tabs(["🧾 New Bill", "📋 Bill History"])
    amman_img = get_amman_image()
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            manual_bill = st.text_input("Manual Bill No (optional)")
            book_no = st.text_input("Book No (optional)")
            bill_date_str = st.text_input("Bill Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
            pooja_types = supabase.table('pooja_types').select('name,amount').eq('is_active',True).execute()
            pooja_options = {p['name']:p['amount'] for p in pooja_types.data} if pooja_types.data else {}
            pooja = st.selectbox("Pooja Type", list(pooja_options.keys()))
            default_amount = pooja_options.get(pooja, 0)
            amount = st.number_input("Amount", min_value=0.0, value=default_amount, step=10.0, key="bill_amount")
            st.info(f"Amount: {TEMPLE_CONFIG['currency']}{amount}")
            payment = st.selectbox("Payment Mode", ["cash","card","upi","bank"])
        with col2:
            dev_type = st.radio("Devotee Type", ["Registered","Guest"])
            if dev_type == "Registered":
                st.markdown("### Search Devotee")
                search_by = st.selectbox("Search by", ["Name","Mobile No","Address"])
                search_term = st.text_input(f"Enter {search_by}")
                devotee_id = None
                dev_name = ""
                dev_mobile = ""
                dev_address = ""
                if search_term:
                    query = supabase.table('devotees').select('id,name,mobile_no,address')
                    if search_by == "Name":
                        query = query.ilike('name',f'%{search_term}%')
                    elif search_by == "Mobile No":
                        query = query.ilike('mobile_no',f'%{search_term}%')
                    else:
                        query = query.ilike('address',f'%{search_term}%')
                    res = query.limit(10).execute()
                    if res.data:
                        dev_opts = {f"{d['name']} - {d.get('mobile_no','')}":d for d in res.data}
                        selected = st.selectbox("Select Devotee", list(dev_opts.keys()))
                        dev = dev_opts[selected]
                        devotee_id = dev['id']
                        dev_name = dev['name']
                        dev_mobile = dev.get('mobile_no','')
                        dev_address = dev.get('address','')
                        st.success(f"Selected: {dev_name}")
                    else:
                        st.warning("No devotees found")
            else:
                devotee_id = None
                guest_name = st.text_input("Guest Name *")
                guest_mobile = st.text_input("Mobile")
                guest_address = st.text_area("Address")
                dev_name = guest_name
                dev_mobile = guest_mobile
                dev_address = guest_address

        if st.button("Generate Bill", type="primary"):
            if dev_type=="Guest" and not guest_name:
                st.error("Enter guest name")
            elif amount<=0:
                st.error("Invalid amount")
            else:
                bill_date = parse_date_ddmmyyyy(bill_date_str)
                if not bill_date:
                    st.error("Invalid bill date. Use DD/MM/YYYY")
                else:
                    bill_no = generate_unique_id('BILL')
                    bill_date_display = format_date_ddmmyyyy(bill_date)
                    data = {
                        'bill_no':bill_no,'manual_bill_no':manual_bill,'bill_book_no':book_no,
                        'devotee_type':'registered' if dev_type=="Registered" else 'guest',
                        'devotee_id':devotee_id if dev_type=="Registered" else None,
                        'guest_name':guest_name if dev_type=="Guest" else None,
                        'guest_mobile':guest_mobile if dev_type=="Guest" else None,
                        'guest_address':guest_address if dev_type=="Guest" else None,
                        'pooja_type':pooja,'amount':amount,'bill_date':date_to_db(bill_date),
                        'payment_mode':payment
                    }
                    supabase.table('bills').insert(data).execute()
                    st.success(f"Bill generated: {bill_no}")
                    st.balloons()
                    st.markdown(f"""
                    <div style='border:2px solid #667eea; padding:20px; border-radius:10px; background:white; margin:10px 0;'>
                        <h3 style='text-align:center'>{TEMPLE_NAME}</h3>
                        <p style='text-align:center'>{TEMPLE_TRUST}<br>{TEMPLE_ADDRESS}<br>✉ {TEMPLE_EMAIL}</p>
                        <hr><h4>BILL / RECEIPT</h4><hr>
                        <p><strong>Bill No:</strong> {bill_no}<br><strong>Date:</strong> {bill_date_display}<br>
                        <strong>Name:</strong> {dev_name}<br><strong>Address:</strong> {dev_address}<br>
                        <strong>Mobile:</strong> {dev_mobile}<br><strong>Pooja:</strong> {pooja}<br>
                        <strong>Amount:</strong> {TEMPLE_CONFIG['currency']}{amount:,.2f}</p>
                        <hr><p>🙏 Thank you! {TEMPLE_TAMIL} 🙏</p>
                    </div>
                    """, unsafe_allow_html=True)
                    colA, colB = st.columns(2)
                    with colA:
                        if PDF_AVAILABLE:
                            pdf = generate_bill_pdf(bill_no,manual_bill,book_no,bill_date_display,dev_name,dev_address,dev_mobile,pooja,amount,amman_base64=amman_img)
                            if pdf:
                                st.download_button("📥 Download PDF", data=pdf, file_name=f"Bill_{bill_no}.pdf", mime="application/pdf")
                            else:
                                st.error("PDF generation failed")
                    with colB:
                        wa_num = dev_mobile or (guest_mobile if dev_type=="Guest" else "")
                        if wa_num:
                            wa_msg = build_bill_whatsapp_message(bill_no,bill_date_display,dev_name,pooja,amount,manual_bill,book_no)
                            st.markdown(f'<a href="{make_whatsapp_link(wa_num,wa_msg)}" target="_blank" style="display:inline-block; background:#25D366; color:white; padding:10px 20px; border-radius:10px; text-decoration:none; width:100%; text-align:center;">📲 Send via WhatsApp</a>', unsafe_allow_html=True)
                            if st.button("📋 Copy Bill Message"):
                                st.code(wa_msg, language="text")
                                st.success("Message copied! You can paste it in WhatsApp.")
                        else:
                            st.warning("No mobile number for WhatsApp")
    with tab2:
        st.subheader("Bill History")
        from_date_str = st.text_input("From Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()-timedelta(30)))
        to_date_str = st.text_input("To Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
        from_date = parse_date_ddmmyyyy(from_date_str) if from_date_str else None
        to_date = parse_date_ddmmyyyy(to_date_str) if to_date_str else None
        if from_date and to_date:
            bills = supabase.table('bills').select('*').gte('bill_date',date_to_db(from_date)).lte('bill_date',date_to_db(to_date)).order('bill_date',desc=True).execute()
            if bills.data:
                for bill in bills.data:
                    bill_display_date = format_date_ddmmyyyy(datetime.strptime(bill['bill_date'],'%Y-%m-%d').date())
                    with st.expander(f"🧾 {bill['bill_no']} - {bill.get('guest_name') or 'Registered'} - ₹{bill['amount']} - {bill_display_date}"):
                        col1, col2 = st.columns([3,1])
                        with col1:
                            st.write(f"**Manual Bill:** {bill.get('manual_bill_no','N/A')}")
                            st.write(f"**Book No:** {bill.get('bill_book_no','N/A')}")
                            st.write(f"**Pooja:** {bill['pooja_type']}")
                            st.write(f"**Amount:** ₹{bill['amount']:,.2f}")
                            st.write(f"**Payment:** {bill.get('payment_mode','cash')}")
                        with col2:
                            if st.button("🗑️ Delete", key=f"del_bill_{bill['id']}"):
                                supabase.table('bills').delete().eq('id',bill['id']).execute()
                                st.rerun()
                        if PDF_AVAILABLE:
                            pdf = generate_bill_pdf(bill['bill_no'],bill.get('manual_bill_no',''),bill.get('bill_book_no',''),bill_display_date,
                                                   bill.get('guest_name',''),bill.get('guest_address',''),bill.get('guest_mobile',''),
                                                   bill['pooja_type'],bill['amount'],amman_base64=amman_img)
                            if pdf:
                                st.download_button("📥 PDF", pdf, f"Bill_{bill['bill_no']}.pdf", mime="application/pdf", key=f"pdf_{bill['id']}")
            else:
                st.info("No bills found")
        else:
            st.warning("Invalid date range")

# ============================================================
# POOJA MANAGEMENT (Full)
# ============================================================
def pooja_management_page():
    render_header()
    tab1, tab2, tab3 = st.tabs(["🙏 Pooja Types","📅 Daily Schedule","📋 Yearly Subscriptions"])
    with tab1:
        with st.expander("➕ Add New Pooja Type"):
            with st.form("add_pt"):
                name = st.text_input("Name")
                amount = st.number_input("Amount", min_value=0.0)
                duration = st.text_input("Duration")
                desc = st.text_area("Description")
                if st.form_submit_button("Add"):
                    if name:
                        supabase.table('pooja_types').insert({'name':name,'amount':amount,'duration':duration,'description':desc}).execute()
                        st.rerun()
        pts = supabase.table('pooja_types').select('*').execute()
        if pts.data:
            for p in pts.data:
                col1, col2, col3 = st.columns([3,1,1])
                col1.write(f"**{p['name']}** - {TEMPLE_CONFIG['currency']}{p['amount']}")
                if col2.button("✏️", key=f"edit_{p['id']}"):
                    st.session_state[f"edit_pt_{p['id']}"] = True
                if col3.button("🗑️", key=f"del_{p['id']}"):
                    supabase.table('pooja_types').delete().eq('id',p['id']).execute()
                    st.rerun()
                if st.session_state.get(f"edit_pt_{p['id']}"):
                    with st.form(f"edit_form_{p['id']}"):
                        new_name = st.text_input("Name", p['name'])
                        new_amount = st.number_input("Amount", value=float(p['amount']))
                        if st.form_submit_button("Save"):
                            supabase.table('pooja_types').update({'name':new_name,'amount':new_amount}).eq('id',p['id']).execute()
                            del st.session_state[f"edit_pt_{p['id']}"]
                            st.rerun()
    with tab2:
        with st.form("schedule"):
            col1, col2 = st.columns(2)
            with col1:
                p_name = st.text_input("Pooja Name")
                p_time = st.text_input("Time (e.g., 09:00 AM)")
            with col2:
                p_date_str = st.text_input("Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
                priest = st.text_input("Priest Name")
            notes = st.text_area("Notes")
            if st.form_submit_button("Schedule"):
                p_date = parse_date_ddmmyyyy(p_date_str)
                if p_name and p_date:
                    supabase.table('daily_pooja').insert({'pooja_name':p_name,'pooja_time':p_time,'pooja_date':date_to_db(p_date),'priest_name':priest,'notes':notes}).execute()
                    st.rerun()
                else:
                    st.error("Invalid date")
        view_date_str = st.text_input("View Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
        view_date = parse_date_ddmmyyyy(view_date_str) if view_date_str else None
        if view_date:
            schedule = supabase.table('daily_pooja').select('*').eq('pooja_date',date_to_db(view_date)).execute()
            if schedule.data:
                for s in schedule.data:
                    c1,c2,c3 = st.columns([2,1,1])
                    c1.write(f"**{s['pooja_name']}** at {s.get('pooja_time','')}")
                    if c2.button("✅ Complete" if s['status']!='completed' else "🔄 Pending", key=f"stat_{s['id']}"):
                        new_status = 'completed' if s['status']!='completed' else 'pending'
                        supabase.table('daily_pooja').update({'status':new_status}).eq('id',s['id']).execute()
                        st.rerun()
                    if c3.button("🗑️", key=f"del_daily_{s['id']}"):
                        supabase.table('daily_pooja').delete().eq('id',s['id']).execute()
                        st.rerun()
            else:
                st.info("No poojas scheduled")
        else:
            st.warning("Invalid date")
    with tab3:
        devotees = supabase.table('devotees').select('id,name,mobile_no').execute()
        if devotees.data:
            dev_opt = {f"{d['name']} - {d.get('mobile_no','')}": d['id'] for d in devotees.data}
            selected = st.selectbox("Select Devotee", list(dev_opt.keys()))
            dev_id = dev_opt[selected]
            with st.form("add_sub"):
                pooja_type = st.selectbox("Pooja", [p['name'] for p in supabase.table('pooja_types').select('name').execute().data or []])
                pooja_date_str = st.text_input("Pooja Date (DD/MM/YYYY)")
                amount = st.number_input("Amount", min_value=0.0)
                desc = st.text_area("Description")
                if st.form_submit_button("Add Subscription"):
                    pooja_date = parse_date_ddmmyyyy(pooja_date_str)
                    if pooja_date:
                        supabase.table('devotee_yearly_pooja').insert({'devotee_id':dev_id,'pooja_type':pooja_type,'pooja_date':date_to_db(pooja_date),'amount':amount,'description':desc}).execute()
                        st.rerun()
                    else:
                        st.error("Invalid date")
            subs = supabase.table('devotee_yearly_pooja').select('*').eq('devotee_id',dev_id).execute()
            if subs.data:
                for sub in subs.data:
                    pooja_date_obj = datetime.strptime(sub['pooja_date'],'%Y-%m-%d').date() if sub.get('pooja_date') else None
                    date_str = format_date_ddmmyyyy(pooja_date_obj) if pooja_date_obj else ''
                    col1, col2 = st.columns([3,1])
                    col1.write(f"{sub['pooja_type']} on {date_str} - {TEMPLE_CONFIG['currency']}{sub.get('amount',0)}")
                    if col2.button("✅ Complete" if not sub.get('is_completed') else "🔄 Undo", key=f"sub_{sub['id']}"):
                        supabase.table('devotee_yearly_pooja').update({'is_completed': not sub.get('is_completed')}).eq('id',sub['id']).execute()
                        st.rerun()
        else:
            st.warning("No devotees found")

# ============================================================
# EXPENSE TRACKING (Full)
# ============================================================
def expense_page():
    render_header()
    tab1, tab2 = st.tabs(["➕ Add Expense","📋 History"])
    with tab1:
        with st.form("add_exp"):
            col1, col2 = st.columns(2)
            with col1:
                exp_types = supabase.table('expense_types').select('name').execute()
                exp_list = [e['name'] for e in exp_types.data] if exp_types.data else []
                exp_type = st.selectbox("Expense Type", exp_list)
                amount = st.number_input("Amount", min_value=0.0, step=10.0)
                date_exp_str = st.text_input("Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
            with col2:
                bill_no = st.text_input("Bill/Invoice No")
                vendor = st.text_input("Vendor")
            desc = st.text_area("Description")
            if st.form_submit_button("Add"):
                date_exp = parse_date_ddmmyyyy(date_exp_str)
                if exp_type and amount>0 and date_exp:
                    supabase.table('expenses').insert({
                        'expense_type':exp_type,'amount':amount,'description':desc,
                        'expense_date':date_to_db(date_exp),'bill_no':bill_no,'vendor_name':vendor
                    }).execute()
                    st.success("Expense added")
                    st.rerun()
                else:
                    st.error("Invalid date or missing fields")
    with tab2:
        from_date_str = st.text_input("From Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()-timedelta(30)))
        to_date_str = st.text_input("To Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
        from_date = parse_date_ddmmyyyy(from_date_str) if from_date_str else None
        to_date = parse_date_ddmmyyyy(to_date_str) if to_date_str else None
        if from_date and to_date:
            exps = supabase.table('expenses').select('*').gte('expense_date',date_to_db(from_date)).lte('expense_date',date_to_db(to_date)).order('expense_date',desc=True).execute()
            if exps.data:
                df = pd.DataFrame(exps.data)
                total = df['amount'].sum()
                st.metric("Total Expenses", f"{TEMPLE_CONFIG['currency']}{total:,.2f}")
                df['expense_date_display'] = df['expense_date'].apply(lambda x: format_date_ddmmyyyy(datetime.strptime(x,'%Y-%m-%d').date()) if x else '')
                st.dataframe(df[['expense_date_display','expense_type','amount','description','vendor_name']])
                csv = df.to_csv(index=False).encode()
                st.download_button("📥 Export", csv, "expenses.csv")
            else:
                st.info("No expenses")
        else:
            st.warning("Invalid date range")

# ============================================================
# DONATIONS (Full)
# ============================================================
def donations_page():
    render_header()
    tab1, tab2 = st.tabs(["🎁 Record Donation","📋 History"])
    with tab1:
        with st.form("donation"):
            col1, col2 = st.columns(2)
            with col1:
                donor = st.text_input("Donor Name *")
                mobile = st.text_input("Mobile")
                email = st.text_input("Email")
            with col2:
                amount = st.number_input("Amount *", min_value=0.0)
                don_type = st.selectbox("Type", ["General","Temple Construction","Annadhanam","Festival","Other"])
                date_don_str = st.text_input("Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
            purpose = st.text_area("Purpose")
            payment = st.selectbox("Payment Mode", ["cash","card","upi","bank"])
            if st.form_submit_button("Record"):
                date_don = parse_date_ddmmyyyy(date_don_str)
                if donor and amount>0 and date_don:
                    don_no = generate_unique_id('DON')
                    supabase.table('donations').insert({
                        'donation_no':don_no,'donor_name':donor,'donor_mobile':mobile,'donor_email':email,
                        'amount':amount,'donation_type':don_type,'purpose':purpose,
                        'donation_date':date_to_db(date_don),'payment_mode':payment
                    }).execute()
                    st.success(f"Donation recorded! Receipt: {don_no}")
                    st.balloons()
                else:
                    st.error("Invalid date or missing fields")
    with tab2:
        from_date_str = st.text_input("From Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()-timedelta(365)))
        to_date_str = st.text_input("To Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
        from_date = parse_date_ddmmyyyy(from_date_str) if from_date_str else None
        to_date = parse_date_ddmmyyyy(to_date_str) if to_date_str else None
        if from_date and to_date:
            don = supabase.table('donations').select('*').gte('donation_date',date_to_db(from_date)).lte('donation_date',date_to_db(to_date)).order('donation_date',desc=True).execute()
            if don.data:
                df = pd.DataFrame(don.data)
                total = df['amount'].sum()
                st.metric("Total Donations", f"{TEMPLE_CONFIG['currency']}{total:,.2f}")
                df['donation_date_display'] = df['donation_date'].apply(lambda x: format_date_ddmmyyyy(datetime.strptime(x,'%Y-%m-%d').date()) if x else '')
                st.dataframe(df[['donation_no','donation_date_display','donor_name','donation_type','amount','payment_mode']])
                csv = df.to_csv(index=False).encode()
                st.download_button("📥 Export", csv, "donations.csv")
            else:
                st.info("No donations")
        else:
            st.warning("Invalid date range")

# ============================================================
# SAMAYA VAKUPPU (Full)
# ============================================================
def samaya_vakuppu_page():
    render_header()
    st.markdown("## 📚 Samaya Vakuppu - Bond Management")
    tab1, tab2 = st.tabs(["➕ Register Bond", "📋 Bond List"])
    with tab1:
        with st.form("samaya_bond"):
            col1, col2 = st.columns(2)
            with col1:
                student_name = st.text_input("Student Name *")
                father_name = st.text_input("Father's Name *")
                bond_no = st.text_input("Bond No *")
            with col2:
                bond_issue_date_str = st.text_input("Bond Issue Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
                issued_bank = st.text_input("Issued Bank")
            address = st.text_area("Address")
            bond_scan = st.file_uploader("Upload Bond Scan Copy", type=['pdf','jpg','png','jpeg'])
            student_photo = st.file_uploader("Student Photo", type=['jpg','png','jpeg'])
            if st.form_submit_button("Register Bond"):
                bond_issue_date = parse_date_ddmmyyyy(bond_issue_date_str)
                if student_name and father_name and bond_no and bond_issue_date:
                    bond_id = generate_unique_id('SAM')
                    bond_scan_b64 = base64.b64encode(bond_scan.getvalue()).decode() if bond_scan else None
                    photo_b64 = base64.b64encode(student_photo.getvalue()).decode() if student_photo else None
                    supabase.table('samaya_vakuppu').insert({
                        'bond_id':bond_id,'student_name':student_name,'father_name':father_name,
                        'bond_no':bond_no,'bond_issue_date':date_to_db(bond_issue_date),
                        'issued_bank':issued_bank,'address':address,
                        'bond_scan_url':bond_scan_b64,'photo_url':photo_b64
                    }).execute()
                    st.success(f"Bond registered! ID: {bond_id}")
                    st.balloons()
                else:
                    st.error("Please fill all required fields and valid date")
    with tab2:
        bonds = supabase.table('samaya_vakuppu').select('*').order('created_at',desc=True).execute()
        if bonds.data:
            for b in bonds.data:
                issue_date_obj = datetime.strptime(b['bond_issue_date'],'%Y-%m-%d').date() if b.get('bond_issue_date') else None
                issue_date_str = format_date_ddmmyyyy(issue_date_obj) if issue_date_obj else ''
                with st.expander(f"📄 {b['student_name']} - Bond: {b['bond_no']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Father:** {b['father_name']}")
                        st.write(f"**Issue Date:** {issue_date_str}")
                        st.write(f"**Bank:** {b.get('issued_bank','N/A')}")
                        st.write(f"**Address:** {b.get('address','N/A')}")
                    with col2:
                        if b.get('photo_url'):
                            st.image(base64.b64decode(b['photo_url']), width=120)
                    if b.get('bond_scan_url'):
                        st.markdown("**Bond Scan:**")
                        if 'pdf' in b['bond_scan_url'][:100]:
                            st.download_button("📥 Download Bond PDF", data=base64.b64decode(b['bond_scan_url']), file_name=f"bond_{b['bond_no']}.pdf", mime="application/pdf", key=f"dl_sam_{b['id']}")
                        else:
                            st.image(base64.b64decode(b['bond_scan_url']), width=200)
                    if st.button("🗑️ Delete", key=f"del_sam_{b['id']}"):
                        supabase.table('samaya_vakuppu').delete().eq('id',b['id']).execute()
                        st.rerun()
        else:
            st.info("No bonds registered")

# ============================================================
# THIRUMANA MANDAPAM (Full)
# ============================================================
def thirumana_mandapam_page():
    render_header()
    st.markdown("## 💒 Thirumana Mandapam - Bond Management")
    tab1, tab2 = st.tabs(["➕ Register Bond", "📋 Bond List"])
    with tab1:
        with st.form("thirumana_bond"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name *")
                bond_no = st.text_input("Bond No *")
                address = st.text_area("Address")
            with col2:
                bond_issue_date_str = st.text_input("Bond Issue Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
                issued_by = st.text_input("Issued By")
            bond_scan = st.file_uploader("Upload Bond Scan Copy", type=['pdf','jpg','png','jpeg'])
            photo = st.file_uploader("Photo", type=['jpg','png','jpeg'])
            if st.form_submit_button("Register Bond"):
                bond_issue_date = parse_date_ddmmyyyy(bond_issue_date_str)
                if name and bond_no and bond_issue_date:
                    bond_id = generate_unique_id('THI')
                    scan_b64 = base64.b64encode(bond_scan.getvalue()).decode() if bond_scan else None
                    photo_b64 = base64.b64encode(photo.getvalue()).decode() if photo else None
                    supabase.table('thirumana_mandapam').insert({
                        'bond_id':bond_id,'name':name,'bond_no':bond_no,
                        'address':address,'bond_issue_date':date_to_db(bond_issue_date),
                        'issued_by':issued_by,'scan_copy_url':scan_b64,'photo_url':photo_b64
                    }).execute()
                    st.success(f"Bond registered! ID: {bond_id}")
                    st.balloons()
                else:
                    st.error("Please fill all required fields and valid date")
    with tab2:
        bonds = supabase.table('thirumana_mandapam').select('*').order('created_at',desc=True).execute()
        if bonds.data:
            for b in bonds.data:
                issue_date_obj = datetime.strptime(b['bond_issue_date'],'%Y-%m-%d').date() if b.get('bond_issue_date') else None
                issue_date_str = format_date_ddmmyyyy(issue_date_obj) if issue_date_obj else ''
                with st.expander(f"💒 {b['name']} - Bond: {b['bond_no']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Address:** {b.get('address','N/A')}")
                        st.write(f"**Issue Date:** {issue_date_str}")
                        st.write(f"**Issued By:** {b.get('issued_by','N/A')}")
                    with col2:
                        if b.get('photo_url'):
                            st.image(base64.b64decode(b['photo_url']), width=120)
                    if b.get('scan_copy_url'):
                        st.markdown("**Bond Scan:**")
                        if 'pdf' in b['scan_copy_url'][:100]:
                            st.download_button("📥 Download Bond PDF", data=base64.b64decode(b['scan_copy_url']), file_name=f"bond_{b['bond_no']}.pdf", mime="application/pdf", key=f"dl_thi_{b['id']}")
                        else:
                            st.image(base64.b64decode(b['scan_copy_url']), width=200)
                    if st.button("🗑️ Delete", key=f"del_thi_{b['id']}"):
                        supabase.table('thirumana_mandapam').delete().eq('id',b['id']).execute()
                        st.rerun()
        else:
            st.info("No bonds registered")

# ============================================================
# ASSET MANAGEMENT (Full)
# ============================================================
def assets_page():
    render_header()
    tab1, tab2 = st.tabs(["🏷️ Add Asset", "📋 List & Barcodes"])
    with tab1:
        with st.form("add_asset"):
            col1, col2 = st.columns(2)
            with col1:
                tag = st.text_input("Asset Tag *")
                name = st.text_input("Asset Name *")
                category = st.selectbox("Category", ["Furniture","Electronics","Vehicles","Idols","Jewelry","Other"])
                serial = st.text_input("Serial No")
            with col2:
                donor = st.text_input("Donor")
                date_don_str = st.text_input("Donation/Purchase Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
                cost = st.number_input("Cost", min_value=0.0)
                location = st.text_input("Location")
            desc = st.text_area("Description")
            status = st.selectbox("Status", ["active","maintenance","damaged","donated"])
            generate_barcode = st.checkbox("Generate Barcode", value=True)
            if st.form_submit_button("Add Asset"):
                date_don = parse_date_ddmmyyyy(date_don_str)
                if tag and name and date_don:
                    data = {
                        'asset_tag':tag,'asset_name':name,'category':category,'serial_no':serial,
                        'donor_name':donor,'donation_date':date_to_db(date_don),'purchase_cost':cost,
                        'location':location,'description':desc,'status':status
                    }
                    if generate_barcode:
                        barcode_img,_ = generate_barcode_image(tag)
                        if barcode_img:
                            data['barcode_url'] = barcode_img
                    supabase.table('assets').insert(data).execute()
                    st.success(f"Asset '{name}' added")
                    st.rerun()
                else:
                    st.error("Invalid date or missing fields")
    with tab2:
        search = st.text_input("Search by tag/name/donor")
        query = supabase.table('assets').select('*').order('created_at',desc=True)
        if search:
            query = query.or_(f"asset_tag.ilike.%{search}%,asset_name.ilike.%{search}%,donor_name.ilike.%{search}%")
        assets = query.execute()
        if assets.data:
            for a in assets.data:
                with st.expander(f"🏷️ {a['asset_tag']} - {a['asset_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Category:** {a.get('category','N/A')}")
                        st.write(f"**Serial:** {a.get('serial_no','N/A')}")
                        st.write(f"**Donor:** {a.get('donor_name','N/A')}")
                        donation_date_obj = datetime.strptime(a['donation_date'],'%Y-%m-%d').date() if a.get('donation_date') else None
                        st.write(f"**Date:** {format_date_ddmmyyyy(donation_date_obj) if donation_date_obj else 'N/A'}")
                        st.write(f"**Cost:** {TEMPLE_CONFIG['currency']}{a.get('purchase_cost',0):,.2f}")
                        st.write(f"**Location:** {a.get('location','N/A')}")
                        st.write(f"**Status:** {a.get('status','N/A')}")
                    with col2:
                        barcode_img,barcode_bytes = generate_barcode_image(a['asset_tag'])
                        if barcode_img:
                            st.image(barcode_img, width=200)
                            if barcode_bytes:
                                st.download_button("📥 Barcode PNG", data=barcode_bytes, file_name=f"barcode_{a['asset_tag']}.png", mime="image/png", key=f"bc_{a['id']}")
                        else:
                            st.info("Barcode not generated")
                    if st.button("🗑️ Delete", key=f"del_asset_{a['id']}"):
                        supabase.table('assets').delete().eq('id',a['id']).execute()
                        st.rerun()
        else:
            st.info("No assets")

# ============================================================
# REPORTS (Full)
# ============================================================
def reports_page():
    render_header()
    report_type = st.selectbox("Report Type", ["Income Report","Financial Summary","Devotee Report","Pooja Income","Expense Report","Donation Report"])
    from_date_str = st.text_input("From Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()-timedelta(30)))
    to_date_str = st.text_input("To Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()))
    from_date = parse_date_ddmmyyyy(from_date_str) if from_date_str else None
    to_date = parse_date_ddmmyyyy(to_date_str) if to_date_str else None
    if not from_date or not to_date:
        st.warning("Please enter valid date range")
        return
    if report_type == "Income Report":
        bills = supabase.table('bills').select('*').gte('bill_date',date_to_db(from_date)).lte('bill_date',date_to_db(to_date)).execute()
        if bills.data:
            data = []
            for b in bills.data:
                name = b.get('guest_name')
                address = b.get('guest_address')
                mobile = b.get('guest_mobile')
                if b.get('devotee_type')=='registered' and b.get('devotee_id'):
                    dev = supabase.table('devotees').select('name,address,mobile_no').eq('id',b['devotee_id']).execute()
                    if dev.data:
                        name = dev.data[0]['name']
                        address = dev.data[0].get('address','')
                        mobile = dev.data[0].get('mobile_no','')
                data.append({
                    'Name':name or '','Address':address or '','Manual Bill No':b.get('manual_bill_no',''),
                    'Book No':b.get('bill_book_no',''),'Bill No':b['bill_no'],'Mobile No':mobile or '',
                    'Amount':b['amount'],'Pooja Type':b['pooja_type']
                })
            df = pd.DataFrame(data)
            df['Amount'] = df['Amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(df)
            st.download_button("📥 Download", df.to_csv(index=False).encode(), "income_report.csv")
        else:
            st.info("No bills")
    elif report_type == "Financial Summary":
        summary = get_financial_summary(from_date,to_date)
        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Income", f"{TEMPLE_CONFIG['currency']}{summary['income']:,.2f}")
        col2.metric("Expenses", f"{TEMPLE_CONFIG['currency']}{summary['expenses']:,.2f}")
        col3.metric("Donations", f"{TEMPLE_CONFIG['currency']}{summary['donations']:,.2f}")
        col4.metric("Balance", f"{TEMPLE_CONFIG['currency']}{summary['balance']:,.2f}")
    elif report_type == "Devotee Report":
        devs = supabase.table('devotees').select('devotee_id,name,mobile_no,email,created_at').execute()
        if devs.data:
            st.dataframe(pd.DataFrame(devs.data))
            st.download_button("📥 Download", pd.DataFrame(devs.data).to_csv(index=False).encode(), "devotees.csv")
    elif report_type == "Pooja Income":
        bills = supabase.table('bills').select('pooja_type,amount').gte('bill_date',date_to_db(from_date)).lte('bill_date',date_to_db(to_date)).execute()
        if bills.data:
            df = pd.DataFrame(bills.data).groupby('pooja_type')['amount'].sum().reset_index()
            df['amount'] = df['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(df)
    elif report_type == "Expense Report":
        exps = supabase.table('expenses').select('expense_type,amount').gte('expense_date',date_to_db(from_date)).lte('expense_date',date_to_db(to_date)).execute()
        if exps.data:
            df = pd.DataFrame(exps.data).groupby('expense_type')['amount'].sum().reset_index()
            df['amount'] = df['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(df)
    elif report_type == "Donation Report":
        don = supabase.table('donations').select('donation_type,amount').gte('donation_date',date_to_db(from_date)).lte('donation_date',date_to_db(to_date)).execute()
        if don.data:
            df = pd.DataFrame(don.data).groupby('donation_type')['amount'].sum().reset_index()
            df['amount'] = df['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(df)

# ============================================================
# SETTINGS (Full)
# ============================================================
def settings_page():
    render_header()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏛️ Temple Info","🖼️ Amman Image","📢 News Ticker","💸 Expense Types","👤 Profile"])
    with tab1:
        with st.form("temple_info"):
            name = st.text_input("Temple Name", TEMPLE_CONFIG['name'])
            trust = st.text_input("Trust", TEMPLE_CONFIG['trust'])
            addr = st.text_area("Address", TEMPLE_CONFIG['address'])
            phone = st.text_input("Phone", TEMPLE_CONFIG['phone'])
            email = st.text_input("Email", TEMPLE_CONFIG['email'])
            tagline = st.text_input("Tagline", TEMPLE_CONFIG['tagline'])
            if st.form_submit_button("Save"):
                TEMPLE_CONFIG.update({'name':name,'trust':trust,'address':addr,'phone':phone,'email':email,'tagline':tagline})
                st.success("Saved")
                st.rerun()
    with tab2:
        st.subheader("Upload Amman Image")
        current_img = get_amman_image()
        st.image(current_img, width=150)
        uploaded_img = st.file_uploader("Choose JPG/PNG (for PDF bill)", type=['jpg','jpeg','png'])
        if uploaded_img:
            img_b64 = "data:image/jpeg;base64," + base64.b64encode(uploaded_img.getvalue()).decode()
            st.image(img_b64, width=120)
            if st.button("Save Amman Image"):
                set_amman_image(img_b64)
                st.success("Updated! Refresh page.")
                st.rerun()
        if st.button("Reset to Default"):
            set_amman_image("")
            st.rerun()
    with tab3:
        with st.form("add_news"):
            msg = st.text_input("News Message")
            prio = st.slider("Priority",0,10,0)
            if st.form_submit_button("Add"):
                if msg:
                    supabase.table('news_ticker').insert({'message':msg,'priority':prio}).execute()
                    st.rerun()
        news = supabase.table('news_ticker').select('*').order('priority',desc=True).execute()
        if news.data:
            for n in news.data:
                c1,c2,c3 = st.columns([4,1,1])
                c1.write(f"{'🟢' if n['is_active'] else '🔴'} {n['message']}")
                if c2.button("Toggle", key=f"toggle_{n['id']}"):
                    supabase.table('news_ticker').update({'is_active': not n['is_active']}).eq('id',n['id']).execute()
                    st.rerun()
                if c3.button("🗑️", key=f"del_news_{n['id']}"):
                    supabase.table('news_ticker').delete().eq('id',n['id']).execute()
                    st.rerun()
    with tab4:
        with st.form("add_exp_type"):
            exp_name = st.text_input("Expense Type Name")
            cat = st.selectbox("Category", ["Utilities","Maintenance","Daily Operations","Staff","Events","Other"])
            if st.form_submit_button("Add"):
                if exp_name:
                    supabase.table('expense_types').insert({'name':exp_name,'category':cat}).execute()
                    st.rerun()
        exps = supabase.table('expense_types').select('*').execute()
        if exps.data:
            for e in exps.data:
                c1,c2 = st.columns([3,1])
                c1.write(f"**{e['name']}** ({e.get('category','')})")
                if c2.button("Delete", key=f"del_exp_{e['id']}"):
                    supabase.table('expense_types').delete().eq('id',e['id']).execute()
                    st.rerun()
    with tab5:
        user = supabase.table('users').select('*').eq('username',st.session_state.username).execute()
        if user.data:
            u = user.data[0]
            with st.form("profile"):
                full = st.text_input("Full Name", u.get('full_name',''))
                em = st.text_input("Email", u.get('email',''))
                old = st.text_input("Current Password", type="password")
                new = st.text_input("New Password", type="password")
                confirm = st.text_input("Confirm", type="password")
                if st.form_submit_button("Update"):
                    updates = {}
                    if full: updates['full_name']=full
                    if em: updates['email']=em
                    if updates:
                        supabase.table('users').update(updates).eq('id',u['id']).execute()
                    if old and new and new==confirm and verify_password(old, u['password_hash']):
                        supabase.table('users').update({'password_hash':hash_password(new)}).eq('id',u['id']).execute()
                        st.success("Password changed")
                    st.success("Profile updated")

# ============================================================
# USER MANAGEMENT (Admin only)
# ============================================================
def user_management_page():
    if st.session_state.get('role')!='admin':
        st.error("Admin only")
        return
    render_header()
    tab1, tab2 = st.tabs(["👥 Users","➕ Add"])
    with tab1:
        users = supabase.table('users').select('id,username,role,full_name,email').execute()
        if users.data:
            for u in users.data:
                col1, col2 = st.columns([3,1])
                col1.write(f"**{u['username']}** ({u['role']}) - {u.get('full_name','')}")
                if col2.button("Delete", key=f"del_user_{u['id']}"):
                    if u['username']!='admin':
                        supabase.table('users').delete().eq('id',u['id']).execute()
                        st.rerun()
    with tab2:
        with st.form("add_user"):
            uname = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["user","admin"])
            full = st.text_input("Full Name")
            email = st.text_input("Email")
            if st.form_submit_button("Create"):
                if uname and pwd:
                    supabase.table('users').insert({
                        'username':uname,'password_hash':hash_password(pwd),'role':role,
                        'full_name':full,'email':email
                    }).execute()
                    st.success("User created")
                    st.rerun()

# ============================================================
# MAIN
# ============================================================
def main():
    if not st.session_state.get('logged_in', False):
        login_page()
    else:
        render_sidebar()
        pages = {
            "Dashboard": dashboard_page,
            "Devotee Management": devotee_management_page,
            "Billing System": billing_page,
            "Pooja Management": pooja_management_page,
            "Expense Tracking": expense_page,
            "Donations": donations_page,
            "Samaya Vakuppu": samaya_vakuppu_page,
            "Thirumana Mandapam": thirumana_mandapam_page,
            "Asset Management": assets_page,
            "Reports": reports_page,
            "Settings": settings_page,
            "User Management": user_management_page
        }
        current = st.session_state.get('current_page', 'Dashboard')
        pages.get(current, dashboard_page)()

if __name__ == "__main__":
    main()
