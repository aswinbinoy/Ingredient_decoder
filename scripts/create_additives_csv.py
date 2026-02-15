import pdfplumber
import pandas as pd
import re
import os

def extract_additive_tables():
    pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    
    print("Looking for additive tables in the PDF...")
    
    with pdfplumber.open(pdf_path) as pdf:
        all_tables_data = []
        
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if table and len(table) > 0:  # If table is not empty
                    # Check if this looks like an additive table
                    # Look for keywords that suggest additive info
                    flat_table = [cell for row in table for cell in row if cell]
                    text_content = " ".join([str(cell) for cell in flat_table if cell and str(cell).strip()]).lower()
                    
                    if any(keyword in text_content for keyword in ['ins', 'e', 'additive', 'sl. no.', 'no.', 'substance', 'food', 'common name', 'synonyms', 'characteristic', 'requirement']):
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
    # Convert to string and remove special characters
    text = str(text).strip().replace('\n', ' ').replace('\r', ' ')
    # Remove non-printable characters
    text = ''.join(char for char in text if ord(char) < 127 or char in ' \t\n\r')
    return text

def parse_additive_data(all_tables_data):
    """Parse the tables to extract additive information"""
    parsed_data = []
    
    for table_info in all_tables_data:
        table = table_info['data']
        page = table_info['page']
        
        if table and len(table) > 0:
            header_row = table[0]
            
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
                    elif 'ins' in col_text or 'e' in col_text or 'no.' in col_text.replace('.', ''):
                        col_mapping['ins_number'] = idx
                    elif 'category' in col_text or 'class' in col_text:
                        col_mapping['category'] = idx
                    elif 'limit' in col_text or 'level' in col_text or 'permitted' in col_text or 'usage' in col_text:
                        col_mapping['permitted_limit'] = idx
            
            # Extract data rows (skip header)
            for row_idx, row in enumerate(table[1:], 1):
                if len(row) > 0:
                    # Create entry with safe indexing
                    entry = {
                        'ingredient_name': clean_text(row[col_mapping.get('ingredient_name', 0)]) if col_mapping.get('ingredient_name') is not None and col_mapping.get('ingredient_name') < len(row) else "",
                        'ins_number': clean_text(row[col_mapping.get('ins_number', 1)]) if col_mapping.get('ins_number') is not None and col_mapping['ins_number'] < len(row) else "",
                        'category': clean_text(row[col_mapping.get('category', 2)]) if col_mapping.get('category') is not None and col_mapping['category'] < len(row) else "",
                        'permitted_limit': clean_text(row[col_mapping.get('permitted_limit', 3)]) if col_mapping.get('permitted_limit') is not None and col_mapping['permitted_limit'] < len(row) else "",
                        'remarks': clean_text(row[min(len(row)-1, 4)]) if len(row) > 4 else ""
                    }
                    
                    # Additional check: if we don't have a good mapping, try to infer from row content
                    if not entry['ingredient_name'] and len(row) > 0:
                        # Look for common additive names in the row
                        row_text = " ".join([clean_text(cell) for cell in row if cell and clean_text(str(cell))])
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
    
    return parsed_data

def extract_additives_from_specific_pages():
    """Extract additives from known pages with common name and INS number tables"""
    pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    
    additives_list = []
    
    with pdfplumber.open(pdf_path) as pdf:
        # Look for pages that likely contain additive names and INS numbers
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text:
                # Look for patterns like "Common Name" followed by substance name and INS number
                lines = text.split('\n')
                
                for line_num, line in enumerate(lines):
                    # Look for common additive names and INS numbers
                    # Pattern: Common Name followed by substance, then INS No. followed by number
                    if 'common name' in line.lower():
                        # Get next few lines to find the corresponding INS number
                        for next_line_idx in range(line_num + 1, min(line_num + 5, len(lines))):
                            next_line = lines[next_line_idx]
                            ins_match = re.search(r'ins\s+no\.?\s*(\d{3,4}(?:\(\w+\))?)', next_line, re.IGNORECASE)
                            if ins_match:
                                # Extract the substance name from the original line
                                name_match = re.split(r'common name', line, flags=re.IGNORECASE)
                                if len(name_match) > 1:
                                    substance_name = name_match[1].strip().split('\n')[0].strip()
                                    if len(substance_name) > 2:  # Valid name
                                        additive_entry = {
                                            'ingredient_name': clean_text(substance_name),
                                            'ins_number': f"INS {ins_match.group(1)}",
                                            'category': 'Food Additive',
                                            'permitted_limit': '',
                                            'remarks': clean_text(line[:100])
                                        }
                                        additives_list.append(additive_entry)
                                        break  # Found the INS number, move to next line
    
    return additives_list

def main():
    print("Starting extraction of additive information from PDF...")
    
    # Method 1: Extract from tables
    print("Looking for tables with additive information...")
    table_data = extract_additive_tables()
    
    print(f"Found {len(table_data)} potential tables with additive info")
    
    # Method 2: Parse the table data
    print("Parsing table data...")
    try:
        parsed_data = parse_additive_data(table_data)
    except Exception as e:
        print(f"Error parsing table data: {e}")
        parsed_data = []
    
    # Method 3: Extract from specific pages with known patterns
    print("Extracting from specific pages...")
    specific_extracted = extract_additives_from_specific_pages()
    
    # Combine all data
    combined_data = parsed_data + specific_extracted
    
    print(f"Total extracted entries: {len(combined_data)}")
    
    # Create DataFrame
    if combined_data:
        df = pd.DataFrame(combined_data, columns=['ingredient_name', 'ins_number', 'category', 'permitted_limit', 'remarks'])
        
        # Clean up the DataFrame
        df = df.drop_duplicates(subset=['ingredient_name', 'ins_number'], keep='first')
        df = df[df['ingredient_name'].str.len() > 0]  # Remove empty ingredient names
        
        print(f"Final DataFrame shape: {df.shape}")
        print("\nFirst few rows:")
        print(df.head(10))
        
        # Save to CSV
        output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\fssai_additives.csv'
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\nSaved to: {output_path}")
        
        return df
    else:
        print("No data extracted!")
        # Create an empty DataFrame with the required columns
        df = pd.DataFrame(columns=['ingredient_name', 'ins_number', 'category', 'permitted_limit', 'remarks'])
        output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\fssai_additives.csv'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Created empty CSV at: {output_path}")
        return df

if __name__ == "__main__":
    df = main()