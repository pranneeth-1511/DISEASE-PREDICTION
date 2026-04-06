import streamlit as st
import appwrite_utils as aw

@st.dialog("Confirm Permanent Deletion")
def confirm_delete_dialog(entry_id, diagnosis):
    st.warning(f"Are you sure you want to permanently delete the diagnosis record for **{diagnosis}**?")
    st.markdown(f"**Record ID:** `{entry_id}`")
    st.error("This action cannot be undone.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Confirm Purge", type="primary", use_container_width=True):
            with st.spinner("Purging record..."):
                aw.delete_diagnosis(entry_id)
                st.toast(f"Record {entry_id} has been permanently removed.", icon="🗑️")
                st.rerun()

def show_patient_history():
    st.markdown("""
    <style>
        .block-container {
            background: 
                radial-gradient(circle at 50% 0%, rgba(0, 104, 201, 0.06) 0%, transparent 75%),
                linear-gradient(180deg, #f8fafc 0%, #eff6ff 100%) !important;
        }
        
        .header-text {
            font-weight: 700;
            color: #1e293b;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        
        .row-text {
            color: #334155;
            font-size: 0.9rem;
        }
        
        .notes-text {
            font-size: 0.8rem;
            color: #64748b;
            font-style: italic;
            margin-top: 4px;
        }
        
        .badge {
            padding: 4px 10px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 700;
        }
        .badge-success { background-color: #dcfce7; color: #166534; }
        .badge-warning { background-color: #fef9c3; color: #854d0e; }
    </style>
    """, unsafe_allow_html=True)
    st.header("🩺 Patient Records Archive")
    st.markdown("Administrative access to all patient diagnostic data.")
    
    with st.container():
        all_users = aw.get_all_users()
        user_options = {f"{u['email']} (ID: {u['userid']})": u['userid'] for u in all_users if u.get('role', 'user') == 'user'}
        
        selected_user_label = st.selectbox("Select Patient to View", 
                                          options=["--- Select a Patient ---"] + list(user_options.keys()),
                                          help="Search for a patient by email or UUID.")

    if selected_user_label and selected_user_label != "--- Select a Patient ---":
        selected_userid = user_options[selected_user_label]
        st.divider()
        st.subheader(f"📊 Activity for {selected_user_label.split(' ')[0]}")
        
        with st.spinner("Retrieving secure records..."):
            try:
                p_history = aw.get_diagnosis_history(selected_userid)
                if not p_history:
                    st.info("This patient has no recorded diagnostic activity.")
                else:
                    # Table Headers
                    th_cols = st.columns([1.5, 1.2, 2.5, 0.8, 1.5], gap="medium")
                    with th_cols[0]: st.markdown('<span class="header-text">📅 Datetime</span>', unsafe_allow_html=True)
                    with th_cols[1]: st.markdown('<span class="header-text">🧪 Category</span>', unsafe_allow_html=True)
                    with th_cols[2]: st.markdown('<span class="header-text">📄 Diagnosis</span>', unsafe_allow_html=True)
                    with th_cols[3]: st.markdown('<span class="header-text">📊 Conf.</span>', unsafe_allow_html=True)
                    with th_cols[4]: st.markdown('<span class="header-text">🛠️ Actions</span>', unsafe_allow_html=True)
                    
                    st.markdown('<hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #e2e8f0;">', unsafe_allow_html=True)

                    for index, entry in enumerate(p_history):
                        conf_percent = entry['confidence'] * 100
                        badge_style = "badge-success" if conf_percent > 85 else "badge-warning"
                        timestamp = entry['timestamp'].strftime('%b %d, %Y • %H:%M')
                        
                        row_cols = st.columns([1.5, 1.2, 2.5, 0.8, 1.5], gap="medium")
                        
                        with row_cols[0]: 
                            st.markdown(f'<span class="row-text">{timestamp}</span>', unsafe_allow_html=True)
                        
                        with row_cols[1]:
                            st.markdown(f'<span class="badge badge-success" style="opacity: 0.8;">{entry.get("type", "General")}</span>', unsafe_allow_html=True)
                        
                        with row_cols[2]:
                            st.markdown(f'**{entry.get("diagnosis", "Unknown")}**', unsafe_allow_html=True)
                            if 'notes' in entry and entry['notes']:
                                st.markdown(f'<div class="notes-text">📝 {entry["notes"][:70]}...</div>' if len(entry['notes']) > 70 else f'<div class="notes-text">📝 {entry["notes"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div style="font-size: 0.65rem; color: #cbd5e1; font-family: monospace; margin-top: 4px;">Record ID: {entry.get("id", "N/A")}</div>', unsafe_allow_html=True)

                        with row_cols[3]:
                            st.markdown(f'<span class="badge {badge_style}">{conf_percent:.1f}%</span>', unsafe_allow_html=True)
                        
                        with row_cols[4]:
                            # Action Column with buttons
                            a_col1, a_col2 = st.columns(2)
                            with a_col1:
                                view_image = st.button("🖼️", key=f"view_{entry['id']}", help="View Clinical Scan")
                            with a_col2:
                                purge_request = st.button("🗑️", key=f"del_{entry['id']}", help="Purge Patient Record")
                            
                            if view_image:
                                if 'image_url' in entry and entry['image_url']:
                                    show_scan_modal(entry['image_url'], entry.get('diagnosis', 'Unknown'))
                                else:
                                    st.warning("No image found.")
                                    
                            if purge_request:
                                confirm_delete_dialog(entry['id'], entry.get('diagnosis', 'Unknown'))

                        st.markdown('<hr style="margin: 0.3rem 0; border: none; border-top: 1px solid #f1f5f9;">', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error accessing patient database: {e}")
