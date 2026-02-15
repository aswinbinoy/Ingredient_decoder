import pdfplumber
import pandas as pd
import os

def extract_pdf_info():
    # Define file paths
    pdf_path1 = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    pdf_path2 = r'C:\code\llm_project\Ingredient_decoder\data\raw\Ingredient_Decoder_Abstract_UPDATED.pdf'
    
    print("Processing PDF files...")
    
    # Process first PDF
    print("\n=== Processing Chapter 3_Substances added to food(1).pdf ===")
    try:
        with pdfplumber.open(pdf_path1) as pdf:
            print(f"Number of pages: {len(pdf.pages)}")
            
            # Look for tables in the first few pages
            all_tables = []
            for i in range(min(10, len(pdf.pages))):  # Check first 10 pages
                page = pdf.pages[i]
                
                # Extract tables from this page
                tables = page.extract_tables()
                if tables:
                    print(f"Page {i+1} has {len(tables)} table(s)")
                    for j, table in enumerate(tables):
                        print(f"  Table {j+1} on page {i+1} has {len(table)} rows")
                        if table and len(table) > 0:
                            print(f"    First row: {table[0]}")
                        
                        # Store table data
                        all_tables.extend(tables)
            
            # Also extract some text to understand structure
            text = ""
            for i in range(min(3, len(pdf.pages))):
                page = pdf.pages[i]
                text += page.extract_text()
                text += "\n---PAGE BREAK---\n"
            
            print(f"\nSample text from first 3 pages:\n{text[:1000]}")
            
    except Exception as e:
        print(f"Error processing first PDF: {e}")
    
    # Process second PDF
    print(f"\n=== Processing Ingredient_Decoder_Abstract_UPDATED.pdf ===")
    try:
        with pdfplumber.open(pdf_path2) as pdf:
            print(f"Number of pages: {len(pdf.pages)}")
            
            # Extract text from first few pages
            text = ""
            for i in range(min(3, len(pdf.pages))):
                page = pdf.pages[i]
                text += page.extract_text()
                text += "\n---PAGE BREAK---\n"
            
            print(f"\nSample text from first 3 pages:\n{text[:1000]}")
            
    except Exception as e:
        print(f"Error processing second PDF: {e}")

if __name__ == "__main__":
    extract_pdf_info()