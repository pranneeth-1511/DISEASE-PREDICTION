import streamlit as st
import appwrite_utils as aw

def show_user_management():
    st.header("👥 System User Directory")
    st.markdown("Monitor and adjust access levels for all registered healthcare professionals.")
    st.divider()
    
    with st.spinner("Synchronizing user data..."):
        try:
            users = aw.get_all_users()
            
            # Header Row
            h1, h2, h3 = st.columns([3, 1.5, 1])
            with h1: st.markdown("**User Identity**")
            with h2: st.markdown("**Assigned Role**")
            with h3: st.markdown("**Actions**")
            st.markdown('<div style="height: 1px; background: var(--border); margin: 8px 0 16px 0;"></div>', unsafe_allow_html=True)

            for u in users:
                with st.container():
                    c1, c2, c3 = st.columns([3, 1.5, 1])
                    
                    with c1:
                        st.markdown(f"""
                        <div style="font-weight: 600; color: var(--text-main);">{u['email']}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">UUID: {u['userid']}</div>
                        """, unsafe_allow_html=True)
                    
                    with c2:
                        current_role = u.get('role', 'user')
                        new_role = st.selectbox("Role", 
                                              ["user", "admin"], 
                                              index=0 if current_role == 'user' else 1, 
                                              key=f"role_{u['id']}", 
                                              label_visibility="collapsed")
                    
                    with c3:
                        if new_role != current_role:
                            if st.button("Update", key=f"btn_{u['id']}", use_container_width=True):
                                try:
                                    aw.update_user_role(u['id'], new_role)
                                    st.toast(f"Updated {u['email']} to {new_role}", icon="✅")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Update failed: {e}")
                        else:
                            st.button("Saved", key=f"saved_{u['id']}", disabled=True, use_container_width=True)
                    
                    st.markdown('<div style="height: 1px; background: #F1F5F9; margin: 12px 0;"></div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"User synchronization failed: {e}")
