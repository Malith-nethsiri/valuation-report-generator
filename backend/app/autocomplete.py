"""
Autocomplete data constants for Sri Lankan professional valuers
Based on research of Institute of Valuers of Sri Lanka (IVSL) and banking industry
"""

# Honorifics
HONORIFICS = [
    "Mr.",
    "Ms.",
    "Mrs.",
    "Dr.",
    "Prof.",
    "Rev.",
    "Hon."
]

# IVSL Membership Levels
MEMBERSHIP_LEVELS = [
    "Student Member",
    "Associate Member",
    "Professional Associate Member",
    "Fellow Member",
    "Technical Member",
    "Graduate Member",
    "Corporate Member"
]

# Academic Qualifications (Common in Sri Lanka)
ACADEMIC_QUALIFICATIONS = [
    "B.Sc. Estate Management and Valuation",
    "B.Sc. Estate Management and Valuation (Honours)",
    "B.Sc. Est. Mgt and Val (Special)",
    "B.Sc. Quantity Surveying",
    "B.Sc. Quantity Surveying (Honours)",
    "M.Sc. Real Estate Management and Valuation",
    "PG Diploma Real Estate Management and Valuation",
    "B.Sc. Building Economics",
    "B.Sc. Surveying",
    "B.Com. (Real Estate)",
    "Bachelor of Laws (LLB)",
    "Master of Laws (LLM)",
    "MBA (Real Estate)",
    "Diploma in Valuation"
]

# Professional Designations
PROFESSIONAL_DESIGNATIONS = [
    "Chartered Valuer",
    "Chartered Valuation Surveyor",
    "Chartered Quantity Surveyor",
    "Incorporated Valuer",
    "Government Valuer",
    "Registered Valuer",
    "Panel Valuer",
    "Chief Valuer",
    "Deputy Chief Valuer",
    "Assistant Valuer",
    "Senior Valuer",
    "Property Valuer"
]

# Post-Nominal Letters (Professional Certifications)
POST_NOMINAL_LETTERS = [
    "FRICS",  # Fellow, Royal Institution of Chartered Surveyors
    "MRICS",  # Member, Royal Institution of Chartered Surveyors
    "FIV",    # Fellow, Institute of Valuers
    "AIV",    # Associate, Institute of Valuers
    "FIVSL",  # Fellow, Institute of Valuers Sri Lanka
    "MIVSL",  # Member, Institute of Valuers Sri Lanka
    "FIQSSL", # Fellow, Institute of Quantity Surveyors Sri Lanka
    "AIQSSL", # Associate, Institute of Quantity Surveyors Sri Lanka
    "FITP",   # Fellow, Institute of Town Planners Sri Lanka
    "MAIQS",  # Member, Australian Institute of Quantity Surveyors
    "FCIOB",  # Fellow, Chartered Institute of Building
    "MCIOB"   # Member, Chartered Institute of Building
]

# Sri Lankan Banks (Licensed Commercial Banks + Specialized Banks)
SRI_LANKAN_BANKS = [
    # State-Owned Banks
    "Bank of Ceylon",
    "People's Bank",

    # Major Private Commercial Banks
    "Commercial Bank of Ceylon PLC",
    "Hatton National Bank PLC",
    "Sampath Bank PLC",
    "Seylan Bank PLC",
    "DFCC Bank PLC",
    "National Development Bank PLC",
    "Nations Trust Bank PLC",
    "Pan Asia Banking Corporation PLC",
    "Union Bank of Colombo PLC",

    # Other Licensed Commercial Banks
    "Amana Bank PLC",
    "Cargills Bank PLC",
    "Bank of China Ltd",
    "Citibank, N.A.",
    "Deutsche Bank AG, Colombo Branch",
    "Habib Bank Ltd",
    "Indian Bank",
    "Indian Overseas Bank",
    "MCB Bank Ltd",
    "Public Bank Berhad",
    "Standard Chartered Bank",
    "State Bank of India",
    "The Hongkong & Shanghai Banking Corporation Ltd (HSBC)",

    # Licensed Specialized Banks
    "Housing Development Finance Corporation Bank of Sri Lanka (HDFC)",
    "National Savings Bank",
    "Pradeshiya Sanwardhana Bank",
    "Sanasa Development Bank PLC",
    "Sri Lanka Savings Bank Ltd",
    "State Mortgage & Investment Bank",

    # Regional Development Bank
    "Regional Development Bank"
]

# Professional Institutes in Sri Lanka
PROFESSIONAL_INSTITUTES = [
    "Institute of Valuers of Sri Lanka (IVSL)",
    "Royal Institution of Chartered Surveyors (RICS)",
    "Institute of Quantity Surveyors Sri Lanka (IQSSL)",
    "Ceylon Institute of Builders (CIOB)",
    "Institute of Town Planners Sri Lanka (ITPSL)",
    "Institute of Automotive & Machinery Valuers Sri Lanka (IAMV)",
    "Sri Lanka Institute of Architects (SLIA)"
]

# Common Office Departments for Valuers
OFFICE_DEPARTMENTS = [
    "Valuation Department",
    "Property Valuation Division",
    "Real Estate Department",
    "Technical Department",
    "Surveying Department",
    "Regional Office",
    "Head Office",
    "Branch Office"
]

# Sri Lankan Provinces/Regions
SRI_LANKAN_PROVINCES = [
    "Western Province",
    "Central Province",
    "Southern Province",
    "Northern Province",
    "Eastern Province",
    "North Western Province",
    "Northwestern Province",
    "North Central Province",
    "Uva Province",
    "Sabaragamuwa Province"
]

# Major Cities/Towns in Sri Lanka
SRI_LANKAN_CITIES = [
    # Western Province
    "Colombo", "Gampaha", "Kalutara", "Dehiwala-Mount Lavinia", "Moratuwa",
    "Kesbewa", "Maharagama", "Kotte", "Nugegoda", "Homagama", "Panadura",
    "Beruwala", "Negombo", "Katunayake", "Ja-Ela", "Wattala", "Kelaniya",

    # Central Province
    "Kandy", "Matale", "Nuwara Eliya", "Hatton", "Gampola", "Nawalapitiya",
    "Dambulla", "Sigiriya", "Peradeniya", "Kadugannawa",

    # Southern Province
    "Galle", "Matara", "Hambantota", "Akuressa", "Tangalle", "Unawatuna",
    "Hikkaduwa", "Bentota", "Ambalangoda", "Weligama",

    # Northern Province
    "Jaffna", "Kilinochchi", "Mannar", "Mullaitivu", "Vavuniya", "Point Pedro",

    # Eastern Province
    "Trincomalee", "Batticaloa", "Ampara", "Kalmunai", "Akkaraipattu",

    # North Western Province
    "Kurunegala", "Puttalam", "Chilaw", "Wariyapola", "Kuliyapitiya",

    # North Central Province
    "Anuradhapura", "Polonnaruwa", "Mihintale", "Habarana",

    # Uva Province
    "Badulla", "Bandarawela", "Ella", "Monaragala", "Wellawaya",

    # Sabaragamuwa Province
    "Ratnapura", "Kegalle", "Balangoda", "Embilipitiya", "Pelmadulla"
]

# Major Universities and Educational Institutions
SRI_LANKAN_UNIVERSITIES = [
    # State Universities
    "University of Colombo",
    "University of Peradeniya",
    "University of Sri Jayewardenepura",
    "University of Kelaniya",
    "University of Moratuwa",
    "University of Ruhuna (Matara)",
    "Eastern University, Sri Lanka",
    "South Eastern University of Sri Lanka",
    "Rajarata University of Sri Lanka",
    "Sabaragamuwa University of Sri Lanka",
    "Wayamba University of Sri Lanka",
    "Uva Wellassa University",
    "University of the Visual & Performing Arts",
    "University of Jaffna",
    "Open University of Sri Lanka",

    # Campus/Institute Level
    "Institute for Agri-Technology (IAT)",
    "Ceylon Institute of Technology",
    "National Institute of Business Management (NIBM)",
    "Sri Lanka Institute of Information Technology (SLIIT)",
    "University of Vocational Technology",

    # International Collaborations
    "Curtin University Singapore Campus",
    "Cardiff Metropolitan University",
    "Northumbria University"
]

# Common Areas/Developments (for residential addresses)
RESIDENTIAL_AREAS = [
    # Colombo Areas
    "Colombo 1 - Fort", "Colombo 2 - Slave Island", "Colombo 3 - Kollupitiya",
    "Colombo 4 - Bambalapitiya", "Colombo 5 - Narahenpita", "Colombo 6 - Wellawatta",
    "Colombo 7 - Cinnamon Gardens", "Colombo 8 - Borella", "Colombo 9 - Dematagoda",
    "Colombo 10 - Maradana", "Colombo 11 - Pettah", "Colombo 12 - Hulftsdorp",
    "Colombo 13 - Kotahena", "Colombo 14 - Grandpass", "Colombo 15 - Mutwal",

    # Popular Residential Areas
    "Nugegoda", "Maharagama", "Kotte", "Rajagiriya", "Battaramulla",
    "Malabe", "Thalawathugoda", "Athurugiriya", "Hokandara", "Kaduwela",
    "Mount Lavinia", "Dehiwala", "Wellawatta", "Bambalapitiya", "Kirillapone",
    "Narahenpita", "Rajagiriya", "Mirihana", "Nugegoda", "Delkanda",

    # Gampaha District
    "Negombo", "Ja-Ela", "Katunayake", "Wattala", "Kelaniya", "Kiribathgoda",
    "Kadawatha", "Ragama", "Gampaha", "Minuwangoda", "Divulapitiya",

    # Kandy Areas
    "Kandy City", "Peradeniya", "Katugastota", "Gampola", "Kadugannawa",
    "Pilimatalawa", "Digana", "Pallekele", "Gelioya", "Akurana"
]

def get_all_autocomplete_data():
    """
    Return all autocomplete data as a dictionary for API response
    """
    return {
        "honorifics": HONORIFICS,
        "membership_levels": MEMBERSHIP_LEVELS,
        "academic_qualifications": ACADEMIC_QUALIFICATIONS,
        "professional_designations": PROFESSIONAL_DESIGNATIONS,
        "post_nominal_letters": POST_NOMINAL_LETTERS,
        "sri_lankan_banks": SRI_LANKAN_BANKS,
        "professional_institutes": PROFESSIONAL_INSTITUTES,
        "office_departments": OFFICE_DEPARTMENTS,
        "provinces": SRI_LANKAN_PROVINCES,
        "cities": SRI_LANKAN_CITIES,
        "universities": SRI_LANKAN_UNIVERSITIES,
        "residential_areas": RESIDENTIAL_AREAS
    }

def search_autocomplete(category: str, query: str, limit: int = 10):
    """
    Search within a specific autocomplete category
    """
    data_map = {
        "membership_levels": MEMBERSHIP_LEVELS,
        "academic_qualifications": ACADEMIC_QUALIFICATIONS,
        "professional_designations": PROFESSIONAL_DESIGNATIONS,
        "post_nominal_letters": POST_NOMINAL_LETTERS,
        "sri_lankan_banks": SRI_LANKAN_BANKS,
        "professional_institutes": PROFESSIONAL_INSTITUTES,
        "office_departments": OFFICE_DEPARTMENTS,
        "provinces": SRI_LANKAN_PROVINCES,
        "cities": SRI_LANKAN_CITIES,
        "universities": SRI_LANKAN_UNIVERSITIES,
        "residential_areas": RESIDENTIAL_AREAS
    }

    if category not in data_map:
        return []

    items = data_map[category]
    query_lower = query.lower()

    # Filter items that contain the query (case insensitive)
    filtered_items = [item for item in items if query_lower in item.lower()]

    return filtered_items[:limit]