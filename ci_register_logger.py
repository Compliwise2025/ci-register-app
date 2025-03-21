
import streamlit as st
import difflib
import pandas as pd
from datetime import datetime
from docx import Document
import fitz  # PyMuPDF

st.title("AI-Powered CI Register Logger (Docx & PDF Support)")

def extract_text_from_docx(file):
    doc = Document(file)
    return [para.text for para in doc.paragraphs if para.text.strip() != ""]

def extract_text_from_pdf(file):
    text = []
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            lines = page.get_text().split("\n")
            text.extend([line.strip() for line in lines if line.strip()])
    return text

def extract_text(file):
    if file.name.endswith(".txt"):
        return file.read().decode("utf-8").splitlines()
    elif file.name.endswith(".docx"):
        return extract_text_from_docx(file)
    elif file.name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    else:
        st.error("Unsupported file type.")
        return []

# Upload old and new document files
old_file = st.file_uploader("Upload OLD version of the document", type=["txt", "docx", "pdf"])
new_file = st.file_uploader("Upload NEW version of the document", type=["txt", "docx", "pdf"])

if old_file and new_file:
    old_text = extract_text(old_file)
    new_text = extract_text(new_file)

    diff = difflib.ndiff(old_text, new_text)
    change_summary = []
    for line in diff:
        if line.startswith("+ "):
            change_summary.append(f"Added: {line[2:]}")
        elif line.startswith("- "):
            change_summary.append(f"Removed: {line[2:]}")

    summary_text = "\n".join(change_summary)
    st.subheader("Detected Changes")
    st.text(summary_text)

    # Input metadata for CI Register
    document_name = st.text_input("Document Name")
    logged_by = st.text_input("Logged By")

    if st.button("Log Changes to CI Register"):
        ci_entry = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Document Name": document_name,
            "Summary of Changes": summary_text,
            "Logged By": logged_by
        }])

        try:
            existing = pd.read_csv("ci_register.csv")
            updated_register = pd.concat([existing, ci_entry], ignore_index=True)
        except FileNotFoundError:
            updated_register = ci_entry

        updated_register.to_csv("ci_register.csv", index=False)
        st.success("Changes logged to CI Register successfully.")
        st.dataframe(updated_register)

    st.download_button("Download CI Register", data=updated_register.to_csv(index=False), file_name="ci_register.csv", mime="text/csv")
