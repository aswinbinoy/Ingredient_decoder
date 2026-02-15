import pdfplumber
import pandas as pd
import re

def extract_additive_tables():
    pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    
    print("Looking for additive tables in the PDF...")
    
    # This PDF contains many tables with different structures
    # Let's look for tables that contain additive information
    with pdfplumber.open(pdf_path) as pdf:
        all_tables_data = []
        
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if table:  # If table is not empty
                    print(f"\nPage {page_num + 1}, Table {table_idx + 1}:")
                    print(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}")
                    
                    # Print first few rows to understand structure
                    for i, row in enumerate(table[:3]):
                        print(f"  Row {i}: {row}")
                    
                    # Check if this looks like an additive table
                    # Look for keywords that suggest additive info
                    flat_table = [cell for row in table for cell in row if cell]
                    text_content = " ".join([str(cell) for cell in flat_table if cell]).lower()
                    
                    if any(keyword in text_content for keyword in ['ins', 'e', 'additive', 'sl. no.', 'no.', 'substance', 'food']):
                        print(f"  *** POTENTIAL ADDITIVE TABLE FOUND ***")
                        all_tables_data.append({
                            'page': page_num + 1,
                            'table_idx': table_idx + 1,
                            'data': table
                        })
    
    return all_tables_data

def clean_text(text):
    """Clean text by removing extra whitespace and special characters"""
    if pd.isna(text) or text is None:
        return ""
    return str(text).strip().replace('\n', ' ').replace('\r', ' ')

def parse_additive_data(all_tables_data):
    """Parse the tables to extract additive information"""
    parsed_data = []
    
    for table_info in all_tables_data:
        table = table_info['data']
        page = table_info['page']
        
        print(f"\nParsing table from page {page}")
        
        # Check if this table has headers that match our target columns
        if table and len(table) > 0:
            header_row = table[0]
            print(f"Header row: {header_row}")
            
            # Look for tables that might contain additive information
            # Common patterns in FSSAI documents
            header_str = " ".join([str(h) if h else "" for h in header_row]).lower()
            
            # Look for tables with substance/additive related columns
            if any(pattern in header_str for pattern in ['sl. no.', 'substance', 'ins', 'e', 'additive', 'name']):
                print("Found potential additive table with matching headers")
                
                # Determine column positions based on header
                col_mapping = {}
                for idx, col_header in enumerate(header_row):
                    if col_header:
                        col_text = str(col_header).lower()
                        if 'sl. no.' in col_text or 'no.' in col_text:
                            col_mapping['number'] = idx
                        elif 'substance' in col_text or 'name' in col_text or 'additive' in col_text:
                            col_mapping['ingredient_name'] = idx
                        elif 'ins' in col_text or 'e' in col_text:
                            col_mapping['ins_number'] = idx
                        elif 'category' in col_text or 'class' in col_text:
                            col_mapping['category'] = idx
                        elif 'limit' in col_text or 'level' in col_text or 'permitted' in col_text:
                            col_mapping['permitted_limit'] = idx
                
                print(f"Column mapping: {col_mapping}")
                
                # Extract data rows (skip header)
                for row_idx, row in enumerate(table[1:], 1):
                    if len(row) > max(col_mapping.values()) if col_mapping else 0:
                        entry = {
                            'ingredient_name': clean_text(row[col_mapping.get('ingredient_name', 0)]),
                            'ins_number': clean_text(row[col_mapping.get('ins_number', 1)]),
                            'category': clean_text(row[col_mapping.get('category', 2)]),
                            'permitted_limit': clean_text(row[col_mapping.get('permitted_limit', 3)]),
                            'remarks': clean_text(row[min(len(row)-1, 4)]) if len(row) > 4 else ""
                        }
                        
                        # Only add if we have meaningful data
                        if any(entry.values()):
                            parsed_data.append(entry)
                            print(f"  Added entry: {entry}")
    
    return parsed_data

def extract_additives_from_text():
    """Alternative approach: extract additive information from text content"""
    pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    
    additives_list = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(min(20, len(pdf.pages))):  # Check first 20 pages
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text:
                # Look for patterns that might indicate additive listings
                # Common patterns in FSSAI documents
                lines = text.split('\n')
                
                for line_num, line in enumerate(lines):
                    # Look for INS numbers (E numbers) patterns
                    # INS numbers typically follow patterns like INS 100, E100, etc.
                    ins_pattern = r'(?:INS|E)\s*(\d{3,4}(?:\w)?)'
                    ins_matches = re.findall(ins_pattern, line, re.IGNORECASE)
                    
                    if ins_matches:
                        # Extract potential additive name from context
                        # Usually the name appears before or after the INS/E number
                        cleaned_line = re.sub(r'\s+', ' ', line.strip())
                        
                        # Look for potential additive names near INS/E numbers
                        for ins_match in ins_matches:
                            # Simple approach: take the text chunk before INS/E number
                            parts = re.split(r'(?:INS|E)\s*' + ins_match, line, flags=re.IGNORECASE)
                            if len(parts) > 0:
                                potential_name = parts[0].split()[-5:]  # Last 5 words before INS
                                ingredient_name = ' '.join(potential_name).strip(' ;,.-')
                                
                                if len(ingredient_name) > 2:  # Valid name
                                    additive_entry = {
                                        'ingredient_name': ingredient_name,
                                        'ins_number': f"INS {ins_match}",
                                        'category': 'Food Additive',
                                        'permitted_limit': '',
                                        'remarks': cleaned_line[:100]  # First 100 chars as remark
                                    }
                                    
                                    additives_list.append(additive_entry)
                                    print(f"Found potential additive: {additive_entry}")
    
    return additives_list

def main():
    print("Starting extraction of additive information from PDF...")
    
    # Method 1: Extract from tables
    print("\n1. Looking for tables with additive information...")
    table_data = extract_additive_tables()
    
    print(f"\nFound {len(table_data)} potential tables with additive info")
    
    # Method 2: Parse the table data
    print("\n2. Parsing table data...")
    parsed_data = parse_additive_data(table_data)
    
    # Method 3: Extract from text as backup
    print("\n3. Extracting from text content...")
    text_extracted = extract_additives_from_text()
    
    # Combine all data
    combined_data = parsed_data + text_extracted
    
    print(f"\nTotal extracted entries: {len(combined_data)}")
    
    # Create DataFrame
    df = pd.DataFrame(combined_data, columns=['ingredient_name', 'ins_number', 'category', 'permitted_limit', 'remarks'])
    
    # Clean up the DataFrame
    df = df.drop_duplicates(subset=['ingredient_name', 'ins_number'], keep='first')
    
    print(f"\nFinal DataFrame shape: {df.shape}")
    print("\nFirst few rows:")
    print(df.head(10))
    
    # Save to CSV
    output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\fssai_additives.csv'
    df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")
    
    return df

if __name__ == "__main__":
    df = main()