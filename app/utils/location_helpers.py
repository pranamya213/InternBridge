import re

KARNATAKA_CITIES = [
    'bengaluru', 'bangalore', 'mysuru', 'mysore', 'mangaluru', 'mangalore',
    'hubballi', 'hubli', 'belagavi', 'belgaum', 'kalaburagi', 'gulbarga',
    'dharwad', 'vijayapura', 'bijapur', 'hosapete', 'hospet', 'shivamogga',
    'shimoga', 'tumakuru', 'tumkur', 'udupi', 'hassan', 'ballari', 'bellary',
    'davanagere'
]

INDIAN_STATES = {
    'karnataka': 'Karnataka',
    'andhra pradesh': 'Andhra Pradesh',
    'telangana': 'Telangana',
    'tamil nadu': 'Tamil Nadu',
    'kerala': 'Kerala',
    'maharashtra': 'Maharashtra',
    'delhi': 'Delhi',
    'uttar pradesh': 'Uttar Pradesh',
    'west bengal': 'West Bengal',
    'gujarat': 'Gujarat',
    'rajasthan': 'Rajasthan',
    'punjab': 'Punjab',
    'haryana': 'Haryana',
    'madhya pradesh': 'Madhya Pradesh',
    'bihar': 'Bihar',
    'odisha': 'Odisha',
    'assam': 'Assam',
    'jharkhand': 'Jharkhand',
    'chhattisgarh': 'Chhattisgarh',
    'uttarakhand': 'Uttarakhand',
    'himachal pradesh': 'Himachal Pradesh',
    'goa': 'Goa',
    'tripura': 'Tripura',
    'meghalaya': 'Meghalaya',
    'manipur': 'Manipur',
    'nagaland': 'Nagaland',
    'arunachal pradesh': 'Arunachal Pradesh',
    'mizoram': 'Mizoram',
    'sikkim': 'Sikkim'
}

def normalize_location(raw_location):
    """
    Takes a raw location string and attempts to identify if it's in India/Karnataka.
    Returns a dict with 'country', 'state', 'city'.
    Uses 'Unknown' if unrecognized, and 'International' if known to be outside India.
    """
    if not raw_location or raw_location.strip() == '':
        return {'country': 'Unknown', 'state': None, 'city': None}
        
    loc_lower = raw_location.lower()
    
    # Check for Karnataka cities
    for city in KARNATAKA_CITIES:
        if re.search(r'\b' + city + r'\b', loc_lower):
            # Special case for Bangalore vs Bengaluru
            display_city = 'Bengaluru' if city in ['bangalore', 'bengaluru'] else city.title()
            return {'country': 'India', 'state': 'Karnataka', 'city': display_city}
            
    # Check for Indian states
    for state_key, state_name in INDIAN_STATES.items():
        if state_key in loc_lower:
            # We found the state, but city is unknown
            return {'country': 'India', 'state': state_name, 'city': None}
            
    # Check if 'india' is simply mentioned
    if 'india' in loc_lower:
        return {'country': 'India', 'state': None, 'city': None}
        
    # Check some common international keywords
    international_keywords = [
        'usa', 'united states', 'uk', 'united kingdom', 'germany', 'france',
        'canada', 'australia', 'singapore', 'remote - us', 'remote - europe',
        'berlin', 'london', 'new york', 'san francisco', 'tokyo', 'dubai'
    ]
    
    for kw in international_keywords:
        if kw in loc_lower:
            return {'country': 'International', 'state': None, 'city': None}
            
    # If we really can't tell, keep it Unknown
    return {'country': 'Unknown', 'state': None, 'city': None}
