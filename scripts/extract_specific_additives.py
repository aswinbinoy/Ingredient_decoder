import pdfplumber
import pandas as pd
import re
import os

def extract_specific_additive_info():
    """
    Extract specific additive information from the PDF focusing on 
    Common Name, INS No., and related information
    """
    pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    
    additives_list = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text:
                # Look for patterns indicating additive information
                # Pattern 1: "Common Name" followed by substance name, then "INS No." followed by number
                # Find all occurrences of "Common Name" and extract the following information
                
                lines = text.split('\n')
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    if 'common name' in line.lower():
                        # Extract the substance name from this line
                        parts = re.split(r'common name', line, flags=re.IGNORECASE)
                        if len(parts) > 1:
                            # The substance name comes after "Common Name"
                            name_part = parts[1].strip()
                            if name_part:
                                # Look for INS number in the next few lines
                                for j in range(i + 1, min(i + 8, len(lines))):
                                    next_line = lines[j].strip()
                                    # Look for INS No. pattern
                                    ins_match = re.search(r'ins\s+no\.?\s*(\d{3,4}(?:\([ivx]+\))?)', next_line, re.IGNORECASE)
                                    if ins_match:
                                        substance_name = name_part
                                        ins_number = f"INS {ins_match.group(1)}"
                                        
                                        # Look for category information in nearby lines
                                        category = "Food Additive"
                                        for k in range(max(0, i-2), min(len(lines), i+10)):
                                            nearby_line = lines[k].lower()
                                            if 'colour' in nearby_line or 'color' in nearby_line:
                                                category = "Food Colour"
                                            elif 'preserv' in nearby_line:
                                                category = "Preservative"
                                            elif 'antioxid' in nearby_line:
                                                category = "Antioxidant"
                                            elif 'emulsifier' in nearby_line or 'stabiliz' in nearby_line:
                                                category = "Emulsifier/Stabilizer"
                                        
                                        additive_entry = {
                                            'ingredient_name': substance_name.strip(' :;'),
                                            'ins_number': ins_number,
                                            'category': category,
                                            'permitted_limit': '',  # Will try to find this later
                                            'remarks': f'Page {page_num + 1}'
                                        }
                                        additives_list.append(additive_entry)
                                        break
                    i += 1
    
    return additives_list

def extract_permissible_limits():
    """
    Extract permissible limits from the document
    """
    pdf_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\Chapter 3_Substances added to food(1).pdf'
    
    limits_info = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text:
                # Look for usage level tables
                if 'usage level' in text.lower() or 'maximum' in text.lower():
                    # Look for tables with usage information
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            # Check if table has usage-related headers
                            header = table[0] if table else []
                            header_str = " ".join([str(h) if h else "" for h in header]).lower()
                            
                            if 'usage' in header_str or 'maximum' in header_str or 'level' in header_str:
                                for row in table[1:]:  # Skip header
                                    if len(row) >= 3:
                                        limits_info.append({
                                            'category': str(row[0]) if row[0] else '',
                                            'usage_level': str(row[1]) if row[1] else '',
                                            'max_level': str(row[2]) if row[2] else '',
                                            'page': page_num + 1
                                        })
    
    return limits_info

def main():
    print("Extracting specific additive information from PDF...")
    
    # Extract additive names and INS numbers
    additives_data = extract_specific_additive_info()
    
    print(f"Found {len(additives_data)} additives")
    
    # Extract permissible limits
    limits_data = extract_permissible_limits()
    
    print(f"Found {len(limits_data)} limit entries")
    
    # Create DataFrame
    if additives_data:
        df = pd.DataFrame(additives_data, columns=['ingredient_name', 'ins_number', 'category', 'permitted_limit', 'remarks'])
        
        # Add limit information if available
        for limit_info in limits_data:
            # Try to match limit info with existing additives
            pass  # For now, we'll just store the basic info
        
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