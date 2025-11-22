import os
import json
import requests
import wikipediaapi
from google import genai
from dotenv import load_dotenv
from SPARQLWrapper import SPARQLWrapper, JSON
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache


def get_quote(request):
    wiki_wiki = wikipediaapi.Wikipedia(user_agent='TestProject (test@gmail.com)', language='en')
    load_dotenv()
    GEMINI_API_KEY=os.getenv('GEMINI_API_KEY')
    TOKEN = os.getenv("TOKEN")
    client = genai.Client(api_key=GEMINI_API_KEY)
    r = requests.get(f"https://api.2ip.io/?token={TOKEN}")
    datarequest = r.json()
    city_name = datarequest["city"]
    country_name = datarequest["country"]
    
    
    def fetch_city_data(city_name, country_name):
        r = requests.get("https://api.2ip.io/?token=bwrl3ve9n2pevkd7")
        datarequest = r.json()
        city_name = datarequest["city"]
        country_name = datarequest["country"]
        
        page = wiki_wiki.page(city_name)
        if page.exists():
            summary = '. '.join(page.summary.split('. ')[:5])

        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        query = f"""
        SELECT ?city ?population ?founded WHERE {{
          ?city rdfs:label "{city_name}"@en.
          ?city wdt:P17 ?country.
          ?country rdfs:label "{country_name}"@en.
          OPTIONAL {{ ?city wdt:P1082 ?population. }}
        }}
        LIMIT 1
        """
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        if results["results"]["bindings"]:
            res = results["results"]["bindings"][0]
            return {
                "city": city_name,
                "country": country_name,
                "population": res.get("population", {}).get("value"),
                "info": summary
            }
        return None
    
    data = fetch_city_data(country_name, city_name)
    data_json = json.dumps(data, ensure_ascii=False)
    

    prompt = (
        "Ты — генератор кратких фактов о городах. "
        "Отвечай строго на Русском. "
        "Работай строго на основе данных, переданных в INPUT. "
        "Нельзя добавлять фактов, которых нет в INPUT. "
        "Требования: 1 факт, максимум 2 предложения. Факт должен быть конкретным. "
        "Без оценочных суждений. Формат: FACT: <текст>. "
        f"\nINPUT:\n{data_json}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    try:
        text = response.text
    except:
        text = response.candidates[0].content.parts[0].text
        
    cache.set(city_name, text, timeout=259200)

    return render(request, "quote/main.html", {"text": text, "data_json": data_json, "citygpt": city_name, "countrygpt": country_name})