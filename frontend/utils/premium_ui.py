"""
Premium UI utilities for Streamlit pages.
Provides consistent styling and theming across the application.
"""

import streamlit as st


def set_premium_theme():
    """Apply premium theme to Streamlit app."""
    # Custom CSS for premium look
    premium_css = """
    <style>
        /* Import premium fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap');
        
        /* Root styling - Finesse Theme */
        :root {
            --primary-color: #4f46e5;
            --secondary-color: #7c3aed;
            --accent-color: #2563eb;
            --success-color: #059669;
            --warning-color: #d97706;
            --danger-color: #dc2626;
            --light-bg: #f9fafb;
            --dark-bg: #111827;
            --card-bg: #ffffff;
            --border-color: #e5e7eb;
            --text-primary: #111827;
            --text-secondary: #6b7280;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: #ffffff !important;
            border-right: 1px solid #e5e7eb;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #111827 !important;
        }
        
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            color: #111827 !important;
        }
        
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] label {
            color: #374151 !important;
        }
        
        /* Main container */
        .main {
            background: linear-gradient(135deg, #f0e7ff 0%, #e0e7ff 50%, #dbeafe 100%) !important;
            font-family: 'Inter', sans-serif;
        }
        
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #f0e7ff 0%, #e0e7ff 50%, #dbeafe 100%) !important;
        }
        
        /* Header styling */
        h1, h2, h3 {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }
        
        h2 {
            font-size: 1.875rem;
            color: #1e293b;
            margin-bottom: 1.5rem;
        }
        
        h3 {
            font-size: 1.25rem;
            color: #334155;
        }
        
        /* Card styling */
        .stContainer, [data-testid="stExpander"], [data-testid="stForm"] {
            background: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .stContainer:hover, [data-testid="stExpander"]:hover {
            box-shadow: 0 10px 25px rgba(79, 70, 229, 0.08);
            border-color: #c7d2fe;
        }
        
        /* Button styling - Enhanced for readability */
        .stButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white !important;
            font-weight: 700;
            font-size: 1rem;
            letter-spacing: 0.5px;
            border: none !important;
            border-radius: 8px;
            padding: 0.85rem 2rem !important;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.35);
            min-height: 44px;
            text-transform: none;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.45);
            color: white !important;
        }
        
        .stButton > button:active {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
        }
        
        /* Download button styling */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            color: white !important;
            font-weight: 700;
            font-size: 1rem;
            letter-spacing: 0.5px;
            border: none !important;
            border-radius: 8px;
            padding: 0.85rem 2rem !important;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35);
            min-height: 44px;
        }
        
        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, #047857 0%, #059669 100%);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.45);
            color: white !important;
        }
        
        /* Input styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input {
            background: white;
            border: 1.5px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus,
        .stNumberInput > div > div > input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        /* Metric styling */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #e0e7ff;
        }
        
        /* Alert styling */
        .stAlert {
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid;
        }
        
        .stSuccess {
            background-color: rgba(16, 185, 129, 0.1);
            border-color: #10b981;
        }
        
        .stError {
            background-color: rgba(239, 68, 68, 0.1);
            border-color: #ef4444;
        }
        
        .stWarning {
            background-color: rgba(245, 158, 11, 0.1);
            border-color: #f59e0b;
        }
        
        .stInfo {
            background-color: rgba(79, 70, 229, 0.1);
            border-color: #4f46e5;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        }
        
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: white;
        }
        
        /* Divider */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
            margin: 2rem 0;
        }
        
        /* Text styling */
        p {
            line-height: 1.6;
            color: #475569;
            font-size: 0.95rem;
        }
        
        /* Links */
        a {
            color: #4f46e5;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        a:hover {
            color: #7c3aed;
            text-decoration: underline;
        }
        
        /* Table styling */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
        }
        
        /* Caption styling */
        .stCaption {
            color: #64748b;
            font-size: 0.85rem;
        }
    </style>
    """
    
    st.markdown(premium_css, unsafe_allow_html=True)


def header_with_icon(icon: str, title: str, subtitle: str = ""):
    """
    Create a premium header with icon.
    
    Args:
        icon: Emoji or icon character
        title: Main title
        subtitle: Optional subtitle
    """
    col1, col2 = st.columns([0.08, 0.92])
    
    with col1:
        st.markdown(f"<div style='font-size: 2.5rem; margin-top: 0.5rem;'>{icon}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<h1 style='margin: 0;'>{title}</h1>", unsafe_allow_html=True)
        if subtitle:
            st.markdown(f"<p style='margin: 0.5rem 0 0 0; color: #64748b;'>{subtitle}</p>", unsafe_allow_html=True)


def premium_card(title: str = "", content_func=None):
    """
    Create a premium card container.
    
    Args:
        title: Card title (optional)
        content_func: Function to call inside card (optional)
    """
    with st.container(border=True):
        if title:
            st.markdown(f"<h3 style='margin-top: 0;'>{title}</h3>", unsafe_allow_html=True)
        
        if content_func:
            content_func()


def auth_container():
    """Create a centered auth container for login/signup."""
    st.markdown("""
        <style>
            .auth-container {
                max-width: 450px;
                margin: auto;
                padding: 2rem;
            }
            
            .auth-card {
                background: white;
                border-radius: 16px;
                padding: 2.5rem;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
                border: 1px solid #e2e8f0;
            }
            
            .auth-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .auth-title {
                font-family: 'Poppins', sans-serif;
                font-size: 1.75rem;
                font-weight: 700;
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 0;
            }
            
            .auth-subtitle {
                color: #64748b;
                font-size: 0.9rem;
                margin: 0.5rem 0 0 0;
            }
            
            .toggle-button {
                display: inline-block;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                border: 2px solid #e2e8f0;
                background: white;
                color: #64748b;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .toggle-button.active {
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                border-color: #4f46e5;
            }
        </style>
    """, unsafe_allow_html=True)


def add_user_navbar():
    """Add premium user navbar with logout button."""
    import streamlit as st
    
    col1, col2, col3 = st.columns([2, 1, 0.5])
    
    with col1:
        if "username" in st.session_state:
            st.markdown(f"<p style='margin: 0; color: #6b7280; font-size: 0.95rem;'>Logged in as: <strong>{st.session_state.get('username', 'User')}</strong></p>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Logout", key="logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.success("Logged out successfully!")
            import time
            time.sleep(0.5)
            st.switch_page("pages/0_Login.py")
