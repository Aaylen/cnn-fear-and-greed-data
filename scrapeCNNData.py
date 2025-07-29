import requests

def fetch_fear_greed_data():
    """Fetch fear and greed index data"""
    url = "https://www.finhacker.cz/wp-content/custom-api/fear-greed-data.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://www.finhacker.cz/fear-and-greed-index-historical-data-and-chart/",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json().get("agg", [])
        return data
    except Exception as e:
        print(f"Error fetching fear/greed data: {e}")
        return None