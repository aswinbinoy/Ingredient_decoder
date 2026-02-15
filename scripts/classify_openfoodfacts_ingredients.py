import pandas as pd
import gzip
import os
import re
from collections import Counter

def process_openfoodfacts_and_classify():
    """
    Process Open Food Facts data and classify ingredients as Safe/Moderate/Harmful
    """
    print("Processing Open Food Facts data and classifying ingredients...")
    
    # Load our FSSAI safety data
    safety_df = pd.read_csv(r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv')
    print(f"FSSAI safety data shape: {safety_df.shape}")
    
    # Create ingredient to safety mapping
    ingredient_to_safety = {}
    for _, row in safety_df.iterrows():
        ingredient_name = row['ingredient_name'].lower().strip()
        ingredient_to_safety[ingredient_name] = {
            'ins_number': row['ins_number'],
            'category': row['category'],
            'safety_category': row['safety_category'],
            'safety_description': row['safety_description']
        }
    
    # For ingredients not in our safety database, we'll use heuristics
    # Based on common knowledge of food additives
    known_harmful_keywords = [
        'bha', 'bht', 'tert-butylhydroquinone', 'potassium bromate', 
        'sodium nitrite', 'butylated hydroxyanisole', 'butylated hydroxytoluene'
    ]
    
    known_moderate_keywords = [
        'sodium benzoate', 'potassium sorbate', 'sulfite', 'sulphite',
        'tartrazine', 'sunset yellow', 'allura red', 'ponceau 4r'
    ]
    
    def classify_ingredient_heuristic(ingredient_name):
        """Classify ingredient based on keywords if not in safety database"""
        if pd.isna(ingredient_name):
            return 'Unknown', 'No safety data available'
        
        ing_lower = ingredient_name.lower()
        
        # Check for harmful keywords
        for keyword in known_harmful_keywords:
            if keyword in ing_lower:
                return 'Harmful', f'Contains {keyword} which may pose health risks'
        
        # Check for moderate keywords
        for keyword in known_moderate_keywords:
            if keyword in ing_lower:
                return 'Moderate', f'Contains {keyword} which is safe within limits'
        
        # Default to Safe for common food ingredients
        common_safe_ingredients = [
            'sugar', 'salt', 'water', 'oil', 'butter', 'milk', 'egg', 'flour',
            'citric acid', 'ascorbic acid', 'tocopherol', 'lecithin', 'pectin',
            'guar gum', 'xanthan gum', 'carrageenan'
        ]
        
        for safe_ing in common_safe_ingredients:
            if safe_ing in ing_lower:
                return 'Safe', f'{ingredient_name} is generally recognized as safe'
        
        # If uncertain, default to Moderate (conservative approach)
        return 'Moderate', f'{ingredient_name} classification based on conservative assumption'
    
    # Process Open Food Facts data in chunks to handle large file
    csv_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\en.openfoodfacts.org.products.csv.gz'
    
    # Define columns of interest
    needed_columns = ['ingredients_text', 'product_name', 'categories_en', 'additives_en']
    
    classified_ingredients = []
    
    print("Processing Open Food Facts data (this may take a moment)...")
    
    # Read the file in chunks to handle large size
    chunk_size = 10000
    chunk_count = 0
    
    try:
        with gzip.open(csv_path, 'rt', encoding='utf-8', errors='replace') as f:
            # Read header
            header_line = f.readline().strip()
            all_columns = header_line.split(',')
            
            # Find indices of needed columns
            needed_indices = []
            needed_col_names = []
            for col in needed_columns:
                if col in all_columns:
                    needed_indices.append(all_columns.index(col))
                    needed_col_names.append(col)
            
            print(f"Found columns: {needed_col_names}")
            
            # Process data in chunks
            chunk_lines = []
            line_count = 0
            
            for line in f:
                chunk_lines.append(line)
                line_count += 1
                
                if line_count >= chunk_size:
                    # Process this chunk
                    for chunk_line in chunk_lines:
                        values = chunk_line.rstrip().split('\t') if '\t' in chunk_line else chunk_line.rstrip().split(',')
                        
                        # Extract needed values
                        if len(values) >= len(all_columns):
                            row_data = {}
                            for col_name, idx in zip(needed_col_names, needed_indices):
                                if idx < len(values):
                                    row_data[col_name] = values[idx]
                                else:
                                    row_data[col_name] = ''
                            
                            # Process ingredients text
                            ingredients_text = row_data.get('ingredients_text', '')
                            if ingredients_text and ingredients_text.lower() != 'nan':
                                # Extract individual ingredients
                                # Split by common separators
                                separators = [',', ';', 'and', '&', '(']
                                temp_text = ingredients_text.lower()
                                
                                for sep in separators:
                                    temp_text = temp_text.replace(sep, '|')
                                
                                individual_ingredients = [ing.strip() for ing in temp_text.split('|') if ing.strip()]
                                
                                # Process each ingredient
                                for ingr in individual_ingredients:
                                    # Clean the ingredient name
                                    ingr_clean = re.sub(r'[^\w\s]', '', ingr).strip()
                                    if len(ingr_clean) > 2:  # Skip very short entries
                                        # Check if in our safety database
                                        if ingr_clean in ingredient_to_safety:
                                            safety_info = ingredient_to_safety[ingr_clean]
                                            classified_ingredients.append({
                                                'ingredient_name': ingr.title(),
                                                'original_ingredient_text': ingredients_text,
                                                'product_name': row_data.get('product_name', ''),
                                                'ins_number': safety_info['ins_number'],
                                                'category': safety_info['category'],
                                                'safety_category': safety_info['safety_category'],
                                                'safety_description': safety_info['safety_description'],
                                                'source': 'FSSAI_Match'
                                            })
                                        else:
                                            # Use heuristic classification
                                            safety_cat, safety_desc = classify_ingredient_heuristic(ingr_clean)
                                            classified_ingredients.append({
                                                'ingredient_name': ingr.title(),
                                                'original_ingredient_text': ingredients_text,
                                                'product_name': row_data.get('product_name', ''),
                                                'ins_number': 'Not in FSSAI',
                                                'category': 'General Food Ingredient',
                                                'safety_category': safety_cat,
                                                'safety_description': safety_desc,
                                                'source': 'Heuristic_Classification'
                                            })
                    
                    # Reset for next chunk
                    chunk_lines = []
                    line_count = 0
                    chunk_count += 1
                    print(f"Processed chunk {chunk_count}")
                    
                    # For demo purposes, let's stop after a few chunks
                    if chunk_count >= 2:  # Just process first 2 chunks for demo
                        break
            
            # Process remaining lines in the last chunk
            for chunk_line in chunk_lines:
                values = chunk_line.rstrip().split('\t') if '\t' in chunk_line else chunk_line.rstrip().split(',')
                
                # Extract needed values
                if len(values) >= len(all_columns):
                    row_data = {}
                    for col_name, idx in zip(needed_col_names, needed_indices):
                        if idx < len(values):
                            row_data[col_name] = values[idx]
                        else:
                            row_data[col_name] = ''
                    
                    # Process ingredients text
                    ingredients_text = row_data.get('ingredients_text', '')
                    if ingredients_text and ingredients_text.lower() != 'nan':
                        # Extract individual ingredients
                        separators = [',', ';', 'and', '&', '(']
                        temp_text = ingredients_text.lower()
                        
                        for sep in separators:
                            temp_text = temp_text.replace(sep, '|')
                        
                        individual_ingredients = [ing.strip() for ing in temp_text.split('|') if ing.strip()]
                        
                        # Process each ingredient
                        for ingr in individual_ingredients:
                            # Clean the ingredient name
                            ingr_clean = re.sub(r'[^\w\s]', '', ingr).strip()
                            if len(ingr_clean) > 2:  # Skip very short entries
                                # Check if in our safety database
                                if ingr_clean in ingredient_to_safety:
                                    safety_info = ingredient_to_safety[ingr_clean]
                                    classified_ingredients.append({
                                        'ingredient_name': ingr.title(),
                                        'original_ingredient_text': ingredients_text,
                                        'product_name': row_data.get('product_name', ''),
                                        'ins_number': safety_info['ins_number'],
                                        'category': safety_info['category'],
                                        'safety_category': safety_info['safety_category'],
                                        'safety_description': safety_info['safety_description'],
                                        'source': 'FSSAI_Match'
                                    })
                                else:
                                    # Use heuristic classification
                                    safety_cat, safety_desc = classify_ingredient_heuristic(ingr_clean)
                                    classified_ingredients.append({
                                        'ingredient_name': ingr.title(),
                                        'original_ingredient_text': ingredients_text,
                                        'product_name': row_data.get('product_name', ''),
                                        'ins_number': 'Not in FSSAI',
                                        'category': 'General Food Ingredient',
                                        'safety_category': safety_cat,
                                        'safety_description': safety_desc,
                                        'source': 'Heuristic_Classification'
                                    })
    
    except Exception as e:
        print(f"Error processing Open Food Facts data: {e}")
        print("Creating dataset with just FSSAI data and sample classifications...")
        
        # Create a sample dataset with our FSSAI data and some examples
        for _, row in safety_df.head(20).iterrows():  # Use first 20 as example
            classified_ingredients.append({
                'ingredient_name': row['ingredient_name'],
                'original_ingredient_text': f"Sample product containing {row['ingredient_name']}",
                'product_name': f"Sample Product with {row['ingredient_name']}",
                'ins_number': row['ins_number'],
                'category': row['category'],
                'safety_category': row['safety_category'],
                'safety_description': row['safety_description'],
                'source': 'FSSAI_Regulation'
            })
    
    # Create DataFrame
    if classified_ingredients:
        classified_df = pd.DataFrame(classified_ingredients)
        
        # Remove duplicates based on ingredient name
        classified_df = classified_df.drop_duplicates(subset=['ingredient_name'], keep='first')
        
        print(f"Classified {len(classified_df)} unique ingredients")
        print(f"Safety category distribution:")
        print(classified_df['safety_category'].value_counts())
        
        # Save the classified dataset
        output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\openfoodfacts_classified_ingredients.csv'
        classified_df.to_csv(output_path, index=False)
        print(f"Classified ingredients saved to: {output_path}")
        
        # Also create a summary file
        summary_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_classification_summary.csv'
        summary_df = classified_df.groupby('safety_category').agg({
            'ingredient_name': 'count',
            'safety_description': 'first'
        }).rename(columns={'ingredient_name': 'count'})
        summary_df.to_csv(summary_path)
        print(f"Classification summary saved to: {summary_path}")
        
        print("\nSample of classified data:")
        print(classified_df[['ingredient_name', 'safety_category', 'safety_description', 'source']].head(10))
        
        return classified_df
    else:
        print("No ingredients were classified")
        return pd.DataFrame()

if __name__ == "__main__":
    df = process_openfoodfacts_and_classify()
    print("\nOpen Food Facts ingredient classification completed!")