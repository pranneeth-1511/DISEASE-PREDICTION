import streamlit as st
import appwrite_utils as aw

@st.dialog("Diagnostic Scan View")
def show_scan_modal(image_url, diagnosis):
    st.image(image_url, caption=f"Scan Analysis: {diagnosis}", use_container_width=True)
    if st.button("Close View", use_container_width=True):
        st.rerun()

def show_diagnosis_history():
    # --- Enhanced CSS for Responsiveness ---
    st.markdown("""
    <style>
        .history-card {
            background-color: var(--background-color);
            border: 1px solid var(--border-color, #e0e0e0);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .badge {
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .badge-success { background-color: #dcfce7; color: #166534; }
        .badge-warning { background-color: #fef9c3; color: #854d0e; }
        
        /* Mobile adjustment */
        @media (max-width: 640px) {
            .history-header { flex-direction: column; align-items: flex-start; }
        }
    </style>
    """, unsafe_allow_html=True)

    st.header("📂 Personal Diagnosis History")
    st.markdown("All your previous AI-assisted diagnostic reports are stored securely here.")
    
    col_search, col_refresh = st.columns([4, 1])
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()

    with st.spinner("Fetching your records..."):
        try:
            # Assuming 'id' is the correct key for user identification
            history = aw.get_diagnosis_history(st.session_state.user['localId'])
            
            if not history:
                st.markdown("""
                <div style="text-align: center; padding: 60px; border: 2px dashed #cbd5e1; border-radius: 15px;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📂</div>
                    <h3 style="color: #64748b;">No records found</h3>
                    <p style="color: #94a3b8;">Your diagnostic history will appear here once you complete an analysis.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for index, entry in enumerate(history):
                    # Data Preparation
                    conf_val = entry.get('confidence', 0) * 100
                    badge_class = "badge-success" if conf_val > 80 else "badge-warning"
                    timestamp = entry['timestamp'].strftime('%b %d, %Y • %H:%M')
                    
                    # Main Card Container
                    with st.container():
                        st.markdown(f"""
                        <div class="history-card">
                            <div class="history-header">
                                <div>
                                    <span style="font-size: 0.7rem; color: #64748b; font-weight: 700; text-transform: uppercase;">{entry.get('type', 'General')}</span>
                                    <h3 style="margin: 0; color: var(--primary-color);">{entry.get('diagnosis', 'Unknown')}</h3>
                                    <p style="margin: 0; font-size: 0.85rem; color: #64748b;">📅 {timestamp}</p>
                                </div>
                                <span class="badge {badge_class}">{conf_val:.1f}% Confidence</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Action Row (Notes and Image View)
                        col_text, col_action = st.columns([3, 1])
                        
                        with col_text:
                            if 'notes' in entry:
                                st.info(f"**Clinical Notes:** {entry['notes']}")
                        
                        with col_action:
                            # Unique key for every button in the loop
                            view_image = st.button(f"🖼️ View Scan", key=f"btn_{index}", use_container_width=True)
                        
                        # Trigger Image Modal (Popup)
                        if view_image:
                            if 'image_url' in entry and entry['image_url']:
                                show_scan_modal(entry['image_url'], entry.get('diagnosis', 'Unknown'))
                            else:
                                st.warning("No visual evidence found for this diagnostic record.")
                        
                        # Depth details and ID
                        st.markdown(f"""
                            <div style="display: flex; justify-content: space-between; margin-top: -10px; padding: 0 5px;">
                                <small style="color: #94a3b8;">🔬 Scans: {entry.get('scan_count', 1)}</small>
                                <small style="color: #cbd5e1; font-family: monospace;">ID: {entry.get('id', 'N/A')[:8]}...</small>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Failed to load history: {e}")