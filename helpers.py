CITIES_CODE = {
        "Delhi": "DEL",
        "Mumbai": "BOM",
        "New Delhi": "DEL",
        "Bangalore": "BLR",
        "Goa": "GOI",
        "Chennai": "MAA",
        "Kolkata": "CCU",
        "Hyderabad": "HYD",
        "Pune": "PNQ",
        "Ahmedabad": "AMD",
        "Cochin": "COK",
        "Jaipur": "JAI",
    }


def get_city_code(city):
    return CITIES_CODE.get(city, '')

