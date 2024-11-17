import streamlit as st
import mimetypes
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders.csv_loader import CSVLoader

# Add a title to the Streamlit app
st.title("Chat with Document")

# Create an area to upload documents of specified types
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "csv"])

if uploaded_file is not None:
    file_type, _ = mimetypes.guess_type(uploaded_file.name)

    if file_type == "application/pdf":

        st.write("Processing as PDF document...")

        # Save the uploaded PDF into the "files" folder
        path = os.path.join("files", uploaded_file.name)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("File saved successfully.")

        loader = PyPDFLoader(path)
        pages = []
        for page in loader.load():
            pages.append(page)

        st.write("File loaded successfully.")

        for page in pages:
            st.write(page.page_content)

    elif file_type == "text/csv":

        st.write("Processing as CSV document...")

        # Save the uploaded CSV into the "files" folder
        path = os.path.join("files", uploaded_file.name)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("File saved successfully.")

        # Load and print the CSV content
        csv_loader = CSVLoader(path)
        rows = csv_loader.load()
        st.write("CSV loaded successfully.")

    else:
        st.write("Unsupported file type.")
