import pdfplumber
import pandas as pd
import re

def extract_additive_tables():
    pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    
    print("Looking for additive tables in the PDF...")
    
    with pdfplumber.open(pdf_path) as pdf:
        all_tables_data = []
        
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if table and len(table) > 0:  # If table is not empty
                    print(f"\nPage {page_num + 1}, Table {table_idx + 1}:")
                    print(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}")
                    
                    # Print first few rows to understand structure
                    for i, row in enumerate(table[:2]):
                        print(f"  Row {i}: {row}")
                    
                    # Check if this looks like an additive table
                    # Look for keywords that suggest additive info
                    flat_table = [cell for row in table for cell in row if cell]
                    text_content = " ".join([str(cell) for cell in flat_table if cell and str(cell).strip()]).lower()
                    
                    if any(keyword in text_content for keyword in ['ins', 'e', 'additive', 'sl. no.', 'no.', 'substance', 'food', 'common name', 'synonyms', 'characteristic', 'requirement']):
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
        
        if table and len(table) > 0:
            header_row = table[0]
            print(f"Header row: {header_row}")
            
            # Look for tables that might contain additive information
            header_str = " ".join([str(h) if h else "" for h in header_row]).lower()
            
            # Check if this table has headers that could map to our target columns
            col_mapping = {}
            for idx, col_header in enumerate(header_row):
                if col_header:
                    col_text = str(col_header).lower()
                    if 'sl. no.' in col_text or 'no.' in col_text:
                        col_mapping['number'] = idx
                    elif 'substance' in col_text or 'name' in col_text or 'additive' in col_text or 'common name' in col_text:
                        col_mapping['ingredient_name'] = idx
                    elif 'ins' in col_text or 'e' in col_text or 'no.' in col_text.lower().replace('no.', 'no'):
                        col_mapping['ins_number'] = idx
                    elif 'category' in col_text or 'class' in col_text:
                        col_mapping['category'] = idx
                    elif 'limit' in col_text or 'level' in col_text or 'permitted' in col_text or 'usage' in col_text:
                        col_mapping['permitted_limit'] = idx
            
            print(f"Column mapping: {col_mapping}")
            
            # Extract data rows (skip header)
            for row_idx, row in enumerate(table[1:], 1):
                # Ensure row has enough columns to avoid index errors
                if len(row) > 0:
                    # Create entry with safe indexing
                    entry = {
                        'ingredient_name': clean_text(row[col_mapping.get('ingredient_name', 0)]) if col_mapping.get('ingredient_name') is not None and col_mapping['ingredient_name'] < len(row) else "",
                        'ins_number': clean_text(row[col_mapping.get('ins_number', 1)]) if col_mapping.get('ins_number') is not None and col_mapping['ins_number'] < len(row) else "",
                        'category': clean_text(row[col_mapping.get('category', 2)]) if col_mapping.get('category') is not None and col_mapping['category'] < len(row) else "",
                        'permitted_limit': clean_text(row[col_mapping.get('permitted_limit', 3)]) if col_mapping.get('permitted_limit') is not None and col_mapping['permitted_limit'] < len(row) else "",
                        'remarks': clean_text(row[min(len(row)-1, 4)]) if len(row) > 4 else ""
                    }
                    
                    # Additional check: if we don't have a good mapping, try to infer from row content
                    if not entry['ingredient_name'] and len(row) > 0:
                        # Look for common additive names in the row
                        row_text = " ".join([str(cell) for cell in row if cell and str(cell).strip()])
                        if any(word in row_text.lower() for word in ['vitamin', 'acid', 'sodium', 'potassium', 'calcium', 'magnesium', 'chloride', 'oxide', 'benzoate', 'sorbate', 'propionate']):
                            # This might be an additive row, try to extract info
                            # Look for INS/E numbers in the row
                            ins_match = re.search(r'(?:INS|E)\s*(\d{3,4}(?:\w)?)', row_text, re.IGNORECASE)
                            if ins_match:
                                entry['ins_number'] = f"INS {ins_match.group(1)}"
                            
                            # Look for potential name (usually before INS/E number)
                            parts = re.split(r'(?:INS|E)\s*\d{3,4}(?:\w)?', row_text, flags=re.IGNORECASE)
                            if len(parts) > 0:
                                potential_name = parts[0].strip().split()[-5:]  # Last 5 words before INS
                                if potential_name:
                                    entry['ingredient_name'] = ' '.join(potential_name).strip(' ;,.-')
                    
                    # Only add if we have meaningful data
                    if any(val.strip() for val in entry.values()):
                        # Clean up the entry
                        for key in entry:
                            if len(entry[key]) > 100:  # Truncate very long entries
                                entry[key] = entry[key][:100] + "..."
                        
                        parsed_data.append(entry)
                        print(f"  Added entry: {entry}")
    
    return parsed_data

