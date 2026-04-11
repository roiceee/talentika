"""
Resume PDF generator for seed_demo_data.

50 applicants per job profile are spread across 5 tiers (10 each):
  Tier 0 – Completely unqualified
  Tier 1 – Underqualified
  Tier 2 – Minimally qualified (meets basic requirements)
  Tier 3 – Well qualified
  Tier 4 – Highly qualified / overqualified
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ─────────────────────────────────────────────────────────────────────────────
# Resume content templates  (job_title → list of 5 tier dicts, index 0–4)
# ─────────────────────────────────────────────────────────────────────────────

RESUME_TEMPLATES = {
    "Accountant III": [
        # ── Tier 0: Unqualified ──────────────────────────────────────────────
        {
            "summary": (
                "Dedicated IT professional with 2 years of experience in technical support and "
                "system administration. Eager to explore new career opportunities."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Information Technology",
                    "school": "Davao City University",
                    "year": "2021",
                },
            ],
            "experience": [
                {
                    "title": "IT Support Technician",
                    "company": "TechServe Solutions",
                    "period": "June 2021 – Present",
                    "duties": [
                        "Provided first-level technical support for hardware and software issues",
                        "Installed and configured operating systems and office applications",
                        "Maintained local area network and server infrastructure",
                    ],
                }
            ],
            "skills": ["Technical Support", "Network Administration", "Windows Server", "MS Office"],
            "certifications": [],
        },
        # ── Tier 1: Underqualified ───────────────────────────────────────────
        {
            "summary": (
                "Business administration graduate with 1 year of bookkeeping experience. "
                "Seeking to grow in financial roles within a dynamic organization."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Business Administration (Major in Management)",
                    "school": "University of Southern Philippines",
                    "year": "2022",
                },
            ],
            "experience": [
                {
                    "title": "Bookkeeper",
                    "company": "Metro Davao Cooperative",
                    "period": "March 2023 – Present",
                    "duties": [
                        "Recorded daily cash and non-cash transactions in the general ledger",
                        "Assisted in monthly financial summary preparation",
                        "Maintained petty cash fund and disbursements log",
                    ],
                }
            ],
            "skills": ["Basic Bookkeeping", "MS Excel", "Data Entry", "Accounts Payable"],
            "certifications": [],
        },
        # ── Tier 2: Minimally qualified ──────────────────────────────────────
        {
            "summary": (
                "Junior accountant with 2 years of experience in government financial recording "
                "and reporting. Civil Service eligible with a solid grasp of accounting principles."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Commerce, Major in Accounting",
                    "school": "St. Theresa's College of Davao",
                    "year": "2021",
                },
            ],
            "experience": [
                {
                    "title": "Junior Accountant",
                    "company": "City Government of Davao",
                    "period": "August 2022 – Present",
                    "duties": [
                        "Processed and recorded daily financial transactions",
                        "Assisted in the preparation of barangay financial reports",
                        "Evaluated claims and expense vouchers for completeness",
                        "Filed and maintained accounting documents and records",
                    ],
                }
            ],
            "skills": [
                "Financial Recording", "Accounts Payable/Receivable",
                "MS Excel", "Government Accounting",
            ],
            "certifications": [
                "Civil Service Professional Eligible (RA 1080)",
                "8 hours Basic Government Accounting Training",
            ],
        },
        # ── Tier 3: Well qualified ───────────────────────────────────────────
        {
            "summary": (
                "Experienced government accountant with 3 years of service in financial management "
                "and reporting. Civil Service eligible with proven competency in budget monitoring, "
                "transaction control, and financial statement preparation."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Accountancy",
                    "school": "Mindanao State University – Davao",
                    "year": "2020",
                },
            ],
            "experience": [
                {
                    "title": "Accountant II",
                    "company": "City Government of Davao – Budget and Finance Office",
                    "period": "January 2021 – Present",
                    "duties": [
                        "Supervised the recording and control of daily financial transactions",
                        "Processed and audited barangay-level financial transactions",
                        "Prepared monthly and quarterly financial reports for submission to COA",
                        "Monitored budget utilization and flagged deviations from the approved plan",
                        "Coordinated with the Division Head on claims evaluation and reconciliation",
                    ],
                }
            ],
            "skills": [
                "Government Accounting", "Financial Reporting", "Budget Monitoring",
                "Internal Controls", "MS Excel", "NGAS",
            ],
            "certifications": [
                "Civil Service Professional Eligible (RA 1080)",
                "16 hours Training – New Government Accounting System (NGAS)",
                "8 hours Seminar on Government Expenditure Management",
            ],
        },
        # ── Tier 4: Highly qualified ─────────────────────────────────────────
        {
            "summary": (
                "Senior accountant and CPA with over 5 years in government financial management. "
                "Experienced in supervising accounting teams, preparing consolidated financial "
                "statements, and ensuring COA compliance."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Accountancy",
                    "school": "Ateneo de Davao University",
                    "year": "2018",
                },
                {
                    "degree": "Units in Master of Business Administration (in progress)",
                    "school": "University of Mindanao",
                    "year": "2023 – Present",
                },
            ],
            "experience": [
                {
                    "title": "Accountant III",
                    "company": "Department of Budget and Management – Region XI",
                    "period": "June 2022 – Present",
                    "duties": [
                        "Led a team of 5 accountants in the recording and reconciliation of transactions",
                        "Prepared consolidated financial statements for central office submission",
                        "Developed and implemented internal control procedures for claims evaluation",
                        "Coordinated the annual COA audit and addressed all audit findings",
                        "Supervised processing of all barangay financial transactions in the region",
                    ],
                },
                {
                    "title": "Accountant II",
                    "company": "City Government of Davao",
                    "period": "July 2019 – May 2022",
                    "duties": [
                        "Handled daily recording of financial transactions across multiple accounts",
                        "Prepared barangay financial summaries and assisted in budget preparation",
                        "Performed monthly reconciliation of general ledger accounts",
                    ],
                },
            ],
            "skills": [
                "Government Accounting", "Budget Control", "Financial Statement Preparation",
                "Internal Audit", "Team Supervision", "COA Compliance", "NGAS", "QuickBooks",
            ],
            "certifications": [
                "Certified Public Accountant (CPA) – Board Passer 2018",
                "Civil Service Professional Eligible (RA 1080)",
                "QuickBooks Certified User",
                "40 hours Advanced Training in Government Financial Management",
                "Certificate in Public Sector Accounting (COA Training Center)",
            ],
        },
    ],

    "Staff Nurse - ICU": [
        # ── Tier 0: Unqualified ──────────────────────────────────────────────
        {
            "summary": (
                "Licensed physical therapist with 2 years of rehabilitation experience in "
                "clinical settings. Passionate about patient wellness and holistic recovery."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Physical Therapy",
                    "school": "Davao City University",
                    "year": "2021",
                },
            ],
            "experience": [
                {
                    "title": "Physical Therapist",
                    "company": "Rehabilitation Institute of Davao",
                    "period": "March 2022 – Present",
                    "duties": [
                        "Assessed and treated patients with musculoskeletal and neurological conditions",
                        "Developed individualized rehabilitation and exercise programs",
                        "Maintained patient records and therapy progress notes",
                    ],
                }
            ],
            "skills": [
                "Physical Assessment", "Therapeutic Exercise",
                "Patient Documentation", "Rehabilitation Planning",
            ],
            "certifications": ["PRC License – Physical Therapist"],
        },
        # ── Tier 1: Underqualified ───────────────────────────────────────────
        {
            "summary": (
                "Registered nurse with 1.5 years of experience in a general medical-surgical ward. "
                "Seeking to advance clinical skills in a specialized critical care environment."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Nursing",
                    "school": "St. Theresa's College of Davao",
                    "year": "2022",
                },
            ],
            "experience": [
                {
                    "title": "Staff Nurse – Medical-Surgical Ward",
                    "company": "Davao Regional Medical Center",
                    "period": "January 2023 – Present",
                    "duties": [
                        "Provided direct nursing care to post-operative and general medical patients",
                        "Administered medications and monitored patient vital signs every shift",
                        "Assisted physicians during ward rounds and minor bedside procedures",
                        "Maintained nursing records and performed shift-to-shift endorsements",
                    ],
                }
            ],
            "skills": [
                "Vital Signs Monitoring", "Medication Administration", "IV Therapy", "Patient Education",
            ],
            "certifications": [
                "PRC License – Registered Nurse (Board Passer 2022)",
                "Basic Life Support (BLS) – American Heart Association",
            ],
        },
        # ── Tier 2: Minimally qualified ──────────────────────────────────────
        {
            "summary": (
                "Registered nurse with 1 year of ICU experience. Proficient in critical care "
                "monitoring and life support management. PRC licensed and BLS certified."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Nursing",
                    "school": "Ateneo de Davao University",
                    "year": "2021",
                },
            ],
            "experience": [
                {
                    "title": "Staff Nurse – Intensive Care Unit",
                    "company": "Southern Philippines Medical Center",
                    "period": "May 2022 – Present",
                    "duties": [
                        "Provided direct nursing care to critically ill patients in the ICU",
                        "Monitored and recorded hemodynamic parameters and ventilator settings",
                        "Managed invasive lines, feeding tubes, and life support equipment",
                        "Communicated patient status updates to attending physicians and families",
                    ],
                }
            ],
            "skills": [
                "Critical Care Monitoring", "Ventilator Management",
                "IV Therapy", "Hemodynamic Assessment", "Patient and Family Education",
            ],
            "certifications": [
                "PRC License – Registered Nurse (Board Passer 2021)",
                "Basic Life Support (BLS) – American Heart Association",
            ],
        },
        # ── Tier 3: Well qualified ───────────────────────────────────────────
        {
            "summary": (
                "ICU registered nurse with 3 years of critical care experience. Skilled in "
                "managing complex life-threatening conditions, operating advanced life support "
                "equipment, and coordinating multidisciplinary care. ACLS and Critical Care certified."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Nursing",
                    "school": "Mindanao State University – Davao",
                    "year": "2019",
                },
            ],
            "experience": [
                {
                    "title": "Staff Nurse – Intensive Care Unit",
                    "company": "Davao Doctors Hospital",
                    "period": "October 2020 – Present",
                    "duties": [
                        "Delivered comprehensive ICU nursing care for 2–3 critically ill patients per shift",
                        "Operated and troubleshot mechanical ventilators, cardiac monitors, and infusion pumps",
                        "Assessed and responded to acute deterioration including rapid resuscitation",
                        "Conducted family conferences and supported end-of-life care decisions",
                        "Mentored newly hired ICU nurses on unit protocols and equipment use",
                    ],
                }
            ],
            "skills": [
                "Advanced Critical Care", "Ventilator Management", "Hemodynamic Monitoring",
                "ACLS Protocols", "Rapid Response", "Clinical Documentation", "Family Education",
            ],
            "certifications": [
                "PRC License – Registered Nurse (Board Passer 2019)",
                "Basic Life Support (BLS) – American Heart Association",
                "Advanced Cardiac Life Support (ACLS) – American Heart Association",
                "Critical Care Nursing Training Certificate (48 hours) – PCNIN",
            ],
        },
        # ── Tier 4: Highly qualified ─────────────────────────────────────────
        {
            "summary": (
                "Senior ICU nurse with 6 years of progressive critical care experience including "
                "2 years as Charge Nurse. Expert in managing life-threatening emergencies, advanced "
                "life support technology, and leading ICU nursing teams. Pursuing Master in Nursing."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Nursing",
                    "school": "University of the Philippines – Mindanao",
                    "year": "2017",
                },
                {
                    "degree": "Units in Master of Arts in Nursing (in progress)",
                    "school": "Ateneo de Davao University",
                    "year": "2024 – Present",
                },
            ],
            "experience": [
                {
                    "title": "Senior Staff Nurse / Charge Nurse – ICU",
                    "company": "Southern Philippines Medical Center",
                    "period": "March 2022 – Present",
                    "duties": [
                        "Supervised a team of 8 ICU nurses across rotating shifts",
                        "Managed complex cases including ARDS, multi-organ failure, and post-cardiac surgery",
                        "Coordinated with intensivists, residents, and allied health staff for care planning",
                        "Developed and updated ICU nursing protocols and quality improvement initiatives",
                        "Conducted bedside orientation and clinical competency assessment for new hires",
                    ],
                },
                {
                    "title": "Staff Nurse – Intensive Care Unit",
                    "company": "Davao Doctors Hospital",
                    "period": "August 2018 – February 2022",
                    "duties": [
                        "Provided 1:1 care for mechanically ventilated and hemodynamically unstable patients",
                        "Responded to code blue situations and led bedside resuscitation efforts",
                        "Maintained accurate clinical documentation in the electronic medical record",
                    ],
                },
            ],
            "skills": [
                "Advanced Critical Care", "Team Leadership", "Ventilator Management",
                "ACLS & PALS Protocols", "Rapid Response", "EMR Documentation",
                "Staff Training & Mentoring", "Quality Improvement",
            ],
            "certifications": [
                "PRC License – Registered Nurse (Board Passer 2017, Renewal 2024)",
                "Basic Life Support (BLS) – American Heart Association",
                "Advanced Cardiac Life Support (ACLS) – American Heart Association",
                "Pediatric Advanced Life Support (PALS) – American Heart Association",
                "Critical Care Nursing Training Certificate (48 hours) – PCNIN",
                "Certified Critical Care Registered Nurse (CCRN) – ANCC",
            ],
        },
    ],

    "Barista": [
        # ── Tier 0: Unqualified ──────────────────────────────────────────────
        {
            "summary": (
                "Reliable and hardworking retail professional with 1 year of cashier experience. "
                "Looking for opportunities to grow in a customer-facing service role."
            ),
            "education": [
                {
                    "degree": "Senior High School Graduate (ABM Strand)",
                    "school": "Davao City National High School",
                    "year": "2022",
                },
            ],
            "experience": [
                {
                    "title": "Cashier",
                    "company": "Gaisano Mall – Davao",
                    "period": "April 2023 – Present",
                    "duties": [
                        "Processed customer purchases and handled cash and digital payments",
                        "Maintained accurate transaction records and end-of-day cash counts",
                        "Assisted in stock replenishment and merchandise display",
                    ],
                }
            ],
            "skills": ["Cash Handling", "Customer Service", "POS System", "Inventory Counting"],
            "certifications": [],
        },
        # ── Tier 1: Underqualified ───────────────────────────────────────────
        {
            "summary": (
                "Food service worker with 8 months of fast-food experience. Enthusiastic team "
                "player with a strong customer service orientation and willingness to learn."
            ),
            "education": [
                {
                    "degree": "Senior High School Graduate (TVL – Food & Beverage Services)",
                    "school": "Holy Cross of Davao College",
                    "year": "2023",
                },
            ],
            "experience": [
                {
                    "title": "Service Crew",
                    "company": "Jollibee – SM Davao",
                    "period": "October 2023 – Present",
                    "duties": [
                        "Prepared food and beverage orders following company quality standards",
                        "Operated cash register and handled customer transactions accurately",
                        "Maintained cleanliness and sanitation of the workstation and dining area",
                    ],
                }
            ],
            "skills": ["Food Preparation", "Customer Service", "Cash Handling", "Food Safety Practices"],
            "certifications": ["NCII Food and Beverage Services (in progress)"],
        },
        # ── Tier 2: Minimally qualified ──────────────────────────────────────
        {
            "summary": (
                "Barista with 1 year of experience in espresso preparation and café operations. "
                "Knowledgeable in standard coffee drinks and basic latte art. Passionate about "
                "delivering a quality coffee experience to every customer."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Hospitality Management (2nd Year, ongoing)",
                    "school": "University of Mindanao",
                    "year": "Expected 2026",
                },
            ],
            "experience": [
                {
                    "title": "Barista",
                    "company": "Figaro Coffee Company – Davao",
                    "period": "February 2023 – Present",
                    "duties": [
                        "Prepared espresso, drip, and blended coffee beverages per standard recipes",
                        "Provided product recommendations based on customer taste preferences",
                        "Operated and performed daily cleaning of espresso machines and grinders",
                        "Assisted in monitoring coffee bean and syrup inventory levels",
                    ],
                }
            ],
            "skills": [
                "Espresso Preparation", "Latte Art (Basic)", "Customer Service",
                "POS System", "Inventory Tracking",
            ],
            "certifications": ["Barista Training Certificate – Figaro Academy (16 hours)"],
        },
        # ── Tier 3: Well qualified ───────────────────────────────────────────
        {
            "summary": (
                "Experienced barista with 2 years of specialty coffee experience and a Hospitality "
                "Management background. Skilled in manual brewing, espresso dialing, and customer "
                "engagement. Has experience training new café staff on beverage standards."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Hospitality Management",
                    "school": "Holy Cross of Davao College",
                    "year": "2022",
                },
            ],
            "experience": [
                {
                    "title": "Barista / Shift Supervisor",
                    "company": "Bo's Coffee – SM Lanang Premier",
                    "period": "July 2022 – Present",
                    "duties": [
                        "Prepared all espresso-based, cold brew, and manual pour-over beverages",
                        "Supervised a shift team of 3 baristas and maintained service quality standards",
                        "Calibrated espresso machines and performed weekly equipment deep cleaning",
                        "Managed daily ingredient inventory and coordinated supply restocking",
                        "Onboarded and trained 2 newly hired baristas on techniques and service etiquette",
                    ],
                }
            ],
            "skills": [
                "Espresso Dialing", "Manual Brewing (Pour-Over, AeroPress, Chemex)",
                "Latte Art", "Shift Supervision", "Staff Training", "Inventory Management",
            ],
            "certifications": [
                "SCAE Introduction to Coffee Certificate",
                "Barista Level 1 – Specialty Coffee Association (SCA)",
            ],
        },
        # ── Tier 4: Highly qualified ─────────────────────────────────────────
        {
            "summary": (
                "Senior barista and coffee trainer with 3+ years of specialty café experience. "
                "SCA-certified with competition background and expertise in menu development, "
                "machine maintenance, and staff training. Seeking a challenging role in a "
                "premium café environment."
            ),
            "education": [
                {
                    "degree": "Bachelor of Science in Hospitality Management",
                    "school": "Ateneo de Davao University",
                    "year": "2020",
                },
            ],
            "experience": [
                {
                    "title": "Lead Barista / Coffee Trainer",
                    "company": "Starbucks Reserve – Abreeza Mall Davao",
                    "period": "March 2022 – Present",
                    "duties": [
                        "Prepared and served Starbucks Reserve signature and single-origin offerings",
                        "Conducted in-store coffee education sessions for customers and café staff",
                        "Trained 10+ baristas on brewing techniques, machine calibration, and service standards",
                        "Assisted in seasonal menu development and promotional product campaigns",
                        "Maintained La Marzocca espresso machines and Clover brewing systems",
                    ],
                },
                {
                    "title": "Barista",
                    "company": "7Cups Specialty Coffee",
                    "period": "August 2020 – February 2022",
                    "duties": [
                        "Brewed and served specialty pour-over, cold brew, and espresso beverages",
                        "Managed green and roasted coffee bean inventory using FIFO protocol",
                        "Placed 3rd in the Davao Regional Barista Championship 2021",
                    ],
                },
            ],
            "skills": [
                "Specialty Espresso & Manual Brewing", "Advanced Latte Art",
                "Staff Training & Mentoring", "Menu Development",
                "Machine Maintenance (La Marzocca, Clover)", "Inventory Management",
            ],
            "certifications": [
                "SCA Barista Skills – Foundation & Intermediate",
                "SCA Brewing – Foundation",
                "Coffee Quality Institute (CQI) – Introduction to Green Coffee",
                "NCII Food and Beverage Services",
            ],
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

_NAVY   = colors.HexColor("#1a3c6e")
_TEAL   = colors.HexColor("#0e7c6e")
_SLATE  = colors.HexColor("#4a5568")
_GREY   = colors.HexColor("#cccccc")
_LGREY  = colors.HexColor("#f5f5f5")
_WHITE  = colors.white
_BLACK  = colors.black
_DKGREY = colors.HexColor("#333333")


def _doc(buffer, *, lm=0.75, rm=0.75, tm=0.75, bm=0.75):
    return SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=lm * inch, rightMargin=rm * inch,
        topMargin=tm * inch, bottomMargin=bm * inch,
    )


def _hr(color=_GREY, thickness=0.5, space_after=4):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=space_after)


# ─────────────────────────────────────────────────────────────────────────────
# Style 0 — Classic (Times Roman, centred name, navy rule)
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_0_classic(first_name, last_name, email, phone, template) -> bytes:
    buffer = BytesIO()
    doc = _doc(buffer)
    base = getSampleStyleSheet()

    name_s = ParagraphStyle("s0_name", parent=base["Title"],
                            fontName="Times-Bold", fontSize=20,
                            spaceAfter=2, alignment=TA_CENTER, textColor=_NAVY)
    contact_s = ParagraphStyle("s0_contact", parent=base["Normal"],
                               fontName="Times-Roman", fontSize=9,
                               alignment=TA_CENTER, spaceAfter=6)
    section_s = ParagraphStyle("s0_section", parent=base["Normal"],
                               fontName="Times-Bold", fontSize=11,
                               spaceBefore=10, spaceAfter=2, textColor=_NAVY)
    body_s = ParagraphStyle("s0_body", parent=base["Normal"],
                            fontName="Times-Roman", fontSize=9, spaceAfter=2)
    jh_s = ParagraphStyle("s0_jh", parent=base["Normal"],
                          fontName="Times-Bold", fontSize=9, spaceAfter=1)
    bullet_s = ParagraphStyle("s0_bullet", parent=base["Normal"],
                              fontName="Times-Roman", fontSize=9,
                              leftIndent=14, spaceAfter=1)

    story = []
    story.append(Paragraph(f"{first_name} {last_name}", name_s))
    story.append(Paragraph(f"{email}  |  {phone}  |  Davao City, Philippines", contact_s))
    story.append(_hr(_NAVY, thickness=2, space_after=6))

    story.append(Paragraph("PROFESSIONAL SUMMARY", section_s))
    story.append(_hr(_GREY, 0.5, 3))
    story.append(Paragraph(template["summary"], body_s))

    story.append(Paragraph("EDUCATION", section_s))
    story.append(_hr(_GREY, 0.5, 3))
    for edu in template["education"]:
        story.append(Paragraph(f"<b>{edu['degree']}</b>", body_s))
        story.append(Paragraph(f"{edu['school']}  |  {edu['year']}", body_s))
        story.append(Spacer(1, 3))

    story.append(Paragraph("WORK EXPERIENCE", section_s))
    story.append(_hr(_GREY, 0.5, 3))
    for exp in template["experience"]:
        story.append(Paragraph(f"<b>{exp['title']}</b>  —  {exp['company']}", jh_s))
        story.append(Paragraph(exp["period"], body_s))
        for duty in exp["duties"]:
            story.append(Paragraph(f"• {duty}", bullet_s))
        story.append(Spacer(1, 4))

    story.append(Paragraph("SKILLS", section_s))
    story.append(_hr(_GREY, 0.5, 3))
    story.append(Paragraph(",  ".join(template["skills"]), body_s))

    if template.get("certifications"):
        story.append(Paragraph("CERTIFICATIONS & LICENSES", section_s))
        story.append(_hr(_GREY, 0.5, 3))
        for cert in template["certifications"]:
            story.append(Paragraph(f"• {cert}", bullet_s))

    doc.build(story)
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Style 1 — Modern Blue (Helvetica, filled navy section header boxes)
# ─────────────────────────────────────────────────────────────────────────────

def _filled_header(text, bg_color, fg_color=_WHITE, font="Helvetica-Bold", fs=10):
    """Return a 1-cell Table that looks like a coloured section header bar."""
    style = ParagraphStyle("_fh_inner", fontName=font, fontSize=fs, textColor=fg_color)
    p = Paragraph(text, style)
    tbl = Table([[p]], colWidths=["100%"])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _build_style_1_modern_blue(first_name, last_name, email, phone, template) -> bytes:
    buffer = BytesIO()
    doc = _doc(buffer)
    base = getSampleStyleSheet()

    name_s = ParagraphStyle("s1_name", parent=base["Normal"],
                            fontName="Helvetica-Bold", fontSize=22,
                            spaceAfter=0, textColor=_NAVY)
    contact_s = ParagraphStyle("s1_contact", parent=base["Normal"],
                               fontName="Helvetica", fontSize=9,
                               spaceAfter=8, textColor=_SLATE)
    body_s = ParagraphStyle("s1_body", parent=base["Normal"],
                            fontName="Helvetica", fontSize=9, spaceAfter=2)
    jh_s = ParagraphStyle("s1_jh", parent=base["Normal"],
                          fontName="Helvetica-Bold", fontSize=9, spaceAfter=1)
    bullet_s = ParagraphStyle("s1_bullet", parent=base["Normal"],
                              fontName="Helvetica", fontSize=9,
                              leftIndent=14, spaceAfter=1)

    story = []
    story.append(Paragraph(f"{first_name} {last_name}", name_s))
    story.append(Paragraph(f"{email}  |  {phone}  |  Davao City, Philippines", contact_s))
    story.append(_hr(_NAVY, 2, 8))

    story.append(_filled_header("PROFESSIONAL SUMMARY", _NAVY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(template["summary"], body_s))

    story.append(Spacer(1, 6))
    story.append(_filled_header("EDUCATION", _NAVY))
    story.append(Spacer(1, 4))
    for edu in template["education"]:
        story.append(Paragraph(f"<b>{edu['degree']}</b>", body_s))
        story.append(Paragraph(f"{edu['school']}  |  {edu['year']}", body_s))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 6))
    story.append(_filled_header("WORK EXPERIENCE", _NAVY))
    story.append(Spacer(1, 4))
    for exp in template["experience"]:
        story.append(Paragraph(f"<b>{exp['title']}</b>  —  {exp['company']}", jh_s))
        story.append(Paragraph(exp["period"], body_s))
        for duty in exp["duties"]:
            story.append(Paragraph(f"• {duty}", bullet_s))
        story.append(Spacer(1, 4))

    story.append(_filled_header("SKILLS", _NAVY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(",  ".join(template["skills"]), body_s))

    if template.get("certifications"):
        story.append(Spacer(1, 6))
        story.append(_filled_header("CERTIFICATIONS & LICENSES", _NAVY))
        story.append(Spacer(1, 4))
        for cert in template["certifications"]:
            story.append(Paragraph(f"• {cert}", bullet_s))

    doc.build(story)
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Style 2 — Teal Accent (coloured top banner, teal section underlines)
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_2_teal(first_name, last_name, email, phone, template) -> bytes:
    buffer = BytesIO()
    doc = _doc(buffer, tm=0.5)
    base = getSampleStyleSheet()

    # Coloured name banner via a Table
    banner_name_s = ParagraphStyle("s2_bname", fontName="Helvetica-Bold",
                                   fontSize=20, textColor=_WHITE)
    banner_contact_s = ParagraphStyle("s2_bc", fontName="Helvetica",
                                      fontSize=9, textColor=_WHITE)
    banner_tbl = Table(
        [[Paragraph(f"{first_name} {last_name}", banner_name_s)],
         [Paragraph(f"{email}  |  {phone}  |  Davao City, Philippines", banner_contact_s)]],
        colWidths=["100%"],
    )
    banner_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_TEAL]),
    ]))

    section_s = ParagraphStyle("s2_section", parent=base["Normal"],
                               fontName="Helvetica-Bold", fontSize=10,
                               spaceBefore=10, spaceAfter=1, textColor=_TEAL)
    body_s = ParagraphStyle("s2_body", parent=base["Normal"],
                            fontName="Helvetica", fontSize=9, spaceAfter=2)
    jh_s = ParagraphStyle("s2_jh", parent=base["Normal"],
                          fontName="Helvetica-Bold", fontSize=9, spaceAfter=1)
    bullet_s = ParagraphStyle("s2_bullet", parent=base["Normal"],
                              fontName="Helvetica", fontSize=9,
                              leftIndent=14, spaceAfter=1)

    story = []
    story.append(banner_tbl)
    story.append(Spacer(1, 8))

    def section(title):
        story.append(Paragraph(title, section_s))
        story.append(_hr(_TEAL, 1, 3))

    section("PROFESSIONAL SUMMARY")
    story.append(Paragraph(template["summary"], body_s))

    section("EDUCATION")
    for edu in template["education"]:
        story.append(Paragraph(f"<b>{edu['degree']}</b>", body_s))
        story.append(Paragraph(f"{edu['school']}  |  {edu['year']}", body_s))
        story.append(Spacer(1, 3))

    section("WORK EXPERIENCE")
    for exp in template["experience"]:
        story.append(Paragraph(f"<b>{exp['title']}</b>  —  {exp['company']}", jh_s))
        story.append(Paragraph(exp["period"], body_s))
        for duty in exp["duties"]:
            story.append(Paragraph(f"• {duty}", bullet_s))
        story.append(Spacer(1, 4))

    section("SKILLS")
    story.append(Paragraph(",  ".join(template["skills"]), body_s))

    if template.get("certifications"):
        section("CERTIFICATIONS & LICENSES")
        for cert in template["certifications"]:
            story.append(Paragraph(f"• {cert}", bullet_s))

    doc.build(story)
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Style 3 — Minimal (clean, grey palette, no rules, generous whitespace)
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_3_minimal(first_name, last_name, email, phone, template) -> bytes:
    buffer = BytesIO()
    doc = _doc(buffer, lm=1.0, rm=1.0, tm=1.0, bm=1.0)
    base = getSampleStyleSheet()

    name_s = ParagraphStyle("s3_name", parent=base["Normal"],
                            fontName="Helvetica",
                            fontSize=24, spaceAfter=2, textColor=_DKGREY)
    contact_s = ParagraphStyle("s3_contact", parent=base["Normal"],
                               fontName="Helvetica", fontSize=8,
                               spaceAfter=14, textColor=_SLATE)
    section_s = ParagraphStyle("s3_section", parent=base["Normal"],
                               fontName="Helvetica-Bold", fontSize=9,
                               spaceBefore=14, spaceAfter=4,
                               textColor=_SLATE, letterSpacing=1)
    body_s = ParagraphStyle("s3_body", parent=base["Normal"],
                            fontName="Helvetica", fontSize=9,
                            spaceAfter=2, textColor=_DKGREY)
    jh_s = ParagraphStyle("s3_jh", parent=base["Normal"],
                          fontName="Helvetica-Bold", fontSize=9,
                          spaceAfter=1, textColor=_DKGREY)
    bullet_s = ParagraphStyle("s3_bullet", parent=base["Normal"],
                              fontName="Helvetica", fontSize=9,
                              leftIndent=14, spaceAfter=1, textColor=_DKGREY)

    story = []
    story.append(Paragraph(f"{first_name} {last_name}", name_s))
    story.append(Paragraph(f"{email}  ·  {phone}  ·  Davao City, Philippines", contact_s))

    def section(title):
        story.append(Paragraph(title.upper(), section_s))

    section("Summary")
    story.append(Paragraph(template["summary"], body_s))

    section("Education")
    for edu in template["education"]:
        story.append(Paragraph(f"<b>{edu['degree']}</b>", body_s))
        story.append(Paragraph(f"{edu['school']}  ·  {edu['year']}", body_s))
        story.append(Spacer(1, 4))

    section("Experience")
    for exp in template["experience"]:
        story.append(Paragraph(f"<b>{exp['title']}</b>  ·  {exp['company']}", jh_s))
        story.append(Paragraph(exp["period"], body_s))
        for duty in exp["duties"]:
            story.append(Paragraph(f"– {duty}", bullet_s))
        story.append(Spacer(1, 6))

    section("Skills")
    story.append(Paragraph("  ·  ".join(template["skills"]), body_s))

    if template.get("certifications"):
        section("Certifications")
        for cert in template["certifications"]:
            story.append(Paragraph(f"– {cert}", bullet_s))

    doc.build(story)
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Style 4 — Two-Column Sidebar (dark left panel, white right panel)
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_4_sidebar(first_name, last_name, email, phone, template) -> bytes:
    """
    Layout: narrow dark-navy left column (contact, skills, certs) |
            wider white right column (summary, experience, education).
    Implemented as a single wide Table with two cells.
    """
    buffer = BytesIO()
    doc = _doc(buffer, lm=0.5, rm=0.5, tm=0.5, bm=0.5)
    base = getSampleStyleSheet()

    usable_w = letter[0] - 1.0 * inch  # 7.5 inches
    left_w  = 2.1 * inch
    right_w = usable_w - left_w

    # ── Left-column styles ──────────────────────────────────────────────────
    lname_s = ParagraphStyle("s4_lname", fontName="Helvetica-Bold",
                             fontSize=14, textColor=_WHITE, spaceAfter=2)
    lcontact_s = ParagraphStyle("s4_lcontact", fontName="Helvetica",
                                fontSize=7.5, textColor=colors.HexColor("#c0cfe0"),
                                spaceAfter=3)
    lsection_s = ParagraphStyle("s4_lsect", fontName="Helvetica-Bold",
                                fontSize=8.5, textColor=_WHITE,
                                spaceBefore=10, spaceAfter=3,
                                borderPad=0)
    lbody_s = ParagraphStyle("s4_lbody", fontName="Helvetica",
                             fontSize=8, textColor=colors.HexColor("#c0cfe0"),
                             spaceAfter=2)

    # ── Right-column styles ─────────────────────────────────────────────────
    rsection_s = ParagraphStyle("s4_rsect", fontName="Helvetica-Bold",
                                fontSize=10, textColor=_NAVY,
                                spaceBefore=10, spaceAfter=2)
    rbody_s = ParagraphStyle("s4_rbody", fontName="Helvetica",
                             fontSize=9, spaceAfter=2, textColor=_DKGREY)
    rjh_s = ParagraphStyle("s4_rjh", fontName="Helvetica-Bold",
                           fontSize=9, spaceAfter=1, textColor=_DKGREY)
    rbullet_s = ParagraphStyle("s4_rbullet", fontName="Helvetica",
                               fontSize=9, leftIndent=12, spaceAfter=1,
                               textColor=_DKGREY)

    # ── Build left column content ───────────────────────────────────────────
    left = []
    left.append(Paragraph(f"{first_name}<br/>{last_name}", lname_s))
    left.append(Spacer(1, 4))
    left.append(Paragraph(email, lcontact_s))
    left.append(Paragraph(phone, lcontact_s))
    left.append(Paragraph("Davao City, Philippines", lcontact_s))

    left.append(Paragraph("SKILLS", lsection_s))
    left.append(_hr(colors.HexColor("#3a5c8e"), 0.5, 4))
    for skill in template["skills"]:
        left.append(Paragraph(f"• {skill}", lbody_s))

    if template.get("certifications"):
        left.append(Paragraph("LICENSES &amp; CERTS", lsection_s))
        left.append(_hr(colors.HexColor("#3a5c8e"), 0.5, 4))
        for cert in template["certifications"]:
            left.append(Paragraph(f"• {cert}", lbody_s))

    # ── Build right column content ──────────────────────────────────────────
    right = []
    right.append(Paragraph("PROFESSIONAL SUMMARY", rsection_s))
    right.append(_hr(_NAVY, 1, 3))
    right.append(Paragraph(template["summary"], rbody_s))

    right.append(Paragraph("WORK EXPERIENCE", rsection_s))
    right.append(_hr(_NAVY, 1, 3))
    for exp in template["experience"]:
        right.append(Paragraph(f"<b>{exp['title']}</b>  —  {exp['company']}", rjh_s))
        right.append(Paragraph(exp["period"], rbody_s))
        for duty in exp["duties"]:
            right.append(Paragraph(f"• {duty}", rbullet_s))
        right.append(Spacer(1, 4))

    right.append(Paragraph("EDUCATION", rsection_s))
    right.append(_hr(_NAVY, 1, 3))
    for edu in template["education"]:
        right.append(Paragraph(f"<b>{edu['degree']}</b>", rbody_s))
        right.append(Paragraph(f"{edu['school']}  |  {edu['year']}", rbody_s))
        right.append(Spacer(1, 3))

    # Wrap columns in a 2-cell table
    tbl = Table([[left, right]], colWidths=[left_w, right_w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), _NAVY),
        ("BACKGROUND",    (1, 0), (1, -1), _WHITE),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (0, -1), 10),
        ("RIGHTPADDING",  (0, 0), (0, -1), 10),
        ("LEFTPADDING",   (1, 0), (1, -1), 14),
        ("RIGHTPADDING",  (1, 0), (1, -1), 8),
    ]))

    doc.build([tbl])
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────────────────────────────────────

_BUILDERS = [
    _build_style_0_classic,
    _build_style_1_modern_blue,
    _build_style_2_teal,
    _build_style_3_minimal,
    _build_style_4_sidebar,
]


def build_resume_pdf(
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    template: dict,
    style_idx: int = 0,
) -> bytes:
    builder = _BUILDERS[style_idx % len(_BUILDERS)]
    return builder(first_name, last_name, email, phone, template)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_tier(applicant_index: int, total: int = 30) -> int:
    """Return tier 0-4 for a 1-based applicant index (6 applicants per tier for total=30)."""
    per_tier = total // 5
    return min((applicant_index - 1) // per_tier, 4)


def generate_resume(
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    job_title: str,
    applicant_index: int,
) -> bytes:
    """Generate a unique resume PDF for the given applicant and job title."""
    tier = get_tier(applicant_index)
    style_idx = (applicant_index - 1) % 5
    template = RESUME_TEMPLATES[job_title][tier]
    return build_resume_pdf(first_name, last_name, email, phone, template, style_idx)
