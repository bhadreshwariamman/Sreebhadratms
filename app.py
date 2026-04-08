# app.py - Temple Management System with Supabase
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import base64
import time
import hashlib
from typing import Optional, Dict, List, Any
import asyncio

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
from supabase import create_client, Client

# Initialize Supabase client
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
# TEMPLE CONFIGURATION
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

# ============================================================
# DATABASE HELPER FUNCTIONS
# ============================================================

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hash_value: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hash_value

def generate_unique_id(prefix: str = 'DEV') -> str:
    """Generate unique ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_part = str(uuid.uuid4())[:8].upper()
    return f"{prefix}{timestamp}{unique_part}"

def get_temple_setting(key: str) -> str:
    """Get temple setting from Supabase"""
    if not supabase:
        return ''
    try:
        response = supabase.table('temple_settings').select('value').eq('key', key).execute()
        if response.data:
            return response.data[0]['value']
        return ''
    except Exception as e:
        st.error(f"Error fetching setting: {str(e)}")
        return ''

def set_temple_setting(key: str, value: str):
    """Set temple setting in Supabase"""
    if not supabase:
        return
    try:
        # Check if exists
        response = supabase.table('temple_settings').select('id').eq('key', key).execute()
        if response.data:
            supabase.table('temple_settings').update({'value': value, 'updated_at': datetime.now().isoformat()}).eq('key', key).execute()
        else:
            supabase.table('temple_settings').insert({'key': key, 'value': value}).execute()
    except Exception as e:
        st.error(f"Error saving setting: {str(e)}")

def get_todays_birthdays() -> List[str]:
    """Get today's birthdays from Supabase"""
    if not supabase:
        return []
    today = date.today()
    birthdays = []
    
    try:
        # Devotees birthdays
        response = supabase.table('devotees').select('name').execute()
        for devotee in response.data:
            if devotee.get('dob'):
                try:
                    dob = datetime.strptime(devotee['dob'], '%Y-%m-%d').date()
                    if dob.month == today.month and dob.day == today.day:
                        birthdays.append(f"🎂 {devotee['name']} (Devotee)")
                except:
                    pass
        
        # Family members birthdays
        response = supabase.table('family_members').select('name, dob').execute()
        for member in response.data:
            if member.get('dob'):
                try:
                    dob = datetime.strptime(member['dob'], '%Y-%m-%d').date()
                    if dob.month == today.month and dob.day == today.day:
                        birthdays.append(f"🎂 {member['name']} (Family)")
                except:
                    pass
    except Exception as e:
        st.error(f"Error fetching birthdays: {str(e)}")
    
    return birthdays

def get_todays_anniversaries() -> List[str]:
    """Get today's anniversaries from Supabase"""
    if not supabase:
        return []
    today = date.today()
    anniversaries = []
    
    try:
        response = supabase.table('devotees').select('name, wedding_day').execute()
        for devotee in response.data:
            if devotee.get('wedding_day'):
                try:
                    wedding = datetime.strptime(devotee['wedding_day'], '%Y-%m-%d').date()
                    if wedding.month == today.month and wedding.day == today.day:
                        anniversaries.append(f"💒 {devotee['name']} (Wedding Anniversary)")
                except:
                    pass
    except Exception as e:
        st.error(f"Error fetching anniversaries: {str(e)}")
    
    return anniversaries

def get_financial_summary(start_date: date, end_date: date) -> Dict:
    """Get financial summary from Supabase"""
    if not supabase:
        return {'income': 0, 'expenses': 0, 'donations': 0, 'balance': 0}
    
    try:
        # Get income from bills
        income_response = supabase.table('bills').select('amount').gte('bill_date', start_date.isoformat()).lte('bill_date', end_date.isoformat()).execute()
        total_income = sum(item.get('amount', 0) for item in income_response.data) if income_response.data else 0
        
        # Get expenses
        expense_response = supabase.table('expenses').select('amount').gte('expense_date', start_date.isoformat()).lte('expense_date', end_date.isoformat()).execute()
        total_expense = sum(item.get('amount', 0) for item in expense_response.data) if expense_response.data else 0
        
        # Get donations
        donation_response = supabase.table('donations').select('amount').gte('donation_date', start_date.isoformat()).lte('donation_date', end_date.isoformat()).execute()
        total_donations = sum(item.get('amount', 0) for item in donation_response.data) if donation_response.data else 0
        
        return {
            'income': total_income,
            'expenses': total_expense,
            'donations': total_donations,
            'balance': total_income + total_donations - total_expense
        }
    except Exception as e:
        st.error(f"Error fetching financial summary: {str(e)}")
        return {'income': 0, 'expenses': 0, 'donations': 0, 'balance': 0}

# ============================================================
# UI COMPONENTS
# ============================================================

