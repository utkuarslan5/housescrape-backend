import os
import json
from openai import OpenAI
from langchain_openai.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
import pandas as pd
import modal

stub = modal.Stub("llm-ranking", image=modal.Image.debian_slim().pip_install(["openai", "langchain-openai", "langchain"]))

@stub.function(secrets=[modal.Secret.from_name("openai-secret")])                
def expand_query(original_query, model='gpt-3.5-turbo-0125'):
    try:
        client = OpenAI()        
        prompt = f"Convert these search terms into a natural description. Output only the description, pay attention to spelling and grammar. Search terms: '{original_query}' "
        response = client.chat.completions.create(model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ])
        expanded_query = response.choices[0].message.content.strip().split(', ')
        return expanded_query
    except Exception as e:
        return f"An error occurred: {e}"
    
@stub.function(secrets=[modal.Secret.from_name("openai-secret")])                
def generate_evaluation_criteria(query, model='gpt-3.5-turbo-0125'):
    try:
        client = OpenAI()        
        prompt = f"Generate specific short evaluation criteria for the following query: '{query}'. Output the criteria names in a list."
        response = client.chat.completions.create(model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0)
        criteria = response.choices[0].message.content.strip()
        return criteria
    except Exception as e:
        return f"An error occurred: {e}"
    
@stub.function(secrets=[modal.Secret.from_name("openai-secret")])                
def analyze_property(property_row, query, criterias, model='gpt-3.5-turbo-0125'):
    try:
        prompt = f"""
        Task: Analyze the property based on the description and search query, then generate a JSON-only response.
        Determine if the property description mentions the search criteria positively, negatively, or not at all.

        Search Query: {query}
        Criterias: {criterias}
        Property Description: {property_row['description_en']}
        
        Response:
        {{
        "criteria name": "✅/🚫/❔",
        "criteria name": "✅/🚫/❔",
        ...
        }}
        """
        model = ChatOpenAI(model=model, max_tokens=256, temperature=0)
        chain = model | StrOutputParser() | json.loads
        chain_with_fallback = chain.with_fallbacks([chain])
        return chain_with_fallback.invoke(prompt)
    except Exception as e:
        return f"An error occurred: {e}"
    
@stub.local_entrypoint()
def main():
    # Example usage
    original_query = "Maastricht university nearby or within 20 minutes by public transport, Furnished, Open for sharing, Rentable to students"
    expanded_query = expand_query.remote(original_query)
    print(f"Expanded Query: {expanded_query}")

    criterias = generate_evaluation_criteria.remote(expanded_query)
    print(f"Generated Evaluation Criteria: {criterias}")

    # Sample data for demonstration
    sample_property_row = {
        'description_en': 'A spacious apartment close to Maastricht University, fully furnished and ideal for students.'
    }
    analysis_result = analyze_property.remote(sample_property_row, expanded_query, criterias)
    print(f"Property Analysis: {analysis_result}")
