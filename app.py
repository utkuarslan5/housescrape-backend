from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import streamlit as st
import pandas as pd
# You may need to import specific libraries for your vector DB

# Placeholder function for database connection (adjust based on your DB)
def connect_to_vector_db():
    persist_directory = './data/vecdb/'

    db_client = Chroma(persist_directory=persist_directory, 
                embedding_function=OpenAIEmbeddings())
    return db_client

def search_vector_db(query, db_client):
    # Convert query to vector (using your model or method)
    # Perform search in vector database
    results = db_client.similarity_search_with_score(query,)
    # Return top 3 results
    return results

def display_result(result):
    result, score = result
    st.subheader(f"Match Score: {score:.3f}")

    # Extracting and formatting metadata
    metadata_df = pd.DataFrame([result.metadata])
    
    # Using try-except to handle missing columns
    try:
        metadata_df.drop(columns=['url', 'row', 'source', 'house_id'], inplace=True)
        st.table(metadata_df)
        
    except KeyError:
        # Handle the case where one or more columns don't exist
        st.info("No metadata found, better luck next time!")
        pass
    
    # Extracting and displaying description
    try:
        descrip = result.page_content.split('descrip: ')[1]  # Assuming description starts after 'descrip: '
        st.markdown('**Description:**')
        st.markdown(descrip)
    except IndexError:
        st.markdown('**Description:** Not available')

    try:
        url = result.metadata['url']
        st.markdown(f'[View Listing]({url})\n\n----\n')
    except KeyError:
        st.markdown("\n-----\n")
        pass
    
def main():
    import dotenv
    dotenv.load_dotenv()
    st.set_page_config(layout="wide")
    st.title('HouSearch 🏠')
    
    query = st.text_input("Enter your search query:", value="""Er is een gemeubileerd vastgoed te huur met twee slaapkamers, gelegen op een gunstige locatie nabij de Universiteit Maastricht, of bereikbaar binnen 20 minuten met het openbaar vervoer. \n
        Deze accommodatie is beschikbaar voor delen en kan worden gehuurd door studenten, aangezien het studenten accepteert. \n
        De maximale maandhuur bedraagt € 1650,- en de advertentie is recentelijk geplaatst, hoogstens binnen de afgelopen week.""")

    if query:
        db_client = connect_to_vector_db()
        results = search_vector_db(query, db_client)

        for result in results:
            display_result(result)
if __name__ == "__main__":
    main()
