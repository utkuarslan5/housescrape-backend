from funda_scraper import FundaScraper
import pandas as pd
from typing import Dict
from fastapi import HTTPException
from modal import Image, Stub, asgi_app, Volume, Secret
import json
from openai import OpenAI
from langchain_openai.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from fastapi import FastAPI
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

stub = Stub("funda-scraper")
image = Image.debian_slim(python_version="3.10").run_commands(
    "apt-get update",
    "pip install funda-scraper openai langchain-openai langchain",
)

vol = Volume.from_name("scraped-houses", create_if_missing=True)

web_app = FastAPI()

# Pydantic models for input validation
class SearchParams(BaseModel):
    area: str = "amsterdam"
    want_to: str = "rent"
    n_pages: int = 1
    min_price: int = 0
    max_price: int = 1000000
    days_since: int = 10

class QueryModel(BaseModel):
    original_query: str = "Student friendly, close to center, spacious"

class CombinedParams(BaseModel):
    search_params: SearchParams
    query_model: QueryModel

async def fetch_properties(search_params: SearchParams):
    try:
        scraper = FundaScraper(**search_params.dict())
        df = scraper.run(raw_data=False, save=False)
        # Save the fetched DataFrame to a file in /data directory
        with open("/data/fetched_df.json", "w") as f:
            f.write(df.to_json(orient='records'))
        vol.commit()
        return df
    except Exception as e:
        logger.error(f"Error in fetch_properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))   

async def expand_query(original_query: str, model='gpt-3.5-turbo-0125'):
    try:
        client = OpenAI()
        prompt = f"Convert these search terms into a natural description. Output only the description, pay attention to spelling and grammar. Search terms: '{original_query}' "
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        expanded_query = response.choices[0].message.content.strip().split(', ')
        return expanded_query
    except Exception as e:
        logger.error(f"Error in expand_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TODO: combine expansion and criteria generation to single query, than chain in langchain
async def generate_evaluation_criteria(criteria_query: str, model='gpt-3.5-turbo-0125'):
    try:  
        client = OpenAI()     
        prompt = f"Generate specific short evaluation criteria for the following query: '{criteria_query}'. Output the criteria names in a list."
        response = client.chat.completions.create(model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0)
        criteria = response.choices[0].message.content.strip()
        return criteria
    except Exception as e:
        logger.error(f"Error in generate_evaluation_criteria: {e}")
        raise HTTPException(status_code=500, detail=str(e))
              

async def analyze_property(row, criterias, model='gpt-3.5-turbo-0125'):
    try:
        prompt = f"""
        Task: Translate the description. Analyze the property based on the translated description and search criterias, then generate a JSON-only response.
        Your task is to determine if the description mentiones the criterias positievely, negatively or not at all.
        Finally give an overall match score between 0-1.

        Criterias: {criterias}
        Property Description: {row['descrip']}
        
        Response:
        {{
        "match score": "0-1",
        "criteria name": "✅/🚫/❔",
        "criteria name": "✅/🚫/❔",
        ...
        }}
        """
        model = ChatOpenAI(model=model, max_tokens=256, temperature=0)
        chain = model | StrOutputParser() | json.loads
        chain_with_fallback = chain.with_fallbacks([chain])
        response = chain_with_fallback.invoke(prompt)
        return response
    except Exception as e:
        logger.error(f"Error in analyze_property: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
async def process_data_frame(df, criterias):
    try:
        results = []
        for _, row in df.iterrows():
            result = await analyze_property(row, criterias)
            results.append(result)
        return pd.concat([pd.DataFrame(results), df], axis=1)
    except Exception as e:
        logger.error(f"Error in process_data_frame: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@web_app.post("/fetch-analyze")
async def fetch_and_analyze(combined_params: CombinedParams):
    try:
        # Step 1: Fetch properties
        df = await fetch_properties(combined_params.search_params)

        # Check if the DataFrame is empty and return an error if true
        if df.empty:
            logger.warning("No properties found. Possible API error, or query parameters returned no results.")
            detail_msg = (
                "No properties found. This could be due to an API error, "
                "or the query parameters you provided did not match any results. "
                "Please try again with different parameters. If the issue persists, "
                "consider refreshing the page or note that we might have hit the API quota."
            )
            raise HTTPException(status_code=404, detail=detail_msg)
        
        # Step 2: Expand the query
        logger.info("Expanding the query using AI model.")
        expanded_query = await expand_query(combined_params.query_model.original_query)

        # Step 3: Generate evaluation criteria
        logger.info("Generating evaluation criteria from expanded query.")
        criterias = await generate_evaluation_criteria(expanded_query)

        # Step 4: Process the DataFrame
        logger.info("Analyzing properties based on evaluation criteria.")
        results_df = await process_data_frame(df, criterias)

        logger.info("Process completed successfully. Sending back the data")
        return results_df.to_json(orient='records')
    except Exception as e:
        logger.error(f"An error occurred during fetch and analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@stub.function(image=image, volumes={"/data": vol}, 
               secrets=[Secret.from_name("openai-secret")])
@asgi_app()
def fastapi_app():
    return web_app