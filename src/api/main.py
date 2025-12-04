from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import json
import os
from datetime import datetime

from src.api.schemas import (
    BasicInfo,
    BusinessStabilityGoal,
    FirstResponse,
    MeasureItem,
    EquipmentList,
    CooperationPartner,
    PDCA,
    FinancialPlan,
    AttachmentsChecklist,
    ApplicationRoot
)

app = FastAPI(
    title="Jigyokei Co-Pilot API",
    description="API for Jigyokei Electronic Application System",
    version="1.0.0"
)

# --- Validation Endpoints ---

@app.post("/validate/basic_info")
async def validate_basic_info(data: BasicInfo):
    """Validate Section 1: Basic Information"""
    return {"status": "ok", "message": "Basic Info is valid", "data": data.model_dump()}

@app.post("/validate/goals")
async def validate_goals(data: BusinessStabilityGoal):
    """Validate Section 2: Goals"""
    return {"status": "ok", "message": "Goals are valid", "data": data.model_dump()}

@app.post("/validate/response_procedures")
async def validate_response_procedures(data: List[FirstResponse]):
    """Validate Section 3: Response Procedures"""
    return {"status": "ok", "message": "Response Procedures are valid", "data": [d.model_dump() for d in data]}

@app.post("/validate/measures")
async def validate_measures(data: List[MeasureItem]):
    """Validate Section 3(2): Measures"""
    return {"status": "ok", "message": "Measures are valid", "data": [d.model_dump() for d in data]}

@app.post("/validate/equipment")
async def validate_equipment(data: EquipmentList):
    """Validate Section 3(3): Equipment"""
    return {"status": "ok", "message": "Equipment List is valid", "data": data.model_dump()}

@app.post("/validate/cooperation")
async def validate_cooperation(data: List[CooperationPartner]):
    """Validate Section 4: Cooperation"""
    return {"status": "ok", "message": "Cooperation Partners are valid", "data": [d.model_dump() for d in data]}

@app.post("/validate/pdca")
async def validate_pdca(data: PDCA):
    """Validate Section 5: PDCA"""
    return {"status": "ok", "message": "PDCA is valid", "data": data.model_dump()}

@app.post("/validate/financial_plan")
async def validate_financial_plan(data: FinancialPlan):
    """Validate Section 5: Financial Plan"""
    return {"status": "ok", "message": "Financial Plan is valid", "data": data.model_dump()}

@app.post("/validate/attachments")
async def validate_attachments(data: AttachmentsChecklist):
    """Validate Section 4 & 5: Attachments & Checklist"""
    return {"status": "ok", "message": "Attachments & Checklist are valid", "data": data.model_dump()}

# --- Submission Endpoint ---

@app.post("/submit")
async def submit_application(application: ApplicationRoot):
    """
    Submit the full application.
    Saves the data to a JSON file and triggers the Excel generation process (TODO).
    """
    # 1. Save to Database (Mock: JSON file)
    output_dir = os.path.join(os.getcwd(), "output", "submissions")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"application_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(application.model_dump(), f, indent=2, ensure_ascii=False)
        
    # 2. Trigger Excel Generation (TODO)
    # This is where we would call the Excel generation tool using the saved JSON
    # e.g., generate_excel_from_json(filepath)
    
    return {
        "status": "success",
        "message": "Application submitted successfully",
        "submission_id": filename,
        "saved_path": filepath
    }

# --- Schema Endpoint ---

@app.get("/schema")
async def get_schema():
    """
    Get the JSON Schema for the ApplicationRoot model.
    Useful for LLM Structured Output or Function Calling.
    """
    return ApplicationRoot.model_json_schema()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
