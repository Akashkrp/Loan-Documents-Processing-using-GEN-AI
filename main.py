import os
import io
import json
import base64
import re
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Dict, Any, List
from PIL import Image
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

load_dotenv()
app = FastAPI(title="Intelligent Document Processor API")

# --- Local Storage Setup (Replaces MongoDB) ---
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
APPLICATIONS_FILE = os.path.join(STORAGE_DIR, "applications.json")
VERIFIED_DOCS_FILE = os.path.join(STORAGE_DIR, "verified_documents.json")

os.makedirs(UPLOADS_DIR, exist_ok=True)

def load_json_file(file_path: str) -> list:
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_json_file(file_path: str, data: list):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

# --- PROMPT ENGINEERING UPGRADE ---

# 1. More specific classification options
classification_prompt_template = """
You are an expert document classifier. Your task is to analyze the provided document image and identify its type.
Respond with only one of the following categories: 'Payslip', 'Tax Form', 'PAN Card', 'Aadhaar Card', 'Driving License', 'Bank Statement', 'Form 16', 'ITR', or 'Other'.
Do not add any other text or explanation.
"""

# 2. More detailed extraction prompts for each document type
extraction_prompts = {
    "Payslip": """
    You are an expert AI assistant. From the provided payslip image, extract: "Applicant Name", "Gross Income", "Net Pay", "Total Taxes", and "Pay Period End Date".
    For each field, provide the 'value' and a 'confidence' score.
    Provide your response as a single, valid JSON object with keys "extracted_data" and "analysis".
    """,
    "Tax Form": """
    You are an expert AI assistant. From the provided tax form image, extract: "Applicant Name", "Total Income", "Taxes Paid", and "Assessment Year".
    For each field, provide the 'value' and a 'confidence' score.
    Provide your response as a single, valid JSON object with keys "extracted_data" and "analysis".
    """,
    "PAN Card": """
    You are an expert AI assistant. From the provided PAN Card image, extract: "Name", "Father's Name", "Date of Birth", and "PAN Number".
    For each field, provide the 'value' and a 'confidence' score.
    Provide your response as a single, valid JSON object with keys "extracted_data" and "analysis".
    """,
    "Aadhaar Card": """
    You are an expert AI assistant. From the provided Aadhaar Card image, extract: "Name", "Date of Birth", "Address", "Gender", and "Aadhaar Number" (the 12-digit number).
    For each field, provide the 'value' and a 'confidence' score.
    Provide your response as a single, valid JSON object with keys "extracted_data" and "analysis".
    """,
    "Driving License": """
    You are an expert AI assistant. From the provided Driving License image, extract: "Name", "Date of Birth", "Address", and "DL No" (the license number).
    For each field, provide the 'value' and a 'confidence' score.
    Provide your response as a single, valid JSON object with keys "extracted_data" and "analysis".
    """,
    "Default": """
    You are an expert AI assistant. From the provided document image, extract any personally identifiable information (PII) and key financial figures you can find.
    For each field, provide the 'value' and a 'confidence' score.
    Provide your response as a single, valid JSON object with keys "extracted_data" and "analysis".
    """
}

cross_validation_prompt = """
You are a senior loan underwriter AI. You have been provided with extracted data from multiple documents for a single loan application.
Your task is to perform a final cross-validation check. Analyze all the data and identify any critical inconsistencies between the documents.
Specifically check for mismatches in "Applicant Name" and "Date of Birth".
Here is the data from all documents:
---
{summarized_data}
---
Provide a summary of your findings as a single, valid JSON object with two keys: "overall_summary" (a string) and "validation_passed" (a boolean).
The final output must be ONLY the JSON object, with no extra text or markdown.
"""

# 3. A robust, detailed final summary prompt with bullet points, green flags, and red flags
final_summary_prompt = """
You are the lead AI loan underwriter. You have been given the complete data extracted from a loan application package.
Your task is to generate a comprehensive, detailed underwriting assessment report.

Based on all the information provided below:
1. **Overall Detailed Summary**: Provide 3 to 5 detailed bullet points analyzing the applicant's profile, income stability, documentation completeness, and verification status.
2. **Positive Highlights (Green Flags 🟢)**: Provide a list of positive aspects (e.g., valid government IDs, consistent identity details, strong monthly net pay, complete tax filings, no document discrepancies).
3. **Consolidated Red Flags (Red Flags 🔴)**: Provide a list of all risk factors, mismatches, or missing details (e.g., DOB/Name spelling mismatches across documents, unreadable text, low confidence extractions). If no red flags exist, return an empty list.
4. **Key Financial Metrics**: List key financial figures formatted as "Metric Name: Value".
5. **Final Recommendation**: Respond strictly with one of: 'Approve', 'Deny', or 'Manual Review Required'.

Here is all the data:
---
{complete_data}
---

Provide your response strictly as a single, valid JSON object with the following 5 keys:
- "overall_summary": [ "Bullet point 1", "Bullet point 2", "Bullet point 3" ],
- "positive_highlights": [ "Green flag 1", "Green flag 2" ],
- "consolidated_red_flags": [ "Red flag 1", "Red flag 2" ],
- "key_financial_metrics": [ "Metric: Value", "Metric: Value" ],
- "final_recommendation": "Approve" | "Deny" | "Manual Review Required"

The final output must be ONLY the JSON object, with no markdown codeblocks or extra text.
"""


