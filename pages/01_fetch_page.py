import requests
import streamlit as st
import pandas as pd
from io import StringIO
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DataFrameLoader
from dotenv import load_dotenv, find_dotenv
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain, HypotheticalDocumentEmbedder

load_dotenv(find_dotenv())

# Define base URL for the backend API
SCRAPER_URL = 'https://utkuarslan5-housearch--funda-scraper-fetch-properties-dev.modal.run/'

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

prompt = PromptTemplate.from_template("""
    As an AI real estate agent assistant, I'll produce a concise summary in markdown format, detailing the key features of each real estate listing. 
    The summary will also point out any missing elements from the search query. This format allows for a clear and structured presentation, making it easier for you to quickly assess the suitability of each listing based on your specific needs and preferences. 

    Output Format:
    ```
    ### [Address with href to url]
    [720p Photo]
    - [Key features]
        - ...
        - ...
    - **Missing elements**:
        - ...
        - ...
    - **Summary**: [Write your summary here]
    --------
    ```
    Search Query: {query}

    Listings:
    {listings}

    Summary:
    """)    

llm = ChatOpenAI(model_name="gpt-3.5-turbo-0125", temperature=0)

hyde_prompt = """As a Dutch real estate agent, you are tasked with creating an online house ad in Dutch based on a given house description. 
Please provide a detailed and comprehensive description of the house, including key features, amenities, and any unique selling points that would appeal to potential buyers. 
Ensure that your ad is engaging, informative, and accurately represents the property in order to attract interested buyers. 

House description: {description}
House ad:
"""

hyde_prompt = PromptTemplate(input_variables=["description"], template=hyde_prompt)

hyde_chain = LLMChain(llm=llm, prompt=hyde_prompt)

hyde_embeddings  = HypotheticalDocumentEmbedder(llm_chain=hyde_chain, base_embeddings=embeddings)

password = "testapp"

# Function to fetch 
@st.cache_data 
def fetch(search_params):
    response = requests.post(SCRAPER_URL, json=search_params)
    response.raise_for_status()  # Raise error if request fails

    # Parse JSON response
    data_json = response.json()

    # Wrap the JSON string in StringIO
    data_io = StringIO(data_json)

    # Read JSON using StringIO
    df = pd.read_json(data_io, orient='records')

    return df

@st.cache_resource
def create_chroma_db(df, text_column):
    loader = DataFrameLoader(df, page_content_column=text_column)
    houses = loader.load()
    
    db = Chroma.from_documents(
        documents=houses,
        embedding=embeddings
    )
    st.session_state['db'] = db
    return db

def drop_columns(df, columns_to_drop):
    if df is not None:
        df = df.copy()
        for col in columns_to_drop:
            try:
                df.drop(columns=[col], inplace=True) 
            except KeyError:
                print(f"Column {col} does not exist in DataFrame")

        return df
      
def display_result(result):
    doc, score = result
    
    try:
        url = doc.metadata['url']
    except KeyError:
        url = "Not available"
        
    st.subheader(f"Match Score: {score:.3f} [View Listing]({url})")

    # Extracting and formatting metadata
    metadata_df = pd.DataFrame([doc.metadata])
    # Using try-except to handle missing columns
    try:
        dead_cols = ['url', 'house_id', 'photo']
        metadata_df = drop_columns(metadata_df, dead_cols)
        st.table(metadata_df)
        
    except KeyError:
        # Handle the case where one or more columns don't exist
        st.info("No metadata found, better luck next time!")
        pass
    
    # Extracting and displaying description
    try:
        descrip = doc.page_content
        with st.expander("Description"):
            st.markdown(descrip)
    except IndexError:
        st.markdown('**Description:** Not available')

    st.markdown("\n-----\n")
    
def format_docs(docs):
    return "\n\n".join(str(doc) for doc in docs)

def main():
    st.set_page_config(layout="wide")
    authentication_status = True
    
    # with st.empty():
    #     input_pass = st.text_input("Password", type="password")
        
    #     if input_pass and input_pass == password:
    #         authentication_status = True
    #     elif input_pass:
    #         st.error("Wrong password!")
    
    if authentication_status:

        tab1, tab2 = st.tabs(["🏠 House", "🗃 Search"])

        with st.sidebar:
            st.header('🔍')
            area = st.text_input('Area:', help="Area you're interested in", value="maastricht").strip()
            want_to = st.sidebar.selectbox('Want to:', ['rent', 'buy'])
            n_pages = st.sidebar.number_input('Number of Pages:', value=1, key="n_pages")
            max_price_search = st.sidebar.number_input('Maximum Price:', value=2000, key="max_price_search")
            days_since = st.sidebar.selectbox('Days Since:', [1, 3, 5, 10, 30], key="days_since")
            query = st.text_input("Search Query:", value="spacious house with lost of light and potentially with a garden an near the city center") 
            # threshold = st.number_input("Similarity Threshold:", value=0.15, key="threshold", min_value=0.0, max_value=1.0)
                    
        if st.sidebar.button("Search", key='search_button'):
            search_params = dict(
                area=area,
                want_to=want_to,
                n_pages=n_pages,
                max_price=max_price_search,
                days_since=days_since
            )
            
            with tab1:        
                try:
                    df = fetch(search_params)
                    
                    # Display error message from server
                    if df is not None:
                        if not df.empty:
                            st.session_state['df'] = df
                            st.success(f"{len(st.session_state['df'])} Listings Fetched!", icon="✅")
                            st.data_editor(st.session_state['df'],
                                        column_config= {
                                            
                                        },
                                            hide_index=True,
                                        )
                            db = create_chroma_db(df, "descrip")
                            st.session_state['db'] = db
                        else:
                            st.warning("Either no houses found or caught Funda's bot detection. Try later or different parameters!", icon="🤖")
                except Exception as e:
                    st.error(f"If you're seeing this, it means smth I couldn't foresee went wrong. \n{e}", icon="🚨")
            
            with tab2:
                rag_chain = (
                            # {"listings": retriever | format_docs, "query": RunnablePassthrough()}
                            prompt
                            | llm
                            | StrOutputParser()
                        )
                
                if query and not df.empty:
                    db = st.session_state.get('db')
                    
                
                    with st.spinner("Analyzing..."):
                        # Perform search
                        embedded_query = hyde_embeddings.embed_query(str(search_params)+str(query))

                        docs = format_docs(db.similarity_search_by_vector(embedded_query, k=2))
                        print(docs)
                        
                        response = rag_chain.invoke({"listings":docs, "query": query})
                        st.markdown(response, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
