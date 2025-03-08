import os
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def load_assignments(file_path: str) -> dict:
    """Loads assignments from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def flatten_assignments(assignments: dict):
    """
    Flattens the assignment structure: creates a textual description for each entry
    along with corresponding metadata.
    """
    documents = []
    metadatas = []
    for cat, subcats in assignments.items():
        for subcat, entries in subcats.items():
            for entry in entries:
                doc_text = (
                    f"Name: {entry.get('name', '')} {entry.get('surname', '')}. "
                    f"Skill: {entry.get('skill', '')}. "
                    f"Description: {entry.get('description', '')}. "
                    f"Category: {cat}. Subcategory: {subcat}."
                )
                documents.append(doc_text)
                metadatas.append({
                    "name": entry.get("name", ""),
                    "surname": entry.get("surname", ""),
                    "skill": entry.get("skill", ""),
                    "description": entry.get("description", ""),
                    "category": cat,
                    "subcategory": subcat
                })
    return documents, metadatas

def main():
    st.title("Vector Search Interface")

    # Load environment variables
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    assignments_file = "assignment.json"
    if not os.path.exists(assignments_file):
        st.error(f"File {assignments_file} does not exist!")
        return

    st.info("Loading assignments...")
    assignments = load_assignments(assignments_file)

    documents, metadatas = flatten_assignments(assignments)
    if not documents:
        st.warning("No documents to index!")
        return

    st.info("Indexing documents, please wait...")
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(documents, embeddings, metadatas=metadatas)
    st.success("Index created!")

    query = st.text_input("Enter a query:", "developer who trains large language models")
    if query:
        with st.spinner("Searching..."):
            results = vectorstore.similarity_search(query, k=5)

        st.subheader("Query Results (JSON):")
        results_list = []
        for res in results:
            results_list.append({
                "metadata": res.metadata,
                "content": res.page_content
            })
        st.json(results_list)

if __name__ == "__main__":
    main()