def pil_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

def extract_text_from_response(res) -> str:
    content = res.content if hasattr(res, 'content') else str(res)
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            else:
                text_parts.append(str(part))
        return "".join(text_parts).strip()
    return str(content).strip()

import asyncio

AVAILABLE_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash"]

async def invoke_llm_with_retry(messages, retries=3) -> str:
    for model_name in AVAILABLE_MODELS:
        llm = ChatGoogleGenerativeAI(model=model_name)
        for attempt in range(retries):
            try:
                res = await llm.ainvoke(messages)
                return extract_text_from_response(res)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "QUOTA" in err_str.upper():
                    print(f"[Backend Warning] Model {model_name} rate-limited/busy (Attempt {attempt+1}/{retries}). Waiting 2s...", flush=True)
                    await asyncio.sleep(2)
                else:
                    print(f"[Backend Warning] Model {model_name} error: {err_str[:100]}. Trying next model...", flush=True)
                    break
    raise HTTPException(status_code=500, detail="Gemini AI rate limit reached across models. Please wait 1 minute and try again.")

async def process_single_file(file_content: bytes, filename: str) -> dict:
    print(f"[Backend] Starting processing for: {filename}", flush=True)
    images_to_process = []
    if filename.endswith('.pdf'):
        images_to_process = convert_from_bytes(file_content)
    elif filename.endswith(('.png', '.jpg', '.jpeg')):
        images_to_process.append(Image.open(io.BytesIO(file_content)))
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")

    if not images_to_process:
         raise HTTPException(status_code=400, detail="Could not convert document to image.")

    print(f"[Backend] Classifying document: {filename}...", flush=True)
    # 1. Classify
    classification_message = HumanMessage(content=[{"type": "text", "text": classification_prompt_template}, {"type": "image_url", "image_url": pil_to_base64(images_to_process[0])}])
    doc_type = await invoke_llm_with_retry([classification_message])
    print(f"[Backend] Classified {filename} as: {doc_type}", flush=True)

    # 2. Extract
    extraction_prompt = extraction_prompts.get(doc_type, extraction_prompts["Default"])
    content_parts = [{"type": "text", "text": extraction_prompt}]
    for img in images_to_process:
        content_parts.append({"type": "image_url", "image_url": pil_to_base64(img)})
    
    print(f"[Backend] Extracting data from {filename}...", flush=True)
    message = HumanMessage(content=content_parts)
    response_json_string = await invoke_llm_with_retry([message])
    
    try:
        clean_response = response_json_string.replace("```json", "").replace("```", "").strip()
        final_result = json.loads(clean_response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"AI returned a non-JSON response: {response_json_string}")

    final_result['document_type'] = doc_type
    final_result['filename'] = filename
    print(f"[Backend] Finished extracting data for {filename}", flush=True)
    return final_result

