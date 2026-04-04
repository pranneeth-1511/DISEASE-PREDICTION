import streamlit as st
import appwrite_utils as aw

def show_auth_page():
    # --- Responsive CSS ---
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px;
        }

        /* Image Styling */
        .login-image-container img {
            border-radius: 20px;
            object-fit: cover;
            width: 100%;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        }

        /* Form Card Styling */
        .auth-card {
            background-color: #ffffff;
            border-radius: 15px;
            border: 1px solid #f0f2f6;
            box-shadow: 0 8px 24px rgba(0,0,0,0.05);
        }

        /* Badge Styling */
        .badge-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .badge-item {
            display: inline-block;
            padding: 0.35rem 0.8rem;
            font-size: 0.8rem;
            font-weight: 600;
            border-radius: 50px;
            background-color: #f8f9fa;
            color: #343a40;
            border: 1px solid #e9ecef;
        }

        /* Fix for smaller screens to ensure padding doesn't break layout */
        @media (max-width: 768px) {
            .auth-card {
                padding: 1.5rem;
            }
            .login-image-container {
                margin-bottom: 2rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Define columns: Image on left (1.2), Branding + Form on right (1)
    login_col1, login_col2 = st.columns([1.2, 1], gap="large")

    with login_col1:
        # The image stays on the left side
        st.image("medical_login.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with login_col2:
        # --- Access Portal Card ---
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center; margin-top: 0; margin-bottom: 1.2rem; color: #212529; font-size: 1.4rem;">Access Portal</h3>', unsafe_allow_html=True)
        
        choice = st.radio("Mode", ["Login", "Sign Up"], horizontal=True, label_visibility="collapsed")
        
        # Add a small margin after radio
        st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="doctor@mediscan.ai")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
        
        if choice == "Login":
            if st.button("Secure Login", use_container_width=True, type="primary"):
                if email and password:
                    res = aw.sign_in_with_email(email, password)
                    if res and 'stoken' in res:
                        st.session_state.user = res
                        st.query_params["userid"] = res["localId"]
                        st.query_params["stoken"] = res["stoken"] # Persist HMAC for refresh
                        st.rerun()
                    else:
                        st.query_params.clear()
                        st.error("Authentication failed. Check your credentials.")
                else:
                    st.warning("Please enter your email and password.")
        else:
            if st.button("Create Account", use_container_width=True, type="primary"):
                if email and password:
                    res = aw.sign_up_with_email(email, password)
                    if res and 'stoken' in res:
                        st.session_state.user = res
                        st.query_params["userid"] = res["localId"]
                        st.query_params["stoken"] = res["stoken"] # Persist HMAC for refresh
                        st.success("Success! Account created.")
                        st.rerun()
                    else:
                        st.query_params.clear()
                        st.error(res.get('error', {}).get('message', 'Signup error'))
                else:
                    st.warning("Please provide valid details.")

        st.markdown('</div>', unsafe_allow_html=True)

        # Footer inside the second column for better alignment
        st.markdown("""
            <p style="text-align: center; font-size: 0.8rem; color: #ADB5BD; margin-top: 1.5rem;">
                © 2024 MediScan AI • Secure Healthcare Gateway
            </p>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(
        page_title="MediScan AI | Auth", 
        layout="wide", 
        initial_sidebar_state="collapsed"
    )
    show_auth_page()