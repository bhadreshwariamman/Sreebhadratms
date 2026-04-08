# app.py - Complete Temple Management System with Supabase
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import base64
import time
import hashlib
from typing import Optional, Dict, List, Any
from supabase import create_client, Client

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🛕 Temple Management System",
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
# CONSTANTS & CONFIG
# ============================================================
TEMPLE_CONFIG = {
    "name": "Sri Bhadreshwari Amman Temple",
    "trust": "Sri Bhadreshwari Charitable Trust",
    "address": "Temple Street, Devotional City - 123456",
    "phone": "+91 9876543210",
    "email": "temple@example.com",
    "website": "www.templeexample.com",
    "tagline": "Om Namah Shivaya",
    "currency": "₹"
}

NATCHATHIRAM_LIST = [
    "Ashwini", "Bharani", "Karthigai", "Rohini", "Mrigashirsha",
    "Thiruvadirai", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

RELATION_TYPES = [
    "Self", "Spouse", "Son", "Daughter", "Father", "Mother",
    "Brother", "Sister", "Grandfather", "Grandmother",
    "Father-in-law", "Mother-in-law", "Son-in-law",
    "Daughter-in-law", "Uncle", "Aunt", "Nephew", "Niece", "Other"
]

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
        existing = supabase.table('users').select('id').eq('username', 'admin').execute()
        if not existing.data:
            admin_data = {
                'username': 'admin',
                'password_hash': hash_password('admin123'),
                'role': 'admin',
                'full_name': 'Administrator',
                'email': 'admin@temple.com'
            }
            supabase.table('users').insert(admin_data).execute()
    except Exception as e:
        st.error(f"Admin creation error: {e}")

def get_temple_setting(key: str) -> str:
    if not supabase: return ''
    try:
        res = supabase.table('temple_settings').select('value').eq('key', key).execute()
        return res.data[0]['value'] if res.data else ''
    except:
        return ''

def set_temple_setting(key: str, value: str):
    if not supabase: return
    try:
        existing = supabase.table('temple_settings').select('id').eq('key', key).execute()
        if existing.data:
            supabase.table('temple_settings').update({'value': value}).eq('key', key).execute()
        else:
            supabase.table('temple_settings').insert({'key': key, 'value': value}).execute()
    except:
        pass

def get_todays_birthdays():
    if not supabase: return []
    today = date.today()
    birthdays = []
    try:
        res = supabase.table('devotees').select('name, dob').execute()
        for d in res.data:
            if d.get('dob'):
                try:
                    dob = datetime.strptime(d['dob'], '%Y-%m-%d').date()
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
        res = supabase.table('devotees').select('name, wedding_day').execute()
        for d in res.data:
            if d.get('wedding_day'):
                try:
                    wedding = datetime.strptime(d['wedding_day'], '%Y-%m-%d').date()
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
        return {'income':total_inc, 'expenses':total_exp, 'donations':total_don, 'balance':total_inc+total_don-total_exp}
    except:
        return {'income':0,'expenses':0,'donations':0,'balance':0}

# ============================================================
# UI COMPONENTS
# ============================================================
def render_header():
    logo = get_temple_setting('temple_logo')
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        if logo:
            st.image(logo, width=100)
        st.markdown(f"""
        <div style='text-align:center; padding:20px; background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); border-radius:10px; margin-bottom:20px;'>
            <h1 style='color:white; margin:0;'>🛕 {TEMPLE_CONFIG['name']}</h1>
            <p style='color:#f0f0f0;'>{TEMPLE_CONFIG['trust']}</p>
            <p style='color:#e0e0e0;'>📍 {TEMPLE_CONFIG['address']} | 📞 {TEMPLE_CONFIG['phone']} | ✉ {TEMPLE_CONFIG['email']}</p>
            <p style='color:#ffd700; font-style:italic;'>{TEMPLE_CONFIG['tagline']}</p>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("<div style='text-align:center;'><h2 style='color:#667eea;'>🛕 Temple MS</h2></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#667eea,#764ba2); padding:15px; border-radius:10px; text-align:center;'>
            <p style='color:white;'>👤 {st.session_state.get('username','Guest')}</p>
            <p style='color:#ffd700; font-size:12px;'>{st.session_state.get('role','user')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        pages = {
            "Dashboard":"🏠","Devotee Management":"👥","Billing System":"🧾",
            "Pooja Management":"🙏","Expense Tracking":"💰","Donations":"🎁",
            "Asset Management":"🏷️","Reports":"📊","Settings":"⚙️","User Management":"👥"
        }
        for page, icon in pages.items():
            if page=="User Management" and st.session_state.get('role')!='admin': continue
            if st.button(f"{icon} {page}", key=page, use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for k in ['logged_in','username','role','user_id','current_page']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

# ============================================================
# LOGIN PAGE
# ============================================================
def login_page():
    if not supabase:
        st.error("⚠️ Database connection failed. Check Supabase secrets.")
        return
    create_default_admin()
    st.markdown("""
    <style>.login-container{max-width:400px; margin:100px auto; padding:40px; background:white; border-radius:20px; box-shadow:0 10px 40px rgba(0,0,0,0.1);}</style>
    """, unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown("<h2 style='text-align:center;'>🛕 Temple Management System</h2>", unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True):
                    if username and password:
                        try:
                            res = supabase.table('users').select('*').eq('username', username).execute()
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
                                st.error("Invalid credentials")
                        except Exception as e:
                            st.error(f"Error: {e}")
            st.info("🔑 Default: admin / admin123")
            st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# DASHBOARD PAGE
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
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💰 Income", f"{TEMPLE_CONFIG['currency']}{summary['income']:,.2f}")
    c2.metric("💸 Expenses", f"{TEMPLE_CONFIG['currency']}{summary['expenses']:,.2f}")
    c3.metric("🎁 Donations", f"{TEMPLE_CONFIG['currency']}{summary['donations']:,.2f}")
    c4.metric("💎 Balance", f"{TEMPLE_CONFIG['currency']}{summary['balance']:,.2f}")
    st.markdown("---")
    # News ticker
    if supabase:
        try:
            news = supabase.table('news_ticker').select('message').eq('is_active',True).order('priority', desc=True).execute()
            if news.data:
                st.markdown(f"<marquee style='background:#f0f0f0; padding:10px; border-radius:10px;'>{' | '.join([n['message'] for n in news.data])}</marquee>", unsafe_allow_html=True)
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
# DEVOTEE MANAGEMENT (FULL)
# ============================================================
def devotee_management_page():
    render_header()
    tab1, tab2, tab3 = st.tabs(["➕ Register","📋 View","📤 Bulk Import"])
    with tab1:
        with st.form("reg_devotee"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *")
                dob = st.date_input("DOB", value=date(1980,1,1))
                gender = st.selectbox("Gender", ["Male","Female","Other"])
                mobile = st.text_input("Mobile")
                email = st.text_input("Email")
            with col2:
                address = st.text_area("Address")
                natchathiram = st.selectbox("Natchathiram", ["--"]+NATCHATHIRAM_LIST)
                wedding = st.date_input("Wedding Day", value=None)
                occupation = st.text_input("Occupation")
                gothram = st.text_input("Gothram")
            photo = st.file_uploader("Photo", type=['jpg','png','jpeg'])
            if st.form_submit_button("Register"):
                if name:
                    dev_id = generate_unique_id('DEV')
                    photo_b64 = base64.b64encode(photo.getvalue()).decode() if photo else None
                    data = {
                        'devotee_id': dev_id, 'name': name, 'dob': dob.isoformat(), 'gender': gender,
                        'mobile_no': mobile, 'email': email, 'address': address,
                        'natchathiram': natchathiram if natchathiram!="--" else None,
                        'wedding_day': wedding.isoformat() if wedding else None,
                        'occupation': occupation, 'gothram': gothram, 'photo_url': photo_b64
                    }
                    supabase.table('devotees').insert(data).execute()
                    st.success(f"✅ {name} registered! ID: {dev_id}")
                    st.balloons()
    with tab2:
        search = st.text_input("🔍 Search by name/mobile")
        query = supabase.table('devotees').select('*').order('created_at', desc=True)
        if search:
            query = query.or_(f"name.ilike.%{search}%,mobile_no.ilike.%{search}%")
        res = query.execute()
        devotees = res.data if res.data else []
        st.write(f"**Total: {len(devotees)}**")
        for d in devotees:
            with st.expander(f"👤 {d['name']} - {d['devotee_id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📱 {d.get('mobile_no','N/A')}")
                    st.write(f"📧 {d.get('email','N/A')}")
                    st.write(f"🎂 {d.get('dob','N/A')}")
                with col2:
                    st.write(f"⭐ {d.get('natchathiram','N/A')}")
                    st.write(f"💒 {d.get('wedding_day','N/A')}")
                    st.write(f"🏠 {d.get('address','N/A')}")
                if d.get('photo_url'):
                    st.image(base64.b64decode(d['photo_url']), width=100)
                if st.button("🗑️ Delete", key=f"del_{d['id']}"):
                    supabase.table('devotees').delete().eq('id', d['id']).execute()
                    st.rerun()
    with tab3:
        st.markdown("Download template, fill, and upload.")
        template = pd.DataFrame([["Sample","1980-01-01","Male","9876543210","email@ex.com","Address","Ashwini","2005-05-10","Business","Vishwamitra"]],
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
                        supabase.table('devotees').insert({
                            'devotee_id': dev_id, 'name': str(row['Name']), 'dob': row['DOB'] if pd.notna(row['DOB']) else None,
                            'gender': str(row['Gender']), 'mobile_no': str(row['Mobile']), 'email': str(row['Email']),
                            'address': str(row['Address']), 'natchathiram': str(row['Natchathiram']),
                            'wedding_day': row['WeddingDay'] if pd.notna(row['WeddingDay']) else None,
                            'occupation': str(row['Occupation']), 'gothram': str(row['Gothram'])
                        }).execute()
                        success+=1
                    except: pass
                st.success(f"Imported {success} devotees")

# ============================================================
# BILLING SYSTEM (FULL)
# ============================================================
def billing_page():
    render_header()
    tab1, tab2 = st.tabs(["🧾 New Bill", "📋 History"])
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            manual_bill = st.text_input("Manual Bill No (optional)")
            book_no = st.text_input("Book No (optional)")
            bill_date = st.date_input("Date", date.today())
            pooja_types = supabase.table('pooja_types').select('name,amount').eq('is_active',True).execute()
            pooja_options = {p['name']: p['amount'] for p in pooja_types.data} if pooja_types.data else {}
            pooja = st.selectbox("Pooja Type", list(pooja_options.keys()))
            amount = pooja_options.get(pooja, 0)
            st.info(f"Amount: {TEMPLE_CONFIG['currency']}{amount}")
            payment = st.selectbox("Payment Mode", ["cash","card","upi","bank"])
        with col2:
            dev_type = st.radio("Devotee Type", ["Registered","Guest"])
            if dev_type == "Registered":
                search = st.text_input("Search devotee")
                if search:
                    res = supabase.table('devotees').select('id,name,mobile_no,address').or_(f"name.ilike.%{search}%,mobile_no.ilike.%{search}%").limit(10).execute()
                    if res.data:
                        selected = st.selectbox("Select", [f"{d['name']} - {d['mobile_no']}" for d in res.data])
                        dev_id = next(d['id'] for d in res.data if f"{d['name']} - {d['mobile_no']}"==selected)
                        dev = next(d for d in res.data if d['id']==dev_id)
                        st.write(f"**Name:** {dev['name']}\n**Mobile:** {dev.get('mobile_no','')}\n**Address:** {dev.get('address','')}")
                    else:
                        dev_id = None
                else:
                    dev_id = None
            else:
                dev_id = None
                guest_name = st.text_input("Guest Name *")
                guest_mobile = st.text_input("Mobile")
                guest_address = st.text_area("Address")
        if st.button("Generate Bill", type="primary"):
            if dev_type=="Guest" and not guest_name:
                st.error("Enter guest name")
            elif amount<=0:
                st.error("Invalid amount")
            else:
                bill_no = generate_unique_id('BILL')
                data = {
                    'bill_no': bill_no, 'manual_bill_no': manual_bill, 'bill_book_no': book_no,
                    'devotee_type': 'registered' if dev_type=="Registered" else 'guest',
                    'devotee_id': dev_id if dev_type=="Registered" else None,
                    'guest_name': guest_name if dev_type=="Guest" else None,
                    'guest_mobile': guest_mobile if dev_type=="Guest" else None,
                    'guest_address': guest_address if dev_type=="Guest" else None,
                    'pooja_type': pooja, 'amount': amount, 'bill_date': bill_date.isoformat(),
                    'payment_mode': payment
                }
                supabase.table('bills').insert(data).execute()
                st.success(f"Bill generated: {bill_no}")
                st.balloons()
                # Receipt display
                st.markdown(f"""
                <div style='border:2px solid #667eea; padding:20px; border-radius:10px; background:white;'>
                    <h3 style='text-align:center'>{TEMPLE_CONFIG['name']}</h3>
                    <p style='text-align:center'>{TEMPLE_CONFIG['trust']}<br>{TEMPLE_CONFIG['address']}</p>
                    <hr><h4 style='text-align:center'>RECEIPT</h4><hr>
                    <p><strong>Bill No:</strong> {bill_no}<br>
                    <strong>Date:</strong> {bill_date}<br>
                    <strong>Devotee:</strong> {guest_name if dev_type=='Guest' else dev['name'] if dev_id else 'N/A'}<br>
                    <strong>Pooja:</strong> {pooja}<br>
                    <strong>Amount:</strong> {TEMPLE_CONFIG['currency']}{amount:,.2f}</p>
                    <hr><p style='text-align:center'>🙏 Thank you! 🙏</p>
                </div>
                """, unsafe_allow_html=True)
    with tab2:
        from_date = st.date_input("From", date.today()-timedelta(30))
        to_date = st.date_input("To", date.today())
        bills = supabase.table('bills').select('*').gte('bill_date',from_date.isoformat()).lte('bill_date',to_date.isoformat()).order('bill_date', desc=True).execute()
        if bills.data:
            df = pd.DataFrame(bills.data)
            df['amount_display'] = df['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(df[['bill_no','bill_date','pooja_type','amount_display','payment_mode']])
            csv = df.to_csv(index=False).encode()
            st.download_button("📥 Export CSV", csv, "bills.csv")
        else:
            st.info("No bills")

# ============================================================
# POOJA MANAGEMENT (FULL)
# ============================================================
def pooja_management_page():
    render_header()
    tab1, tab2, tab3 = st.tabs(["🙏 Pooja Types","📅 Daily Schedule","📋 Yearly Subscriptions"])
    with tab1:
        with st.expander("➕ Add New Pooja Type"):
            with st.form("add_pt"):
                name = st.text_input("Name")
                amount = st.number_input("Amount", min_value=0.0)
                duration = st.text_input("Duration (e.g., 30 min)")
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
                    supabase.table('pooja_types').delete().eq('id', p['id']).execute()
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
                p_date = st.date_input("Date", date.today())
                priest = st.text_input("Priest Name")
            notes = st.text_area("Notes")
            if st.form_submit_button("Schedule"):
                if p_name:
                    supabase.table('daily_pooja').insert({'pooja_name':p_name,'pooja_time':p_time,'pooja_date':p_date.isoformat(),'priest_name':priest,'notes':notes}).execute()
                    st.rerun()
        view_date = st.date_input("View date", date.today())
        schedule = supabase.table('daily_pooja').select('*').eq('pooja_date',view_date.isoformat()).execute()
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
    with tab3:
        devotees = supabase.table('devotees').select('id,name,mobile_no').execute()
        if devotees.data:
            dev_opt = {f"{d['name']} - {d.get('mobile_no','')}": d['id'] for d in devotees.data}
            selected = st.selectbox("Select Devotee", list(dev_opt.keys()))
            dev_id = dev_opt[selected]
            with st.form("add_sub"):
                pooja_type = st.selectbox("Pooja", [p['name'] for p in supabase.table('pooja_types').select('name').execute().data or []])
                pooja_date = st.date_input("Pooja Date")
                amount = st.number_input("Amount", min_value=0.0)
                desc = st.text_area("Description")
                if st.form_submit_button("Add Subscription"):
                    supabase.table('devotee_yearly_pooja').insert({'devotee_id':dev_id,'pooja_type':pooja_type,'pooja_date':pooja_date.isoformat(),'amount':amount,'description':desc}).execute()
                    st.rerun()
            subs = supabase.table('devotee_yearly_pooja').select('*').eq('devotee_id',dev_id).execute()
            if subs.data:
                for sub in subs.data:
                    col1, col2 = st.columns([3,1])
                    col1.write(f"{sub['pooja_type']} on {sub.get('pooja_date','')} - {TEMPLE_CONFIG['currency']}{sub.get('amount',0)}")
                    if col2.button("✅ Complete" if not sub.get('is_completed') else "🔄 Undo", key=f"sub_{sub['id']}"):
                        supabase.table('devotee_yearly_pooja').update({'is_completed': not sub.get('is_completed')}).eq('id',sub['id']).execute()
                        st.rerun()
        else:
            st.warning("No devotees found")

# ============================================================
# EXPENSE TRACKING (FULL)
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
                date_exp = st.date_input("Date", date.today())
            with col2:
                bill_no = st.text_input("Bill/Invoice No")
                vendor = st.text_input("Vendor")
            desc = st.text_area("Description")
            if st.form_submit_button("Add"):
                if exp_type and amount>0:
                    supabase.table('expenses').insert({
                        'expense_type':exp_type,'amount':amount,'description':desc,
                        'expense_date':date_exp.isoformat(),'bill_no':bill_no,'vendor_name':vendor
                    }).execute()
                    st.success("Expense added")
                    st.rerun()
    with tab2:
        from_d = st.date_input("From", date.today()-timedelta(30))
        to_d = st.date_input("To", date.today())
        exps = supabase.table('expenses').select('*').gte('expense_date',from_d.isoformat()).lte('expense_date',to_d.isoformat()).order('expense_date', desc=True).execute()
        if exps.data:
            df = pd.DataFrame(exps.data)
            total = df['amount'].sum()
            st.metric("Total Expenses", f"{TEMPLE_CONFIG['currency']}{total:,.2f}")
            st.dataframe(df[['expense_date','expense_type','amount','description','vendor_name']])
            csv = df.to_csv(index=False).encode()
            st.download_button("📥 Export", csv, "expenses.csv")
        else:
            st.info("No expenses")

# ============================================================
# DONATIONS (FULL)
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
                date_don = st.date_input("Date", date.today())
            purpose = st.text_area("Purpose")
            payment = st.selectbox("Payment Mode", ["cash","card","upi","bank"])
            if st.form_submit_button("Record"):
                if donor and amount>0:
                    don_no = generate_unique_id('DON')
                    supabase.table('donations').insert({
                        'donation_no':don_no,'donor_name':donor,'donor_mobile':mobile,'donor_email':email,
                        'amount':amount,'donation_type':don_type,'purpose':purpose,
                        'donation_date':date_don.isoformat(),'payment_mode':payment
                    }).execute()
                    st.success(f"Donation recorded! Receipt: {don_no}")
                    st.balloons()
    with tab2:
        from_d = st.date_input("From", date.today()-timedelta(365))
        to_d = st.date_input("To", date.today())
        don = supabase.table('donations').select('*').gte('donation_date',from_d.isoformat()).lte('donation_date',to_d.isoformat()).order('donation_date', desc=True).execute()
        if don.data:
            df = pd.DataFrame(don.data)
            total = df['amount'].sum()
            st.metric("Total Donations", f"{TEMPLE_CONFIG['currency']}{total:,.2f}")
            st.dataframe(df[['donation_no','donation_date','donor_name','donation_type','amount','payment_mode']])
            csv = df.to_csv(index=False).encode()
            st.download_button("📥 Export", csv, "donations.csv")
        else:
            st.info("No donations")

# ============================================================
# ASSET MANAGEMENT (FULL)
# ============================================================
def assets_page():
    render_header()
    tab1, tab2 = st.tabs(["🏷️ Add Asset","📋 List"])
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
                date_don = st.date_input("Donation/Purchase Date", date.today())
                cost = st.number_input("Cost", min_value=0.0)
                location = st.text_input("Location")
            desc = st.text_area("Description")
            status = st.selectbox("Status", ["active","maintenance","damaged","donated"])
            if st.form_submit_button("Add"):
                if tag and name:
                    supabase.table('assets').insert({
                        'asset_tag':tag,'asset_name':name,'category':category,'serial_no':serial,
                        'donor_name':donor,'donation_date':date_don.isoformat(),'purchase_cost':cost,
                        'location':location,'description':desc,'status':status
                    }).execute()
                    st.success("Asset added")
                    st.rerun()
    with tab2:
        search = st.text_input("Search")
        query = supabase.table('assets').select('*').order('created_at', desc=True)
        if search:
            query = query.or_(f"asset_tag.ilike.%{search}%,asset_name.ilike.%{search}%,donor_name.ilike.%{search}%")
        assets = query.execute()
        if assets.data:
            for a in assets.data:
                with st.expander(f"{a['asset_tag']} - {a['asset_name']}"):
                    st.write(f"**Category:** {a.get('category','')}")
                    st.write(f"**Cost:** {TEMPLE_CONFIG['currency']}{a.get('purchase_cost',0):,.2f}")
                    st.write(f"**Donor:** {a.get('donor_name','')}")
                    st.write(f"**Location:** {a.get('location','')}")
                    st.write(f"**Status:** {a.get('status','')}")
                    if st.button("Delete", key=f"del_asset_{a['id']}"):
                        supabase.table('assets').delete().eq('id', a['id']).execute()
                        st.rerun()
        else:
            st.info("No assets")

# ============================================================
# REPORTS (FULL)
# ============================================================
def reports_page():
    render_header()
    report_type = st.selectbox("Report Type", ["Financial Summary","Devotee Report","Pooja Income","Expense Report","Donation Report"])
    from_date = st.date_input("From", date.today()-timedelta(30))
    to_date = st.date_input("To", date.today())
    if report_type == "Financial Summary":
        summary = get_financial_summary(from_date, to_date)
        st.metric("Income", f"{TEMPLE_CONFIG['currency']}{summary['income']:,.2f}")
        st.metric("Expenses", f"{TEMPLE_CONFIG['currency']}{summary['expenses']:,.2f}")
        st.metric("Donations", f"{TEMPLE_CONFIG['currency']}{summary['donations']:,.2f}")
        st.metric("Balance", f"{TEMPLE_CONFIG['currency']}{summary['balance']:,.2f}")
    elif report_type == "Devotee Report":
        devs = supabase.table('devotees').select('devotee_id,name,mobile_no,email,created_at').execute()
        if devs.data:
            df = pd.DataFrame(devs.data)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode()
            st.download_button("📥 Download", csv, "devotees.csv")
    elif report_type == "Pooja Income":
        bills = supabase.table('bills').select('pooja_type,amount').gte('bill_date',from_date.isoformat()).lte('bill_date',to_date.isoformat()).execute()
        if bills.data:
            df = pd.DataFrame(bills.data)
            summary = df.groupby('pooja_type')['amount'].sum().reset_index()
            summary['amount'] = summary['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(summary)
    elif report_type == "Expense Report":
        exps = supabase.table('expenses').select('expense_type,amount').gte('expense_date',from_date.isoformat()).lte('expense_date',to_date.isoformat()).execute()
        if exps.data:
            df = pd.DataFrame(exps.data)
            summary = df.groupby('expense_type')['amount'].sum().reset_index()
            summary['amount'] = summary['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(summary)
    elif report_type == "Donation Report":
        don = supabase.table('donations').select('donation_type,amount').gte('donation_date',from_date.isoformat()).lte('donation_date',to_date.isoformat()).execute()
        if don.data:
            df = pd.DataFrame(don.data)
            summary = df.groupby('donation_type')['amount'].sum().reset_index()
            summary['amount'] = summary['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(summary)

# ============================================================
# SETTINGS (FULL)
# ============================================================
def settings_page():
    render_header()
    tab1, tab2, tab3, tab4 = st.tabs(["🏛️ Temple Info","📢 News Ticker","💸 Expense Types","👤 Profile"])
    with tab1:
        with st.form("temple_info"):
            name = st.text_input("Temple Name", TEMPLE_CONFIG['name'])
            trust = st.text_input("Trust", TEMPLE_CONFIG['trust'])
            addr = st.text_area("Address", TEMPLE_CONFIG['address'])
            phone = st.text_input("Phone", TEMPLE_CONFIG['phone'])
            email = st.text_input("Email", TEMPLE_CONFIG['email'])
            tagline = st.text_input("Tagline", TEMPLE_CONFIG['tagline'])
            logo = st.file_uploader("Logo", type=['jpg','png'])
            if st.form_submit_button("Save"):
                TEMPLE_CONFIG.update({'name':name,'trust':trust,'address':addr,'phone':phone,'email':email,'tagline':tagline})
                if logo:
                    set_temple_setting('temple_logo', base64.b64encode(logo.getvalue()).decode())
                st.success("Saved")
                st.rerun()
    with tab2:
        with st.form("add_news"):
            msg = st.text_input("News Message")
            prio = st.slider("Priority",0,10,0)
            if st.form_submit_button("Add"):
                if msg:
                    supabase.table('news_ticker').insert({'message':msg,'priority':prio}).execute()
                    st.rerun()
        news = supabase.table('news_ticker').select('*').order('priority', desc=True).execute()
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
    with tab3:
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
    with tab4:
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
# USER MANAGEMENT (ADMIN ONLY)
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
                        'username':uname, 'password_hash':hash_password(pwd), 'role':role,
                        'full_name':full, 'email':email
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
            "Asset Management": assets_page,
            "Reports": reports_page,
            "Settings": settings_page,
            "User Management": user_management_page
        }
        current = st.session_state.get('current_page', 'Dashboard')
        pages.get(current, dashboard_page)()

if __name__ == "__main__":
    main()