@app.post("/process-application/")
async def process_application(
    files: List[UploadFile] = File(...),
    applicant_name: str = Form(""),
    contact_number: str = Form(""),
    loan_type: str = Form("Personal Loan"),
    loan_amount: str = Form("")
):
    print(f"\n[Backend] Received application from '{applicant_name}' ({contact_number}, {loan_type}) with {len(files)} files.", flush=True)
    try:
        application_id = str(uuid.uuid4())
        app_upload_folder = os.path.join(UPLOADS_DIR, application_id)
        os.makedirs(app_upload_folder, exist_ok=True)
        
        file_tasks = []
        for file in files:
            file_content = await file.read()
            
            # Save uploaded physical file to local storage folder
            saved_file_path = os.path.join(app_upload_folder, file.filename)
            with open(saved_file_path, "wb") as f_out:
                f_out.write(file_content)
                
            file_tasks.append(process_single_file(file_content, file.filename.lower()))

        # Run document processing concurrently in parallel!
        application_results = await asyncio.gather(*file_tasks)
        
        print("[Backend] Running cross-validation...", flush=True)
        summarized_data_for_ai = [{"filename": res.get('filename'), "document_type": res.get('document_type'), "data": res.get('extracted_data')} for res in application_results]
        
        cross_val_message = HumanMessage(content=cross_validation_prompt.format(summarized_data=json.dumps(summarized_data_for_ai, indent=2)))
        cross_val_response_str = await invoke_llm_with_retry([cross_val_message])
        
        try:
            json_match = re.search(r'\{.*\}', cross_val_response_str, re.DOTALL)
            cross_val_json = json.loads(json_match.group(0)) if json_match else {}
        except json.JSONDecodeError:
            cross_val_json = {"overall_summary": "AI cross-validation returned an invalid format.", "validation_passed": False}

        print("[Backend] Generating final summary report...", flush=True)
        complete_data_for_summary = { 
            "applicant_info": {
                "applicant_name": applicant_name,
                "contact_number": contact_number,
                "loan_type": loan_type,
                "loan_amount": loan_amount
            },
            "individual_documents": application_results,
            "initial_cross_validation": cross_val_json
        }
        summary_message = HumanMessage(content=final_summary_prompt.format(complete_data=json.dumps(complete_data_for_summary, indent=2)))
        summary_response_str = await invoke_llm_with_retry([summary_message])

        try:
            json_match = re.search(r'\{.*\}', summary_response_str, re.DOTALL)
            summary_json = json.loads(json_match.group(0)) if json_match else {}
        except json.JSONDecodeError:
            summary_json = {"final_recommendation": "Error", "overall_summary": "AI failed to generate a final summary report."}

        # Structure complete application record
        app_record = {
            "application_id": application_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "applicant_name": applicant_name or "N/A",
            "contact_number": contact_number or "N/A",
            "loan_type": loan_type or "Personal Loan",
            "loan_amount": loan_amount or "N/A",
            "individual_document_results": application_results,
            "cross_validation_report": cross_val_json,
            "final_summary_report": summary_json
        }

        # Save to local JSON database
        applications = load_json_file(APPLICATIONS_FILE)
        applications.append(app_record)
        save_json_file(APPLICATIONS_FILE, applications)

        print(f"[Backend] Application {application_id} saved locally in storage/!\n", flush=True)
        return app_record

    except Exception as e:
        print(f"[Backend Error] {str(e)}", flush=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during application processing: {str(e)}")


class VerificationPayload(BaseModel):
    application_id: str
    filename: str
    original_ai_data: Dict[str, Any]
    verified_data: Dict[str, str]

@app.post("/save-verified-document/")
async def save_verified_document(payload: VerificationPayload):
    try:
        docs = load_json_file(VERIFIED_DOCS_FILE)
        
        # Deactivate previous active records for this document
        now_str = datetime.now(timezone.utc).isoformat()
        for d in docs:
            if d.get("application_id") == payload.application_id and d.get("filename") == payload.filename and d.get("is_active"):
                d["is_active"] = False
                d["end_date"] = now_str
                
        doc_id = str(uuid.uuid4())
        new_doc = {
            "_id": doc_id,
            "application_id": payload.application_id,
            "filename": payload.filename,
            "ai_data": payload.original_ai_data.get("extracted_data", {}),
            "verified_data": payload.verified_data,
            "start_date": now_str,
            "end_date": None,
            "is_active": True
        }
        docs.append(new_doc)
        save_json_file(VERIFIED_DOCS_FILE, docs)
        
        return {"status": "success", "message": f"Verified data for {payload.filename} saved locally with ID {doc_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save data locally: {str(e)}")

@app.get("/get-report-data/")
async def get_report_data():
    try:
        docs = load_json_file(VERIFIED_DOCS_FILE)
        active_docs = [d for d in docs if d.get("is_active")]
        return active_docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch report data: {str(e)}")

@app.get("/get-application-history/")
async def get_application_history():
    try:
        applications = load_json_file(APPLICATIONS_FILE)
        return applications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch application history: {str(e)}")

@app.delete("/delete-application/{application_id}")
async def delete_application(application_id: str):
    try:
        applications = load_json_file(APPLICATIONS_FILE)
        updated_apps = [a for a in applications if a.get("application_id") != application_id]
        if len(updated_apps) == len(applications):
            raise HTTPException(status_code=404, detail="Application ID not found.")
        
        save_json_file(APPLICATIONS_FILE, updated_apps)
        
        # Remove uploaded physical files for this application
        app_upload_folder = os.path.join(UPLOADS_DIR, application_id)
        if os.path.exists(app_upload_folder):
            import shutil
            shutil.rmtree(app_upload_folder, ignore_errors=True)

        # Remove from verified documents list
        verified_docs = load_json_file(VERIFIED_DOCS_FILE)
        updated_docs = [d for d in verified_docs if d.get("application_id") != application_id]
        save_json_file(VERIFIED_DOCS_FILE, updated_docs)

        return {"status": "success", "message": f"Application {application_id} deleted successfully."}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to delete application: {str(e)}")

@app.delete("/delete-all-data/")
async def delete_all_data():
    try:
        save_json_file(APPLICATIONS_FILE, [])
        save_json_file(VERIFIED_DOCS_FILE, [])
        if os.path.exists(UPLOADS_DIR):
            import shutil
            for item in os.listdir(UPLOADS_DIR):
                item_path = os.path.join(UPLOADS_DIR, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        return {"status": "success", "message": "All local application data and files have been cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete local data: {str(e)}")
