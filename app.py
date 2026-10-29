import streamlit as st
import requests
import json
import pandas as pd
import re
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

# --- Page Configuration ---
st.set_page_config(
    page_title="LoanIQ - Intelligent Loan Application Processor 🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling & Hiding Deploy Button ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Permanent 20% Left Sidebar (Dark Blue #0F172A) & 80% Main Content Partition */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    [data-testid="stToolbar"], .stAppDeployButton, #MainMenu, footer, [data-testid="stDecoration"],
    [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"] {
        display: none !important;
        visibility: hidden !important;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    /* Headings - Professional Dark Blue */
    h1, h2, h3, h4, h5, h6 {
        color: #0A2540 !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Sidebar Styling - 20% Screen Width Permanent Dark Blue Partition */
    section[data-testid="stSidebar"] {
        width: 20vw !important;
        min-width: 250px !important;
        max-width: 320px !important;
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B !important;
        transform: none !important;
        margin-left: 0 !important;
        display: flex !important;
        visibility: visible !important;
        position: relative !important;
    }

    /* Main Content Styling - 80% Screen Width Partition */
    [data-testid="stMainBlockContainer"], .stMainBlockContainer {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 100% !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #E2E8F0 !important;
        font-weight: 500;
        font-size: 15px !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        color: #60A5FA !important;
    }
    section[data-testid="stSidebar"] .stAlert {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        margin-top: 2rem !important;
    }
    section[data-testid="stSidebar"] .stAlert * {
        color: #E2E8F0 !important;
    }

    /* Primary & Standard Buttons */
    div.stButton > button[kind="primary"] {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.25);
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 6px 12px -2px rgba(30, 58, 138, 0.35);
        transform: translateY(-1px);
    }

    div.stButton > button {
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        color: #0F172A !important;
        background-color: #F8FAFC !important;
        font-weight: 500 !important;
    }
    div.stButton > button:hover {
        border-color: #1E3A8A !important;
        color: #1E3A8A !important;
        background-color: #F0F4F8 !important;
    }

    /* Input Controls & Text Fields */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #1E3A8A !important;
        box-shadow: 0 0 0 2px rgba(30, 58, 138, 0.2) !important;
    }

    /* File Uploaders */
    section[data-testid="stFileUploader"] {
        background-color: #F0F4F8 !important;
        border: 2px dashed #1E3A8A !important;
        border-radius: 12px !important;
        padding: 1rem;
    }

    /* Custom Cards & Report Boxes */
    .report-box {
        border: 1px solid #CBD5E1;
        border-top: 4px solid #1E3A8A;
        border-radius: 12px;
        padding: 24px;
        background-color: #F8FAFC;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    /* Expanders & Accordions */
    .stExpander {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.03) !important;
    }
    .stExpander summary {
        font-weight: 600 !important;
        color: #0F172A !important;
    }

    /* Metric Cards Font Resizing & Contextual Scaling */
    div[data-testid="stMetricValue"] {
        color: #1E3A8A !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }

    /* Interactive Table & Single Continuous Row Selection Styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    [data-testid="stDataFrame"] [role="gridcell"],
    [data-testid="stDataFrame"] [role="columnheader"] {
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
        padding: 10px 14px !important;
    }
    [data-testid="stDataFrame"] [role="row"]:hover {
        background-color: #F0F4F8 !important;
        cursor: pointer !important;
    }
    [data-testid="stDataFrame"] [aria-selected="true"] {
        background-color: #E2E8F0 !important;
        font-weight: 600 !important;
    }

    /* Divider styling */
    hr {
        margin: 1.5rem 0 !important;
        border-color: #E2E8F0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Initialize session state variables ---
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'application_results' not in st.session_state:
    st.session_state.application_results = None
# --- Sidebar for Navigation ---
st.sidebar.title("LoanIQ Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Loan Application Processor", "Dashboard"],
    key="nav_radio"
)
st.sidebar.markdown("---")
st.sidebar.info("LoanIQ leverages Generative AI to automate loan document processing, cross-validation, and human-in-the-loop verification.")

# --- Helper function for pointwise data display ---
def display_extracted_data_pointwise(extracted_data):
    if not extracted_data:
        st.write("No extracted fields available.")
        return
    
    for field, details in extracted_data.items():
        if isinstance(details, dict):
            val = details.get('value', 'N/A')
            conf = details.get('confidence', 0.0)
            if val is None or str(val).strip() == "" or str(val).lower() == "null":
                val_str = "<span style='color: #94A3B8; font-style: italic;'>(Not Found)</span>"
            else:
                val_str = f"<strong style='color: #0F172A;'>{val}</strong>"
            
            conf_badge = f"<span style='font-size: 12px; color: #475569; background-color: #F1F5F9; padding: 2px 6px; border-radius: 4px; font-weight: 500;'>Confidence: {conf*100:.1f}%</span>" if conf else ""
            st.markdown(f"- 🔹 <span style='font-size: 14px;'><strong>{field}</strong>: {val_str} {conf_badge}</span>", unsafe_allow_html=True)
        else:
            val_str = f"<strong style='color: #0F172A;'>{details}</strong>" if details else "<span style='color: #94A3B8;'>(Not Found)</span>"
            st.markdown(f"- 🔹 <span style='font-size: 14px;'><strong>{field}</strong>: {val_str}</span>", unsafe_allow_html=True)

# --- Helper function to render AI summary report with Red & Green Flags ---
def display_underwriting_report(results):
    report = results.get('final_summary_report', {})
    recommendation = report.get('final_recommendation', 'Error')
    summary = report.get('overall_summary', [])
    green_flags = report.get('positive_highlights', [])
    red_flags = report.get('consolidated_red_flags', [])
    metrics = report.get('key_financial_metrics', [])

    # Recommendation badge
    if recommendation == 'Approve':
        st.success(f"### 🟢 Underwriting Recommendation: **{recommendation}**")
    elif recommendation == 'Manual Review Required':
        st.warning(f"### ⚠️ Underwriting Recommendation: **{recommendation}**")
    else:
        st.error(f"### 🔴 Underwriting Recommendation: **{recommendation}**")

    # Detailed AI Summary
    st.markdown("#### 📝 AI Detailed Assessment & Findings")
    if isinstance(summary, list) and summary:
        for point in summary:
            st.markdown(f"- 🔹 <span style='font-size: 14px;'>{point}</span>", unsafe_allow_html=True)
    elif isinstance(summary, str) and summary:
        st.markdown(f"🔹 <span style='font-size: 14px;'><em>{summary}</em></span>", unsafe_allow_html=True)
    else:
        st.write("No overall summary provided.")

    st.markdown("---")

    # Red & Green Flags Columns
    col_green, col_red = st.columns(2)

    with col_green:
        st.markdown(
            """
            <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; padding: 16px; border-radius: 10px; margin-bottom: 15px;">
                <h5 style="color: #166534; margin-top: 0; margin-bottom: 10px; font-size: 16px;">🟢 Positive Highlights (Green Flags)</h5>
            """,
            unsafe_allow_html=True
        )
        if green_flags:
            for gf in green_flags:
                st.markdown(f"- 🟢 **{gf}**")
        else:
            st.markdown("*(No specific positive flags generated)*")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_red:
        st.markdown(
            """
            <div style="background-color: #FEF2F2; border: 1px solid #FECACA; border-left: 5px solid #DC2626; padding: 16px; border-radius: 10px; margin-bottom: 15px;">
                <h5 style="color: #991B1B; margin-top: 0; margin-bottom: 10px; font-size: 16px;">🔴 Risk Factors & Mismatches (Red Flags)</h5>
            """,
            unsafe_allow_html=True
        )
        if red_flags:
            for rf in red_flags:
                st.markdown(f"- 🔴 **{rf}**")
        else:
            st.markdown("🟢 **No critical red flags or mismatches detected.**")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Proportional, Contextually-Sized Financial Metric Cards
    st.markdown("#### 📈 Key Financial Metrics")
    if metrics:
        metric_cols = st.columns(min(len(metrics), 4))
        for idx, metric_str in enumerate(metrics):
            col_target = metric_cols[idx % 4]
            
            # Extract Label and Value safely
            if ":" in metric_str:
                parts = metric_str.split(":", 1)
                label_text = parts[0].strip()
                val_text = parts[1].strip()
            else:
                label_text = "Metric"
                val_text = metric_str.strip()

            col_target.markdown(
                f"""
                <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-top: 3px solid #1E3A8A; border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.02em;">{label_text}</div>
                    <div style="font-size: 18px; font-weight: 700; color: #1E3A8A; word-break: break-word;">{val_text}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.write("None identified.")

# --- Helper function for the verification form ---
def display_verification_form(doc_data, application_id, unique_key):
    extracted_data = doc_data.get("extracted_data", {})
    filename = doc_data.get("filename", "unknown_file")

    if not extracted_data:
        st.warning("No structured data was extracted to verify.")
        return

    with st.form(key=f"verification_form_{unique_key}"):
        corrected_data = {}
        for field, details in extracted_data.items():
            value = details.get('value', '') if isinstance(details, dict) else details
            confidence = details.get('confidence', 0.0) * 100 if isinstance(details, dict) else 0.0

            help_text = f"Confidence: {confidence:.1f}%"
            if confidence < 75:
                help_text = f"⚠️ Low Confidence ({confidence:.1f}%) - Please verify carefully."

            corrected_data[field] = st.text_input(
                label=f"{field}",
                value=value,
                key=f"{unique_key}_{field.lower().replace(' ', '_')}",
                help=help_text
            )

        submitted = st.form_submit_button("Approve & Save This Document's Data")

        if submitted:
            with st.spinner("Saving verified data..."):
                payload = {
                    "application_id": application_id,
                    "filename": filename,
                    "original_ai_data": doc_data,
                    "verified_data": corrected_data
                }
                try:
                    save_response = requests.post(f"{BACKEND_URL}/save-verified-document/", json=payload)
                    if save_response.status_code == 200:
                        st.success(f"✅ Verified data for `{filename}` saved successfully!")
                    else:
                        st.error(f"Failed to save data for `{filename}`: {save_response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("🚫 Connection Error: Could not connect to the backend to save data.")

# --- Page 1: Loan Application Processor ---
if page == "Loan Application Processor":
    st.title("🏦 LoanIQ - Intelligent Loan Application Processor")
    st.markdown("---")
    st.markdown(
        """
        Fill in applicant details, upload all financial and ID documents (Payslip, Tax Form, ID card), 
        and **LoanIQ AI** will analyze the package, cross-verify records, and generate an underwriting report.
        """
    )
    st.markdown("---")

    # --- Applicant Information Section ---
    st.header("👤 1. Applicant Details")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        applicant_name = st.text_input("Applicant Full Name *", placeholder="e.g. Rajesh Kumar")
        contact_number = st.text_input("Contact Number *", placeholder="e.g. +91 9876543210")
    with col_info2:
        loan_type = st.selectbox("Loan Type *", ["Personal Loan", "Home Loan", "Auto Loan", "Business Loan", "Education Loan"])
        loan_amount = st.text_input("Requested Loan Amount (₹)", placeholder="e.g. 5,00,000")

    st.markdown("---")
    st.header("📁 2. Upload Loan Application Package")
    col1_upload, col2_upload, col3_upload = st.columns(3)
    with col1_upload:
        st.subheader("KYC Documents")
        kyc_files = st.file_uploader("Upload PAN, Aadhaar, Driving License", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True, key="kyc_uploader")
    with col2_upload:
        st.subheader("Bank Statements")
        bank_files = st.file_uploader("Upload latest bank statements", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True, key="bank_uploader")
    with col3_upload:
        st.subheader("Income Proof")
        income_files = st.file_uploader("Upload Payslips, Form 16, ITR", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True, key="income_uploader")

    uploaded_files = kyc_files + bank_files + income_files

    if uploaded_files:
        st.markdown("---")
        if st.button("Process Full Application", type="primary", disabled=st.session_state.processing):
            if not applicant_name.strip() or not contact_number.strip():
                st.error("⚠️ Please fill in Applicant Name and Contact Number before proceeding.")
            else:
                st.session_state.processing = True
                st.info(f"✨ Processing {len(uploaded_files)} documents for **{applicant_name}**...")
                with st.spinner('LoanIQ AI is analyzing the application package...'):
                    multipart_files = [('files', (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                    payload_data = {
                        "applicant_name": applicant_name,
                        "contact_number": contact_number,
                        "loan_type": loan_type,
                        "loan_amount": loan_amount
                    }
                    try:
                        response = requests.post(f"{BACKEND_URL}/process-application/", files=multipart_files, data=payload_data)
                        if response.status_code == 200:
                            st.success('✅ Application processed & saved successfully!')
                            st.session_state.application_results = response.json()
                        else:
                            try:
                                error_detail = response.json().get('detail', response.text)
                            except json.JSONDecodeError:
                                error_detail = response.text
                            st.error(f"❌ Error from server ({response.status_code}): {error_detail}")
                            st.session_state.application_results = None
                    except requests.exceptions.ConnectionError:
                        st.error("🚫 Connection Error: Could not connect to the backend server.")
                        st.session_state.application_results = None
                st.session_state.processing = False
                st.rerun()

    if st.session_state.application_results:
        results = st.session_state.application_results
        application_id = results.get("application_id")

        st.markdown("---")
        st.header("🏁 LoanIQ Underwriting Assessment Report")
        
        info_col1, info_col2, info_col3 = st.columns(3)
        info_col1.write(f"**Applicant:** {results.get('applicant_name', 'N/A')}")
        info_col2.write(f"**Contact:** {results.get('contact_number', 'N/A')}")
        info_col3.write(f"**Loan Type & Amount:** {results.get('loan_type', 'N/A')} (₹{results.get('loan_amount', 'N/A')})")
        st.caption(f"Application ID: `{application_id}`")

        display_underwriting_report(results)

        with st.expander("View AI Cross-Validation Technical Details"):
            cross_val_report = results.get('cross_validation_report', {})
            st.json(cross_val_report)

        st.markdown("---")
        st.subheader("📄 Individual Document Verification")
        st.info("Review extracted fields below. Correct any values and click Approve to save to local database history.")

        for i, doc_result in enumerate(results.get('individual_document_results', [])):
            doc_type = doc_result.get('document_type', 'Unknown')
            filename = doc_result.get('filename', 'N/A')

            with st.expander(f"📄 **{doc_type}** (`{filename}`)"):
                col1_doc, col2_doc = st.columns(2)
                with col1_doc:
                    display_verification_form(doc_result, application_id, unique_key=f"doc_{i}")
                with col2_doc:
                    st.markdown("##### AI Extraction Analysis")
                    analysis = doc_result.get('analysis', {})
                    if isinstance(analysis, dict):
                        display_extracted_data_pointwise(analysis)
                    elif analysis:
                        st.write(str(analysis))
                    else:
                        st.write("No detailed analysis provided.")

                if st.checkbox("View Full Raw JSON", key=f"raw_data_checkbox_{i}"):
                    st.json(doc_result)

# --- Page 2: Dashboard & Application History ---
elif page == "Dashboard":
    st.title("📊 Dashboard & Application History")
    st.markdown("---")

    try:
        # Fetch application history
        history_resp = requests.get(f"{BACKEND_URL}/get-application-history/")
        verified_resp = requests.get(f"{BACKEND_URL}/get-report-data/")
        
        if history_resp.status_code == 200:
            history_data = history_resp.json()
            verified_data = verified_resp.json() if verified_resp.status_code == 200 else []

            if history_data:
                # Key Performance Indicators
                total_apps = len(history_data)
                approved_cnt = sum(1 for a in history_data if a.get('final_summary_report', {}).get('final_recommendation') == 'Approve')
                review_cnt = sum(1 for a in history_data if a.get('final_summary_report', {}).get('final_recommendation') == 'Manual Review Required')
                denied_cnt = sum(1 for a in history_data if a.get('final_summary_report', {}).get('final_recommendation') == 'Deny')
                active_verified_docs = len(verified_data)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Applications", f"{total_apps}")
                col2.metric("Approved", f"{approved_cnt}")
                col3.metric("Manual Review", f"{review_cnt}")
                col4.metric("Active Verified Docs", f"{active_verified_docs}")

                st.markdown("---")
                st.subheader("📋 Application History")
                st.caption("💡 **Click anywhere on a row** in the table below to automatically select and preview its detailed report below.")

                # Build flat list for table view
                history_records = []
                for app_rec in reversed(history_data):
                    rep = app_rec.get('final_summary_report', {})
                    cross_val = app_rec.get('cross_validation_report', {})
                    
                    created = app_rec.get('created_at', '')
                    formatted_date = created[:16].replace('T', ' ') if created else 'N/A'
                    
                    history_records.append({
                        "Date & Time": formatted_date,
                        "Application ID": app_rec.get('application_id', ''),
                        "Applicant Name": app_rec.get('applicant_name', 'N/A'),
                        "Contact": app_rec.get('contact_number', 'N/A'),
                        "Loan Type": app_rec.get('loan_type', 'Personal Loan'),
                        "Amount (₹)": app_rec.get('loan_amount', 'N/A'),
                        "Docs Count": len(app_rec.get('individual_document_results', [])),
                        "Recommendation": rep.get('final_recommendation', 'N/A'),
                        "Validation Passed": "✅ Yes" if cross_val.get('validation_passed') else "⚠️ Mismatch"
                    })

                df_history = pd.DataFrame(history_records)

                # Single continuous row interactive table
                event = st.dataframe(
                    df_history,
                    use_container_width=True,
                    selection_mode="single-row",
                    on_select="rerun",
                    hide_index=True,
                    key="history_dataframe"
                )

                # Extract clicked row's Application ID instantly
                clicked_app_id = None
                if event and hasattr(event, "selection") and event.selection and "rows" in event.selection and event.selection["rows"]:
                    selected_row_idx = event.selection["rows"][0]
                    if selected_row_idx < len(df_history):
                        clicked_app_id = df_history.iloc[selected_row_idx]["Application ID"]

                st.markdown("---")
                st.subheader("🔍 Past Application Preview & Report")

                app_options = [a['application_id'] for a in reversed(history_data)]
                default_index = 0
                if clicked_app_id and clicked_app_id in app_options:
                    default_index = app_options.index(clicked_app_id)

                col_select, col_del = st.columns([3, 1])

                with col_select:
                    selected_app_id = st.selectbox(
                        "Selected Application ID (Click any row in the table above to preview):",
                        options=app_options,
                        index=default_index,
                        format_func=lambda x: f"{next((a['applicant_name'] for a in history_data if a['application_id'] == x), 'App')} ({x[:8]}...)",
                        key="app_select_dropdown"
                    )

                with col_del:
                    st.write("")
                    st.write("")
                    if selected_app_id:
                        selected_name = next((a['applicant_name'] for a in history_data if a['application_id'] == selected_app_id), "Selected App")
                        if st.button("🗑️ Delete Entry", key=f"delete_app_btn_{selected_app_id}"):
                            try:
                                del_res = requests.delete(f"{BACKEND_URL}/delete-application/{selected_app_id}")
                                if del_res.status_code == 200:
                                    st.success(f"✅ Application for `{selected_name}` deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete: {del_res.text}")
                            except requests.exceptions.ConnectionError:
                                st.error("🚫 Connection Error.")

                if selected_app_id:
                    selected_app = next((a for a in history_data if a['application_id'] == selected_app_id), None)
                    if selected_app:
                        st.markdown(f"#### Application Details: `{selected_app.get('applicant_name')}`")
                        col_dt1, col_dt2, col_dt3 = st.columns(3)
                        col_dt1.write(f"**Contact:** {selected_app.get('contact_number')}")
                        col_dt2.write(f"**Loan Type:** {selected_app.get('loan_type')}")
                        col_dt3.write(f"**Requested Amount:** ₹{selected_app.get('loan_amount')}")

                        # Render detailed report with Red & Green Flags
                        display_underwriting_report(selected_app)

                        with st.expander("📄 Uploaded Documents & Extracted Field Details", expanded=True):
                            for doc in selected_app.get('individual_document_results', []):
                                st.markdown(f"#### 📄 {doc.get('document_type', 'Document')} (`{doc.get('filename')}`)")
                                display_extracted_data_pointwise(doc.get('extracted_data', {}))
                                if doc.get('analysis'):
                                    st.markdown("**AI Field Analysis:**")
                                    display_extracted_data_pointwise(doc.get('analysis'))
                                st.markdown("---")

            else:
                st.info("No applications stored in database history yet. Submit an application from the Loan Application Processor page!")

            st.markdown("---")
            st.subheader("🧹 Database Management")
            if st.checkbox("Permanently clear all application history and stored database records."):
                if st.button("Delete All Stored Database Data", type="primary"):
                    try:
                        del_res = requests.delete(f"{BACKEND_URL}/delete-all-data/")
                        if del_res.status_code == 200:
                            st.success("✅ All database application records and stored files cleared successfully.")
                            st.rerun()
                        else:
                            st.error(f"Failed to clear data: {del_res.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("🚫 Connection Error.")
        else:
            st.error(f"Failed to fetch application history from server ({history_resp.status_code}): {history_resp.text}")
    except requests.exceptions.ConnectionError:
        st.error("🚫 Connection Error: Could not connect to the backend server.")
    except Exception as e:
        st.error(f"An unexpected error occurred while loading the dashboard: {e}")
