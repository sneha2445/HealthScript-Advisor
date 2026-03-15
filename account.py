import streamlit as st
import os
try:
    import firebase_admin
    from firebase_admin import auth
    firebase_available = True
except ImportError:
    firebase_available = False
import requests
import re
# from google.auth import exceptions as google_exceptions

import smtplib
from email.mime.text import MIMEText
import random
import time
from dotenv import load_dotenv

load_dotenv()

# GMAIL OTP SETTINGS & HELP
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "healthscriptadvisor@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
API_KEY = os.getenv("FIREBASE_WEB_API_KEY") 
countries = {
    "India (+91)": "+91",
    "USA (+1)": "+1",
    "UK (+44)": "+44",
    "Canada (+1)": "+1",
    "Australia (+61)": "+61",
    "Germany (+49)": "+49"
}

def send_email_otp(receiver_email, otp):
    """Gmail ke zariye OTP bhejne ka function"""
    # Read variables inside the function to catch .env updates without restarting the whole app
    load_dotenv()
    sender_user = os.getenv("SENDER_EMAIL", "healthscriptadvisor@gmail.com")
    sender_pass = os.getenv("SENDER_PASSWORD")

    if not sender_pass or sender_pass == "your-google-app-password-here":
        return False, "SENDER_PASSWORD is not set correctly in your .env file. Please put your 16-character Google App Password there."

    subject = "HealthScript Advisor - OTP Verification"
    body = f"""Hello,
Your OTP for HealthScript Advisor verification is: {otp}
This OTP will expire in 2 minutes. Do not share this OTP with anyone.
Regards,
HealthScript Advisor Team 🩺"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_user
    msg["To"] = receiver_email

    try:
        # Try SSL port 465 first
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
            server.login(sender_user, sender_pass)
            server.sendmail(sender_user, receiver_email, msg.as_string())
            server.quit()
            return True, ""
        except Exception:
            # Fallback to STARTTLS on port 587
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
            server.starttls()
            server.login(sender_user, sender_pass)
            server.sendmail(sender_user, receiver_email, msg.as_string())
            server.quit()
            return True, ""
    except Exception as e:
        error_msg = str(e)
        print("Email sending failed:", error_msg)
        return False, error_msg

def validate_username(username):
    """Check karega ki username unique aur sahi hai ya nahi"""
    if not firebase_available:
        return False, "Username validation unavailable due to Firebase configuration."
    
    if len(username) < 8:
        return False, "Username must be at least 8 characters long."
    if not username.isalnum():
        return False, "Username must contain only letters and numbers."
    try:
        # Check if UID (Username) already exists in Firebase
        auth.get_user(username)
        return False, "Username already exists. Please choose a different one."
    except firebase_admin.auth.UserNotFoundError:
        # If the user is NOT found, then the username is unique and valid!
        return True, ""
    except Exception as e:
        # If some other unexpected error occurs (e.g. network issue)
        return False, f"Error validating username: {e}"

#  ACCOUNT CREATION & LOGIN 
def account():
    # ---------------- SESSION STATES ----------------
    if "user_role" not in st.session_state:
        st.session_state.user_role = "Patient"
    if "user_mail" not in st.session_state:
        st.session_state.user_mail = ""
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""
    if "signedOut" not in st.session_state:
        st.session_state.signedOut = False
    if "signOut" not in st.session_state:
        st.session_state.signOut = False
    
    # OTP specific session states
    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False
    if "otp_verified" not in st.session_state:
        st.session_state.otp_verified = False
    if "generated_otp" not in st.session_state:
        st.session_state.generated_otp = None
    if "otp_time" not in st.session_state:
        st.session_state.otp_time = None

    def logout():
        st.session_state.predicted = False
        st.session_state.signOut = False
        st.session_state.signedOut = False
        st.session_state.user_name = ""
        st.session_state.user_mail = ""
        st.session_state.otp_sent = False
        st.session_state.otp_verified = False

 # ---------------- LOGIN / SIGNUP MENU ----------------
    if not st.session_state['signedOut']:
        st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem !important;
            max-width: 900px !important;
        }
        button[kind="secondary"] {
            border: none;
            background: none;
            padding: 0;
            color: #1f77b4;
            text-align: left;
        }
        button[kind="secondary"]:hover {
            color: #0c5087;
            text-decoration: underline;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            try:
                st.image("static/Login-DocBuddy.png")
            except Exception as e:
                st.info("Welcome to HealthScript Advisor! Login image not available.")
            if "auth_mode" not in st.session_state:
                st.session_state.auth_mode = "Login"

            #Login 
            if st.session_state.auth_mode == "Login":
                st.subheader("Login to Your Account 🔐")
                login_input = st.text_input("Email OR Username 📧 / 👤").strip()
                password = st.text_input("Password 🔑", type="password")

                col1, col2 = st.columns([2.5, 1.5])
                with col1:
                    if st.button("Forgot Password?"):
                        st.session_state.show_forgot_pw = not st.session_state.get("show_forgot_pw", False)
                
                login_submit = st.button("Login")

                if st.session_state.get("show_forgot_pw", False):
                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 14px; margin-bottom: 5px;'><b>Reset Password</b></p>", unsafe_allow_html=True)
                    reset_email = st.text_input("Enter your registered Email to get a reset link", placeholder="Email")
                    if st.button("Send Reset Link"):
                        if reset_email:
                            reset_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}"
                            requests.post(reset_url, json={"requestType": "PASSWORD_RESET", "email": reset_email})
                            st.success("Password Reset Email Sent successfully 📩")
                            st.session_state.show_forgot_pw = False
                            st.rerun()
                        else:
                            st.warning("Please enter your email first.")
                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

                if login_submit:
                    if not st.session_state.get("firebase_available", False):
                        st.error("❌ Firebase is not initialized. Please check your credentials file or Streamlit Secrets.")
                        return

                    st.toast("Attempting login...", icon="🔐")
                    # Enforce Doctor Login
                    if login_input == "Tripathipramoad24" or login_input == "pramoadtri24@gmail.com":
                        if password == "Pramoad@1984":
                            try:
                                user_record = auth.get_user("Tripathipramoad24")
                            except Exception:
                                try:
                                    auth.create_user(
                                        uid="Tripathipramoad24",
                                        email="pramoadtri24@gmail.com",
                                        password="Pramoad@1984",
                                        display_name="DR. Pramoad Suryakant Tripathi",
                                        email_verified=True
                                    )
                                except Exception as e:
                                    st.error(f"❌ Firebase Error: {e}")
                                    return
                            
                            st.success("Login Successful 🎉 Welcome back, Doctor!")
                            st.session_state.user_uid = "Tripathipramoad24"
                            st.session_state.user_mail = "pramoadtri24@gmail.com"
                            st.session_state.user_name = "DR. Pramoad Suryakant Tripathi"
                            st.session_state.user_role = "Doctor"
                            st.session_state.signedOut = True
                            st.session_state.signOut = True
                            st.rerun()

                    try:
                        email_to_login = login_input
                        display_name = login_input
                        if "@" not in login_input:
                            try:
                                user_record = auth.get_user(login_input)
                                email_to_login = user_record.email
                            except Exception:
                                st.error("❌ Username not found.")
                                return
                        
                        login_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
                        payload = {"email": email_to_login, "password": password, "returnSecureToken": True}
                        resp = requests.post(login_url, json=payload, timeout=10)
    
                        if resp.status_code == 200:
                            user_data = resp.json()
                            id_token = user_data["idToken"]
                            
                            # Check verification
                            lookup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={API_KEY}"
                            lookup_resp = requests.post(lookup_url, json={"idToken": id_token})
                            verified = lookup_resp.json()["users"][0]["emailVerified"]
    
                            if verified:
                                # Fetch role from Firestore
                                from firebase_admin import firestore
                                try:
                                    db = firestore.client()
                                    user_doc = db.collection("users").document(email_to_login).get()
                                    role = user_doc.to_dict().get("role", "Patient") if user_doc.exists else "Patient"
                                except:
                                    role = "Patient"
                                
                                st.success("Login Successful 🎉")
                                st.session_state.user_mail = email_to_login
                                st.session_state.user_name = display_name
                                st.session_state.user_role = role
                                st.session_state.signedOut = True
                                st.session_state.signOut = True
                                st.rerun()
                            else:
                                st.warning("⚠️ Email not verified.")
                        else:
                            st.error("❌ Invalid credentials.")
                    except Exception as e:
                        st.error(f"Login failed: {e}")
                st.write("")
                c1, c2 = st.columns([0.65, 0.35])
                with c1:
                    st.markdown("<p style='margin-top: 5px; text-align: right;'>Don't have an account?</p>", unsafe_allow_html=True)
                with c2:
                    if st.button("Sign Up", key="btn_signup_link", use_container_width=True):
                        st.session_state.auth_mode = "Sign Up"
                        st.rerun()
    
            # --------------------SIGNUP SECTION ------------
            else:
                st.subheader("Create a New Account 🌟")
                email = st.text_input("Enter Email 📧").strip()
    
                #  STEP 1: SEND OTP 
                if not st.session_state.otp_sent:
                    if st.button("Send OTP"):
                        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                        if not re.match(email_pattern, email):
                            st.error("Invalid Email format! Please use standard format.")
                        else:
                            otp = random.randint(100000, 999999)
                            sent, error_log = send_email_otp(email, otp)
                            if sent:
                                st.session_state.generated_otp = otp
                                st.session_state.otp_sent = True
                                st.session_state.otp_time = time.time()
                                st.success(f"OTP successfully sent to {email} 📩")
                                st.rerun()
                            else:
                                st.error(f"Failed to send OTP: {error_log}")
                                st.info("Check if: 1. SENDER_EMAIL/PASSWORD in .env are correct. 2. You are using a 16-character App Password (not your Gmail password). 3. Internet is working.")
    
                # -------- STEP 2: VERIFY OTP --------
                elif st.session_state.otp_sent and not st.session_state.otp_verified:
                    st.info(f"OTP sent to: {email}")
                    entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6)              
                    # Check Expiry
                    if st.session_state.otp_time:
                        remaining = 120 - int(time.time() - st.session_state.otp_time)
                        if remaining > 0:
                            st.caption(f"⏳ OTP expires in {remaining} seconds")
                        else:
                            st.error("OTP has Expired! Please request a new one.")
                            if st.button("Reset / Resend OTP"):
                                st.session_state.otp_sent = False
                                st.rerun()
    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Verify OTP"):
                            if str(entered_otp) == str(st.session_state.generated_otp):
                                st.success("OTP Verified Successfully ✅")
                                st.session_state.otp_verified = True
                                st.rerun()
                            else:
                                st.error("❌ Invalid OTP entered. Try again.")
                    with col2:
                        if st.button("Cancel & Change Email"):
                            st.session_state.otp_sent = False
                            st.rerun()
    
                # -------- STEP 3: CREATE ACCOUNT DETAILS --------
                if st.session_state.otp_verified:
                    st.success("Email Verified ✅ Now complete your profile.")
                    # Distinguish between Patient Name (Display) and Username (Login UID)
                    patientName = st.text_input("Full Name 🏷️")
                    userRole = st.selectbox("I am a:", ["Patient", "Doctor"])
                    userName = st.text_input("Create Username 👤 (min 8 chars, alphanumeric) - Used for Login")
                    password = st.text_input("Create Password 🔑", type="password")
                    st.caption("Password must be 8+ chars, contain A-Z, a-z, 0-9, and special char (@#$%&*)")             
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        country = st.selectbox("Country 🌍", list(countries.keys()))
                        std_code = countries[country]
                    with c2:
                        phone = st.text_input(f"Mobile Number ({std_code})")
    
                    if st.button("Create My Account"):
                        if not patientName.strip():
                            st.error("❌ Please enter your Patient Name.")
                            return
                        # Username Validation
                        valid, msg = validate_username(userName)
                        if not valid:
                            st.error(f"❌ {msg}")
                            return
                        # Password Validation
                        pass_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%&*])[A-Za-z\d@#$%&*]{8,}$"
                        if not re.match(pass_pattern, password):
                            st.error("❌ Weak Password! Check the requirements mentioned above.")
                            return
                        
                        if not phone.isdigit():
                            st.error("❌ Please enter a valid phone number.")
                            return
                        try:
                            # Account Create in Firebase
                            user_params = {
                                "email": email,
                                "password": password,
                                "uid": userName, # Set UID as Username for login capability
                                "display_name": patientName.strip(), # Display name is the real patient name
                                "email_verified": False # Forced false so they get verification link on 1st login if needed
                            }
                            if phone:
                                user_params["phone_number"] = std_code + phone                      
                            if not st.session_state.get('firebase_available', True):
                                st.error("❌ Firebase Authorization Failed: Account creation is currently unavailable.")
                                return
                            try:
                                user = auth.create_user(**user_params)
                            except (google_exceptions.RefreshError, Exception) as e:
                                st.error(f"❌ Firebase Error: {e}")
                                return
                            
                            # Save additional info to Firestore
                            try:
                                from firebase_admin import firestore
                                db = firestore.client()
                                db.collection("users").document(email).set({
                                    "role": userRole,
                                    "name": patientName.strip(),
                                    "username": userName,
                                    "email": email
                                })
                            except Exception as e:
                                st.warning(f"⚠️ Account created but profile details could not be saved to Firestore: {e}")
                            
                            st.success(f"Account Created Successfully! Welcome {patientName.strip()} 🥳")
                            st.balloons()
                            st.info("Please switch to 'Login' from the menu above to login with your new Username/Email.")                  
                            # Reset states for next time
                            st.session_state.otp_sent = False
                            st.session_state.otp_verified = False                  
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")

                st.write("")
                c1, c2 = st.columns([0.65, 0.35])
                with c1:
                    st.markdown("<p style='margin-top: 5px; text-align: right;'>Already have an account?</p>", unsafe_allow_html=True)
                with c2:
                    if st.button("Login", key="btn_login_link", use_container_width=True):
                        st.session_state.auth_mode = "Login"
                        st.rerun()

    # ---------------- DASHBOARD (LOGGED IN STATE) ----------------
    if st.session_state.signOut:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Dashboard")
        st.sidebar.success(f"Logged in as: {st.session_state.user_name}")
        st.sidebar.button("Log Out 👋", on_click=logout)

        # ---- Profile Update Section ----------------------------------------
        st.title("👤 Account & Profile")
        st.caption(f"Logged in as **{st.session_state.user_name}** | 📧 {st.session_state.user_mail}")
        st.divider()

        uid = st.session_state.get('user_uid', st.session_state.get('user_name', ''))
        try:
            # First, check if UID exists in Firebase Auth
            user_record = auth.get_user(uid)
            current_email = user_record.email or st.session_state.user_mail
            current_phone = user_record.phone_number or ""
        except Exception as e:
            # If USER_NOT_FOUND, set default for doctors
            if st.session_state.get("user_role") == "Doctor":
                current_email = st.session_state.get('user_mail', 'pramoadtri24@gamil.com')
                current_phone = "8197964567"
            else:
                current_email = st.session_state.get('user_mail', '')
                current_phone = ""
            # Try to get user by Email instead of UID/Username
            try:
                user_record = auth.get_user_by_email(st.session_state.user_mail)
                current_email = user_record.email
                current_phone = user_record.phone_number or ""
                # Update session state UID to match found user if necessary
                uid = user_record.uid
            except Exception:
                pass

        # Init profile OTP state keys
        for key, default in [
            ("prof_otp_sent", False), ("prof_otp_verified", False),
            ("prof_generated_otp", None), ("prof_otp_time", None), ("prof_new_email", "")
        ]:
            if key not in st.session_state:
                st.session_state[key] = default

        if "edit_profile" not in st.session_state:
            st.session_state.edit_profile = False

        if not st.session_state.edit_profile:
            # --- READ-ONLY VIEW ---
            with st.container(border=True):
                st.subheader("Your Profile Details 📋")
                
                # For doctors, always show the fixed name
                if st.session_state.get("user_role") == "Doctor":
                    st.markdown(f"**Name:** &nbsp; DR. Pramoad Suryakant Tripathi")
                else:
                    try:
                        # Robust check for display name
                        user_info = auth.get_user(uid)
                        display_name_val = user_info.display_name
                    except Exception:
                        try:
                            user_info = auth.get_user_by_email(st.session_state.user_mail)
                            display_name_val = user_info.display_name
                        except:
                            display_name_val = "Not Set"
                    st.markdown(f"**Patient Name / Display Name:** &nbsp; {display_name_val or 'Not Set'}")
                
                st.markdown(f"**Email Address:** &nbsp; {current_email}")
                st.markdown(f"**Phone Number:** &nbsp; {current_phone or 'Not Set'}")
                
                st.write("")
                if st.button("Edit Profile ✏️"):
                    st.session_state.edit_profile = True
                    st.rerun()
        else:
            # --- EDIT MODE ---
            if st.button("⬅️ Cancel Editing"):
                st.session_state.edit_profile = False
                st.rerun()
                
            # ── 1. Patient / Display Name ──────────────────────────────────────
            with st.container(border=True):
                st.subheader("🏷️ Patient / Display Name")
                
                # For doctors, show name as read-only
                if st.session_state.get("user_role") == "Doctor":
                    st.info(f"Name: **DR. Pramoad Suryakant Tripathi**")
                    st.caption("Doctor name cannot be changed.")
                else:
                    new_patient_name = st.text_input("Full Name", placeholder="Enter your full name", key="prof_patient_name")
                    if st.button("Save Name", key="save_patient_name"):
                        if new_patient_name.strip():
                            try:
                                auth.update_user(uid, display_name=new_patient_name.strip())
                                # Update or Create Firestore record
                                from firebase_admin import firestore
                                db = firestore.client()
                                user_ref = db.collection("users").document(st.session_state.user_mail)
                                user_ref.set({
                                    "name": new_patient_name.strip(),
                                    "email": st.session_state.user_mail,
                                    "role": st.session_state.get("user_role", "Patient")
                                }, merge=True)
                                st.success(f"✅ Name updated to **{new_patient_name.strip()}**")
                            except Exception as e:
                                st.error(f"❌ {e}")
                        else:
                            st.warning("Please enter a name.")
    
            # ── 2. Email (OTP verified) ────────────────────────────────────────
            with st.container(border=True):
                st.subheader("📧 Email Address")
                st.info(f"Current Email: **{current_email}**")
    
                # Allow doctors to update email
                if not st.session_state.prof_otp_sent and not st.session_state.prof_otp_verified:
                    new_email_input = st.text_input("New Email Address", key="prof_new_email_input")
                    if st.button("Send OTP to New Email", key="prof_send_otp"):
                        import re as _re
                        if not _re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email_input):
                            st.error("❌ Invalid email format.")
                        else:
                            otp = random.randint(100000, 999999)
                            if send_email_otp(new_email_input, otp):
                                st.session_state.prof_generated_otp = otp
                                st.session_state.prof_otp_sent = True
                                st.session_state.prof_otp_time = time.time()
                                st.session_state.prof_new_email = new_email_input
                                st.success(f"OTP sent to **{new_email_input}** 📩")
                                st.rerun()
                            else:
                                st.error("Failed to send OTP.")
    
                elif st.session_state.prof_otp_sent and not st.session_state.prof_otp_verified:
                    st.info(f"OTP sent to: **{st.session_state.prof_new_email}**")
                    entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6, key="prof_enter_otp")
                    remaining = 120 - int(time.time() - st.session_state.prof_otp_time)
                    st.caption(f"⏳ OTP expires in {max(0, remaining)} seconds")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Verify & Update Email", key="prof_verify_otp"):
                            if str(entered_otp).strip() == str(st.session_state.prof_generated_otp):
                                try:
                                    auth.update_user(uid, email=st.session_state.prof_new_email, email_verified=True)
                                    # Update Firestore
                                    from firebase_admin import firestore
                                    db = firestore.client()
                                    # Get current data or create default to move to new document
                                    old_doc_ref = db.collection("users").document(st.session_state.user_mail)
                                    old_doc = old_doc_ref.get()
                                    if old_doc.exists:
                                        old_data = old_doc.to_dict()
                                        old_data['email'] = st.session_state.prof_new_email
                                        db.collection("users").document(st.session_state.prof_new_email).set(old_data)
                                        old_doc_ref.delete()
                                    else:
                                        db.collection("users").document(st.session_state.prof_new_email).set({
                                            "email": st.session_state.prof_new_email,
                                            "name": auth.get_user(uid).display_name or "User",
                                            "role": st.session_state.get("user_role", "Patient")
                                        })
                                    
                                    st.session_state.user_mail = st.session_state.prof_new_email
                                    st.session_state.prof_otp_verified = True
                                    st.session_state.prof_otp_sent = False
                                    st.success(f"✅ Email updated to **{st.session_state.prof_new_email}**")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ {e}")
                            else:
                                st.error("❌ Incorrect OTP.")
                    with col2:
                        if st.button("Cancel OTP", key="prof_cancel_otp"):
                            st.session_state.prof_otp_sent = False
                            st.rerun()
    
                elif st.session_state.prof_otp_verified:
                    st.success(f"✅ Email updated to: **{st.session_state.prof_new_email}**")
                    if st.button("Change Again", key="prof_reset_email"):
                        st.session_state.prof_otp_verified = False
                        st.rerun()
    
            # ── 3. Phone Number ───────────────────────────────────────────────
            with st.container(border=True):
                st.subheader("📱 Phone Number")
                if current_phone:
                    st.info(f"Current Phone: **{current_phone}**")
                
                # Allow doctors to update phone
                c1, c2 = st.columns([1, 2])
                with c1:
                    country = st.selectbox("Country Code 🌍", list(countries.keys()), key="prof_country")
                    std_code = countries[country]
                with c2:
                    new_phone = st.text_input(f"New Phone Number ({std_code})", key="prof_phone")
                if st.button("Update Phone", key="save_phone"):
                    if not new_phone.strip().isdigit():
                        st.error("❌ Digits only please.")
                    else:
                        try:
                            phone_full = std_code + new_phone.strip()
                            # For doctors, use email-based lookup if UID fails
                            try:
                                auth.update_user(uid, phone_number=phone_full)
                            except Exception:
                                # Fallback: try to get user by email and update
                                user_record = auth.get_user_by_email(st.session_state.user_mail)
                                auth.update_user(user_record.uid, phone_number=phone_full)
                                uid = user_record.uid
                            
                            # Update or Create Firestore record
                            from firebase_admin import firestore
                            db = firestore.client()
                            user_ref = db.collection("users").document(st.session_state.user_mail)
                            user_ref.set({
                                "phone": phone_full,
                                "email": st.session_state.user_mail,
                                "role": st.session_state.get("user_role", "Patient")
                            }, merge=True)
                            st.success(f"✅ Phone updated to **{phone_full}**")
                        except Exception as e:
                            st.error(f"❌ {e}")

