import requests
import streamlit as st
import pandas as pd
from io import StringIO
import time
from pydantic import BaseModel

# Define base URL for the backend API
BASE_URL = 'https://utkuarslan5--funda-scraper-fastapi-app-dev.modal.run'

# Function to fetch and analyze data
@st.cache_data 
def fetch_and_analyze(search_params, query_model):
    combined_params = {"search_params": search_params, "query_model": query_model}
    url = f"{BASE_URL}/fetch-analyze"
    response = requests.post(url, json=combined_params)
    response.raise_for_status()  # Raise error if request fails

    # Parse JSON response
    data_json = response.json()

    # Wrap the JSON string in StringIO
    data_io = StringIO(data_json)

    # Read JSON using StringIO
    df = pd.read_json(data_io, orient='records')
    return df

def main():
    st.set_page_config(layout="wide")
    st.title('🏠 CasaHunt')

    with st.sidebar:
        st.header('🔍')
        area = st.text_input('Area:', help="Area you're interested in", value="maastricht").strip()
        want_to = st.sidebar.selectbox('Want to:', ['rent', 'buy'])
        n_pages = st.sidebar.number_input('Number of Pages:', value=1, key="n_pages")
        max_price_search = st.sidebar.number_input('Maximum Price:', value=2000, key="max_price_search")
        days_since = st.sidebar.selectbox('Days Since:', [1, 3, 5, 10, 30], key="days_since")
        query = st.sidebar.text_area('Enter your query:', 'Student friendly, close to center, spacious')        

    if st.sidebar.button("Get 'em", key='search_button'):
        search_params = dict(
            area=area,
            want_to=want_to,
            n_pages=n_pages,
            max_price=max_price_search,
            days_since=days_since
        )
        
        query_model = dict(original_query=query)
        
        with st.spinner('Fetching listings...'):
            try:
                df_listings = fetch_and_analyze(search_params, query_model)
                # Display error message from server
                if df_listings is not None:
                    if not df_listings.empty:
                        st.success('Listings Fetched!')
                        st.data_editor(df_listings, 
                                    column_config = {
                                        "match score" : st.column_config.ProgressColumn(label="Match Score", min_value=0, max_value=1),
                                        "url" : st.column_config.LinkColumn("URL", max_chars=50),
                                    },
                                    hide_index=True,
                                    )
                    else:
                        st.warning('Hmm, housing market has been silent lately. \nHow about try again with different parameters?', "↩️")
            except requests.exceptions.HTTPError as http_err:
                st.error("Uh-oh, our servers are having a bad day", icon="😔")
                time.sleep(3)
                error_code = http_err.response.status_code
                error_message = http_err.response.reason        
                st.info("Try something else. If it persists, send me the error code: " + f"{error_code} {error_message}")
            except Exception as e:
                st.error(f"Something else went wrong and I don't know what it is PANIKK! \n{e}", icon="🚨")
if __name__ == "__main__":
    main()
