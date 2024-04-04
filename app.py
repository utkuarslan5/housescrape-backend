import requests
import streamlit as st
import pandas as pd
from io import StringIO
from pydantic import BaseModel
from funda_scraper import FundaScraper
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DataFrameLoader
from dotenv import load_dotenv, find_dotenv
from langchain_core.runnables import RunnablePassthrough
from langchain.callbacks.manager import collect_runs
from langchain.schema import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain, HypotheticalDocumentEmbedder
import os
from langsmith import Client
from streamlit_feedback import streamlit_feedback

load_dotenv(find_dotenv())

os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"]="ls__720c11f30f434eaaa6fff81cd608995d"
os.environ["LANGCHAIN_PROJECT"]="housearch"

client = Client()

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

feedback_option = (
    "thumbs"
)

@st.cache_data 
def fetch_properties(search_params: dict):
    try:
        scraper = FundaScraper(**search_params)
        df = scraper.run(raw_data=False, save=False)

        return df
    except Exception as e:
        st.error(f"Error in while fetching properties: {e}")

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
      
def single_photo(photo_string):
  photos = photo_string.split(', ')
  for photo in photos:
    if '720x480.jpg' in photo:
      return photo.split(' ')[0]
  return None
  
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
        st.title("Real Estate Agent Assistant 🏘️")
        with st.sidebar:
            st.header('🔍')
            area = st.text_input('Area:', help="Area you're interested in", value="maastricht").strip()
            want_to = st.sidebar.selectbox('Want to:', ['rent', 'buy'])
            n_pages = st.sidebar.number_input('Number of Pages:', value=1, key="n_pages")
            max_price_search = st.sidebar.number_input('Maximum Price:', value=2000, key="max_price_search")
            days_since = st.sidebar.selectbox('Days Since:', [1, 3, 5, 10, 30], key="days_since")
            query = st.text_input("Search Query:", value="spacious house with lost of light and potentially with a garden an near the city center", key="query") 
            # threshold = st.number_input("Similarity Threshold:", value=0.15, key="threshold", min_value=0.0, max_value=1.0)
                    
        if st.sidebar.button("Search", key='search_button'):
            search_params = dict(
                area=area,
                want_to=want_to,
                n_pages=n_pages,
                max_price=max_price_search,
                days_since=days_since
            )
            
                
            try:
                df = fetch_properties(search_params)
                
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
                        df_to_embed = df.copy()
                        df_to_embed['photo'] = df_to_embed['photo'].apply(single_photo)
                        db = create_chroma_db(df_to_embed, "descrip")
                        st.session_state['db'] = db
                    else:
                        st.warning("Either no houses found or caught Funda's bot detection. Try later or different parameters!", icon="🤖")
            except Exception as e:
                st.error(f"If you're seeing this, it means smth I couldn't foresee went wrong. \n{e}", icon="🚨")
        
            rag_chain = (
                        # {"listings": retriever | format_docs, "query": RunnablePassthrough()}
                        prompt
                        | llm
                        | StrOutputParser()
                    )
            
            if st.session_state.query and not df.empty:
                db = st.session_state.get('db')
                
                with st.spinner("Analyzing..."):
                    with collect_runs() as cb:
                        # Perform search
                        embedded_query = hyde_embeddings.embed_query(str(search_params)+str(query))

                        docs = format_docs(db.similarity_search_by_vector(embedded_query, k=2))
                        
                        response = rag_chain.invoke({"listings":docs, "query": query})
                        st.markdown(response, unsafe_allow_html=True)
                        st.session_state.run_id = cb.traced_runs[1].id
                        print(f"Run ID: {cb.traced_runs[1].id}")
                    
                if st.session_state.get("run_id"):
                    run_id = st.session_state.run_id
                    feedback = streamlit_feedback(
                        feedback_type=feedback_option,
                        optional_text_label="[Optional] Please provide an explanation",
                        key=f"feedback_{run_id}",
                    )

                    # Define score mappings for both "thumbs" and "faces" feedback systems
                    score_mappings = {
                        "thumbs": {"👍": 1, "👎": 0},
                        "faces": {"😀": 1, "🙂": 0.75, "😐": 0.5, "🙁": 0.25, "😞": 0},
                    }

                    # Get the score mapping based on the selected feedback option
                    scores = score_mappings[feedback_option]

                    if feedback:
                        # Get the score from the selected feedback option's score mapping
                        score = scores.get(feedback["score"])

                        if score is not None:
                            # Formulate feedback type string incorporating the feedback option
                            # and score value
                            feedback_type_str = f"{feedback_option} {feedback['score']}"

                            # Record the feedback with the formulated feedback type string
                            # and optional comment
                            feedback_record = client.create_feedback(
                                run_id,
                                feedback_type_str,
                                score=score,
                                comment=feedback.get("text"),
                            )
                            st.session_state.feedback = {
                                "feedback_id": str(feedback_record.id),
                                "score": score,
                            }
                        else:
                            st.warning("Invalid feedback score.")


if __name__ == "__main__":
    main()
