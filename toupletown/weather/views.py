import os
import requests
from django.shortcuts import render
from dotenv import load_dotenv

load_dotenv()
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
TOKEN = os.getenv("TOKEN")


def get_weather(url):
    response = requests.get(url)
    print(f'Request URL: {url}')
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Ошибка: {response.status_code}')
    return None

def main_page(request):
    r = requests.get(f"https://api.2ip.io/?token={TOKEN}")
    if r.status_code != 200:
        return render(request, "weather/main.html")
    datarequest = r.json()
    city_name = datarequest.get("city")
    
    if not isinstance(city_name, str) or not city_name.strip():
        return render(request, "weather/main.html")
    
    city_weather = get_weather(f'https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city_name}&aqi=no')
    if city_weather is not None:
        return render(request, "weather/main.html", {"city_weather": city_weather} if city_weather else {})