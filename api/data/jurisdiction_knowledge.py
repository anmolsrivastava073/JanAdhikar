"""
JanAdhikar Hierarchical Knowledge Graph & GraphRAG Entity Registry
Comprehensive authority mappings, statutory designations, legal query templates,
legal subject synthesizers, and verified public accountability social handles.
"""

from typing import Dict, Any, List, Optional

# Comprehensive Hierarchical Knowledge Graph for Indian Civic, Administrative & Public Authorities
AUTHORITY_KNOWLEDGE_GRAPH: Dict[str, Dict[str, Any]] = {
    "roads_highways_infrastructure": {
        "domain": "Civic Infrastructure, Roads & Highways",
        "keywords": ["road", "pothole", "highway", "expressway", "bridge", "flyover", "nhai", "pwd", "street", "footpath", "drainage", "contractor", "toll"],
        "legal_subject_template": "Request for Certified Records, Technical Sanction, Contractor Agreement, Measurement Book, and Quality Inspection Reports regarding Road Construction and Infrastructure Maintenance in [LOCATION]",
        "legal_issue_statement": "Substandard infrastructure construction, tender non-compliance, and severe road maintenance neglect",
        "central_authority": {
            "name": "National Highways Authority of India (NHAI) / Ministry of Road Transport and Highways (MoRTH)",
            "cpio_designation": "Central Public Information Officer & Project Director, NHAI Project Implementation Unit (PIU)",
            "faa_designation": "First Appellate Authority & Chief General Manager (Regional Office), NHAI",
            "address_template": "Project Implementation Unit (PIU), NHAI, [CITY_NAME], [STATE_NAME]",
            "handles": ["@NHAI_Official", "@MORTHIndia", "@nitin_gadkari"]
        },
        "state_authority": {
            "name": "State Public Works Department (PWD) / State Road Development Corporation",
            "cpio_designation": "Public Information Officer & Executive Engineer, PWD Construction Division",
            "faa_designation": "First Appellate Authority & Superintending Engineer, PWD Circle",
            "address_template": "Office of the Executive Engineer, PWD Division, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MORTHIndia", "@MoHUA_India"]
        },
        "municipal_authority": {
            "name": "Municipal Corporation / Urban Local Body Engineering Department",
            "cpio_designation": "Public Information Officer & Chief City Engineer (Civil/Roads), Municipal Corporation",
            "faa_designation": "First Appellate Authority & Additional Municipal Commissioner",
            "address_template": "Engineering Division (Roads), Municipal Corporation Headquarters, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MoHUA_India", "@CPGRAMS"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the Technical Sanction, Administrative Approval, and Detailed Project Report (DPR) along with the BOQ (Bill of Quantities) for the construction/repair of the specified road stretch in [LOCATION].",
            "Provide certified extract copies of the Measurement Book (MB) recording the thickness, bituminous quality, and material tests conducted prior to releasing contractor payments.",
            "Provide certified copies of the Work Order, Contract Agreement, Tender NIT (Notice Inviting Tender), and name of the executing contractor/agency along with the statutory Defect Liability Period (DLP).",
            "Provide certified copies of all Quality Assurance and Third-Party Audit (TPA) inspection reports conducted by government laboratories or certified institutions during the execution period.",
            "Provide the certified daily progress report, bituminous core test certificates, and daily logbook of the Junior Engineer / Assistant Engineer supervising the road construction.",
            "Under Section 2(j)(i) of the RTI Act 2005, the applicant seeks inspection of all physical records, measurement sheets, and file notings concerning sanction and maintenance of the said stretch."
        ]
    },

    "healthcare_hospitals_ayushman": {
        "domain": "Public Healthcare, Government Hospitals & Health Schemes",
        "keywords": ["hospital", "doctor", "health", "ayushman", "pmjay", "medical", "treatment", "medicine", "cghs", "aiims", "clinic", "dispensary", "admission", "death", "negligence"],
        "legal_subject_template": "Request for Certified Admission Logs, Essential Medicine Inventory Registers, and Cashless Treatment Scheme Approvals in [LOCATION]",
        "legal_issue_statement": "Deficiency in public healthcare service delivery, wrongful denial of cashless hospital admission, and essential medicine unavailability",
        "central_authority": {
            "name": "National Health Authority (NHA) / Ministry of Health and Family Welfare (MoHFW) / AIIMS",
            "cpio_designation": "Central Public Information Officer & Deputy Director (Admin), Medical Institution / NHA",
            "faa_designation": "First Appellate Authority & Medical Superintendent / Director, Health Authority",
            "address_template": "Office of the Medical Superintendent / CPIO, [HOSPITAL_OR_AIIMS], [CITY_NAME], [STATE_NAME]",
            "handles": ["@MoHFW_INDIA", "@AyushmanNHA", "@mansukhmandviya"]
        },
        "state_authority": {
            "name": "Directorate of Medical Health & Family Welfare / District Chief Medical Officer (CMO)",
            "cpio_designation": "Public Information Officer & Chief Medical Officer (CMO) / Medical Superintendent",
            "faa_designation": "First Appellate Authority & Additional Director of Medical Health",
            "address_template": "Office of the Chief Medical Officer (CMO), District Health Office, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MoHFW_INDIA", "@CPGRAMS"]
        },
        "municipal_authority": {
            "name": "Municipal Health Department / Urban Primary Health Centers (UPHC)",
            "cpio_designation": "Public Information Officer & Chief Medical Officer of Health (MOH)",
            "faa_designation": "First Appellate Authority & Municipal Commissioner",
            "address_template": "Municipal Health Division, Municipal Corporation, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MoHFW_INDIA", "@MoHUA_India"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the hospital bed allocation register, admission records, and duty doctor roster for the specified dates and department in [LOCATION].",
            "Provide certified copies of the Ayushman Bharat PM-JAY / State Health Scheme cashless pre-authorization logs, claim rejection memos, and internal reasons recorded by the Hospital Grievance Cell.",
            "Provide certified copies of the stock register, procurement receipts, and daily physical availability logs of essential life-saving medicines and surgical consumables.",
            "Provide certified copies of the enquiry committee report, mortality audit minutes, and file notings regarding patient grievance on record.",
            "Provide certified details of the sanctioned strength vs. existing vacancy position of medical specialists, surgeons, nurses, and lab technicians in the institution."
        ]
    },

    "labor_pension_epfo_esi": {
        "domain": "Labor, EPF, ESI, Gratuity & Pensionary Benefits",
        "keywords": ["pension", "pf", "epf", "epfo", "esi", "esic", "gratuity", "provident fund", "salary", "wages", "withheld", "claim", "uan", "cpao", "treasury"],
        "legal_subject_template": "Request for Certified Processing Sheets, Employer Remittance Verification, and Delay Escalation Logs regarding EPF / Pension Claim in [LOCATION]",
        "legal_issue_statement": "Withheld statutory pensionary benefits, delayed EPF claim settlement, and administrative non-compliance",
        "central_authority": {
            "name": "Employees' Provident Fund Organisation (EPFO) / Employees' State Insurance Corporation (ESIC)",
            "cpio_designation": "Central Public Information Officer & Regional P.F. Commissioner-II / Assistant Director, EPFO/ESIC",
            "faa_designation": "First Appellate Authority & Regional P.F. Commissioner-I / Regional Director, EPFO/ESIC",
            "address_template": "Regional Office, Employees' Provident Fund Organisation (EPFO), [CITY_NAME], [STATE_NAME]",
            "handles": ["@socialepfo", "@LabourMinistry", "@esichq"]
        },
        "state_authority": {
            "name": "State Treasury & Accounts Directorate / State Labor Commissionerate",
            "cpio_designation": "Public Information Officer & Treasury Officer / Assistant Labor Commissioner",
            "faa_designation": "First Appellate Authority & Chief Treasury Officer / Joint Labor Commissioner",
            "address_template": "District Treasury Office / Office of the Labor Commissioner, [CITY_NAME], [STATE_NAME]",
            "handles": ["@LabourMinistry", "@FinMinIndia"]
        },
        "municipal_authority": {
            "name": "Municipal Pension & Welfare Department",
            "cpio_designation": "Public Information Officer & Chief Accounts Officer (Pension Cell)",
            "faa_designation": "First Appellate Authority & Financial Advisor & Chief Accounts Officer (FA&CAO)",
            "address_template": "Accounts & Pension Wing, Municipal Corporation, [CITY_NAME], [STATE_NAME]",
            "handles": ["@CPGRAMS"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the complete file notings, movement history, and processing sheet concerning EPF/Pension Claim Ref/UAN No: [REF_NO].",
            "Provide certified particulars of the exact statutory reason and regulatory provision under which the claim disbursement has been withheld or rejected.",
            "Provide certified copies of the monthly statutory contribution remittances submitted by the establishment (Employer) under Section 6 of EPF Act 1952 for the period [TIME_PERIOD].",
            "Provide the designated officer's name, designation, and official delay escalation log as per the citizen charter service level benchmark."
        ]
    },

    "police_fir_investigation_law": {
        "domain": "Police, Law & Order, FIR Tracking & Public Safety",
        "keywords": ["police", "fir", "complaint", "station", "sho", "crime", "theft", "harassment", "assault", "investigation", "chargesheet", "cyber", "sp", "dcp", "commissioner"],
        "legal_subject_template": "Request for Certified General Diary Extracts, Action Taken Reports (ATR), and Investigation Progress Records in [LOCATION]",
        "legal_issue_statement": "Failure to register FIR, delayed police enquiry, and non-disclosure of statutory investigation progress",
        "central_authority": {
            "name": "Central Armed Police / Central Bureau of Investigation (CBI) / Delhi Police",
            "cpio_designation": "Public Information Officer & Additional Deputy Commissioner of Police (ADCP/DCP)",
            "faa_designation": "First Appellate Authority & Joint Commissioner of Police",
            "address_template": "Office of the Deputy Commissioner of Police, [DISTRICT_NAME], [CITY_NAME]",
            "handles": ["@HMOIndia", "@DelhiPolice", "@CPGRAMS"]
        },
        "state_authority": {
            "name": "State Police Department / Office of the Superintendent of Police (SP)",
            "cpio_designation": "Public Information Officer & Additional Superintendent of Police (Addl. SP / DySP HQ)",
            "faa_designation": "First Appellate Authority & Superintendent of Police (SP) / Senior SP (SSP)",
            "address_template": "District Police Headquarters, Office of the SP/SSP, [DISTRICT_NAME], [STATE_NAME]",
            "handles": ["@HMOIndia", "@CPGRAMS"]
        },
        "municipal_authority": {
            "name": "City Police Commissionerate",
            "cpio_designation": "Public Information Officer & Assistant Commissioner of Police (ACP / Admin)",
            "faa_designation": "First Appellate Authority & Deputy Commissioner of Police (DCP)",
            "address_template": "Office of the Commissioner of Police, [CITY_NAME], [STATE_NAME]",
            "handles": ["@HMOIndia"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the General Diary (GD) / Daily Diary (DD) entry extract recorded on the date of submission of Complaint Ref: [REF_NO].",
            "Provide certified copies of the Action Taken Report (ATR), preliminary inquiry report, and current stage of investigation under Section 157/173 of CrPC / BNSS.",
            "Provide the name, designation, and contact details of the Investigating Officer (IO) to whom the complaint/FIR was marked for enquiry.",
            "Provide certified copies of all supervisory file notings and remarks recorded by the Circle Officer (CO) / ACP on the said investigation file.",
            "In case of delay beyond standard investigation norms, provide certified copies of reasons recorded in writing by the Station House Officer (SHO)."
        ]
    },

    "municipal_sanitation_water_utilities": {
        "domain": "Municipal Governance, Water Supply, Sanitation & Drainage",
        "keywords": ["water", "sewage", "drain", "garbage", "sanitation", "cleanliness", "street light", "cleaning", "park", "illegal construction", "encroachment", "building permit", "property tax"],
        "legal_subject_template": "Request for Certified Water Quality Lab Reports, Solid Waste Management Contracts, and Drainage Desilting Expenditure in [LOCATION]",
        "legal_issue_statement": "Municipal administration deficiency, contaminated water supply, and public sanitation breakdown",
        "central_authority": {
            "name": "Ministry of Housing and Urban Affairs (MoHUA) / Smart Cities Mission",
            "cpio_designation": "Central Public Information Officer & Under Secretary, MoHUA",
            "faa_designation": "First Appellate Authority & Director (Urban Development), MoHUA",
            "address_template": "Nirman Bhawan, Ministry of Housing & Urban Affairs, New Delhi",
            "handles": ["@MoHUA_India", "@SwachhBharatGov", "@HardeepSPuri"]
        },
        "state_authority": {
            "name": "State Urban Development & Water Supply and Sewerage Board (Jal Nigam)",
            "cpio_designation": "Public Information Officer & Executive Engineer, State Water Supply & Sewerage Board",
            "faa_designation": "First Appellate Authority & Superintending Engineer, Jal Nigam",
            "address_template": "Divisional Office, Water Supply & Sewerage Board, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MoHUA_India", "@CPGRAMS"]
        },
        "municipal_authority": {
            "name": "Municipal Corporation / Nagar Nigam / Municipality",
            "cpio_designation": "Public Information Officer & Health Officer / Executive Engineer (Water Supply & Drainage)",
            "faa_designation": "First Appellate Authority & Additional Municipal Commissioner",
            "address_template": "Headquarters, Municipal Corporation, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MoHUA_India", "@SwachhBharatGov"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the water quality testing reports (testing TDS, chemical and bacteriological purity) conducted by the municipal laboratory for [LOCALITY] in the last 6 months.",
            "Provide certified copies of the contract agreement, duty roaster, daily garbage collection logs, and payment deductions for the solid waste management contractor serving Ward No: [WARD_NO].",
            "Provide certified copies of the sanctioned building plans, layout approvals, and structural safety certificates issued for the structure situated at [ADDRESS].",
            "Provide certified extract copies of the complaint redressal register and time-bound action taken on citizen grievance ref: [REF_NO].",
            "Provide certified copies of the tender allocation and expenditure incurred on storm-water drainage cleaning and desilting operations before the monsoon period."
        ]
    },

    "land_revenue_property_records": {
        "domain": "Revenue Department, Land Records, Mutation & Registry",
        "keywords": ["land", "plot", "mutation", "patwari", "tehsildar", "khasra", "khatauni", "registry", "sub registrar", "stamp duty", "bribe", "encroachment", "7/12", "patta", "demarcation"],
        "legal_subject_template": "Request for Certified Order Sheets, Field Demarcation Reports, Patwari Verification Notings, and Registered Conveyance Records in [LOCATION]",
        "legal_issue_statement": "Undue delay in statutory land mutation, refusal of certified land extracts, and revenue administrative default",
        "central_authority": {
            "name": "Department of Land Resources / Ministry of Rural Development",
            "cpio_designation": "Central Public Information Officer & Deputy Secretary, DoLR",
            "faa_designation": "First Appellate Authority & Joint Secretary, DoLR",
            "address_template": "Department of Land Resources, Krishi Bhawan, New Delhi",
            "handles": ["@DoLR_GoI", "@CPGRAMS"]
        },
        "state_authority": {
            "name": "District Revenue Administration / Collectorate / Tehsil Office",
            "cpio_designation": "Public Information Officer & Tehsildar / Sub-Divisional Magistrate (SDM) Revenue",
            "faa_designation": "First Appellate Authority & Additional District Magistrate (ADM) / District Collector",
            "address_template": "Office of the Tehsildar / Sub-Divisional Magistrate, Tehsil [TEHSIL_NAME], District [DISTRICT_NAME], [STATE_NAME]",
            "handles": ["@DoLR_GoI", "@CPGRAMS"]
        },
        "municipal_authority": {
            "name": "City Survey & Land Settlement Office",
            "cpio_designation": "Public Information Officer & City Survey Officer / Town Planning Officer",
            "faa_designation": "First Appellate Authority & District Land Records Officer",
            "address_template": "Land Settlement & Survey Office, [CITY_NAME], [STATE_NAME]",
            "handles": ["@CPGRAMS"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the field demarcation report, panchnama, and digital village survey map concerning Khasra / Khata No: [KHASRA_NO] in Village [VILLAGE_NAME].",
            "Provide certified copies of the complete order sheet, patwari report, and file notings regarding Land Mutation Case No: [MUTATION_NO].",
            "Provide certified copies of the registered Sale Deed / Conveyance Deed along with valuation verification sheets for Property Registration Document No: [REG_NO].",
            "Provide certified details of the statutory time limit fixed under the State Public Services Guarantee Act (RTS) for disposal of land mutation applications and reasons for non-compliance."
        ]
    },

    "ration_pds_food_supplies": {
        "domain": "Food & Public Distribution (PDS), Ration Card & Fair Price Shops",
        "keywords": ["ration", "ration card", "pds", "food", "dealer", "fair price shop", "grain", "wheat", "rice", "bpl", "aay", "quota", "fps", "civil supplies"],
        "legal_subject_template": "Request for Certified Monthly Foodgrain Allocation Registers, ePoS Electronic Logs, and Fair Price Shop Inspection Reports in [LOCATION]",
        "legal_issue_statement": "Foodgrain quota diversion, wrongful ration card withholding, and National Food Security Act violation",
        "central_authority": {
            "name": "Department of Food & Public Distribution / Ministry of Consumer Affairs, Food & Public Distribution",
            "cpio_designation": "Central Public Information Officer & Under Secretary, DoFPD",
            "faa_designation": "First Appellate Authority & Director (PDS), DoFPD",
            "address_template": "Department of Food & Public Distribution, Krishi Bhawan, New Delhi",
            "handles": ["@fooddeptgoi", "@PiyushGoyal"]
        },
        "state_authority": {
            "name": "District Food and Civil Supplies Office (DFSO)",
            "cpio_designation": "Public Information Officer & District Supply Officer (DSO) / Area Rationing Officer (ARO)",
            "faa_designation": "First Appellate Authority & Deputy Commissioner (Food) / District Magistrate",
            "address_template": "Office of the District Supply Officer (DSO), Collectorate Campus, [DISTRICT_NAME], [STATE_NAME]",
            "handles": ["@fooddeptgoi", "@CPGRAMS"]
        },
        "municipal_authority": {
            "name": "Area Civil Supplies Wing",
            "cpio_designation": "Public Information Officer & Supply Inspector (Food)",
            "faa_designation": "First Appellate Authority & Assistant Food Controller",
            "address_template": "Civil Supplies Office, [CITY_NAME], [STATE_NAME]",
            "handles": ["@fooddeptgoi"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the monthly foodgrain allocation and actual lifting register (Form B / Daily Sales Register) for Fair Price Shop (FPS) License No: [FPS_NO].",
            "Provide certified copies of the stock balance sheet, electronic point of sale (ePoS) machine transaction audit logs, and biometric failure exception register for the last 6 months.",
            "Provide certified copies of the inquiry report and inspection remarks recorded by the Supply Inspector during their statutory monthly inspection of the said FPS.",
            "Provide certified reasons recorded in the file for delay/rejection in issuing or updating Ration Card Application Ref: [REF_NO]."
        ]
    },

    "electricity_discom_power": {
        "domain": "Electricity Distribution, Meter Tampering, Power Outages & Billing",
        "keywords": ["electricity", "power", "discom", "meter", "bill", "transformer", "load", "power cut", "fault", "connection", "tariff", "substation"],
        "legal_subject_template": "Request for Certified Meter Calibration Lab Reports, Billing Ledger Breakdown, and Feeder Outage Logbooks in [LOCATION]",
        "legal_issue_statement": "Faulty electricity metering, arbitrary billing calculation, and unnotified power disruption by distribution licensee",
        "central_authority": {
            "name": "Ministry of Power / Central Electricity Regulatory Commission (CERC)",
            "cpio_designation": "Central Public Information Officer & Assistant Secretary, CERC",
            "faa_designation": "First Appellate Authority & Secretary, CERC",
            "address_template": "Chanderlok Building, Janpath, New Delhi",
            "handles": ["@MinOfPower", "@RajKSinghIndia"]
        },
        "state_authority": {
            "name": "State Electricity Distribution Company (DISCOM) / State Power Corporation",
            "cpio_designation": "Public Information Officer & Executive Engineer (Distribution), DISCOM",
            "faa_designation": "First Appellate Authority & Superintending Engineer (SE), Electricity Circle",
            "address_template": "Office of the Executive Engineer (O&M), Electricity Distribution Division, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MinOfPower", "@CPGRAMS"]
        },
        "municipal_authority": {
            "name": "City Power Supply Sub-Division",
            "cpio_designation": "Public Information Officer & Assistant Engineer (AE Power)",
            "faa_designation": "First Appellate Authority & Executive Engineer (Electricity)",
            "address_template": "Power Sub-Station Division, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MinOfPower"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the digital Meter Test Laboratory report and calibration certificates verifying the accuracy of Energy Meter No: [METER_NO].",
            "Provide certified copies of the complete billing ledger, slab calculation break-up, and peak load penalty assessments levied on Consumer Account No: [CONSUMER_NO].",
            "Provide certified copies of the Substation Daily Log Sheet recording the duration and technical causes of all unscheduled power outages/trippings in [FEEDER_NAME] for the last 3 months.",
            "Provide certified copies of the estimate sheet, tender work order, and fund allocation for replacing the damaged distribution transformer located at [LOCATION]."
        ]
    },

    "education_exams_universities": {
        "domain": "Education, Board Exams, Universities, Fee Regulation & RTE",
        "keywords": ["school", "college", "university", "exam", "result", "answer sheet", "cbse", "ugc", "aicte", "neet", "jee", "scholarship", "degree", "marksheet", "rte", "admission"],
        "legal_subject_template": "Request for Certified Evaluated Answer Booklets, Official Answer Keys, and Merit Normalization Records in [LOCATION]",
        "legal_issue_statement": "Withholding of evaluated answer booklets, transparency violation in public examination, and normalization irregularity",
        "central_authority": {
            "name": "Central Board of Secondary Education (CBSE) / National Testing Agency (NTA) / UGC",
            "cpio_designation": "Central Public Information Officer & Assistant Secretary, CBSE / NTA / UGC",
            "faa_designation": "First Appellate Authority & Joint Secretary / Controller of Examinations",
            "address_template": "Regional Office, CBSE / NTA, [CITY_NAME], [STATE_NAME]",
            "handles": ["@EduMinOfIndia", "@cbseindia29", "@ugc_india", "@dpradhanbjp"]
        },
        "state_authority": {
            "name": "State Education Board / Directorate of Higher Education / State University",
            "cpio_designation": "Public Information Officer & Assistant Registrar / Controller of Examinations",
            "faa_designation": "First Appellate Authority & Registrar, University / Board",
            "address_template": "Administrative Block, [UNIVERSITY_OR_BOARD_NAME], [CITY_NAME], [STATE_NAME]",
            "handles": ["@EduMinOfIndia", "@CPGRAMS"]
        },
        "municipal_authority": {
            "name": "District Basic Education Officer (BSA) / Municipal Education Officer",
            "cpio_designation": "Public Information Officer & District Education Officer (DEO / BSA)",
            "faa_designation": "First Appellate Authority & Deputy Director of Education",
            "address_template": "District Education Office, [CITY_NAME], [STATE_NAME]",
            "handles": ["@EduMinOfIndia"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the evaluated answer booklet of the applicant for Roll No: [ROLL_NO], Subject: [SUBJECT], Exam: [EXAM_NAME] as per the Supreme Court landmark ruling in CBSE v. Aditya Bandopadhyay (2011).",
            "Provide certified copies of the master question paper along with the official expert answer key and moderation/normalization committee minutes.",
            "Provide certified details of the category-wise cutoff marks and merit rank list of all selected candidates in the recruitment/admission process ref: [REF_NO].",
            "Provide certified copies of the school inspection and Fee Regulatory Committee audit reports regarding fee collection compliance under state private school regulations."
        ]
    },

    "banking_financial_frauds": {
        "domain": "Public Sector Banks, RBI Ombudsman & Financial Services",
        "keywords": ["bank", "sbi", "pnb", "loan", "fraud", "rbi", "ombudsman", "atm", "unauthorized", "transaction", "emi", "cibil", "cheque", "subsidy"],
        "legal_subject_template": "Request for Certified Internal Audit Reports, CCTV Access Logs, and Switch Transaction Reversal Sheets in [LOCATION]",
        "legal_issue_statement": "Unauthorized digital bank debit, failure in statutory ombudsman redressal, and regulatory deficiency",
        "central_authority": {
            "name": "Reserve Bank of India (RBI) / Specific Public Sector Bank (e.g. State Bank of India, PNB)",
            "cpio_designation": "Central Public Information Officer & Chief Manager / Assistant General Manager (AGM), CPIO Cell, [BANK_NAME]",
            "faa_designation": "First Appellate Authority & General Manager / Chief General Manager, [BANK_NAME]",
            "address_template": "Zonal / Regional Office, CPIO Cell, [BANK_NAME], [CITY_NAME], [STATE_NAME]",
            "handles": ["@RBI", "@FinMinIndia", "@TheOfficialSBI", "@nsitharaman"]
        },
        "state_authority": {
            "name": "State Financial Corporation / Regional Rural Bank (RRB)",
            "cpio_designation": "Public Information Officer & General Manager, Regional Rural Bank",
            "faa_designation": "First Appellate Authority & Chairman / Managing Director",
            "address_template": "Head Office, Regional Rural Bank, [CITY_NAME], [STATE_NAME]",
            "handles": ["@FinMinIndia", "@RBI"]
        },
        "municipal_authority": {
            "name": "Lead District Bank Manager (LDM) Office",
            "cpio_designation": "Public Information Officer & Lead District Manager",
            "faa_designation": "First Appellate Authority & Regional Manager, Lead Bank",
            "address_template": "Lead District Bank Office, Collectorate Complex, [DISTRICT_NAME], [STATE_NAME]",
            "handles": ["@FinMinIndia"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the internal audit report, CCTV log verification, and switch transaction log report concerning the unauthorized debit on Account No: [ACCOUNT_NO] on Date: [DATE].",
            "Provide certified copies of the complete loan sanction terms, processing file notings, and reason for delay in releasing government interest subsidy for Loan Account No: [LOAN_NO].",
            "Provide certified particulars of the Circular / Master Directions issued by RBI based on which penalty charges were deducted on the applicant's savings bank account.",
            "Provide certified copies of the action taken report and disposal file notings on Banking Ombudsman Complaint Ref No: [REF_NO]."
        ]
    },

    "railways_irctc_transport": {
        "domain": "Indian Railways, IRCTC, Train Services & Safety",
        "keywords": ["railway", "train", "irctc", "ticket", "pnr", "refund", "station", "railways", "tatkal", "cancellation", "coach", "cleanliness"],
        "legal_subject_template": "Request for Certified TDR Refund Processing Sheets, Catering Hygiene Audit Reports, and Coach Composition Logs in [LOCATION]",
        "legal_issue_statement": "Uncredited railway ticket refund, deficiency in passenger amenities, and catering quality non-compliance",
        "central_authority": {
            "name": "Ministry of Railways / Railway Board / Zonal Railway Administration",
            "cpio_designation": "Central Public Information Officer & Senior Divisional Commercial Manager (Sr. DCM), [RAILWAY_ZONE]",
            "faa_designation": "First Appellate Authority & Additional Divisional Railway Manager (ADRM), [RAILWAY_ZONE]",
            "address_template": "Divisional Railway Manager (DRM) Office, [ZONE/DIVISION], [CITY_NAME], [STATE_NAME]",
            "handles": ["@RailMinIndia", "@AshwiniVaishnaw", "@IRCTCofficial", "@RailwaySeva"]
        },
        "state_authority": {
            "name": "State Railway Police (SRP) / Rail Infrastructure Development Authority",
            "cpio_designation": "Public Information Officer & Superintendent of Police (Railways)",
            "faa_designation": "First Appellate Authority & Deputy Inspector General (Railways)",
            "address_template": "Railway Police Headquarters, [CITY_NAME], [STATE_NAME]",
            "handles": ["@RailMinIndia", "@RailwaySeva"]
        },
        "municipal_authority": {
            "name": "City Railway Station Management",
            "cpio_designation": "Public Information Officer & Station Director",
            "faa_designation": "First Appellate Authority & Senior Divisional Operations Manager",
            "address_template": "Office of the Station Director, Railway Station, [CITY_NAME]",
            "handles": ["@RailwaySeva"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the TDR (Ticket Deposit Receipt) processing sheet, verification report, and refund calculation for PNR No: [PNR_NO].",
            "Provide certified copies of the pantry car hygiene inspection reports, catering sample test certificates, and penalty ledger for Train No: [TRAIN_NO] for the period [TIME_PERIOD].",
            "Provide certified copies of the CCTV footage review log, security register, and FIR registration follow-up regarding the incident reported on Date: [DATE] at Station [STATION_NAME].",
            "Provide certified particulars of the sanctioned coach composition vs. actual coaches attached to Train No: [TRAIN_NO] on Date: [DATE]."
        ]
    },

    "passport_immigration_consular": {
        "domain": "Passports, Visas, Emigration & Consular Services",
        "keywords": ["passport", "rpo", "psk", "visa", "mea", "police verification", "emigration", "consular", "embassy"],
        "legal_subject_template": "Request for Certified Police Verification Reports (PVR), Adverse Ground File Notings, and Speed Post Dispatch Logs in [LOCATION]",
        "legal_issue_statement": "Arbitrary passport issuance delay, adverse verification remark non-disclosure, and postal delivery failure",
        "central_authority": {
            "name": "Ministry of External Affairs (MEA) / Central Passport Organization (CPO)",
            "cpio_designation": "Central Public Information Officer & Regional Passport Officer (RPO), Passport Office",
            "faa_designation": "First Appellate Authority & Joint Secretary (CPV) / Chief Passport Officer, MEA",
            "address_template": "Regional Passport Office (RPO), [CITY_NAME], [STATE_NAME]",
            "handles": ["@MEAIndia", "@passportsevamea", "@DrSJaishankar"]
        },
        "state_authority": {
            "name": "Special Branch (CID) / District Police Verification Cell",
            "cpio_designation": "Public Information Officer & DySP (Special Branch / Passport Verification)",
            "faa_designation": "First Appellate Authority & Superintendent of Police (Special Branch)",
            "address_template": "Police Verification Branch, District Police Office, [CITY_NAME], [STATE_NAME]",
            "handles": ["@MEAIndia", "@CPGRAMS"]
        },
        "municipal_authority": {
            "name": "Passport Seva Kendra (PSK) Operations",
            "cpio_designation": "Public Information Officer & Assistant Passport Officer, PSK",
            "faa_designation": "First Appellate Authority & Regional Passport Officer",
            "address_template": "Passport Seva Kendra, [CITY_NAME], [STATE_NAME]",
            "handles": ["@passportsevamea"]
        },
        "statutory_legal_queries": [
            "Provide certified copies of the Police Verification Report (PVR) and internal processing sheet concerning Passport Application File No: [FILE_NO].",
            "Provide certified particulars of the exact adverse remark or statutory ground recorded in the system for impounding or delaying Passport File No: [FILE_NO].",
            "Provide certified copies of the dispatch log, speed post consignment tracking number, and physical postal delivery receipt of the passport document."
        ]
    }
}

def resolve_knowledge_graph_node(problem_text: str, location: str = "") -> Dict[str, Any]:
    """
    GraphRAG entity matcher: matches unstructured citizen problem text against the
    multi-tier authority knowledge graph to return optimal statutory entities.
    """
    lower = (problem_text or "").lower()
    best_match_key = "roads_highways_infrastructure" # default
    highest_score = 0

    for key, data in AUTHORITY_KNOWLEDGE_GRAPH.items():
        score = 0
        for kw in data["keywords"]:
            if kw in lower:
                score += 1
        if score > highest_score:
            highest_score = score
            best_match_key = key

    matched_data = AUTHORITY_KNOWLEDGE_GRAPH[best_match_key]
    
    # Determine Tier (Central / State / Municipal)
    city_name = location.strip() if location else "[CITY_NAME]"
    state_name = "[STATE_NAME]"

    # Heuristic for tier selection
    if any(term in lower for term in ["nhai", "national highway", "central", "aiims", "epfo", "pf", "cbse", "rbi", "irctc", "railway", "passport"]):
        chosen_tier = matched_data["central_authority"]
        tier_level = "Central"
    elif any(term in lower for term in ["municipal", "colony", "ward", "gutter", "drain", "garbage", "street light", "local"]):
        chosen_tier = matched_data["municipal_authority"]
        tier_level = "Municipal/Local"
    else:
        chosen_tier = matched_data["state_authority"]
        tier_level = "State"

    # Inject location safely
    formatted_address = chosen_tier["address_template"].replace("[CITY_NAME]", city_name).replace("[STATE_NAME]", state_name).replace("[DISTRICT_NAME]", city_name).replace("[TEHSIL_NAME]", city_name)
    loc_display = city_name if city_name != "[CITY_NAME]" else "the designated jurisdiction"

    legal_subj = matched_data.get("legal_subject_template", "Request for Certified Records under Section 6(1) of RTI Act, 2005").replace("[LOCATION]", loc_display)
    legal_issue = matched_data.get("legal_issue_statement", "Public service deficiency and statutory non-compliance")

    return {
        "domain": matched_data["domain"],
        "jurisdiction_level": tier_level,
        "public_authority_name": chosen_tier["name"],
        "pio_designation": chosen_tier["cpio_designation"],
        "faa_designation": chosen_tier["faa_designation"],
        "suggested_address_template": formatted_address,
        "social_handles": chosen_tier.get("handles", ["@CPGRAMS", "@CIC_India"]),
        "statutory_legal_queries": matched_data["statutory_legal_queries"],
        "legal_subject_title": legal_subj,
        "legal_issue_statement": legal_issue,
        "reasoning": f"Identified {matched_data['domain']} under {tier_level} public jurisdiction as the primary custodian of requested records."
    }

def synthesize_legal_subject(problem_text: str, location: str = "") -> str:
    """Remolds colloquial citizen problem text into an authoritative statutory RTI subject."""
    node = resolve_knowledge_graph_node(problem_text, location)
    return node.get("legal_subject_title", "Request for Certified Records under Section 6(1) of RTI Act, 2005")

def synthesize_legal_issue_statement(problem_text: str, location: str = "") -> str:
    """Remolds colloquial citizen text into a formal legal grievance / accountability statement."""
    node = resolve_knowledge_graph_node(problem_text, location)
    return node.get("legal_issue_statement", "Deficiency in public service delivery and statutory non-compliance")
