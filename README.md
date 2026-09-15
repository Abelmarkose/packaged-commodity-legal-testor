# ⚖️ MetrologyAI: Automated Legal Metrology Compliance & Label Audit System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Computer Vision](https://img.shields.io/badge/Vision-OpenCV%20%7C%20EasyOCR-green.svg)](https://opencv.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-003B57.svg)](https://www.sqlalchemy.org/)

**Problem Statement ID:** SIH26034[cite: 2]  
**Problem Statement Title:** Automated Compliance Verification of Packaged Commodities under Legal Metrology Rules[cite: 2]  
**Theme:** Smart Automation / Consumer Protection / Governance[cite: 2]  
**Category:** Software[cite: 2]  
**Team Name:** ChandanaMazha[cite: 2]  
**Team Lead:** Kevin T John  
**Team Members:** Akshay Mahesh, Ajin Ani Philip, Abel Markose, Abhijith Nambiar, Rekha P S  

---

## 📌 Executive Summary

Under the **Legal Metrology (Packaged Commodities) Rules, 2011**, all pre-packaged commodities distributed in India must display clear statutory declarations[cite: 2]. Manual physical verification by field officers is time-consuming, subjective, and prone to human error when auditing microscopic thermal print, dot-matrix batch stamps, and multi-directional labels[cite: 2].

**MetrologyAI** automates statutory inspection using multi-orientation computer vision, deep-learning optical character recognition (OCR), fuzzy linguistic reconciliation, and a statutory rule-verification engine[cite: 2]. The platform automates compliance checking, provides a **Human-in-the-Loop Review Dashboard** for enforcement officers, flags Section 36 violations, and archives full audit trails with one-click Excel/CSV report exports[cite: 2].

---

## ✨ Key Features & Statutory Capabilities

- **Automated Rule 6 Statutory Auditing:** Validates mandatory package declarations[cite: 2]:
  - **Rule 6(1)(a):** Manufacturer/Packer identity with valid Postal Index Number (PIN).
  - **Rule 6(1)(b):** Generic or common identity of the commodity.
  - **Rule 6(1)(c):** Net quantity in standard metric units ($g, kg, ml, l$).
  - **Rule 6(1)(d):** Date of packing / manufacture and *Best Before / Use By* declarations.
  - **Rule 6(1)(e):** Maximum Retail Price (MRP) containing the mandatory *"inclusive of all taxes"* clause.
  - **Rule 6(1)(g):** Customer grievance redressal contact (toll-free number and email).
  - **Rule 6(10) & Rule 6(11):** Country of origin and Unit Sale Price (USP) per standard unit.
- **Statutory Exemption Intelligence (Rule 26):** Prevents false violations by identifying promotional, institutional, and sample packs (e.g., `"NOT FOR SALE"`), applying statutory exemptions to retail MRP requirements[cite: 2].
- **Split-Token USP Reconstruction:** Uses fuzzy sequence pairing to connect detached parenthetical fragments across line breaks (e.g., `(Rs.` on one line and `per g)` on another)[cite: 2].
- **Multi-Angle Rotation Pipeline ($360^\circ$):** Ingests and processes vertical sidebars ($90^\circ / 270^\circ$) and rotated packaging stamps[cite: 2].
- **HSV Color-First Emblem Segmentation:** Detects mandatory Vegetarian (Green) and Non-Vegetarian (Red/Brown) symbols even through compression artifacts.
- **Digital License Decoding:** Decodes FSSAI/Metrology 2D QR codes and barcodes to verify manufacturer disclosures when physical surface area is constrained[cite: 2].
- **Human-in-the-Loop Review & History Registry:** Enables field officers to confirm verdicts, enter violation remarks, issue Section 36 notices, and export complete audit history into Excel (`.xlsx`) or CSV files[cite: 2].

---

## 🛠️ System Architecture & Workflow
[ Packaging Image Input ] (Camera / High-Res Upload)
               │
               ▼
[ OpenCV Adaptive Preprocessing ] (CLAHE, Morphology, Binarization)
               │
               ▼
[ Multi-Angle Text & Feature Extraction ] (EasyOCR + QR/Symbol Detection)
                │
                ▼
[ Legal Metrology Rule Validator ] (RapidFuzz + Regex + Statutory Logic)
                │
                ▼
[ Human-in-the-Loop Dashboard ] (Inspector Review, Overrides, Remarks)
                │
                ▼
[ Database & Traceable Storage ] (SQLite / SQLAlchemy -> Excel/CSV Export)
---

## 💻 Tech Stack

- **Language:** Python 3.10+[cite: 2]
- **Computer Vision:** OpenCV (`cv2`)[cite: 2]
- **OCR Engine:** EasyOCR[cite: 2]
- **Fuzzy Matching:** RapidFuzz[cite: 2]
- **Application Interface:** Streamlit[cite: 2]
- **Database & Persistence:** SQLite, SQLAlchemy[cite: 2]
- **Data Processing & Export:** Pandas, OpenPyXL[cite: 2]

---

## 🚀 Installation & Local Setup

### 1. Clone the Repository
bash
git clone [https://github.com/your-username/metrology-compliance-ai.git](https://github.com/your-username/metrology-compliance-ai.git)
cd metrology-compliance-ai

2. Create and Activate a Virtual Environment
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt
4. Run the Streamlit Application
streamlit run app.py
📁 Project Directory Structure
metrology-compliance-ai/
├── app.py                     # Streamlit frontend with inspection and audit history tabs
├── requirements.txt           # Project dependencies
├── README.md                  # Project documentation
├── metrology_inspections.db   # SQLite audit history database (auto-generated)
└── core/
    ├── __init__.py
    ├── ocr_engine.py          # Multi-angle OCR and image enhancement pipeline
    ├── detector.py            # HSV color-based statutory emblem detection
    ├── rule_validator.py      # Rule 6 & Rule 26 statutory validation logic
    └── database.py            # SQLAlchemy models and Excel/CSV export utilities
📄 Dependency File (requirements.txt)
streamlit>=1.30.0
opencv-python-headless>=4.8.0
easyocr>=1.7.0
rapidfuzz>=3.5.0
sqlalchemy>=2.0.0
pandas>=2.0.0
openpyxl>=3.1.0
pillow>=10.0.0
numpy>=1.24.0
