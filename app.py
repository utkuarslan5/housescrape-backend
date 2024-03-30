import streamlit as st
# You may need to import specific libraries for your vector DB

# Placeholder function for database connection (adjust based on your DB)
def connect_to_vector_db():
    from langchain_openai.embeddings import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma

    persist_directory = './data/vecdb/'

    db_client = Chroma(persist_directory=persist_directory, 
                embedding_function=OpenAIEmbeddings())
    return db_client

# def translate_query_to_dutch(query):
#     from googletrans import Translator

#     translator = Translator()
#     # Auto-detect source language and translate to Dutch
#     translated = translator.translate(query, dest='nl')
#     return translated.text

def search_vector_db(query, db_client):
    # Convert query to vector (using your model or method)
    # Perform search in vector database
    results = db_client.similarity_search(query)
    # Return top 3 results
    return results[:3]

def display_house_details(house):
    st.subheader(f"House ID: {house['house_id']}")
    st.write(f"URL: {house['url']}")
    st.write(f"City: {house['city']}")
    st.write(f"House Type: {house['house_type']}")
    st.write(f"Building Type: {house['building_type']}")
    st.write(f"Price: €{house['price']}")
    st.write(f"Price per m²: €{house['price_m2']}")
    st.write(f"Rooms: {house['room']} | Bedrooms: {house['bedroom']} | Bathrooms: {house['bathroom']}")
    st.write(f"Living Area: {house['living_area']} m²")
    st.write(f"Energy Label: {house['energy_label']}")
    st.write(f"Zip Code: {house['zip']}")
    st.write(f"Address: {house['address']}")
    st.write(f"Year Built: {house['year_built']}")
    st.write(f"Age of House: {house['house_age']} years")
    st.write(f"Description: {house['descrip']}")

def main():
    import dotenv
    dotenv.load_dotenv()
    st.title('HouSearch')
    
    query = st.text_input("Enter your search query:", value="""2 yatak odalı
                        Maastricht universitesine yakın veya toplu taşıma ile 20dk mesafede
                        EUR 1650 max aylık kirası olan
                        Furnished
                        Paylaşima açık
                        Öğrenciye kiralanabilir, öğrenci kabul eden
                        İlana max son 1 haftada çıkmış
                        Kiralık mülkler""")

    if query:
        db_client = connect_to_vector_db()
        results = search_vector_db(query, db_client)

        for result in results:
            display_house_details(result)

if __name__ == "__main__":
    main()
