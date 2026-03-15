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
import smtplib
from email.mime.text import MIMEText
import random
import time

# ---- Shared config (same as account.py) ----
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "healthscriptadvisor@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
API_KEY = os.getenv("FIREBASE_API_KEY")
countries = {
    "India (+91)": "+91",
    "USA (+1)": "+1",
    "UK (+44)": "+44",
    "Canada (+1)": "+1",
    "Australia (+61)": "+61",
    "Germany (+49)": "+49"
}

def send_otp_email(receiver_email, otp):
    subject = "HealthScript Advisor - Profile Update OTP"
    body = f"""Hello,
Your OTP for updating your profile on HealthScript Advisor is: {otp}
This OTP will expire in 2 minutes. Do not share this with anyone.
Regards,
HealthScript Advisor Team 🩺"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email OTP failed:", e)
        return False


def show_profile():
    """Render the Profile Update page — only shown to logged-in users."""

    if not firebase_available:
        st.error("Profile update feature is currently unavailable due to Firebase configuration.")
        return

    if not st.session_state.get("signOut", False):
        st.warning("🔒 Please log in to access your profile.")
        return

    st.title("👤 My Profile")
    st.caption(f"Logged in as: **{st.session_state.get('user_name', '')}**  |  📧 {st.session_state.get('user_mail', '')}")
    st.divider()

    # ── Fetch current Firebase user record ──────────────────────────────────
    try:
        uid = st.session_state.get('user_name', '')    # UID was set as username
        user_record = auth.get_user(uid)
        current_email = user_record.email or ""
        current_phone = user_record.phone_number or ""
    except Exception:
        # fallback if UID lookup fails
        current_email = st.session_state.get('user_mail', '')
        current_phone = ""

    # ── OTP session state keys (prefixed to avoid clash with signup page) ──
    for key, default in [
        ("prof_otp_sent", False),
        ("prof_otp_verified", False),
        ("prof_generated_otp", None),
        ("prof_otp_time", None),
        ("prof_new_email", ""),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ============================================================
    # SECTION 1 ── Patient / Display Name
    # ============================================================
    with st.container(border=True):
        st.subheader("🏷️ Patient / Display Name")
        new_patient_name = st.text_input(
            "Update Patient Name",
            placeholder="Enter your full name",
            key="prof_patient_name"
        )
        if st.button("Save Patient Name", type="primary", key="save_patient_name"):
            if new_patient_name.strip():
                try:
                    auth.update_user(uid, display_name=new_patient_name.strip())
                    st.success(f"✅ Patient Name updated to **{new_patient_name.strip()}**")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("Please enter a name before saving.")

    # ============================================================
    # SECTION 2 ── Username update
    # ============================================================
    with st.container(border=True):
        st.subheader("👤 Username")
        st.info(f"Current Username: **{st.session_state.get('user_name', '')}**")
        st.caption("⚠️ Changing your username will require you to log in again with the new username.")
        new_username = st.text_input(
            "New Username (min 8 alphanumeric chars)",
            key="prof_username"
        )
        if st.button("Update Username", type="primary", key="save_username"):
            if not new_username.strip():
                st.warning("Please enter a new username.")
            elif len(new_username) < 8 or not new_username.isalnum():
                st.error("❌ Username must be at least 8 alphanumeric characters.")
            else:
                try:
                    auth.get_user(new_username)
                    st.error("❌ That username is already taken. Try another.")
                except firebase_admin.auth.UserNotFoundError:
                    try:
                        # Firebase doesn't support UID rename — create new user record
                        # We store display name as the new username for reference.
                        auth.update_user(uid, display_name=new_username)
                        st.session_state.user_name = new_username
                        st.success(f"✅ Username display updated to **{new_username}**. Please log in again for full changes.")
                    except Exception as e:
                        st.error(f"Error updating: {e}")

    # ============================================================
    # SECTION 3 ── Email update (OTP-verified)
    # ============================================================
    with st.container(border=True):
        st.subheader("📧 Email Address")
        st.info(f"Current Email: **{current_email}**")

        if not st.session_state.prof_otp_sent:
            new_email_input = st.text_input("New Email Address", key="prof_new_email_input")
            if st.button("Send OTP to New Email", key="prof_send_otp"):
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, new_email_input):
                    st.error("❌ Invalid email format.")
                else:
                    otp = random.randint(100000, 999999)
                    if send_otp_email(new_email_input, otp):
                        st.session_state.prof_generated_otp = otp
                        st.session_state.prof_otp_sent = True
                        st.session_state.prof_otp_time = time.time()
                        st.session_state.prof_new_email = new_email_input
                        st.success(f"OTP sent to **{new_email_input}** 📩")
                        st.rerun()
                    else:
                        st.error("Failed to send OTP. Check email settings.")

        elif st.session_state.prof_otp_sent and not st.session_state.prof_otp_verified:
            st.info(f"OTP sent to: **{st.session_state.prof_new_email}**")
            entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6, key="prof_enter_otp")

            remaining = 120 - int(time.time() - st.session_state.prof_otp_time)
            if remaining > 0:
                st.caption(f"⏳ OTP expires in {remaining} seconds")
            else:
                st.error("OTP has expired.")
                if st.button("Resend OTP", key="prof_resend_otp"):
                    st.session_state.prof_otp_sent = False
                    st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Verify OTP & Update Email", type="primary", key="prof_verify_otp"):
                    if str(entered_otp).strip() == str(st.session_state.prof_generated_otp):
                        try:
                            auth.update_user(uid, email=st.session_state.prof_new_email, email_verified=True)
                            st.session_state.user_mail = st.session_state.prof_new_email
                            st.session_state.prof_otp_verified = True
                            st.session_state.prof_otp_sent = False
                            st.success(f"✅ Email updated to **{st.session_state.prof_new_email}**")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Firebase error: {e}")
                    else:
                        st.error("❌ Incorrect OTP. Try again.")
            with col2:
                if st.button("Cancel", key="prof_cancel_otp"):
                    st.session_state.prof_otp_sent = False
                    st.rerun()

        elif st.session_state.prof_otp_verified:
            st.success(f"✅ Email is up-to-date: **{st.session_state.prof_new_email}**")
            if st.button("Change Email Again", key="prof_reset_email"):
                st.session_state.prof_otp_verified = False
                st.session_state.prof_otp_sent = False
                st.rerun()

    # ============================================================
    # SECTION 4 ── Phone Number update
    # ============================================================
    with st.container(border=True):
        st.subheader("📱 Phone Number")
        if current_phone:
            st.info(f"Current Phone: **{current_phone}**")
        else:
            st.caption("No phone number on record.")

        c1, c2 = st.columns([1, 2])
        with c1:
            country = st.selectbox("Country Code 🌍", list(countries.keys()), key="prof_country")
            std_code = countries[country]
        with c2:
            new_phone = st.text_input(f"New Phone Number ({std_code})", key="prof_phone")

        if st.button("Update Phone Number", type="primary", key="save_phone"):
            if not new_phone.strip():
                st.warning("Please enter a phone number.")
            elif not new_phone.strip().isdigit():
                st.error("❌ Phone number must contain digits only.")
            else:
                try:
                    full_phone = std_code + new_phone.strip()
                    auth.update_user(uid, phone_number=full_phone)
                    st.success(f"✅ Phone number updated to **{full_phone}**")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    st.divider()
    st.caption("💡 Tip: Some changes like email require you to log in again to take full effect.")
