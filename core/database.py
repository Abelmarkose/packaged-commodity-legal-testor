import io
import json
import base64
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class InspectionAudit(Base):
    __tablename__ = "inspection_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(150), default="Unknown Commodity")
    timestamp = Column(DateTime, default=datetime.utcnow)
    ai_score = Column(Integer)
    ai_status = Column(String(50))
    compliance_report = Column(Text)  # JSON-encoded compliance dictionary
    raw_tokens = Column(Text)         # JSON-encoded extracted OCR tokens
    image_base64 = Column(Text, nullable=True) # Compressed thumbnail
    
    # Inspector Review Fields
    officer_name = Column(String(100), default="Field Inspector")
    final_decision = Column(String(50), default="APPROVED")
    is_overridden = Column(Boolean, default=False)
    review_notes = Column(Text, nullable=True)

DATABASE_URL = "sqlite:///metrology_inspections.db"
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)

def save_inspection(product_name, ai_score, ai_status, report_dict, tokens_list, 
                    officer_name, final_decision, notes, image_np=None):
    """Saves a verified inspection report to SQLite."""
    session = SessionLocal()
    try:
        b64_str = None
        if image_np is not None:
            import cv2
            h, w = image_np.shape[:2]
            scale = 300 / max(h, w)
            thumb = cv2.resize(image_np, (int(w * scale), int(h * scale)))
            _, buffer = cv2.imencode('.jpg', thumb, [cv2.IMWRITE_JPEG_QUALITY, 75])
            b64_str = base64.b64encode(buffer).decode('utf-8')

        is_overridden = (ai_status == "COMPLIANT" and "NOTICE" in final_decision) or \
                        (ai_status == "NON-COMPLIANT" and "APPROVED" in final_decision)

        record = InspectionAudit(
            product_name=product_name,
            timestamp=datetime.utcnow(),
            ai_score=ai_score,
            ai_status=ai_status,
            compliance_report=json.dumps(report_dict),
            raw_tokens=json.dumps(tokens_list),
            image_base64=b64_str,
            officer_name=officer_name,
            final_decision=final_decision,
            is_overridden=is_overridden,
            review_notes=notes
        )
        session.add(record)
        session.commit()
        return record.id
    finally:
        session.close()

def get_all_inspections():
    """Fetches all past inspection audits ordered by latest timestamp."""
    session = SessionLocal()
    try:
        return session.query(InspectionAudit).order_by(InspectionAudit.timestamp.desc()).all()
    finally:
        session.close()

def get_inspection_by_id(record_id: int):
    """Fetches a specific inspection record."""
    session = SessionLocal()
    try:
        return session.query(InspectionAudit).filter(InspectionAudit.id == record_id).first()
    finally:
        session.close()

def generate_export_files(records):
    """
    Transforms database records into a flattened Pandas DataFrame and generates
    both CSV and Excel (.xlsx) file bytes for download.
    """
    rows = []
    for r in records:
        rep = json.loads(r.compliance_report) if r.compliance_report else {}
        rows.append({
            "Audit ID": r.id,
            "Date & Time (UTC)": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Product Name": r.product_name,
            "AI Score": f"{r.ai_score}%",
            "AI Status": r.ai_status,
            "Final Decision": r.final_decision,
            "Officer Name": r.officer_name,
            "Officer Overridden": "Yes" if r.is_overridden else "No",
            "Officer Notes": r.review_notes or "N/A",
            "MRP Status": rep.get("MRP_Declaration", {}).get("status", "N/A"),
            "MRP Value": rep.get("MRP_Declaration", {}).get("extracted", "N/A"),
            "Net Qty Status": rep.get("Net_Quantity", {}).get("status", "N/A"),
            "Net Qty Value": rep.get("Net_Quantity", {}).get("extracted", "N/A"),
            "Date Pkg Status": rep.get("Date_of_Packaging", {}).get("status", "N/A"),
            "Date Pkg Value": rep.get("Date_of_Packaging", {}).get("extracted", "N/A"),
            "Consumer Care": rep.get("Consumer_Care", {}).get("extracted", "N/A"),
            "Manufacturer Address": rep.get("Manufacturer_Address", {}).get("extracted", "N/A"),
            "Country of Origin": rep.get("Country_of_Origin", {}).get("extracted", "N/A"),
        })

    df = pd.DataFrame(rows)

    # 1. Generate CSV bytes
    csv_bytes = df.to_csv(index=False).encode('utf-8')

    # 2. Generate Excel (.xlsx) bytes
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Metrology_Audit_History")
    excel_bytes = excel_buffer.getvalue()

    return df, csv_bytes, excel_bytes