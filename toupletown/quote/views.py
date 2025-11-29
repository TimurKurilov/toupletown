import os
import json
import requests
import wikipediaapi
from google import genai
from dotenv import load_dotenv
from SPARQLWrapper import SPARQLWrapper, JSON
from django.shortcuts import render, get_object_or_404
from .models import CityRawData
from django.core.cache import cache

    
def fetch_city_data(request, city_name=None, country_name=None):
        wiki_wiki = wikipediaapi.Wikipedia(user_agent='TestProject (test@gmail.com)', language='en')
        load_dotenv()
        GEMINI_API_KEY=os.getenv('GEMINI_API_KEY')
        TOKEN = os.getenv("TOKEN")
        client = genai.Client(api_key=GEMINI_API_KEY)
        if "geo" not in request.session:
            r = requests.get(f"https://api.2ip.io/?token={TOKEN}")
            request.session["geo"] = r.json()
        geo = request.session["geo"]
        city_name = geo.get("city", "Unknown")
        country_name = geo.get("country", "Unknown")


        page = wiki_wiki.page(city_name)
        if page.exists():
            summary = '. '.join(page.summary.split('. ')[:5])
            summary_raw = '. '.join(page.summary.split('. ')[:12])

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
            population = res.get("population", {}).get("value")
        data = {
        "city": city_name,
        "country": country_name,
        "population": population,
        "info": summary,
        "wikidata_raw": summary_raw
    }
        data_json = json.dumps(data, ensure_ascii=False)
        obj, created = CityRawData.objects.get_or_create(
        city=city_name,
        defaults={
            'country': country_name,
            'info': summary,
            'raw': {
                'population': population,
                'founded': None,
                'wikidata_raw': summary_raw,
            }
        }
    )   
        cachee = cache.get(f"{city_name}:{country_name}")
        if cachee:
            return render(request, "quote/main.html", {"text": cachee, "data_json": data_json, "citygpt": city_name, "countrygpt": country_name})
        else:
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
                
            cache.set(f"{city_name}:{country_name}", text, timeout=259200)

        return render(request, "quote/main.html", {"text": text, "data_json": data_json, "citygpt": city_name, "countrygpt": country_name})