def extract_additives_from_text():
    """Alternative approach: extract additive information from text content"""
    pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    
    additives_list = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(min(50, len(pdf.pages))):  # Check first 50 pages
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text:
                # Look for patterns that might indicate additive listings
                lines = text.split('\n')
                
                for line_num, line in enumerate(lines):
                    # Look for INS numbers (E numbers) patterns
                    ins_pattern = r'(?:INS|E)\s*(\d{3,4}(?:\w)?)'
                    ins_matches = re.findall(ins_pattern, line, re.IGNORECASE)
                    
                    if ins_matches:
                        # Extract potential additive name from context
                        cleaned_line = re.sub(r'\s+', ' ', line.strip())
                        
                        for ins_match in ins_matches:
                            # Look for potential additive names near INS/E numbers
                            # Split by INS/E number and look at surrounding text
                            parts = re.split(r'(?:INS|E)\s*' + re.escape(ins_match), line, flags=re.IGNORECASE)
                            if len(parts) > 0:
                                # Look before the INS number
                                before_part = parts[0].strip()
                                if before_part:
                                    # Extract the last few words before INS number
                                    words = before_part.split()
                                    potential_name = ' '.join(words[-4:]) if len(words) >= 4 else ' '.join(words)
                                    
                                    if len(potential_name) > 2 and not potential_name.startswith('('):  # Valid name
                                        additive_entry = {
                                            'ingredient_name': potential_name.strip(),
                                            'ins_number': f"INS {ins_match}",
                                            'category': 'Food Additive',
                                            'permitted_limit': '',
                                            'remarks': cleaned_line[:100]  # First 100 chars as remark
                                        }
                                        
                                        additives_list.append(additive_entry)
                                        print(f"Found potential additive from text: {additive_entry}")
    
    return additives_list

def main():
    print("Starting extraction of additive information from PDF...")
    
    # Method 1: Extract from tables
    print("\n1. Looking for tables with additive information...")
    table_data = extract_additive_tables()
    
    print(f"\nFound {len(table_data)} potential tables with additive info")
    
    # Method 2: Parse the table data
    print("\n2. Parsing table data...")
    try:
        parsed_data = parse_additive_data(table_data)
    except Exception as e:
        print(f"Error parsing table data: {e}")
        parsed_data = []
    
    # Method 3: Extract from text as backup
    print("\n3. Extracting from text content...")
    text_extracted = extract_additives_from_text()
    
    # Combine all data
    combined_data = parsed_data + text_extracted
    
    print(f"\nTotal extracted entries: {len(combined_data)}")
    
    # Create DataFrame
    if combined_data:
        df = pd.DataFrame(combined_data, columns=['ingredient_name', 'ins_number', 'category', 'permitted_limit', 'remarks'])
        
        # Clean up the DataFrame
        df = df.drop_duplicates(subset=['ingredient_name', 'ins_number'], keep='first')
        
        print(f"\nFinal DataFrame shape: {df.shape}")
        print("\nFirst few rows:")
        print(df.head(10))
        
        # Save to CSV
        output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\fssai_additives.csv'
        
        # Create directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path, index=False)
        print(f"\nSaved to: {output_path}")
        
        return df
    else:
        print("No data extracted!")
        return pd.DataFrame(columns=['ingredient_name', 'ins_number', 'category', 'permitted_limit', 'remarks'])

if __name__ == "__main__":
    df = main()