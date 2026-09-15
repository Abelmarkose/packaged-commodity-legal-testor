import streamlit as st
import numpy as np
import cv2
from PIL import Image
import pandas as pd
import json
import base64
import time
import io    # <-- ADD THIS LINE

from core.ocr_engine import OCREngine
from core.detector import LogoDetector
from core.rule_validator import LegalMetrologyValidator
from core.database import (
    save_inspection,
    get_all_inspections,
    get_inspection_by_id,
    generate_export_files
)

st.set_page_config(
    page_title="Legal Metrology AI Inspector",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# GLOBAL STYLING & JUMPING RABBIT CSS ANIMATION
# -------------------------------------------------------------
st.markdown("""
<style>
    /* Modern Slate & Navy Gradient Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(15, 23, 42) 0%, rgb(3, 7, 18) 90.2%);
        color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.36);
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        text-align: center;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Jumping Rabbit Loader Styles */
    .rabbit-loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
    }
    
    .rabbit {
        font-size: 65px;
        display: inline-block;
        animation: rabbit-jump 0.65s infinite alternate ease-in-out;
    }

    .shadow-ground {
        width: 50px;
        height: 12px;
        background: rgba(0, 0, 0, 0.4);
        border-radius: 50%;
        margin-top: -10px;
        animation: shadow-scale 0.65s infinite alternate ease-in-out;
    }

    @keyframes rabbit-jump {
        0% { transform: translateY(0) scale(1.1, 0.85); }
        50% { transform: translateY(-45px) scale(0.9, 1.1); }
        100% { transform: translateY(-60px) scale(1, 1); }
    }

    @keyframes shadow-scale {
        0% { transform: scale(1.2); opacity: 0.6; }
        100% { transform: scale(0.5); opacity: 0.2; }
    }

    .loading-text {
        margin-top: 25px;
        font-size: 1.15rem;
        font-weight: 600;
        color: #38bdf8;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# APP STATE INITIALIZATION
# -------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "scan_image" not in st.session_state:
    st.session_state.scan_image = None
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None

@st.cache_resource
def load_ocr():
    return OCREngine()

def navigate_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# =============================================================
# VIEW 1: HOME PAGE
# =============================================================
if st.session_state.page == "home":
    st.markdown('<div class="hero-title">⚖️ Legal Metrology Compliance AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Automated Statutory Verification Engine | SIH26034 (Team chandanamazha)</div>', unsafe_allow_html=True)

    # Launchpad Call-to-Action
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <h3 style="margin-bottom: 10px;">Ready for Statutory Audit?</h3>
            <p style="color: #94a3b8; font-size: 0.95rem;">Capture packaging using live camera or multi-angle 360° rotational scan to inspect Rule 6 declarations.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📷 Launch Camera / Start Inspection", use_container_width=True, type="primary"):
            navigate_to("camera")

    st.markdown("---")

    # History & Audit Logs Registry
    st.markdown("### 📋 Recent Inspection History & Logs")
    records = get_all_inspections()

    if not records:
        st.info("No past inspection audits recorded. Click 'Launch Camera' above to perform your first audit.")
    else:
        df_history, csv_data, excel_data = generate_export_files(records)

        # Quick KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Scanned Products", len(records))
        k2.metric("Compliant / Approved", sum(1 for r in records if "APPROVED" in r.final_decision or "EXEMPTION" in r.final_decision))
        k3.metric("Notices Issued (Sec 36)", sum(1 for r in records if "NOTICE" in r.final_decision), delta_color="inverse")
        k4.metric("Officer Overrides", sum(1 for r in records if r.is_overridden))

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_history, use_container_width=True, hide_index=True)

        # Master Export Downloads
        dcol1, dcol2, _ = st.columns([1, 1, 2])
        with dcol1:
            st.download_button(
                "📊 Export Master Excel (.xlsx)",
                data=excel_data,
                file_name=f"legal_metrology_master_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with dcol2:
            st.download_button(
                "📄 Export Master CSV",
                data=csv_data,
                file_name=f"legal_metrology_master_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# =============================================================
# VIEW 2: CAMERA & CAPTURE SELECTION
# =============================================================
elif st.session_state.page == "camera":
    top_col1, top_col2 = st.columns([1, 6])
    with top_col1:
        if st.button("⬅️ Home"):
            navigate_to("home")
    with top_col2:
        st.markdown("### 📷 Package Capture & Inspection Angle")

    cam_col, upload_col = st.columns(2)

    with cam_col:
        st.markdown("""
        <div class="glass-card">
            <h4>Option 1: Device Camera Snapshot</h4>
            <p style="color: #94a3b8; font-size: 0.9rem;">Snap packaging back-of-pack or front panel directly.</p>
        </div>
        """, unsafe_allow_html=True)
        camera_photo = st.camera_input("Take Picture")
        if camera_photo:
            st.session_state.scan_image = Image.open(camera_photo)

    with upload_col:
        st.markdown("""
        <div class="glass-card">
            <h4>Option 2: High-Resolution Photo Upload</h4>
            <p style="color: #94a3b8; font-size: 0.9rem;">Upload photo directly from mobile or inspector gallery.</p>
        </div>
        """, unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        if uploaded:
            st.session_state.scan_image = Image.open(uploaded)

    if st.session_state.scan_image is not None:
        st.markdown("---")
        st.markdown("#### Configure Inspection Mode")

        mode_choice = st.radio(
            "Scan Processing Mode:",
            [
                "Standard Single-Frame Scan",
                "🔄 360° Multi-Angle Panoramic Extraction (Scans 0°, 90°, 180°, 270° for Vertical Sidebars & Thermal Stamps)"
            ]
        )
        st.session_state.scan_mode = mode_choice

        if st.button("🚀 Analyze Package Compliance Now", type="primary", use_container_width=True):
            navigate_to("loading")

# =============================================================
# VIEW 3: JUMPING RABBIT AI LOADER
# =============================================================
elif st.session_state.page == "loading":
    loader_placeholder = st.empty()

    with loader_placeholder.container():
        st.markdown("""
        <div class="rabbit-loader-container">
            <div class="rabbit">🐇</div>
            <div class="shadow-ground"></div>
            <div class="loading-text">AI is auditing Legal Metrology Rules...</div>
            <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 8px;">
                Enhancing contrast • Reading thermal ink • Decoding QR licensing • Verifying PIN & MRP
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Perform Analysis
    img_np = np.array(st.session_state.scan_image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Multi-orientation rotation processing if selected
    ocr_engine = load_ocr()
    ocr_results = ocr_engine.extract_text(img_bgr)

    # OpenCV QR Decoder
    detector = cv2.QRCodeDetector()
    qr_text, qr_bbox, _ = detector.detectAndDecode(img_bgr)
    if qr_text:
        ocr_results.append({
            "text": f"QR_METROLOGY_DECODED: {qr_text}",
            "confidence": 1.0,
            "box": qr_bbox[0].tolist() if qr_bbox is not None else []
        })

    # Run Statutory Detectors
    logo_res = LogoDetector.detect_symbol(img_bgr)
    compliance_report = LegalMetrologyValidator.validate(ocr_results)

    # Save to session state
    st.session_state.audit_results = {
        "report": compliance_report,
        "ocr_results": ocr_results,
        "logo_result": logo_res,
        "qr_text": qr_text,
        "annotated_img": img_np
    }

    # Small pause to allow smooth animation before transition
    time.sleep(1.2)
    navigate_to("results")

# =============================================================
# VIEW 4: EVALUATION DASHBOARD & OFFICER REVIEW
# =============================================================
elif st.session_state.page == "results":
    res = st.session_state.audit_results
    compliance_report = res["report"]
    ocr_results = res["ocr_results"]
    logo_res = res["logo_result"]
    qr_text = res["qr_text"]

    nav_col1, nav_col2 = st.columns([1, 7])
    with nav_col1:
        if st.button("⬅️ New Scan"):
            st.session_state.scan_image = None
            st.session_state.audit_results = None
            navigate_to("home")
    with nav_col2:
        st.markdown("### ⚖️ Statutory Evaluation & Audit Verdict")

    col_view, col_eval = st.columns([1, 1.2])

    with col_view:
        st.image(res["annotated_img"], caption="Inspected Commodity Packaging", use_container_width=True)
        with st.expander("🔍 Show Captured Raw OCR Tokens"):
            st.write([item["text"] for item in ocr_results])

    with col_eval:
        total_rules = len(compliance_report)
        passed_rules = sum(1 for v in compliance_report.values() if v["status"] == "PASS")
        score = int((passed_rules / total_rules) * 100)

        # KPIs
        m1, m2, m3 = st.columns(3)
        m1.metric("Compliance Score", f"{score}%")
        
        is_veg = logo_res.get("found", False) or any("veg" in r["text"].lower() for r in ocr_results)
        m2.metric("Veg/Non-Veg Symbol", "Detected" if is_veg else "Not Detected",
                  delta="Compliant" if is_veg else "- Non-Compliant",
                  delta_color="normal" if is_veg else "inverse")

        has_lic = bool(qr_text) or any("lic" in item["text"].lower() for item in ocr_results)
        m3.metric("FSSAI / QR Disclosure", "Verified" if has_lic else "Missing",
                  delta="Compliant" if has_lic else "Manual Check",
                  delta_color="normal" if has_lic else "off")

        # Statutory Verdict Banner
        if score >= 75:
            ai_status = "COMPLIANT"
            st.success("✅ Compliant with Legal Metrology (Packaged Commodities) Rules, 2011")
        elif score >= 40:
            ai_status = "PARTIAL"
            st.warning("⚠️ Partial Compliance: Non-Critical Mandates Missing")
        else:
            ai_status = "NON-COMPLIANT"
            st.error("🚨 Non-Compliance Detected: Subject to Seizure Notice under Section 36")

        # Evaluation Table
        table_rows = []
        for param, d in compliance_report.items():
            table_rows.append({
                "Statutory Parameter": param.replace("_", " "),
                "Status": d["status"],
                "Extracted Text": d["extracted"],
                "Statutory Provision": d["rule"]
            })
        df_eval = pd.DataFrame(table_rows)
        st.dataframe(df_eval, use_container_width=True, hide_index=True)

        # -------------------------------------------------------------
        # OFFICER REMARK & REVIEW SYSTEM
        # -------------------------------------------------------------
        st.markdown("---")
        st.markdown("#### 👮 Officer Review & Action Center")

        with st.form("officer_review_form"):
            rcol1, rcol2 = st.columns(2)
            with rcol1:
                product_name_input = st.text_input("Product / Commodity Name", value="Packaged Commodity Sample")
                officer_id_input = st.text_input("Officer Name / ID", value="LM-Officer-704")
            with rcol2:
                review_decision = st.selectbox(
                    "Officer Final Verdict / Action",
                    [
                        "PASSED (Compliant / Valid Exemption)",
                        "ISSUE NOTICE (Section 36 Seizure / Fine)",
                        "RECHECK (Rescan Sample under better lighting)",
                        "CONFIRM EXEMPTION (Rule 26 Free Sample)"
                    ]
                )

            officer_notes = st.text_area("Officer Remarks / Seizure Notice Justification", 
                                        placeholder="E.g., Missing Unit Sale Price (USP) under Rule 6(11); issuing 15-day rectification notice.")
            
            save_clicked = st.form_submit_button("💾 Save Inspection & Generate Spreadsheet", type="primary", use_container_width=True)

            if save_clicked:
                new_id = save_inspection(
                    product_name=product_name_input,
                    ai_score=score,
                    ai_status=ai_status,
                    report_dict=compliance_report,
                    tokens_list=[item["text"] for item in ocr_results],
                    officer_name=officer_id_input,
                    final_decision=review_decision,
                    notes=officer_notes,
                    image_np=res["annotated_img"]
                )
                st.success(f"🎉 Inspection audit #{new_id} persisted to the database!")

        # -------------------------------------------------------------
        # EXCEL / CSV DOWNLOAD FOR THIS CURRENT AUDIT
        # -------------------------------------------------------------
        st.markdown("#### 📥 Download Individual Audit Report")
        col_dl1, col_dl2 = st.columns(2)

        # Build Excel for this single inspection
        single_excel_buffer = io.BytesIO()
        with pd.ExcelWriter(single_excel_buffer, engine='openpyxl') as writer:
            df_eval.to_excel(writer, index=False, sheet_name="Audit_Checklist")
        single_excel_data = single_excel_buffer.getvalue()

        with col_dl1:
            st.download_button(
                "📊 Download Audit as Excel (.xlsx)",
                data=single_excel_data,
                file_name=f"audit_{product_name_input.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_dl2:
            st.download_button(
                "📄 Download Audit as CSV",
                data=df_eval.to_csv(index=False).encode('utf-8'),
                file_name=f"audit_{product_name_input.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )