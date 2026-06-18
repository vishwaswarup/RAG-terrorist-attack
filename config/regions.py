"""
Regional Geographic Knowledge
=============================

A configuration-driven layer for geographic data.
Allows the extraction pipeline to disambiguate and validate locations
based on strategic areas of interest.
"""

# ---------------------------------------------------------------------------
# South Asia & Strategic Neighborhood
# ---------------------------------------------------------------------------

SOUTH_ASIA_COUNTRIES = [
    "India",
    "Pakistan",
    "China",
    "Bangladesh",
    "Sri Lanka",
    "Nepal",
    "Bhutan",
    "Myanmar",
    "Afghanistan",
    "Maldives"
]

# Mapping of major strategic cities/capitals to their respective countries.
# This enables the system to infer the country even if only the city is mentioned.
COUNTRY_TO_CITIES = {
    "India": [
        "New Delhi", "Delhi", "Mumbai", "Kolkata", "Chennai",
        "Bengaluru", "Hyderabad", "Pune", "Srinagar", "Jammu",
        "Pulwama", "Pathankot", "Uri", "Amritsar", "Chandigarh",
        "Lucknow", "Patna", "Guwahati", "Imphal",
        # Jammu & Kashmir expanded
        "Anantnag", "Baramulla", "Kupwara", "Handwara", "Sopore",
        "Shopian", "Kulgam", "Bandipora", "Ganderbal", "Budgam",
        "Rajouri", "Poonch", "Kishtwar", "Nagrota", "Kathua",
        "Udhampur", "Reasi", "Doda", "Lethpora", "Awantipora",
        # Punjab expanded
        "Jalandhar", "Ludhiana", "Gurdaspur", "Dinanagar",
        "Bathinda", "Patiala", "Mohali", "Firozpur", "Faridkot",
        # Bihar
        "Bodh Gaya", "Gaya", "Muzaffarpur", "Bhagalpur",
        # Northeast
        "Kohima", "Dimapur", "Aizawl", "Shillong", "Agartala", "Itanagar",
        # Others
        "Jaipur", "Ahmedabad", "Bhopal", "Indore", "Nagpur",
        "Varanasi", "Agra", "Kanpur", "Coimbatore",
    ],
    "Pakistan": [
        "Islamabad", "Rawalpindi", "Karachi", "Lahore", "Peshawar",
        "Quetta", "Multan", "Faisalabad", "Gujranwala", "Sialkot",
        "Abbottabad", "Muzaffarabad", "Mirpur",
        # FATA / KP expanded
        "Waziristan", "Swat", "Bannu", "Kohat", "Dera Ismail Khan",
        "Mardan", "Charsadda", "Nowshera", "Hangu", "Parachinar",
        # Balochistan expanded
        "Turbat", "Gwadar", "Khuzdar", "Chaman", "Mastung",
        "Hub", "Naseerabad", "Jaffarabad",
        # Sindh expanded
        "Hyderabad", "Sukkur", "Larkana", "Nawabshah", "Sehwan",
        # Punjab expanded
        "Sargodha", "Jhang", "Bahawalpur", "Rahim Yar Khan",
        # Wagah border area
        "Wagah",
    ],
    "China": [
        "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu",
        "Wuhan", "Lhasa", "Urumqi", "Kashgar", "Hotan"
    ],
    "Bangladesh": [
        "Dhaka", "Chittagong", "Khulna", "Sylhet", "Rajshahi",
        "Cox's Bazar", "Rangpur", "Comilla", "Gazipur", "Narayanganj",
    ],
    "Sri Lanka": [
        "Colombo", "Sri Jayawardenepura Kotte", "Kandy", "Galle",
        "Jaffna", "Trincomalee", "Batticaloa", "Negombo",
        "Matara", "Anuradhapura", "Polonnaruwa", "Kurunegala",
        "Hambantota", "Kilinochchi", "Mullaitivu", "Mannar",
    ],
    "Nepal": [
        "Kathmandu", "Pokhara", "Lalitpur", "Biratnagar", "Bharatpur"
    ],
    "Bhutan": [
        "Thimphu", "Phuntsholing", "Paro", "Punakha"
    ],
    "Myanmar": [
        "Naypyidaw", "Yangon", "Mandalay", "Bago", "Sittwe",
        "Myitkyina"
    ],
    "Afghanistan": [
        "Kabul", "Kandahar", "Herat", "Mazar-i-Sharif", "Jalalabad",
        "Kunduz", "Ghazni",
        # Expanded
        "Lashkar Gah", "Tarin Kowt", "Gardez", "Khost",
        "Farah", "Pul-e-Khumri", "Mehtarlam", "Charikar",
        "Taloqan", "Faizabad", "Zaranj", "Sheberghan",
    ],
    "Maldives": [
        "Male", "Addu City", "Fuvahmulah"
    ]
}

