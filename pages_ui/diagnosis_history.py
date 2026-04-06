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
        .block-container {
            background: 
                linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%),
                repeating-linear-gradient(45deg, rgba(100, 116, 139, 0.01) 0px, rgba(100, 116, 139, 0.01) 1px, transparent 1px, transparent 10px) !important;
        }
        
        /* Table Header Styling */
        .table-header {
            background: #ffffff;
            border-bottom: 2px solid var(--primary-color, #0068C9);
            padding: 1rem 0.5rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
        }

        /* Table Row Styling */
        .table-row {
            background: #ffffff;
            border-bottom: 1px solid #edf2f7;
            padding: 1rem 0.5rem;
            display: flex;
            align-items: center;
            transition: background 0.2s ease;
        }
        .table-row:hover {
            background: #f8fafc;
        }

        .badge {
            padding: 4px 10px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 700;
        }
        .badge-success { background-color: #dcfce7; color: #166534; }
        .badge-warning { background-color: #fef9c3; color: #854d0e; }
        
        .header-text {
            font-weight: 700;
            color: #4a5568;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        
        .row-text {
            color: #2d3748;
            font-size: 0.9rem;
        }
        
        .notes-text {
            font-size: 0.8rem;
            color: #718096;
            font-style: italic;
            margin-top: 4px;
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
                # Table Headers
                th_cols = st.columns([1.8, 1.5, 2.5, 1.2, 1], gap="medium")
                with th_cols[0]: st.markdown('<span class="header-text">📅 Datetime</span>', unsafe_allow_html=True)
                with th_cols[1]: st.markdown('<span class="header-text">🧬 Category</span>', unsafe_allow_html=True)
                with th_cols[2]: st.markdown('<span class="header-text">⚖️ Diagnosis</span>', unsafe_allow_html=True)
                with th_cols[3]: st.markdown('<span class="header-text">📊 Conf.</span>', unsafe_allow_html=True)
                with th_cols[4]: st.markdown('<span class="header-text">🔍 Action</span>', unsafe_allow_html=True)
                
                st.markdown('<hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #edf2f7;">', unsafe_allow_html=True)

                for index, entry in enumerate(history):
                    conf_val = entry.get('confidence', 0) * 100
                    badge_class = "badge-success" if conf_val > 80 else "badge-warning"
                    timestamp = entry['timestamp'].strftime('%b %d, %Y • %H:%M')
                    
                    row_cols = st.columns([1.8, 1.5, 2.5, 1.2, 1], gap="medium")
                    
                    with row_cols[0]: 
                        st.markdown(f'<span class="row-text">{timestamp}</span>', unsafe_allow_html=True)
                    
                    with row_cols[1]:
                        st.markdown(f'<span class="badge badge-success" style="opacity: 0.8;">{entry.get("type", "General")}</span>', unsafe_allow_html=True)
                    
                    with row_cols[2]:
                        st.markdown(f'**{entry.get("diagnosis", "Unknown")}**', unsafe_allow_html=True)
                        if 'notes' in entry and entry['notes']:
                            st.markdown(f'<div class="notes-text">📝 {entry["notes"][:60]}...</div>' if len(entry['notes']) > 60 else f'<div class="notes-text">📝 {entry["notes"]}</div>', unsafe_allow_html=True)
                    
                    with row_cols[3]:
                        st.markdown(f'<span class="badge {badge_class}">{conf_val:.1f}%</span>', unsafe_allow_html=True)
                    
                    with row_cols[4]:
                        view_image = st.button(f"🖼️ View Scan", key=f"btn_{index}", use_container_width=True)
                    
                    if view_image:
                        if 'image_url' in entry and entry['image_url']:
                            show_scan_modal(entry['image_url'], entry.get('diagnosis', 'Unknown'))
                        else:
                            st.warning("No visual evidence found.")
                    
                    st.markdown('<hr style="margin: 0.3rem 0; border: none; border-top: 1px solid #f7fafc;">', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Failed to load history: {e}")

        except Exception as e:
            st.error(f"Failed to load history: {e}")