def render_header():
    """Render page header with temple branding"""
    logo = get_temple_setting('temple_logo')
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        if logo:
            st.image(logo, width=100)
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='color: white; margin: 0;'>🛕 {TEMPLE_CONFIG['name']}</h1>
            <p style='color: #f0f0f0; margin: 5px 0;'>{TEMPLE_CONFIG['trust']}</p>
            <p style='color: #e0e0e0; margin: 5px 0;'>📍 {TEMPLE_CONFIG['address']} | 📞 {TEMPLE_CONFIG['phone']} | ✉ {TEMPLE_CONFIG['email']}</p>
            <p style='color: #ffd700; margin: 5px 0; font-style: italic;'>{TEMPLE_CONFIG['tagline']}</p>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar with navigation"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 10px;'>
            <h2 style='color: #667eea;'>🛕 Temple MS</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; margin: 10px 0; text-align: center;'>
            <p style='color: white; margin: 0;'>👤 {st.session_state.get('username', 'Guest')}</p>
            <p style='color: #ffd700; margin: 5px 0 0 0; font-size: 12px;'>{st.session_state.get('role', 'user')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu
        pages = {
            "Dashboard": "🏠",
            "Devotee Management": "👥",
            "Billing System": "🧾",
            "Pooja Management": "🙏",
            "Expense Tracking": "💰",
            "Donations": "🎁",
            "Asset Management": "🏷️",
            "Reports": "📊",
            "Settings": "⚙️",
            "User Management": "👥"
        }
        
        for page, icon in pages.items():
            if page == "User Management" and st.session_state.get('role') != 'admin':
                continue
            if st.button(f"{icon} {page}", key=page, use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            for key in ['logged_in', 'username', 'role', 'user_id', 'current_page']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():
    """Login page"""
    if not supabase:
        st.error("⚠️ Database connection failed. Please check your Supabase configuration.")
        return
    
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center;'>🛕 Temple Management System</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #666;'>Please login to continue</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        try:
                            response = supabase.table('users').select('*').eq('username', username).execute()
                            
                            if response.data and verify_password(password, response.data[0]['password_hash']):
                                st.session_state.logged_in = True
                                st.session_state.username = response.data[0]['username']
                                st.session_state.role = response.data[0]['role']
                                st.session_state.user_id = response.data[0]['id']
                                st.session_state.current_page = "Dashboard"
                                st.success("Login successful!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Invalid username or password")
                        except Exception as e:
                            st.error(f"Login error: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# DASHBOARD PAGE
# ============================================================

def dashboard_page():
    """Dashboard page"""
    render_header()
    
    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        period = st.selectbox("Period", ["Today", "This Week", "This Month", "This Year", "Custom"])
    
    today = date.today()
    if period == "Today":
        start_date = end_date = today
    elif period == "This Week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "This Month":
        start_date = today.replace(day=1)
        end_date = today
    elif period == "This Year":
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", today - timedelta(days=30))
        with col2:
            end_date = st.date_input("To Date", today)
    
    # Financial summary
    summary = get_financial_summary(start_date, end_date)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Income", f"{TEMPLE_CONFIG['currency']}{summary['income']:,.2f}")
    with col2:
        st.metric("💸 Total Expenses", f"{TEMPLE_CONFIG['currency']}{summary['expenses']:,.2f}")
    with col3:
        st.metric("🎁 Donations", f"{TEMPLE_CONFIG['currency']}{summary['donations']:,.2f}")
    with col4:
        st.metric("💎 Net Balance", f"{TEMPLE_CONFIG['currency']}{summary['balance']:,.2f}", 
                 delta="Profit" if summary['balance'] > 0 else "Loss")
    
    st.markdown("---")
    
    # News ticker
    if supabase:
        try:
            response = supabase.table('news_ticker').select('message').eq('is_active', True).order('priority', desc=True).execute()
            news_items = [item['message'] for item in response.data] if response.data else []
        except:
            news_items = []
    
    if news_items:
        news_text = " | ".join(news_items)
        st.markdown(f"""
        <div style='background: #f0f0f0; padding: 10px; border-radius: 10px; margin: 10px 0; overflow: hidden;'>
            <marquee behavior='scroll' direction='left'>{news_text}</marquee>
        </div>
        """, unsafe_allow_html=True)
    
    # Two column layout for events
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎂 Today's Birthdays")
        birthdays = get_todays_birthdays()
        if birthdays:
            for birthday in birthdays:
                st.info(birthday)
        else:
            st.info("No birthdays today")
        
        st.subheader("💒 Today's Anniversaries")
        anniversaries = get_todays_anniversaries()
        if anniversaries:
            for anniversary in anniversaries:
                st.success(anniversary)
        else:
            st.info("No anniversaries today")
    
    with col2:
        st.subheader("🙏 Today's Pooja Schedule")
        if supabase:
            try:
                response = supabase.table('daily_pooja').select('*').eq('pooja_date', today.isoformat()).order('pooja_time').execute()
                poojas = response.data if response.data else []
            except:
                poojas = []
        
        if poojas:
            for pooja in poojas:
                status_icon = "✅" if pooja.get('status') == 'completed' else "⏳"
                st.markdown(f"{status_icon} **{pooja['pooja_name']}** - {pooja.get('pooja_time', 'Time TBD')}")
                if pooja.get('priest_name'):
                    st.caption(f"Priest: {pooja['priest_name']}")
        else:
            st.info("No poojas scheduled for today")
    
    # Recent transactions
    st.markdown("---")
    st.subheader("📋 Recent Transactions")
    
    if supabase:
        try:
            response = supabase.table('bills').select('bill_no, bill_date, pooja_type, amount').order('created_at', desc=True).limit(5).execute()
            if response.data:
                bills_df = pd.DataFrame(response.data)
                bills_df['amount'] = bills_df['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
                st.dataframe(bills_df, use_container_width=True)
            else:
                st.info("No recent transactions")
        except:
            st.info("No recent transactions")

# ============================================================
# DEVOTEE MANAGEMENT PAGE
# ============================================================

def devotee_management_page():
    """Devotee management page"""
    render_header()
    
    tab1, tab2, tab3 = st.tabs(["➕ Register New Devotee", "📋 View All Devotees", "📤 Bulk Import"])
    
    with tab1:
        with st.form("register_devotee", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name *", placeholder="Enter full name")
                dob = st.date_input("Date of Birth", value=date(1980, 1, 1))
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                mobile = st.text_input("Mobile Number", placeholder="10-digit number")
                email = st.text_input("Email Address")
                
            with col2:
                address = st.text_area("Address", height=100)
                natchathiram = st.text_input("Natchathiram (Star)")
                wedding_day = st.date_input("Wedding Anniversary", value=None)
                occupation = st.text_input("Occupation")
                gothram = st.text_input("Gothram")
            
            photo = st.file_uploader("Upload Photo", type=['jpg', 'jpeg', 'png'])
            
            submitted = st.form_submit_button("Register Devotee", use_container_width=True)
            
            if submitted:
                if not name:
                    st.error("Please enter devotee name")
                elif not supabase:
                    st.error("Database not connected")
                else:
                    devotee_id = generate_unique_id('DEV')
                    
                    # Convert photo to base64 if uploaded
                    photo_base64 = None
                    if photo:
                        photo_base64 = base64.b64encode(photo.getvalue()).decode()
                    
                    try:
                        data = {
                            'devotee_id': devotee_id,
                            'name': name,
                            'dob': dob.isoformat(),
                            'gender': gender,
                            'mobile_no': mobile,
                            'email': email,
                            'address': address,
                            'natchathiram': natchathiram,
                            'wedding_day': wedding_day.isoformat() if wedding_day else None,
                            'occupation': occupation,
                            'gothram': gothram,
                            'photo_url': photo_base64
                        }
                        
                        response = supabase.table('devotees').insert(data).execute()
                        
                        if response.data:
                            st.success(f"✅ Devotee {name} registered successfully with ID: {devotee_id}")
                            st.balloons()
                        else:
                            st.error("Failed to register devotee")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab2:
        # Search and filter
        col1, col2, col3 = st.columns(3)
        with col1:
            search_name = st.text_input("Search by Name", placeholder="Enter name...")
        with col2:
            search_mobile = st.text_input("Search by Mobile", placeholder="Enter mobile...")
        with col3:
            show_all = st.checkbox("Show All", value=True)
        
        # Fetch devotees
        if supabase:
            try:
                query = supabase.table('devotees').select('*').order('created_at', desc=True)
                
                if not show_all:
                    if search_name:
                        query = query.ilike('name', f'%{search_name}%')
                    if search_mobile:
                        query = query.ilike('mobile_no', f'%{search_mobile}%')
                
                response = query.execute()
                devotees = response.data if response.data else []
            except Exception as e:
                st.error(f"Error fetching devotees: {str(e)}")
                devotees = []
        else:
            devotees = []
        
        if devotees:
            st.info(f"Total Devotees: {len(devotees)}")
            
            for devotee in devotees:
                with st.expander(f"👤 {devotee['name']} - {devotee['devotee_id']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**📱 Mobile:** {devotee.get('mobile_no', 'N/A')}")
                        st.markdown(f"**📧 Email:** {devotee.get('email', 'N/A')}")
                        st.markdown(f"**🎂 DOB:** {devotee.get('dob', 'N/A')}")
                        st.markdown(f"**⭐ Star:** {devotee.get('natchathiram', 'N/A')}")
                    
                    with col2:
                        st.markdown(f"**💒 Wedding:** {devotee.get('wedding_day', 'N/A')}")
                        st.markdown(f"**💼 Occupation:** {devotee.get('occupation', 'N/A')}")
                        st.markdown(f"**🙏 Gothram:** {devotee.get('gothram', 'N/A')}")
                        st.markdown(f"**🏠 Address:** {devotee.get('address', 'N/A')}")
                    
                    with col3:
                        if devotee.get('photo_url'):
                            try:
                                st.image(base64.b64decode(devotee['photo_url']), width=100)
                            except:
                                st.image(devotee['photo_url'], width=100)
                    
                    # Actions
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("✏️ Edit", key=f"edit_{devotee['id']}"):
                            st.session_state[f"edit_devotee_{devotee['id']}"] = True
                    with col2:
                        if st.button("👨‍👩‍👧 Family", key=f"family_{devotee['id']}"):
                            st.session_state[f"show_family_{devotee['id']}"] = True
                    with col3:
                        if st.button("🙏 Poojas", key=f"poojas_{devotee['id']}"):
                            st.session_state[f"show_poojas_{devotee['id']}"] = True
                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_{devotee['id']}"):
                            if supabase:
                                try:
                                    supabase.table('devotees').delete().eq('id', devotee['id']).execute()
                                    st.success("Devotee deleted successfully")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting: {str(e)}")
        else:
            st.info("No devotees found")
    
    with tab3:
        st.markdown("### 📤 Bulk Import Devotees")
        st.markdown("Upload an Excel/CSV file with the following columns:")
        st.code("""
        Name, DOB, Gender, Mobile, Email, Address, Natchathiram, WeddingDay, Occupation, Gothram
        """)
        
        template_data = {
            'Name': ['Sample Name'],
            'DOB': ['1980-01-01'],
            'Gender': ['Male'],
            'Mobile': ['9876543210'],
            'Email': ['sample@example.com'],
            'Address': ['Sample Address'],
            'Natchathiram': ['Ashwini'],
            'WeddingDay': ['2005-05-10'],
            'Occupation': ['Business'],
            'Gothram': ['Vishwamitra']
        }
        template_df = pd.DataFrame(template_data)
        
        csv = template_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Template", csv, "devotee_template.csv", "text/csv")
        
        uploaded_file = st.file_uploader("Choose file", type=['csv', 'xlsx', 'xls'])
        
        if uploaded_file and supabase:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.dataframe(df.head(10), use_container_width=True)
                
                if st.button("Import Data", type="primary"):
                    success_count = 0
                    error_count = 0
                    
                    for _, row in df.iterrows():
                        try:
                            devotee_id = generate_unique_id('DEV')
                            data = {
                                'devotee_id': devotee_id,
                                'name': str(row.get('Name', '')),
                                'dob': row.get('DOB') if pd.notna(row.get('DOB')) else None,
                                'gender': str(row.get('Gender', '')),
                                'mobile_no': str(row.get('Mobile', '')) if pd.notna(row.get('Mobile')) else '',
                                'email': str(row.get('Email', '')),
                                'address': str(row.get('Address', '')),
                                'natchathiram': str(row.get('Natchathiram', '')),
                                'wedding_day': row.get('WeddingDay') if pd.notna(row.get('WeddingDay')) else None,
                                'occupation': str(row.get('Occupation', '')),
                                'gothram': str(row.get('Gothram', ''))
                            }
                            
                            supabase.table('devotees').insert(data).execute()
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            st.error(f"Error importing row: {str(e)}")
                    
                    st.success(f"✅ Import completed! Success: {success_count}, Errors: {error_count}")
                    st.balloons()
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

# ============================================================
# BILLING PAGE
# ============================================================

def billing_page():
    """Billing page"""
    render_header()
    
    tab1, tab2 = st.tabs(["🧾 Generate Bill", "📋 Bill History"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Bill Details")
            manual_bill_no = st.text_input("Manual Bill Number (Optional)")
            bill_book_no = st.text_input("Bill Book Number (Optional)")
            bill_date = st.date_input("Bill Date", value=date.today())
            
            # Fetch pooja types
            if supabase:
                try:
                    response = supabase.table('pooja_types').select('id, name, amount').eq('is_active', True).execute()
                    poojas = response.data if response.data else []
                except:
                    poojas = []
            
            if poojas:
                pooja_options = {pooja['name']: pooja['amount'] for pooja in poojas}
                selected_pooja = st.selectbox("Select Pooja Type", list(pooja_options.keys()))
                amount = pooja_options[selected_pooja]
                st.info(f"Amount: {TEMPLE_CONFIG['currency']}{amount:,.2f}")
            else:
                selected_pooja = st.text_input("Pooja Type")
                amount = st.number_input("Amount", min_value=0.0, step=10.0)
            
            payment_mode = st.selectbox("Payment Mode", ["cash", "card", "upi", "bank transfer"])
        
        with col2:
            st.subheader("Devotee Information")
            devotee_type = st.radio("Devotee Type", ["Registered Devotee", "Guest"])
            
            if devotee_type == "Registered Devotee":
                # Search devotee
                search_term = st.text_input("Search Devotee by Name or Mobile")
                if search_term and supabase:
                    try:
                        response = supabase.table('devotees').select('id, name, mobile_no, address').or_(f'name.ilike.%{search_term}%,mobile_no.ilike.%{search_term}%').limit(10).execute()
                        devotees = response.data if response.data else []
                    except:
                        devotees = []
                    
                    if devotees:
                        devotee_options = {f"{d['name']} - {d.get('mobile_no', 'N/A')}": d['id'] for d in devotees}
                        selected_devotee = st.selectbox("Select Devotee", list(devotee_options.keys()))
                        devotee_id = devotee_options[selected_devotee]
                        
                        # Get devotee details
                        try:
                            response = supabase.table('devotees').select('*').eq('id', devotee_id).execute()
                            devotee = response.data[0] if response.data else None
                        except:
                            devotee = None
                        
                        if devotee:
                            st.markdown(f"**Name:** {devotee['name']}")
                            st.markdown(f"**Mobile:** {devotee.get('mobile_no', 'N/A')}")
                            st.markdown(f"**Address:** {devotee.get('address', 'N/A')}")
                    else:
                        st.warning("No devotees found")
                        devotee_id = None
                else:
                    devotee_id = None
            else:
                devotee_id = None
                guest_name = st.text_input("Guest Name *")
                guest_mobile = st.text_input("Guest Mobile")
                guest_address = st.text_area("Guest Address")
        
        # Generate bill button
        if st.button("Generate Bill", type="primary", use_container_width=True):
            if devotee_type == "Guest" and not guest_name:
                st.error("Please enter guest name")
            elif amount <= 0:
                st.error("Please enter valid amount")
            elif not supabase:
                st.error("Database not connected")
            else:
                bill_no = generate_unique_id('BILL')
                
                try:
                    data = {
                        'bill_no': bill_no,
                        'manual_bill_no': manual_bill_no,
                        'bill_book_no': bill_book_no,
                        'devotee_type': devotee_type.lower(),
                        'devotee_id': devotee_id if devotee_type == "Registered Devotee" else None,
                        'guest_name': guest_name if devotee_type == "Guest" else None,
                        'guest_mobile': guest_mobile if devotee_type == "Guest" else None,
                        'guest_address': guest_address if devotee_type == "Guest" else None,
                        'pooja_type': selected_pooja,
                        'amount': amount,
                        'bill_date': bill_date.isoformat(),
                        'payment_mode': payment_mode
                    }
                    
                    response = supabase.table('bills').insert(data).execute()
                    
                    if response.data:
                        st.success(f"✅ Bill generated successfully! Bill No: {bill_no}")
                        st.balloons()
                        
                        # Display bill receipt
                        st.markdown("---")
                        st.subheader("📄 Bill Receipt")
                        
                        devotee_name = guest_name if devotee_type == "Guest" else (devotee['name'] if devotee_id else 'N/A')
                        
                        receipt_html = f"""
                        <div style='border: 2px solid #667eea; padding: 20px; border-radius: 10px; background: white;'>
                            <div style='text-align: center;'>
                                <h2>{TEMPLE_CONFIG['name']}</h2>
                                <p>{TEMPLE_CONFIG['trust']}</p>
                                <p>{TEMPLE_CONFIG['address']}</p>
                                <p>📞 {TEMPLE_CONFIG['phone']} | ✉ {TEMPLE_CONFIG['email']}</p>
                                <hr>
                                <h3>BILL / RECEIPT</h3>
                                <hr>
                            </div>
                            <table style='width: 100%; margin: 20px 0;'>
                                <tr><td><strong>Bill No:</strong></td><td>{bill_no}</td></tr>
                                <tr><td><strong>Date:</strong></td><td>{bill_date}</td></tr>
                                <tr><td><strong>Devotee:</strong></td><td>{devotee_name}</td></tr>
                                <tr><td><strong>Pooja Type:</strong></td><td>{selected_pooja}</td></tr>
                                <tr><td><strong>Amount:</strong></td><td><h3>{TEMPLE_CONFIG['currency']}{amount:,.2f}</h3></td></tr>
                            </table>
                            <hr>
                            <div style='text-align: center;'>
                                <p>🙏 Thank you for your contribution! 🙏</p>
                                <p>{TEMPLE_CONFIG['tagline']}</p>
                            </div>
                        </div>
                        """
                        st.markdown(receipt_html, unsafe_allow_html=True)
                    else:
                        st.error("Failed to generate bill")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Bill History")
        
        col1, col2 = st.columns(2)
        with col1:
            from_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
        with col2:
            to_date = st.date_input("To Date", value=date.today())
        
        if supabase:
            try:
                response = supabase.table('bills').select('*').gte('bill_date', from_date.isoformat()).lte('bill_date', to_date.isoformat()).order('bill_date', desc=True).execute()
                bills = response.data if response.data else []
            except:
                bills = []
        
        if bills:
            bills_df = pd.DataFrame(bills)
            
            # Add devotee names
            def get_devotee_name(row):
                if row.get('devotee_type') == 'guest':
                    return row.get('guest_name', 'N/A')
                elif row.get('devotee_id'):
                    try:
                        response = supabase.table('devotees').select('name').eq('id', row['devotee_id']).execute()
                        if response.data:
                            return response.data[0]['name']
                    except:
                        pass
                return 'Unknown'
            
            bills_df['devotee_name'] = bills_df.apply(get_devotee_name, axis=1)
            bills_df['amount'] = bills_df['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            
            display_df = bills_df[['bill_no', 'bill_date', 'devotee_name', 'pooja_type', 'amount', 'payment_mode']]
            st.dataframe(display_df, use_container_width=True)
            
            # Export option
            csv = bills_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export to CSV", csv, "bills_export.csv", "text/csv")
        else:
            st.info("No bills found for the selected period")

# ============================================================
# POOJA MANAGEMENT PAGE
# ============================================================

def pooja_management_page():
    """Pooja management page"""
    render_header()
    
    tab1, tab2, tab3 = st.tabs(["🙏 Pooja Types", "📅 Daily Schedule", "📋 Yearly Subscriptions"])
    
    with tab1:
        st.subheader("Manage Pooja Types")
        
        # Add new pooja type
        with st.expander("➕ Add New Pooja Type"):
            with st.form("add_pooja"):
                col1, col2 = st.columns(2)
                with col1:
                    pooja_name = st.text_input("Pooja Name")
                with col2:
                    pooja_amount = st.number_input("Amount", min_value=0.0, step=10.0)
                
                pooja_duration = st.text_input("Duration (e.g., 30 min)")
                pooja_description = st.text_area("Description")
                
                if st.form_submit_button("Add Pooja"):
                    if pooja_name and supabase:
                        try:
                            data = {
                                'name': pooja_name,
                                'amount': pooja_amount,
                                'duration': pooja_duration,
                                'description': pooja_description
                            }
                            supabase.table('pooja_types').insert(data).execute()
                            st.success(f"✅ Pooja '{pooja_name}' added successfully")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        # List existing pooja types
        if supabase:
            try:
                response = supabase.table('pooja_types').select('*').order('name').execute()
                poojas = response.data if response.data else []
            except:
                poojas = []
        
        if poojas:
            for pooja in poojas:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{pooja['name']}**")
                    if pooja.get('duration'):
                        st.caption(f"Duration: {pooja['duration']}")
                with col2:
                    st.markdown(f"{TEMPLE_CONFIG['currency']}{pooja['amount']:,.2f}")
                with col3:
                    if st.button("✏️", key=f"edit_pooja_{pooja['id']}"):
                        st.session_state[f"edit_pooja_{pooja['id']}"] = True
                with col4:
                    if st.button("🗑️", key=f"delete_pooja_{pooja['id']}"):
                        if supabase:
                            try:
                                supabase.table('pooja_types').delete().eq('id', pooja['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                # Edit form
                if st.session_state.get(f"edit_pooja_{pooja['id']}", False):
                    with st.form(key=f"edit_pooja_form_{pooja['id']}"):
                        new_name = st.text_input("Name", value=pooja['name'])
                        new_amount = st.number_input("Amount", value=float(pooja['amount']), step=10.0)
                        new_duration = st.text_input("Duration", value=pooja.get('duration', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Save"):
                                if supabase:
                                    try:
                                        supabase.table('pooja_types').update({
                                            'name': new_name,
                                            'amount': new_amount,
                                            'duration': new_duration
                                        }).eq('id', pooja['id']).execute()
                                        del st.session_state[f"edit_pooja_{pooja['id']}"]
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        with col2:
                            if st.form_submit_button("Cancel"):
                                del st.session_state[f"edit_pooja_{pooja['id']}"]
                                st.rerun()
        else:
            st.info("No pooja types found")
    
    with tab2:
        st.subheader("Daily Pooja Schedule")
        
        # Add daily pooja
        with st.form("add_daily_pooja"):
            col1, col2 = st.columns(2)
            with col1:
                pooja_name = st.text_input("Pooja Name")
                pooja_time = st.text_input("Time (e.g., 06:00 AM)")
            with col2:
                pooja_date = st.date_input("Date", value=date.today())
                priest_name = st.text_input("Priest Name")
            
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Schedule Pooja"):
                if pooja_name and supabase:
                    try:
                        data = {
                            'pooja_name': pooja_name,
                            'pooja_time': pooja_time,
                            'pooja_date': pooja_date.isoformat(),
                            'priest_name': priest_name,
                            'notes': notes,
                            'status': 'pending'
                        }
                        supabase.table('daily_pooja').insert(data).execute()
                        st.success("Pooja scheduled successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # View schedule
        view_date = st.date_input("View Schedule For", value=date.today())
        
        if supabase:
            try:
                response = supabase.table('daily_pooja').select('*').eq('pooja_date', view_date.isoformat()).order('pooja_time').execute()
                schedule = response.data if response.data else []
            except:
                schedule = []
        
        if schedule:
            for pooja in schedule:
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    st.markdown(f"**{pooja['pooja_name']}**")
                    if pooja.get('pooja_time'):
                        st.caption(f"🕐 {pooja['pooja_time']}")
                with col2:
                    if pooja.get('priest_name'):
                        st.markdown(f"👨‍🦱 {pooja['priest_name']}")
                    if pooja.get('notes'):
                        st.caption(f"📝 {pooja['notes']}")
                with col3:
                    status = pooja['status']
                    new_status = "✅ Completed" if status == "pending" else "🔄 Mark Pending"
                    if st.button(new_status, key=f"status_{pooja['id']}"):
                        if supabase:
                            try:
                                new_status_value = "completed" if status == "pending" else "pending"
                                supabase.table('daily_pooja').update({'status': new_status_value}).eq('id', pooja['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                with col4:
                    if st.button("🗑️", key=f"delete_daily_{pooja['id']}"):
                        if supabase:
                            try:
                                supabase.table('daily_pooja').delete().eq('id', pooja['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        else:
            st.info("No poojas scheduled for this date")
    
    with tab3:
        st.subheader("Yearly Pooja Subscriptions")
        
        # Select devotee
        if supabase:
            try:
                response = supabase.table('devotees').select('id, name, mobile_no').order('name').execute()
                devotees = response.data if response.data else []
            except:
                devotees = []
        
        if devotees:
            devotee_options = {f"{devotee['name']} - {devotee.get('mobile_no', 'N/A')}": devotee['id'] for devotee in devotees}
            selected_devotee = st.selectbox("Select Devotee", list(devotee_options.keys()))
            devotee_id = devotee_options[selected_devotee]
            
            # Add subscription
            with st.form("add_subscription"):
                col1, col2 = st.columns(2)
                with col1:
                    if supabase:
                        try:
                            response = supabase.table('pooja_types').select('name').eq('is_active', True).execute()
                            poojas = response.data if response.data else []
                            pooja_names = [p['name'] for p in poojas]
                        except:
                            pooja_names = []
                    pooja_type = st.selectbox("Pooja Type", pooja_names if pooja_names else [])
                
                with col2:
                    pooja_date = st.date_input("Pooja Date")
                
                amount = st.number_input("Amount", min_value=0.0, step=10.0)
                description = st.text_area("Description")
                
                if st.form_submit_button("Add Subscription"):
                    if supabase:
                        try:
                            data = {
                                'devotee_id': devotee_id,
                                'pooja_type': pooja_type,
                                'pooja_date': pooja_date.isoformat(),
                                'amount': amount,
                                'description': description,
                                'is_completed': False
                            }
                            supabase.table('devotee_yearly_pooja').insert(data).execute()
                            st.success("Subscription added successfully")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            # List subscriptions
            if supabase:
                try:
                    response = supabase.table('devotee_yearly_pooja').select('*').eq('devotee_id', devotee_id).order('pooja_date', desc=True).execute()
                    subscriptions = response.data if response.data else []
                except:
                    subscriptions = []
            
            if subscriptions:
                st.markdown("### Current Subscriptions")
                for sub in subscriptions:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.markdown(f"**{sub['pooja_type']}**")
                        st.caption(f"Date: {sub.get('pooja_date', 'TBD')}")
                    with col2:
                        if sub.get('amount'):
                            st.markdown(f"{TEMPLE_CONFIG['currency']}{sub['amount']:,.2f}")
                    with col3:
                        status = "✅ Completed" if sub.get('is_completed') else "⏳ Pending"
                        if st.button(f"Toggle", key=f"toggle_sub_{sub['id']}"):
                            if supabase:
                                try:
                                    supabase.table('devotee_yearly_pooja').update({'is_completed': not sub.get('is_completed', False)}).eq('id', sub['id']).execute()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                    with col4:
                        if st.button("🗑️", key=f"delete_sub_{sub['id']}"):
                            if supabase:
                                try:
                                    supabase.table('devotee_yearly_pooja').delete().eq('id', sub['id']).execute()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                st.info("No subscriptions for this devotee")
        else:
            st.warning("No devotees found. Please add devotees first.")

# ============================================================
# EXPENSE PAGE
# ============================================================

def expense_page():
    """Expense tracking page"""
    render_header()
    
    tab1, tab2 = st.tabs(["➕ Add Expense", "📋 Expense History"])
    
    with tab1:
        with st.form("add_expense"):
            col1, col2 = st.columns(2)
            with col1:
                if supabase:
                    try:
                        response = supabase.table('expense_types').select('name').order('name').execute()
                        expense_types = [item['name'] for item in response.data] if response.data else []
                    except:
                        expense_types = []
                expense_type = st.selectbox("Expense Type", expense_types if expense_types else [])
                
                amount = st.number_input("Amount", min_value=0.0, step=10.0)
                expense_date = st.date_input("Expense Date", value=date.today())
            
            with col2:
                bill_no = st.text_input("Bill/Invoice Number (Optional)")
                vendor_name = st.text_input("Vendor Name (Optional)")
            
            description = st.text_area("Description", height=100)
            
            if st.form_submit_button("Add Expense", type="primary"):
                if expense_type and amount > 0 and supabase:
                    try:
                        data = {
                            'expense_type': expense_type,
                            'amount': amount,
                            'description': description,
                            'expense_date': expense_date.isoformat(),
                            'bill_no': bill_no,
                            'vendor_name': vendor_name
                        }
                        supabase.table('expenses').insert(data).execute()
                        st.success("✅ Expense added successfully")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Please fill all required fields")
    
    with tab2:
        st.subheader("Expense History")
        
        col1, col2 = st.columns(2)
        with col1:
            from_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
        with col2:
            to_date = st.date_input("To Date", value=date.today())
        
        if supabase:
            try:
                response = supabase.table('expenses').select('*').gte('expense_date', from_date.isoformat()).lte('expense_date', to_date.isoformat()).order('expense_date', desc=True).execute()
                expenses = response.data if response.data else []
            except:
                expenses = []
        
        if expenses:
            expenses_df = pd.DataFrame(expenses)
            total_expenses = expenses_df['amount'].sum()
            st.metric("Total Expenses", f"{TEMPLE_CONFIG['currency']}{total_expenses:,.2f}")
            
            display_df = expenses_df[['expense_date', 'expense_type', 'amount', 'description', 'vendor_name', 'bill_no']]
            display_df['amount'] = display_df['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(display_df, use_container_width=True)
            
            # Export option
            csv = expenses_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export to CSV", csv, "expenses_export.csv", "text/csv")
            
            # Chart
            st.subheader("Expense Analysis")
            expense_by_type = expenses_df.groupby('expense_type')['amount'].sum().sort_values(ascending=False)
            st.bar_chart(expense_by_type)
        else:
            st.info("No expenses found for the selected period")

# ============================================================
# DONATIONS PAGE
# ============================================================

def donations_page():
    """Donations management page"""
    render_header()
    
    tab1, tab2 = st.tabs(["🎁 Record Donation", "📋 Donation History"])
    
    with tab1:
        with st.form("record_donation"):
            col1, col2 = st.columns(2)
            with col1:
                donor_name = st.text_input("Donor Name *")
                donor_mobile = st.text_input("Mobile Number")
                donor_email = st.text_input("Email Address")
            
            with col2:
                amount = st.number_input("Donation Amount *", min_value=0.0, step=100.0)
                donation_type = st.selectbox("Donation Type", ["General", "Temple Construction", "Annadhanam", "Festival", "Other"])
                donation_date = st.date_input("Donation Date", value=date.today())
            
            purpose = st.text_area("Purpose/Remarks")
            payment_mode = st.selectbox("Payment Mode", ["cash", "card", "upi", "bank transfer", "cheque"])
            
            if st.form_submit_button("Record Donation", type="primary"):
                if donor_name and amount > 0 and supabase:
                    donation_no = generate_unique_id('DON')
                    
                    try:
                        data = {
                            'donation_no': donation_no,
                            'donor_name': donor_name,
                            'donor_mobile': donor_mobile,
                            'donor_email': donor_email,
                            'amount': amount,
                            'donation_type': donation_type,
                            'purpose': purpose,
                            'donation_date': donation_date.isoformat(),
                            'payment_mode': payment_mode
                        }
                        supabase.table('donations').insert(data).execute()
                        
                        st.success(f"✅ Donation recorded successfully! Receipt No: {donation_no}")
                        st.balloons()
                        
                        # Generate receipt
                        st.markdown("---")
                        st.subheader("📄 Donation Receipt")
                        
                        receipt_html = f"""
                        <div style='border: 2px solid #28a745; padding: 20px; border-radius: 10px; background: white;'>
                            <div style='text-align: center;'>
                                <h2>{TEMPLE_CONFIG['name']}</h2>
                                <p>{TEMPLE_CONFIG['trust']}</p>
                                <p>{TEMPLE_CONFIG['address']}</p>
                                <hr>
                                <h3>DONATION RECEIPT</h3>
                                <hr>
                            </div>
                            <table style='width: 100%; margin: 20px 0;'>
                                <tr><td><strong>Receipt No:</strong></td><td>{donation_no}</td></tr>
                                <tr><td><strong>Date:</strong></td><td>{donation_date}</td></tr>
                                <tr><td><strong>Donor Name:</strong></td><td>{donor_name}</td></tr>
                                <tr><td><strong>Donation Type:</strong></td><td>{donation_type}</td></tr>
                                <tr><td><strong>Amount:</strong></td><td><h3>{TEMPLE_CONFIG['currency']}{amount:,.2f}</h3></td></tr>
                            </table>
                            <hr>
                            <div style='text-align: center;'>
                                <p>🙏 Thank you for your generous donation! 🙏</p>
                                <p>May God bless you abundantly!</p>
                            </div>
                        </div>
                        """
                        st.markdown(receipt_html, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Please fill all required fields")
    
    with tab2:
        st.subheader("Donation History")
        
        col1, col2 = st.columns(2)
        with col1:
            from_date = st.date_input("From Date", value=date.today() - timedelta(days=365))
        with col2:
            to_date = st.date_input("To Date", value=date.today())
        
        if supabase:
            try:
                response = supabase.table('donations').select('*').gte('donation_date', from_date.isoformat()).lte('donation_date', to_date.isoformat()).order('donation_date', desc=True).execute()
                donations = response.data if response.data else []
            except:
                donations = []
        
        if donations:
            donations_df = pd.DataFrame(donations)
            total_donations = donations_df['amount'].sum()
            st.metric("Total Donations", f"{TEMPLE_CONFIG['currency']}{total_donations:,.2f}")
            
            display_df = donations_df[['donation_no', 'donation_date', 'donor_name', 'donation_type', 'amount', 'payment_mode']]
            display_df['amount'] = display_df['amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(display_df, use_container_width=True)
            
            # Export
            csv = donations_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export to CSV", csv, "donations_export.csv", "text/csv")
            
            # Charts
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Donations by Type")
                donation_by_type = donations_df.groupby('donation_type')['amount'].sum()
                st.bar_chart(donation_by_type)
            with col2:
                st.subheader("Monthly Donations")
                donations_df['month'] = pd.to_datetime(donations_df['donation_date']).dt.strftime('%Y-%m')
                monthly_donations = donations_df.groupby('month')['amount'].sum()
                st.line_chart(monthly_donations)
        else:
            st.info("No donations found for the selected period")

# ============================================================
# ASSETS PAGE
# ============================================================

def assets_page():
    """Asset management page"""
    render_header()
    
    tab1, tab2 = st.tabs(["🏷️ Add Asset", "📋 Asset List"])
    
    with tab1:
        with st.form("add_asset"):
            col1, col2 = st.columns(2)
            with col1:
                asset_tag = st.text_input("Asset Tag *")
                asset_name = st.text_input("Asset Name *")
                category = st.selectbox("Category", ["Furniture", "Electronics", "Vehicles", "Idols", "Jewelry", "Other"])
                serial_no = st.text_input("Serial Number")
            
            with col2:
                donor_name = st.text_input("Donor Name")
                donation_date = st.date_input("Donation/Purchase Date", value=date.today())
                purchase_cost = st.number_input("Purchase Cost", min_value=0.0, step=1000.0)
                location = st.text_input("Current Location")
            
            description = st.text_area("Description")
            status = st.selectbox("Status", ["active", "maintenance", "damaged", "donated"])
            
            if st.form_submit_button("Add Asset"):
                if asset_tag and asset_name and supabase:
                    try:
                        data = {
                            'asset_tag': asset_tag,
                            'asset_name': asset_name,
                            'category': category,
                            'serial_no': serial_no,
                            'donor_name': donor_name,
                            'donation_date': donation_date.isoformat(),
                            'purchase_cost': purchase_cost,
                            'location': location,
                            'description': description,
                            'status': status
                        }
                        supabase.table('assets').insert(data).execute()
                        st.success(f"✅ Asset '{asset_name}' added successfully")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Please fill all required fields")
    
    with tab2:
        st.subheader("Asset List")
        
        search_term = st.text_input("Search Assets", placeholder="Search by tag, name, or donor...")
        
        if supabase:
            try:
                if search_term:
                    response = supabase.table('assets').select('*').or_(f'asset_tag.ilike.%{search_term}%,asset_name.ilike.%{search_term}%,donor_name.ilike.%{search_term}%').order('created_at', desc=True).execute()
                else:
                    response = supabase.table('assets').select('*').order('created_at', desc=True).execute()
                assets = response.data if response.data else []
            except:
                assets = []
        
        if assets:
            total_value = sum(asset.get('purchase_cost', 0) for asset in assets)
            st.metric("Total Asset Value", f"{TEMPLE_CONFIG['currency']}{total_value:,.2f}")
            
            for asset in assets:
                with st.expander(f"🏷️ {asset['asset_tag']} - {asset['asset_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Category:** {asset.get('category', 'N/A')}")
                        st.markdown(f"**Serial No:** {asset.get('serial_no', 'N/A')}")
                        st.markdown(f"**Donor:** {asset.get('donor_name', 'N/A')}")
                        st.markdown(f"**Date:** {asset.get('donation_date', 'N/A')}")
                    with col2:
                        st.markdown(f"**Cost:** {TEMPLE_CONFIG['currency']}{asset.get('purchase_cost', 0):,.2f}")
                        st.markdown(f"**Location:** {asset.get('location', 'N/A')}")
                        st.markdown(f"**Status:** {asset.get('status', 'N/A')}")
                        st.markdown(f"**Description:** {asset.get('description', 'N/A')}")
                    
                    if st.button("🗑️ Delete", key=f"delete_asset_{asset['id']}"):
                        if supabase:
                            try:
                                supabase.table('assets').delete().eq('id', asset['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        else:
            st.info("No assets found")

# ============================================================
# REPORTS PAGE
# ============================================================

def reports_page():
    """Reports page"""
    render_header()
    
    report_type = st.selectbox("Select Report Type", [
        "Financial Summary",
        "Devotee Report",
        "Pooja Income Report",
        "Expense Report",
        "Donation Report"
    ])
    
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        to_date = st.date_input("To Date", value=date.today())
    
    if report_type == "Financial Summary":
        st.subheader(f"Financial Summary ({from_date} to {to_date})")
        
        summary = get_financial_summary(from_date, to_date)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Income", f"{TEMPLE_CONFIG['currency']}{summary['income']:,.2f}")
        with col2:
            st.metric("Total Donations", f"{TEMPLE_CONFIG['currency']}{summary['donations']:,.2f}")
        with col3:
            st.metric("Total Expenses", f"{TEMPLE_CONFIG['currency']}{summary['expenses']:,.2f}")
        with col4:
            st.metric("Net Balance", f"{TEMPLE_CONFIG['currency']}{summary['balance']:,.2f}")
        
        # Generate detailed report
        report_data = {
            'Income': summary['income'],
            'Donations': summary['donations'],
            'Expenses': summary['expenses'],
            'Net Balance': summary['balance']
        }
        
        report_df = pd.DataFrame([report_data])
        csv = report_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report", csv, "financial_report.csv", "text/csv")
    
    elif report_type == "Devotee Report":
        st.subheader("Devotee Report")
        
        if supabase:
            try:
                response = supabase.table('devotees').select('*').order('created_at', desc=True).execute()
                devotees = response.data if response.data else []
            except:
                devotees = []
        
        if devotees:
            devotees_df = pd.DataFrame(devotees)
            st.metric("Total Devotees", len(devotees_df))
            display_df = devotees_df[['devotee_id', 'name', 'mobile_no', 'email', 'created_at']]
            st.dataframe(display_df, use_container_width=True)
            
            csv = devotees_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Report", csv, "devotee_report.csv", "text/csv")
        else:
            st.info("No devotees found")
    
    elif report_type == "Pooja Income Report":
        st.subheader(f"Pooja Income Report ({from_date} to {to_date})")
        
        if supabase:
            try:
                response = supabase.table('bills').select('pooja_type, amount').gte('bill_date', from_date.isoformat()).lte('bill_date', to_date.isoformat()).execute()
                bills = response.data if response.data else []
            except:
                bills = []
        
        if bills:
            bills_df = pd.DataFrame(bills)
            income_df = bills_df.groupby('pooja_type').agg({'amount': ['sum', 'count']}).round(2)
            income_df.columns = ['total_amount', 'count']
            income_df = income_df.reset_index()
            
            total_income = income_df['total_amount'].sum()
            st.metric("Total Pooja Income", f"{TEMPLE_CONFIG['currency']}{total_income:,.2f}")
            
            income_df['total_amount'] = income_df['total_amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(income_df, use_container_width=True)
            
            # Chart
            st.subheader("Income by Pooja Type")
            chart_data = income_df.set_index('pooja_type')['total_amount'].str.replace(TEMPLE_CONFIG['currency'], '').astype(float)
            st.bar_chart(chart_data)
            
            csv = income_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Report", csv, "pooja_income_report.csv", "text/csv")
        else:
            st.info("No income data found for the selected period")
    
    elif report_type == "Expense Report":
        st.subheader(f"Expense Report ({from_date} to {to_date})")
        
        if supabase:
            try:
                response = supabase.table('expenses').select('expense_type, amount').gte('expense_date', from_date.isoformat()).lte('expense_date', to_date.isoformat()).execute()
                expenses = response.data if response.data else []
            except:
                expenses = []
        
        if expenses:
            expenses_df = pd.DataFrame(expenses)
            expense_df = expenses_df.groupby('expense_type').agg({'amount': ['sum', 'count']}).round(2)
            expense_df.columns = ['total_amount', 'count']
            expense_df = expense_df.reset_index()
            
            total_expenses = expense_df['total_amount'].sum()
            st.metric("Total Expenses", f"{TEMPLE_CONFIG['currency']}{total_expenses:,.2f}")
            
            expense_df['total_amount'] = expense_df['total_amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(expense_df, use_container_width=True)
            
            # Chart
            st.subheader("Expenses by Type")
            chart_data = expense_df.set_index('expense_type')['total_amount'].str.replace(TEMPLE_CONFIG['currency'], '').astype(float)
            st.bar_chart(chart_data)
            
            csv = expense_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Report", csv, "expense_report.csv", "text/csv")
        else:
            st.info("No expense data found for the selected period")
    
    elif report_type == "Donation Report":
        st.subheader(f"Donation Report ({from_date} to {to_date})")
        
        if supabase:
            try:
                response = supabase.table('donations').select('donation_type, amount').gte('donation_date', from_date.isoformat()).lte('donation_date', to_date.isoformat()).execute()
                donations = response.data if response.data else []
            except:
                donations = []
        
        if donations:
            donations_df = pd.DataFrame(donations)
            donation_df = donations_df.groupby('donation_type').agg({'amount': ['sum', 'count']}).round(2)
            donation_df.columns = ['total_amount', 'count']
            donation_df = donation_df.reset_index()
            
            total_donations = donation_df['total_amount'].sum()
            st.metric("Total Donations", f"{TEMPLE_CONFIG['currency']}{total_donations:,.2f}")
            
            donation_df['total_amount'] = donation_df['total_amount'].apply(lambda x: f"{TEMPLE_CONFIG['currency']}{x:,.2f}")
            st.dataframe(donation_df, use_container_width=True)
            
            csv = donation_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Report", csv, "donation_report.csv", "text/csv")
        else:
            st.info("No donation data found for the selected period")

# ============================================================
# SETTINGS PAGE
# ============================================================

def settings_page():
    """Settings page"""
    render_header()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏛️ Temple Settings", "📢 News Ticker", "💸 Expense Types", "👤 Profile"])
    
    with tab1:
        st.subheader("Temple Information")
        
        with st.form("temple_settings"):
            temple_name = st.text_input("Temple Name", value=TEMPLE_CONFIG['name'])
            trust_name = st.text_input("Trust Name", value=TEMPLE_CONFIG['trust'])
            address = st.text_area("Address", value=TEMPLE_CONFIG['address'])
            phone = st.text_input("Phone Number", value=TEMPLE_CONFIG['phone'])
            email = st.text_input("Email", value=TEMPLE_CONFIG['email'])
            website = st.text_input("Website", value=TEMPLE_CONFIG['website'])
            tagline = st.text_input("Tagline", value=TEMPLE_CONFIG['tagline'])
            
            logo = st.file_uploader("Temple Logo", type=['jpg', 'jpeg', 'png'])
            
            if st.form_submit_button("Save Settings"):
                # Update temple config
                TEMPLE_CONFIG.update({
                    'name': temple_name,
                    'trust': trust_name,
                    'address': address,
                    'phone': phone,
                    'email': email,
                    'website': website,
                    'tagline': tagline
                })
                
                if logo:
                    logo_base64 = base64.b64encode(logo.getvalue()).decode()
                    set_temple_setting('temple_logo', logo_base64)
                
                st.success("Settings saved successfully!")
                st.rerun()
    
    with tab2:
        st.subheader("News Ticker Management")
        
        # Add news
        with st.form("add_news"):
            news_message = st.text_input("News Message")
            priority = st.slider("Priority", 0, 10, 0)
            
            if st.form_submit_button("Add News"):
                if news_message and supabase:
                    try:
                        data = {
                            'message': news_message,
                            'priority': priority,
                            'is_active': True
                        }
                        supabase.table('news_ticker').insert(data).execute()
                        st.success("News added successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # List news items
        if supabase:
            try:
                response = supabase.table('news_ticker').select('*').order('priority', desc=True).order('created_at', desc=True).execute()
                news_items = response.data if response.data else []
            except:
                news_items = []
        
        if news_items:
            for news in news_items:
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                with col1:
                    st.markdown(f"{'🟢' if news['is_active'] else '🔴'} {news['message']}")
                with col2:
                    st.caption(f"Priority: {news['priority']}")
                with col3:
                    if st.button("Toggle", key=f"toggle_news_{news['id']}"):
                        if supabase:
                            try:
                                supabase.table('news_ticker').update({'is_active': not news['is_active']}).eq('id', news['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                with col4:
                    if st.button("🗑️", key=f"delete_news_{news['id']}"):
                        if supabase:
                            try:
                                supabase.table('news_ticker').delete().eq('id', news['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        else:
            st.info("No news items found")
    
    with tab3:
        st.subheader("Expense Types Management")
        
        # Add expense type
        with st.form("add_expense_type"):
            expense_name = st.text_input("Expense Type Name")
            category = st.selectbox("Category", ["Utilities", "Maintenance", "Daily Operations", "Staff", "Events", "Other"])
            
            if st.form_submit_button("Add Expense Type"):
                if expense_name and supabase:
                    try:
                        data = {
                            'name': expense_name,
                            'category': category
                        }
                        supabase.table('expense_types').insert(data).execute()
                        st.success("Expense type added successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # List expense types
        if supabase:
            try:
                response = supabase.table('expense_types').select('*').order('name').execute()
                expense_types = response.data if response.data else []
            except:
                expense_types = []
        
        if expense_types:
            for expense in expense_types:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{expense['name']}**")
                    st.caption(f"Category: {expense.get('category', 'N/A')}")
                with col2:
                    if st.button("✏️", key=f"edit_expense_{expense['id']}"):
                        st.session_state[f"edit_expense_{expense['id']}"] = True
                with col3:
                    if st.button("🗑️", key=f"delete_expense_{expense['id']}"):
                        if supabase:
                            try:
                                supabase.table('expense_types').delete().eq('id', expense['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                if st.session_state.get(f"edit_expense_{expense['id']}", False):
                    with st.form(key=f"edit_expense_form_{expense['id']}"):
                        new_name = st.text_input("Name", value=expense['name'])
                        new_category = st.selectbox("Category", ["Utilities", "Maintenance", "Daily Operations", "Staff", "Events", "Other"], 
                                                   index=["Utilities", "Maintenance", "Daily Operations", "Staff", "Events", "Other"].index(expense.get('category', 'Other')))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Save"):
                                if supabase:
                                    try:
                                        supabase.table('expense_types').update({
                                            'name': new_name,
                                            'category': new_category
                                        }).eq('id', expense['id']).execute()
                                        del st.session_state[f"edit_expense_{expense['id']}"]
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        with col2:
                            if st.form_submit_button("Cancel"):
                                del st.session_state[f"edit_expense_{expense['id']}"]
                                st.rerun()
        else:
            st.info("No expense types found")
    
    with tab4:
        st.subheader("Profile Settings")
        
        if st.session_state.get('logged_in') and supabase:
            try:
                response = supabase.table('users').select('*').eq('username', st.session_state.username).execute()
                user = response.data[0] if response.data else None
            except:
                user = None
        
        if user:
            with st.form("profile_settings"):
                full_name = st.text_input("Full Name", value=user.get('full_name', ''))
                email = st.text_input("Email", value=user.get('email', ''))
                
                st.markdown("---")
                st.subheader("Change Password")
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Update Profile"):
                    updates = {}
                    if full_name:
                        updates['full_name'] = full_name
                    if email:
                        updates['email'] = email
                    
                    if updates:
                        try:
                            supabase.table('users').update(updates).eq('username', st.session_state.username).execute()
                            st.success("Profile updated successfully!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    if current_password and new_password:
                        if verify_password(current_password, user['password_hash']):
                            if new_password == confirm_password:
                                new_hash = hash_password(new_password)
                                try:
                                    supabase.table('users').update({'password_hash': new_hash}).eq('username', st.session_state.username).execute()
                                    st.success("Password changed successfully!")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                            else:
                                st.error("New passwords do not match")
                        else:
                            st.error("Current password is incorrect")
                    
                    st.rerun()

# ============================================================
# USER MANAGEMENT PAGE (ADMIN ONLY)
# ============================================================

def user_management_page():
    """User management page (admin only)"""
    if st.session_state.get('role') != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    render_header()
    
    tab1, tab2 = st.tabs(["👥 Manage Users", "➕ Add New User"])
    
    with tab1:
        if supabase:
            try:
                response = supabase.table('users').select('id, username, role, full_name, email, created_at').execute()
                users = response.data if response.data else []
            except:
                users = []
        
        if users:
            for user in users:
                with st.expander(f"👤 {user['username']} - {user['role']}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**Full Name:** {user.get('full_name', 'N/A')}")
                        st.markdown(f"**Email:** {user.get('email', 'N/A')}")
                        st.markdown(f"**Created:** {user['created_at']}")
                    with col2:
                        if user['username'] != 'admin':  # Prevent editing admin
                            new_role = st.selectbox("Role", ["user", "admin"], 
                                                   index=0 if user['role'] == 'user' else 1,
                                                   key=f"role_{user['id']}")
                            if st.button("Update Role", key=f"update_{user['id']}"):
                                if supabase:
                                    try:
                                        supabase.table('users').update({'role': new_role}).eq('id', user['id']).execute()
                                        st.success("Role updated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                    with col3:
                        if user['username'] != 'admin':
                            if st.button("🗑️ Delete", key=f"delete_user_{user['id']}"):
                                if supabase:
                                    try:
                                        supabase.table('users').delete().eq('id', user['id']).execute()
                                        st.success("User deleted!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
        else:
            st.info("No users found")
    
    with tab2:
        with st.form("add_user"):
            username = st.text_input("Username *")
            password = st.text_input("Password *", type="password")
            confirm_password = st.text_input("Confirm Password *", type="password")
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            role = st.selectbox("Role", ["user", "admin"])
            
            if st.form_submit_button("Add User"):
                if not username or not password:
                    st.error("Username and password are required")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif supabase:
                    try:
                        # Check if user exists
                        response = supabase.table('users').select('id').eq('username', username).execute()
                        if response.data:
                            st.error("Username already exists")
                        else:
                            data = {
                                'username': username,
                                'password_hash': hash_password(password),
                                'role': role,
                                'full_name': full_name,
                                'email': email
                            }
                            supabase.table('users').insert(data).execute()
                            st.success(f"User '{username}' added successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """Main application entry point"""
    
    # Check login status
    if not st.session_state.get('logged_in', False):
        login_page()
    else:
        # Render sidebar and main content
        render_sidebar()
        
        # Page routing
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
        
        current_page = st.session_state.get('current_page', 'Dashboard')
        page_function = pages.get(current_page, dashboard_page)
        page_function()

if __name__ == "__main__":
    main()
