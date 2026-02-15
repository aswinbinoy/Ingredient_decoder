import pdfplumber
import pandas as pd
import os

# Check the second PDF file
pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Ingredient_Decoder_Abstract_UPDATED.pdf'

print("Checking second PDF file...")
with pdfplumber.open(pdf_path) as pdf:
    print(f"Number of pages: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(f"Page {i+1} text length: {len(text) if text else 0}")
        if text and len(text) > 0:
            print(f"First 300 chars of page {i+1}: {text[:300]}")

print("\nDone checking second PDF.")