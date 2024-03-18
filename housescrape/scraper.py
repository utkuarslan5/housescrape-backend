from funda_scraper import FundaScraper
import pandas as pd
from typing import Dict
from fastapi import HTTPException
from modal import Image, Stub, asgi_app, Volume
from fastapi import FastAPI
from pydantic import BaseModel, validator
from typing import Dict, Union, Tuple, Optional

stub = Stub("funda-scraper")
image = Image.debian_slim(python_version="3.10").run_commands(
    "apt-get update",
    "pip install funda-scraper",
)

vol = Volume.from_name("scraped-houses", create_if_missing=True)

web_app = FastAPI()

# Pydantic models for input validation
class SearchParams(BaseModel):
    area: str
    want_to: str = "rent"
    n_pages: int = 1
    min_price: int = 0
    max_price: int = 1000000
    days_since: int = 10

class FilterCriteria(BaseModel):
    house_type: Optional[str] = None
    building_type: Optional[str] = None
    price: Optional[Tuple[float, float]] = None
    price_m2: Optional[Tuple[float, float]] = None
    room: Optional[Tuple[int, int]] = None
    bedroom: Optional[Tuple[int, int]] = None
    bathroom: Optional[Tuple[int, int]] = None
    living_area: Optional[Tuple[float, float]] = None
    energy_label: Optional[str] = None
    zip: Optional[str] = None
    address: Optional[str] = None
    year_built: Optional[Tuple[int, int]] = None
    house_age: Optional[Tuple[int, int]] = None

    # @TODO: Pydantic v2 validation
    # @validator('*', pre=True)
    # def check_ranges(cls, v, info):
    #     field_type = info.get('type_')
    #     if field_type == Tuple[int, int] or field_type == Tuple[float, float]:
    #         if not isinstance(v, tuple) or len(v) != 2:
    #             raise ValueError(f"{info.get('name', 'Unknown')} must be a tuple of two values")
    #     return v

class FilterParams(BaseModel):
    filters: FilterCriteria


# Endpoint for fetching properties
@web_app.post("/fetch")
async def fetch_properties(search_params: dict):
    try:
        validated_params = SearchParams(**search_params)
        scraper = FundaScraper(**validated_params.dict())
        df = scraper.run(raw_data=False, save=False)
        # Save the fetched DataFrame to a file in /data directory
        with open("/data/fetched_df.json", "w") as f:
            f.write(df.to_json(orient='records'))
        vol.commit()
        return {"message": "Data fetched and saved successfully"}
    except Exception as e:
        print(f"Error in fetch_properties: {e}")
        return {"error": str(e)}, 500
    

def __read_fetched_data():
    try:
        with open("/data/fetched_df.json", "r") as f:
            data = pd.read_json(f, orient='records')
        return data
    except Exception as e:
        print(f"Error in read_fetched_data: {e}")
        return {"error": str(e)}, 508
    
@web_app.get("/read")
async def read_fetched_data():
    try:
        with open("/data/fetched_df.json", "r") as f:
            data = pd.read_json(f, orient='records')
        return data.to_dict(orient='records')  # Convert DataFrame to a dictionary
    except Exception as e:
        print(f"Error in read_fetched_data: {e}")
        return {"error": str(e)}, 508

@web_app.post("/filter")
async def filter_properties(filter_params: FilterParams):
    try:
        # Load DataFrame from JSON string
        df = __read_fetched_data()
        criteria = filter_params.filters
        for column in df.columns:
            if getattr(criteria, column, None) is not None:
                filter_value = getattr(criteria, column)
                if isinstance(filter_value, tuple):
                    df = df[df[column].between(*filter_value)]
                else:
                    df = df[df[column] == filter_value]

        return df.to_json(orient='records')
    except Exception as e:
        print(f"Error in filter_properties: {e}")
        raise HTTPException(status_code=501, detail=str(e))

    
@stub.function(image=image, volumes={"/data": vol})
@asgi_app()
def fastapi_app():
    return web_app