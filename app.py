# ---
# lambda-test: false
# ---
# ## Demo Streamlit application.
#
# This application is the example from https://docs.streamlit.io/library/get-started/create-an-app.
#
# Streamlit is designed to run its apps as Python scripts, not functions, so we separate the Streamlit
# code into this module, away from the Modal application code.
from typing import Optional, Tuple
from pydantic import BaseModel
import requests
import pandas as pd
import streamlit as st
import io

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

class SearchParams(BaseModel):
    area: str
    want_to: str = "rent"
    n_pages: int = 1
    min_price: int = 0
    max_price: int = 1000000
    days_since: int = 10

def send_filter_request(filters: FilterCriteria, base_url: str) -> pd.DataFrame:
    url = base_url + '/filter'
    filter_params = filters.dict()

    response = requests.post(url, json=filter_params)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the 'data' field from the JSON response
        data_json = response.json().get('data', None)
        if data_json:
            # Deserialize the JSON string into DataFrame
            json_io = io.StringIO(data_json)
            df = pd.read_json(json_io, orient='records')
            return df
        else:
            print("No data found in response.")
            return pd.DataFrame()  # Return empty DataFrame for no data
    else:
        print(f"Request failed with status code: {response.status_code}")
        return pd.DataFrame()  # Return empty DataFrame on failure

def fetch_listings(search_params: SearchParams, base_url: str) -> pd.DataFrame:
    url = base_url + '/fetch'
    search_params_dict = search_params.dict()

    try:
        response = requests.post(url, json=search_params_dict)
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses

        # Parse the JSON response
        data_json = response.json().get('data', None)
        if data_json:
            # Deserialize the JSON string into DataFrame
            json_io = io.StringIO(data_json)
            df = pd.read_json(json_io, orient='records')
            return df
        else:
            print("No data found in response.")
            return pd.DataFrame()  # Return empty DataFrame for no data

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")

    except ValueError as e:
        print(f"Error parsing JSON: {e}")

    except Exception as err:
        print(f"An unexpected error occurred: {err}")

    return pd.DataFrame()  # Return empty DataFrame in case of errors



def export_to_csv(df: pd.DataFrame, file_name: str):
    df.to_csv(file_name, index=False)
    st.success(f'Data exported to {file_name} successfully.')


def main():
    st.title('House Scraper App')
    
    # Define the base URL
    base_url = 'https://utkuarslan5--funda-scraper-fastapi-app-dev.modal.run'

    # Allow user to input search parameters
    st.sidebar.header('Search Parameters')
    area = st.sidebar.text_input('Area:')
    want_to = st.sidebar.selectbox('Want to:', ['rent', 'buy'])
    n_pages = st.sidebar.number_input('Number of Pages:', value=1, key="n_pages")
    min_price_search = st.sidebar.number_input('Minimum Price:', value=0, key="min_price_search")
    max_price_search = st.sidebar.number_input('Maximum Price:', value=1000000, key="max_price_search")
    days_since = st.sidebar.selectbox('Days Since:', [1, 3, 5, 10, 30], key="days_since")

    # Create SearchParams object
    search_params = SearchParams(
        area=area,
        want_to=want_to,
        n_pages=n_pages,
        min_price=min_price_search,
        max_price=max_price_search,
        days_since=days_since
    )

    if st.sidebar.button('Search'):
        df_listings = fetch_listings(search_params, base_url)
        if not df_listings.empty:
            st.write('Fetched Listings:')
            st.dataframe(df_listings)
            
            with st.expander("Set Filter Criteria"):
                house_type = st.text_input('House Type:', key="house_type")
                building_type = st.text_input('Building Type:', key="building_type")
                min_price_filter = st.number_input('Minimum Price:', value=0, key="min_price_filter")
                max_price_filter = st.number_input('Maximum Price:', value=1000000, key="max_price_filter")
                min_room = st.number_input('Minimum Room:', value=1, key="min_room")
                max_room = st.number_input('Maximum Room:', value=10, key="max_room")
                min_bathroom = st.number_input('Minimum Bathroom:', value=1, key="min_bathroom")
                max_bathroom = st.number_input('Maximum Bathroom:', value=5, key="max_bathroom")

                filter_criteria = FilterCriteria(
                    house_type=house_type,
                    building_type=building_type,
                    price=(min_price_filter, max_price_filter),
                    room=(min_room, max_room),
                    bathroom=(min_bathroom, max_bathroom)
                )

                if st.button('Apply Filter'):
                    df_filtered = send_filter_request(filter_criteria, base_url)
                    if not df_filtered.empty:
                        st.write('Filtered Properties:')
                        st.dataframe(df_filtered)
                    else:
                        st.write('No filtered properties available.')

            if st.button('Export to CSV'):
                export_to_csv(df_filtered, 'filtered_properties.csv')
        else:
            st.write('No listings available.')

if __name__ == "__main__":
    main()
