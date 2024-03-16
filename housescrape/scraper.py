from funda_scraper import FundaScraper
import pandas as pd
import modal


stub = modal.Stub("funda-scraper")
funda_image = modal.Image.debian_slim(python_version="3.10").run_commands(
    "apt-get update",
    "pip install funda-scraper",
)

# @TODO: add Pydantic V2
@stub.function(image=funda_image)
@modal.web_endpoint(method="POST")
def fetch_properties(search_params):
    """
    Fetches property listings from Funda based on specified search parameters.

    Parameters:
    search_params (dict): A dictionary containing search parameters like area, want_to, n_pages, min_price, max_price, and days_since.

    Returns:
    pandas.DataFrame: A DataFrame containing the fetched property listings.
    """
    # Initialize and run the FundaScraper with unpacked search parameters
    try:
        scraper = FundaScraper(**search_params)
        df = scraper.run(raw_data=False, save=False)
        return df
    except Exception as e:
        print(f"Error in fetch_properties: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on failure
    
# @TODO: filter by different properties
@stub.function(image=funda_image)
@modal.web_endpoint(method="POST")
def filter_properties(df, filter_params):
    """
    Apply filters to the DataFrame of property listings based on the given filter parameters.

    Parameters:
    df (pandas.DataFrame): DataFrame containing property listings.
    filter_params (dict): A dictionary of filter parameters. Each key is a column name and its value is a tuple representing a range (min, max).

    Returns:
    pandas.DataFrame: Filtered DataFrame.
    """
    try:
        for column, value_range in filter_params.items():
            if column in df.columns:
                min_val, max_val = value_range
                df = df[df[column].between(min_val, max_val)]
        return df
    except Exception as e:
        print(f"Error in filter_properties: {e}")
        return df  # Return the unfiltered DataFrame on failure

@stub.local_entrypoint()
def main():
    # Test the functions (can be removed in production)
    test_search_params = {
        'area': "maastricht",
        'want_to': "rent",
        'n_pages': 3,
        'min_price': 0,
        'max_price': 2000,
        'days_since': 30
    }
    test_filter_params = {
        'bedroom': (2, 5)  # Filter for bedrooms in the range of 2 to 5
    }

    test_properties = fetch_properties.remote(test_search_params)
    test_filtered_properties = filter_properties.remote(test_properties, test_filter_params)

    print(test_filtered_properties.head())  # Display first few rows for testing
