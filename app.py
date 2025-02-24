from flask import Flask, render_template, request, session, jsonify
import os
import sys
import lancedb
from lancedb.rerankers import AnswerdotaiRerankers
import re
import logging
import markdown
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

from prompts import (
    HYDE_SYSTEM_PROMPT,
    HYDE_V2_SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT  
)

# Configuration
CONFIG = {
    'LOG_FILE': 'app.log',
    'LOG_FORMAT': '%(asctime)s - %(message)s',
    'LOG_DATE_FORMAT': '%d-%b-%y %H:%M:%S'
}

# Logging setup
def setup_logging(config):
    """
    Configure and initialize logging for the application.
    
    Args:
        config (dict): Configuration dictionary containing logging settings
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logging.basicConfig(
        filename=config['LOG_FILE'],
        level=logging.INFO,
        format=config['LOG_FORMAT'],
        datefmt=config['LOG_DATE_FORMAT']
    )
    return logging.getLogger(__name__)

# Database setup
def setup_database(codebase_path):
    """
    Initialize database connection and open required tables.
    
    Args:
        codebase_path (str): Path to the codebase directory
        
    Returns:
        tuple: (method_table, class_table) LanceDB table objects
    """
    normalized_path = os.path.normpath(os.path.abspath(codebase_path))
    codebase_folder_name = os.path.basename(normalized_path)

    # lancedb connection
    uri = "database"
    db = lancedb.connect(uri)

    method_table = db.open_table(codebase_folder_name + "_method")
    class_table = db.open_table(codebase_folder_name + "_class")

    return method_table, class_table

# Application setup
def setup_app():
    """
    Initialize and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.update(CONFIG)
    
    # Setup logging
    app.logger = setup_logging(app.config)
    
    return app

# Create the Flask app
app = setup_app()

# OpenAI client setup
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# Initialize the reranker
reranker = AnswerdotaiRerankers(column="source_code")

# Replace groq_hyde function
def openai_hyde(query):
    """
    Generate a hypothetical answer using OpenAI's model for query expansion.
    
    Args:
        query (str): User's original query
        
    Returns:
        str: Generated hypothetical answer
    """
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": HYDE_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"Help predict the answer to the query: {query}",
            }
        ]
    )
    return chat_completion.choices[0].message.content

def openai_hyde_v2(query, temp_context, hyde_query):
    """
    Generate an improved hypothetical answer using additional context.
    
    Args:
        query (str): Original user query
        temp_context (str): Initial context from first search
        hyde_query (str): First hypothetical answer
        
    Returns:
        str: Refined hypothetical answer
    """
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": HYDE_V2_SYSTEM_PROMPT.format(query=query, temp_context=temp_context)
            },
            {
                "role": "user",
                "content": f"Predict the answer to the query: {hyde_query}",
            }
        ]
    )
    return chat_completion.choices[0].message.content


def openai_chat(query, context):
    """
    Generate a response to the user's query using OpenAI's chat model.
    
    Args:
        query (str): User's query
        context (str): Retrieved context for the query
        
    Returns:
        str: Generated response from the model
    """
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": CHAT_SYSTEM_PROMPT.format(context=context)
            },
            {
                "role": "user",
                "content": query,
            }
        ]
    )
    return chat_completion.choices[0].message.content

def process_input(input_text):
    """
    Clean and normalize input text.
    
    Args:
        input_text (str): Raw input text
        
    Returns:
        str: Processed and normalized text
    """
    processed_text = input_text.replace('\n', ' ').replace('\t', ' ')
    processed_text = re.sub(r'\s+', ' ', processed_text)
    processed_text = processed_text.strip()
    
    return processed_text

def generate_context(query, method_table, class_table, rerank=False):
    """
    Generate relevant context for a query using two-stage retrieval.
    
    Args:
        query (str): User's query
        method_table (lancedb.Table): Table containing method information
        class_table (lancedb.Table): Table containing class information
        rerank (bool, optional): Whether to apply reranking. Defaults to False
        
    Returns:
        str: Combined context from methods and classes
    """
    hyde_query = openai_hyde(query)

    method_docs = method_table.search(hyde_query).limit(5).to_pandas()
    class_docs = class_table.search(hyde_query).limit(5).to_pandas()

    temp_context = '\n'.join(method_docs['code'] + '\n'.join(class_docs['source_code']))

    hyde_query_v2 = openai_hyde_v2(query, temp_context, hyde_query)

    logging.info("-query_v2-")
    logging.info(hyde_query_v2)

    method_search = method_table.search(hyde_query_v2)
    class_search = class_table.search(hyde_query_v2)

    if rerank:
        method_search = method_search.rerank(reranker)
        class_search = class_search.rerank(reranker)

    method_docs = method_search.limit(5).to_list()
    class_docs = class_search.limit(5).to_list()

    top_3_methods = method_docs[:3]
    methods_combined = "\n\n".join(f"File: {doc['file_path']}\nCode:\n{doc['code']}" for doc in top_3_methods)

    top_3_classes = class_docs[:3]
    classes_combined = "\n\n".join(f"File: {doc['file_path']}\nClass Info:\n{doc['source_code']} References: \n{doc['references']}  \n END OF ROW {i}" for i, doc in enumerate(top_3_classes))

    logging.info("Context generation complete.")

    return methods_combined + "\n below is class or constructor related code \n" + classes_combined

def main():
    """
    Main application entry point. Handles command line arguments and runs the interactive query loop.
    """
    if len(sys.argv) != 2:
        print("Usage: python app.py <codebase_path>")
        sys.exit(1)

    codebase_path = sys.argv[1]
    
    # Setup database
    method_table, class_table = setup_database(codebase_path)
    
    while True:
        query = input("\nEnter your query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
            
        print("\nGenerating context...")
        context = generate_context(query, method_table, class_table, rerank=True)
        print("\n=== Retrieved Context ===")
        print(context)
        print("\n=== Generated Response ===")
        response = openai_chat(query, context[:12000])
        print(response)
        print("\n" + "="*50)

if __name__ == "__main__":
    main()