# ---------------------------------------------------------------------------
# City → State / Province mapping
# ---------------------------------------------------------------------------
# Maps key cities to their state/province for state extraction.
CITY_TO_STATE = {
    # India — Jammu & Kashmir
    "srinagar": "Jammu and Kashmir",
    "pulwama": "Jammu and Kashmir",
    "anantnag": "Jammu and Kashmir",
    "baramulla": "Jammu and Kashmir",
    "kupwara": "Jammu and Kashmir",
    "handwara": "Jammu and Kashmir",
    "sopore": "Jammu and Kashmir",
    "shopian": "Jammu and Kashmir",
    "kulgam": "Jammu and Kashmir",
    "bandipora": "Jammu and Kashmir",
    "ganderbal": "Jammu and Kashmir",
    "budgam": "Jammu and Kashmir",
    "rajouri": "Jammu and Kashmir",
    "poonch": "Jammu and Kashmir",
    "kishtwar": "Jammu and Kashmir",
    "nagrota": "Jammu and Kashmir",
    "kathua": "Jammu and Kashmir",
    "udhampur": "Jammu and Kashmir",
    "reasi": "Jammu and Kashmir",
    "doda": "Jammu and Kashmir",
    "lethpora": "Jammu and Kashmir",
    "awantipora": "Jammu and Kashmir",
    "uri": "Jammu and Kashmir",
    "jammu": "Jammu and Kashmir",
    # India — Punjab
    "amritsar": "Punjab",
    "chandigarh": "Punjab",
    "pathankot": "Punjab",
    "jalandhar": "Punjab",
    "ludhiana": "Punjab",
    "gurdaspur": "Punjab",
    "dinanagar": "Punjab",
    "bathinda": "Punjab",
    "patiala": "Punjab",
    "mohali": "Punjab",
    "firozpur": "Punjab",
    "faridkot": "Punjab",
    # India — Maharashtra
    "mumbai": "Maharashtra",
    "pune": "Maharashtra",
    "nagpur": "Maharashtra",
    # India — Bihar
    "patna": "Bihar",
    "bodh gaya": "Bihar",
    "gaya": "Bihar",
    "muzaffarpur": "Bihar",
    # India — Delhi
    "new delhi": "Delhi",
    "delhi": "Delhi",
    # India — Others
    "kolkata": "West Bengal",
    "chennai": "Tamil Nadu",
    "bengaluru": "Karnataka",
    "hyderabad": "Telangana",
    "lucknow": "Uttar Pradesh",
    "varanasi": "Uttar Pradesh",
    "agra": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh",
    "jaipur": "Rajasthan",
    "ahmedabad": "Gujarat",
    "bhopal": "Madhya Pradesh",
    "indore": "Madhya Pradesh",
    "guwahati": "Assam",
    "imphal": "Manipur",
    "kohima": "Nagaland",
    "coimbatore": "Tamil Nadu",
    # Pakistan — provinces
    "islamabad": "Islamabad Capital Territory",
    "rawalpindi": "Punjab",
    "lahore": "Punjab",
    "karachi": "Sindh",
    "peshawar": "Khyber Pakhtunkhwa",
    "quetta": "Balochistan",
    "abbottabad": "Khyber Pakhtunkhwa",
    "swat": "Khyber Pakhtunkhwa",
    "waziristan": "Khyber Pakhtunkhwa",
    "bannu": "Khyber Pakhtunkhwa",
    "turbat": "Balochistan",
    "gwadar": "Balochistan",
    "wagah": "Punjab",
    # Afghanistan — provinces
    "kabul": "Kabul",
    "kandahar": "Kandahar",
    "herat": "Herat",
    "mazar-i-sharif": "Balkh",
    "jalalabad": "Nangarhar",
    "kunduz": "Kunduz",
    "ghazni": "Ghazni",
    "lashkar gah": "Helmand",
    "khost": "Khost",
    "gardez": "Paktia",
    "farah": "Farah",
    "taloqan": "Takhar",
    "faizabad": "Badakhshan",
    "sheberghan": "Jowzjan",
    "charikar": "Parwan",
    # Bangladesh — divisions
    "dhaka": "Dhaka",
    "chittagong": "Chittagong",
    "sylhet": "Sylhet",
    # Sri Lanka — no sub-national state in scope
    "colombo": "",
    "negombo": "",
    "batticaloa": "",
    "jaffna": "",
    "trincomalee": "",
    "kandy": "",
    "galle": "",
}
# ---------------------------------------------------------------------------
# Global Configuration
# ---------------------------------------------------------------------------

# Currently active regions for the location extractor
ACTIVE_COUNTRIES = set(SOUTH_ASIA_COUNTRIES)

# Flatten the mapping for fast O(1) city-to-country lookups
# Normalise to lowercase for case-insensitive matching
CITY_TO_COUNTRY_MAP = {}
for country, cities in COUNTRY_TO_CITIES.items():
    for city in cities:
        CITY_TO_COUNTRY_MAP[city.lower()] = country

COUNTRY_SET_LOWER = {c.lower() for c in ACTIVE_COUNTRIES}
