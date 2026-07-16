"""
Professional Login/Signup page with authentication.
"""

import os
import streamlit as st
import httpx
import random

from utils.premium_ui import set_premium_theme

set_premium_theme()

# Redirect if already authenticated
if "authenticated" in st.session_state and st.session_state.authenticated:
    st.switch_page("pages/1_Upload.py")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Initialize session state for CAPTCHA
if "captcha_question" not in st.session_state:
    st.session_state.captcha_question = None
    st.session_state.captcha_answer = None
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False


def generate_captcha():
    """Generate a simple arithmetic CAPTCHA."""
    num1 = random.randint(5, 20)
    num2 = random.randint(2, 10)
    operation = random.choice(["+", "-", "*"])
    
    if operation == "+":
        answer = num1 + num2
    elif operation == "-":
        answer = num1 - num2
    else:
        answer = num1 * num2
    
    question = f"{num1} {operation} {num2}"
    return question, answer


def verify_captcha(user_answer, correct_answer):
    """Verify CAPTCHA answer."""
    try:
        return int(user_answer) == int(correct_answer)
    except:
        return False


def login_user(username: str, password: str):
    """Attempt to login user."""
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Login failed")
    except Exception as e:
        return False, str(e)


def signup_user(email: str, username: str, password: str):
    """Attempt to signup new user."""
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": password
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Signup failed")
    except Exception as e:
        return False, str(e)


# Main page layout
st.markdown("""
    <style>
        .main { padding: 1rem !important; background: linear-gradient(135deg, #f0e7ff 0%, #e0e7ff 50%, #dbeafe 100%) !important; }
        
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #f0e7ff 0%, #e0e7ff 50%, #dbeafe 100%) !important;
        }
        
        .brand-header {
            text-align: center;
            margin-bottom: 1.5rem;
            margin-top: 0.5rem;
        }
        
        .brand-title {
            font-family: 'Poppins', sans-serif;
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
        }
        
        .brand-subtitle {
            color: #4f46e5;
            font-size: 0.9rem;
            margin-top: 0.25rem;
            font-weight: 500;
        }
        
        .form-container {
            background: white;
            border-radius: 12px;
            padding: 1.75rem;
            box-shadow: 0 10px 40px rgba(79, 70, 229, 0.15);
            border: 2px solid #4f46e5;
        }
        
        .form-title {
            text-align: center;
            color: #4f46e5;
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
        }
        
        .form-subtitle {
            text-align: center;
            color: #6b7280;
            font-size: 0.85rem;
            margin-bottom: 1.25rem;
        }
    </style>
""", unsafe_allow_html=True)

# Create centered container
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Brand header
    st.markdown("""
        <div class='brand-header'>
            <div class='brand-title'>Delivery Assurance Copilot</div>
            <div class='brand-subtitle'>AI-Powered Quality Assurance</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Toggle buttons
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    # ==================== SIGN IN ====================
    with tab1:
        st.markdown("""
            <div class='form-container'>
                <p class='form-title'>Welcome Back</p>
                <p class='form-subtitle'>Sign in to your account</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("signin_form", clear_on_submit=True):
            username = st.text_input(
                "Username or Email",
                placeholder="your.email@example.com",
                key="signin_username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••",
                key="signin_password"
            )
            
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    with st.spinner("Signing in..."):
                        success, result = login_user(username, password)
                        
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_id = result.get("user_id")
                            st.session_state.username = result.get("username")
                            st.success("Login successful! Redirecting...")
                            import time
                            time.sleep(1)
                            st.switch_page("pages/1_Upload.py")
                        else:
                            st.error(f"Login failed: {result}")
    
    # ==================== SIGN UP ====================
    with tab2:
        st.markdown("""
            <div class='form-container'>
                <p class='form-title'>Create Account</p>
                <p class='form-subtitle'>Join us today</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("signup_form", clear_on_submit=True):
            email = st.text_input(
                "Email Address",
                placeholder="you@example.com",
                key="signup_email"
            )
            username = st.text_input(
                "Username",
                placeholder="your_username",
                key="signup_username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••",
                key="signup_password"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="••••••••",
                key="signup_confirm"
            )
            
            # CAPTCHA
            if st.session_state.captcha_question is None:
                q, a = generate_captcha()
                st.session_state.captcha_question = q
                st.session_state.captcha_answer = a
            
            st.divider()
            st.markdown("**Verify you're human**")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"<p style='margin: 0.5rem 0; font-weight: 600; font-size: 0.95rem;'>{st.session_state.captcha_question} = ?</p>", unsafe_allow_html=True)
            with col2:
                captcha_answer = st.number_input(
                    "Answer",
                    key="captcha_input",
                    step=1
                )
            
            submitted = st.form_submit_button("Sign Up", use_container_width=True)
            
            if submitted:
                errors = []
                
                if not email or not username or not password:
                    errors.append("All fields are required")
                if password != confirm_password:
                    errors.append("Passwords do not match")
                if not verify_captcha(captcha_answer, st.session_state.captcha_answer):
                    errors.append("Incorrect security answer")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    with st.spinner("Creating account..."):
                        success, result = signup_user(email, username, password)
                        
                        if success:
                            st.success("Account created successfully! Please sign in.")
                            st.session_state.captcha_question = None
                            st.session_state.captcha_answer = None
                            st.balloons()
                        else:
                            st.error(f"Signup failed: {result}")
