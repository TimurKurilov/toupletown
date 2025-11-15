from django.shortcuts import render
import os
import json
from google import genai
from dotenv import load_dotenv
from SPARQLWrapper import SPARQLWrapper, JSON
import wikipediaapi

def get_quote(request):
    wiki_wiki = wikipediaapi.Wikipedia(user_agent='TestProject (test@gmail.com)', language='en')
    load_dotenv()
    GEMINI_API_KEY=os.getenv('GEMINI_API_KEY')
    client = genai.Client(api_key=GEMINI_API_KEY)

    def fetch_city_data(city_name, country_name):
        page = wiki_wiki.page(city_name)
        if page.exists():
            summary = '. '.join(page.summary.split('. ')[:3])

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


    data = fetch_city_data("Berlin", "Germany")
    data_json = json.dumps(data, ensure_ascii=False)

    prompt = (
        "Ты — генератор кратких фактов о городах. "
        "Работай строго на основе данных, переданных в INPUT. "
        "Нельзя добавлять фактов, которых нет в INPUT. "
        "Если информации недостаточно — отвечай: Недостаточно данных для факта. "
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

    return render(request, "quote/main.html", {"text": text})