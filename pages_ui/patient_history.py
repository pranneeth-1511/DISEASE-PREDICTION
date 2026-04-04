import streamlit as st
import appwrite_utils as aw

def show_patient_history():
    st.header("🩺 Patient Records Archive")
    st.markdown("Administrative access to all patient diagnostic data.")
    
    with st.container():
        # st.markdown('<div class="card">', unsafe_allow_html=True)
        all_users = aw.get_all_users()
        user_options = {f"{u['email']} (ID: {u['userid']})": u['userid'] for u in all_users if u.get('role', 'user') == 'user'}
        
        selected_user_label = st.selectbox("Select Patient to View", 
                                          options=["--- Select a Patient ---"] + list(user_options.keys()),
                                          help="Search for a patient by email or UUID.")
        st.markdown('</div>', unsafe_allow_html=True)

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
                    for entry in p_history:
                        # Determine badge style
                        conf_percent = entry['confidence'] * 100
                        badge_style = "badge-success" if conf_percent > 85 else "badge-warning"
                        
                        st.markdown(f"""
                        <div class="card">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                                <div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">{entry['type']}</div>
                                    <h3 style="margin: 4px 0; color: var(--primary);">{entry['diagnosis']}</h3>
                                    <div style="font-size: 0.85rem; color: var(--text-muted);">
                                        📅 {entry['timestamp'].strftime('%b %d, %Y • %H:%M')}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <span class="badge {badge_style}">{conf_percent:.1f}% Confidence</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        col_img, col_txt = st.columns([1, 4])
                        with col_img:
                            if 'image_url' in entry:
                                st.image(entry['image_url'], use_container_width=True)
                            else:
                                st.markdown('<div style="aspect-ratio: 1; background: #F1F5F9; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">📝</div>', unsafe_allow_html=True)

                        with col_txt:
                            if 'notes' in entry:
                                st.markdown(f'<div style="background: #F8FAFC; padding: 10px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid var(--border);"><strong>Notes:</strong> {entry["notes"]}</div>', unsafe_allow_html=True)
                            
                            st.markdown(f"""
                                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 15px;">
                                    <div style="font-size: 0.7rem; color: #CBD5E1; font-family: monospace;">Record: {entry.get("id", "N/A")}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("🗑️ Purge Record", key=f"del_{entry['id']}", help="Permanently delete this diagnosis from the database."):
                                with st.spinner("Deleting..."):
                                    aw.delete_diagnosis(entry['id'])
                                    st.toast(f"Record {entry['id']} deleted.", icon="🗑️")
                                    st.rerun()

                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error accessing patient database: {e}")
