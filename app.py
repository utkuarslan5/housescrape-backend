# ---
# lambda-test: false
# ---
# ## Demo Streamlit application.
#
# This application is the example from https://docs.streamlit.io/library/get-started/create-an-app.
#
# Streamlit is designed to run its apps as Python scripts, not functions, so we separate the Streamlit
# code into this module, away from the Modal application code.


def main():
    import streamlit as st
    import housescrape

    st.title('House Scraper App')

    # Allow user to input location to scrape
    location = st.text_input('Enter a location to scrape:') 

    if location:
        # Call housescrape functions to scrape data for given location
        data = housescrape.scrape_listings(location)
        
        # Display number of listings found
        st.metric('Listings Found', len(data))
        
        # Display table of listing data
        st.table(data)

    else:
        st.write('Enter a location above to scrape listings')


if __name__ == "__main__":
    main()