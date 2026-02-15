import pandas as pd
import gzip
import os
from io import TextIOWrapper

def combine_fssai_and_openfoodfacts():
    """
    Properly combine FSSAI data with Open Food Facts data
    """
    print("Starting to combine FSSAI and Open Food Facts datasets...")
    
    # Load the FSSAI data we created
    fssai_df = pd.read_csv(r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv')
    print(f"FSSAI data shape: {fssai_df.shape}")
    
    # Load Open Food Facts data - only load relevant columns to manage memory
    csv_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\en.openfoodfacts.org.products.csv.gz'
    
    # Define the columns we need from Open Food Facts
    needed_columns = [
        'ingredients_text', 
        'ingredients_tags', 
        'additives_en', 
        'additives_tags',
        'product_name',
        'categories_en'
    ]
    
    print("Reading Open Food Facts data (this may take a moment)...")
    
    # Read the CSV with only needed columns
    try:
        # First, let's try to read just a sample to understand the structure
        with gzip.open(csv_path, 'rt', encoding='utf-8', errors='replace') as f:
            # Read header to identify columns
            header = f.readline().strip()
            columns = header.split(',')
            
            # Find intersection of needed columns with available columns
            available_needed_cols = [col for col in needed_columns if col in columns]
            print(f"Available needed columns: {available_needed_cols}")
            
            # Get indices of needed columns
            col_indices = [columns.index(col) for col in available_needed_cols]
            
            # Read a sample of the data
            sample_lines = []
            for i, line in enumerate(f):
                if i >= 1000:  # Just read first 1000 lines for sample
                    break
                sample_lines.append(line)
        
        # Process the sample lines
        sample_data = []
        for line in sample_lines:
            values = line.rstrip().split(',')
            # Ensure we have enough values
            if len(values) >= len(columns):
                row_data = {col: values[idx] if idx < len(values) else '' 
                           for col, idx in zip(available_needed_cols, col_indices)}
                sample_data.append(row_data)
        
        openfoodfacts_df = pd.DataFrame(sample_data)
        print(f"Open Food Facts sample shape: {openfoodfacts_df.shape}")
        
        # Clean and process the Open Food Facts data
        # Keep only rows with non-empty ingredients
        openfoodfacts_df = openfoodfacts_df[
            openfoodfacts_df['ingredients_text'].notna() & 
            (openfoodfacts_df['ingredients_text'] != '')
        ].copy()
        
        print(f"After filtering for non-empty ingredients: {openfoodfacts_df.shape}")
        
        # Now merge with FSSAI data based on ingredient names
        # Create a combined dataset by linking ingredients from both sources
        
        # For each ingredient in Open Food Facts, try to match with FSSAI data
        def match_safety_info(ingredients_text):
            if pd.isna(ingredients_text):
                return pd.Series(['Unknown', 'Unknown', 'Unknown', 'No safety data available'])
            
            ingredients_lower = ingredients_text.lower()
            safety_matches = []
            
            # Look for matches in FSSAI data
            for _, fssai_row in fssai_df.iterrows:
                ingredient_name = fssai_row['ingredient_name'].lower()
                if ingredient_name in ingredients_lower:
                    safety_matches.append({
                        'ingredient': fssai_row['ingredient_name'],
                        'ins_number': fssai_row['ins_number'],
                        'category': fssai_row['category'],
                        'safety_category': fssai_row['safety_category'],
                        'safety_description': fssai_row['safety_description']
                    })
            
            if safety_matches:
                # Return the first match for simplicity
                match = safety_matches[0]
                return pd.Series([
                    match['ins_number'],
                    match['category'],
                    match['safety_category'],
                    match['safety_description']
                ])
            else:
                return pd.Series(['Unknown', 'Unknown', 'Unknown', 'No safety data available'])
        
        # Apply matching function
        print("Matching ingredients with safety data...")
        result = openfoodfacts_df['ingredients_text'].apply(match_safety_info)
        
        # Assign the results to new columns
        openfoodfacts_df['matched_ins_number'] = result.iloc[:, 0].values
        openfoodfacts_df['matched_category'] = result.iloc[:, 1].values
        openfoodfacts_df['matched_safety_category'] = result.iloc[:, 2].values
        openfoodfacts_df['matched_safety_description'] = result.iloc[:, 3].values
        
        # Create the combined dataset
        combined_df = openfoodfacts_df.copy()
        
        print(f"Combined dataset shape: {combined_df.shape}")
        print("Sample of combined data:")
        print(combined_df[['ingredients_text', 'matched_safety_category', 'matched_ins_number']].head())
        
        # Save the combined dataset
        output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\combined_ingredient_data.csv'
        combined_df.to_csv(output_path, index=False)
        print(f"Combined dataset saved to: {output_path}")
        
        # Also create a summary dataset that combines both sources
        # Add FSSAI data as reference for the ingredient decoder
        fssai_extended = fssai_df.copy()
        fssai_extended['source'] = 'FSSAI_Regulation'
        fssai_extended.rename(columns={
            'safety_category': 'safety_category',
            'safety_description': 'safety_description'
        }, inplace=True)
        
        # Create a similar structure for matched Open Food Facts data
        of_matched = combined_df[
            combined_df['matched_safety_category'] != 'Unknown'
        ][[
            'ingredients_text', 
            'matched_ins_number', 
            'matched_category', 
            'matched_safety_category', 
            'matched_safety_description'
        ]].copy()
        
        of_matched.columns = [
            'ingredient_name', 
            'ins_number', 
            'category', 
            'safety_category', 
            'safety_description'
        ]
        of_matched['source'] = 'OpenFoodFacts'
        
        # Combine both datasets
        final_combined = pd.concat([fssai_extended, of_matched], ignore_index=True)
        
        # Remove duplicates based on ingredient name
        final_combined = final_combined.drop_duplicates(
            subset=['ingredient_name'], 
            keep='first'
        )
        
        final_output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\final_combined_ingredient_data.csv'
        final_combined.to_csv(final_output_path, index=False)
        print(f"Final combined dataset saved to: {final_output_path}")
        print(f"Final dataset shape: {final_combined.shape}")
        
        return final_combined
        
    except Exception as e:
        print(f"Error processing Open Food Facts data: {e}")
        print("Creating combined dataset with just FSSAI data...")
        
        # If there are issues with Open Food Facts, at least save the FSSAI data
        fssai_extended = fssai_df.copy()
        fssai_extended['source'] = 'FSSAI_Regulation'
        fssai_extended.to_csv(
            r'C:\code\llm_project\Ingredient_decoder\data\processed\final_combined_ingredient_data.csv', 
            index=False
        )
        return fssai_df

if __name__ == "__main__":
    combined_data = combine_fssai_and_openfoodfacts()
    print("Dataset combination process completed!")