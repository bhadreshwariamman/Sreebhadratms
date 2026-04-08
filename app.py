# app.py - Temple Management System with Supabase (Fixed Login)
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import base64
import time
import hashlib
from typing import Optional, Dict, List, Any

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
# PASSWORD UTILITIES
# ============================================================

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hash_value: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hash_value

def create_default_admin():
    """Create default admin user if not exists"""
    if not supabase:
        return
    
    try:
        # Check if admin exists
        response = supabase.table('users').select('id').eq('username', 'admin').execute()
        
        if not response.data:
            # Create admin user with hashed password
            admin_data = {
                'username': 'admin',
                'password_hash': hash_password('admin123'),
                'role': 'admin',
                'full_name': 'Administrator',
                'email': 'admin@temple.com'
            }
            supabase.table('users').insert(admin_data).execute()
            print("Default admin user created successfully")
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")

# ============================================================
# DATABASE HELPER FUNCTIONS
# ============================================================

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
        return ''

def set_temple_setting(key: str, value: str):
    """Set temple setting in Supabase"""
    if not supabase:
        return
    try:
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
        response = supabase.table('devotees').select('name, dob').execute()
        for devotee in response.data:
            if devotee.get('dob'):
                try:
                    dob = datetime.strptime(devotee['dob'], '%Y-%m-%d').date()
                    if dob.month == today.month and dob.day == today.day:
                        birthdays.append(f"🎂 {devotee['name']} (Devotee)")
                except:
                    pass
    except Exception as e:
        pass
    
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
        pass
    
    return anniversaries

def get_financial_summary(start_date: date, end_date: date) -> Dict:
    """Get financial summary from Supabase"""
    if not supabase:
        return {'income': 0, 'expenses': 0, 'donations': 0, 'balance': 0}
    
    try:
        response = supabase.table('bills').select('amount').gte('bill_date', start_date.isoformat()).lte('bill_date', end_date.isoformat()).execute()
        total_income = sum(item.get('amount', 0) for item in response.data) if response.data else 0
        
        response = supabase.table('expenses').select('amount').gte('expense_date', start_date.isoformat()).lte('expense_date', end_date.isoformat()).execute()
        total_expense = sum(item.get('amount', 0) for item in response.data) if response.data else 0
        
        response = supabase.table('donations').select('amount').gte('donation_date', start_date.isoformat()).lte('donation_date', end_date.isoformat()).execute()
        total_donations = sum(item.get('amount', 0) for item in response.data) if response.data else 0
        
        return {
            'income': total_income,
            'expenses': total_expense,
            'donations': total_donations,
            'balance': total_income + total_donations - total_expense
        }
    except Exception as e:
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
        st.info("Make sure you have set up the SUPABASE_URL and SUPABASE_KEY in secrets.")
        return
    
    # Create default admin user
    create_default_admin()
    
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
                            # Query user from database
                            response = supabase.table('users').select('*').eq('username', username).execute()
                            
                            if response.data:
                                user = response.data[0]
                                stored_hash = user['password_hash']
                                input_hash = hash_password(password)
                                
                                # Debug info (remove in production)
                                st.write(f"Debug - Input hash: {input_hash[:20]}...")
                                st.write(f"Debug - Stored hash: {stored_hash[:20]}...")
                                
                                if stored_hash == input_hash:
                                    st.session_state.logged_in = True
                                    st.session_state.username = user['username']
                                    st.session_state.role = user['role']
                                    st.session_state.user_id = user['id']
                                    st.session_state.current_page = "Dashboard"
                                    st.success("Login successful! Redirecting...")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid username or password")
                            else:
                                st.error("❌ Invalid username or password")
                        except Exception as e:
                            st.error(f"Login error: {str(e)}")
                            st.info("Please make sure your Supabase connection is working properly.")
            
            st.markdown("---")
            st.info("🔑 Default Login:\n- Username: admin\n- Password: admin123")
            st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# DASHBOARD PAGE
# ============================================================

def dashboard_page():
    """Dashboard page"""
    render_header()
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        period = st.selectbox("Period", ["Today", "This Week", "This Month", "This Year"])
    
    today = date.today()
    if period == "Today":
        start_date = end_date = today
    elif period == "This Week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "This Month":
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = today.replace(month=1, day=1)
        end_date = today
    
    summary = get_financial_summary(start_date, end_date)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Income", f"{TEMPLE_CONFIG['currency']}{summary['income']:,.2f}")
    with col2:
        st.metric("💸 Total Expenses", f"{TEMPLE_CONFIG['currency']}{summary['expenses']:,.2f}")
    with col3:
        st.metric("🎁 Donations", f"{TEMPLE_CONFIG['currency']}{summary['donations']:,.2f}")
    with col4:
        st.metric("💎 Net Balance", f"{TEMPLE_CONFIG['currency']}{summary['balance']:,.2f}")
    
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
        else:
            st.info("No poojas scheduled for today")
    
    st.markdown("---")
    st.success("✅ Welcome to Temple Management System! Use the sidebar to navigate.")

# ============================================================
# SIMPLIFIED VERSIONS OF OTHER PAGES
# ============================================================

def devotee_management_page():
    """Devotee management page"""
    render_header()
    st.info("👥 Devotee Management Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Register new devotees")
    st.write("- View and search devotees")
    st.write("- Bulk import via Excel/CSV")
    st.write("- Family member management")

def billing_page():
    """Billing page"""
    render_header()
    st.info("🧾 Billing System Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Generate bills for poojas")
    st.write("- Print receipts")
    st.write("- Bill history")
    st.write("- Payment tracking")

def pooja_management_page():
    """Pooja management page"""
    render_header()
    st.info("🙏 Pooja Management Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Manage pooja types and prices")
    st.write("- Daily pooja scheduling")
    st.write("- Yearly pooja subscriptions")
    st.write("- Priest assignment")

def expense_page():
    """Expense tracking page"""
    render_header()
    st.info("💰 Expense Tracking Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Record expenses")
    st.write("- Expense categories")
    st.write("- Vendor management")
    st.write("- Expense reports")

def donations_page():
    """Donations page"""
    render_header()
    st.info("🎁 Donations Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Record donations")
    st.write("- Generate donation receipts")
    st.write("- Donor management")
    st.write("- Donation reports")

def assets_page():
    """Assets page"""
    render_header()
    st.info("🏷️ Asset Management Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Track temple assets")
    st.write("- Asset tags and barcodes")
    st.write("- Maintenance scheduling")
    st.write("- Asset valuation")

def reports_page():
    """Reports page"""
    render_header()
    st.info("📊 Reports Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Financial reports")
    st.write("- Devotee reports")
    st.write("- Pooja income reports")
    st.write("- Donation reports")
    st.write("- Expense reports")

def settings_page():
    """Settings page"""
    render_header()
    st.info("⚙️ Settings Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Temple information")
    st.write("- News ticker management")
    st.write("- Expense categories")
    st.write("- Profile settings")

def user_management_page():
    """User management page"""
    if st.session_state.get('role') != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    render_header()
    st.info("👥 User Management Module - Coming Soon")
    st.write("This module will include:")
    st.write("- Add new users")
    st.write("- Manage user roles")
    st.write("- Reset passwords")
    st.write("- View user activity")

# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """Main application entry point"""
    
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
        
        current_page = st.session_state.get('current_page', 'Dashboard')
        page_function = pages.get(current_page, dashboard_page)
        page_function()

if __name__ == "__main__":
    main()
