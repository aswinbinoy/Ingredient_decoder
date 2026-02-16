import pandas as pd
import gzip
import os
import re
from collections import Counter


def load_fssai_safety_data():
    """
    Load our FSSAI safety data
    """
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
    
    return ingredient_to_safety


def create_heuristic_classifications():
    """
    Create heuristic classification rules for ingredients not in FSSAI database
    """
    # Known harmful ingredients
    known_harmful_keywords = [
        'bha', 'bht', 'tert-butylhydroquinone', 'potassium bromate',
        'sodium nitrite', 'butylated hydroxyanisole', 'butylated hydroxytoluene',
        'tbhq', 'trans fat', 'hydrogenated oil', 'partially hydrogenated'
    ]

    # Known moderate ingredients
    known_moderate_keywords = [
        'sodium benzoate', 'potassium sorbate', 'sulfite', 'sulphite',
        'tartrazine', 'sunset yellow', 'allura red', 'ponceau 4r',
        'acesulfame', 'aspartame', 'saccharin', 'neotame', 'cyclamate',
        'brilliant blue', 'indigotine', 'erythrosine', 'quinozoline yellow'
    ]

    # Common safe ingredients
    common_safe_ingredients = [
        'sugar', 'salt', 'water', 'oil', 'butter', 'milk', 'egg', 'flour',
        'citric acid', 'ascorbic acid', 'tocopherol', 'lecithin', 'pectin',
        'guar gum', 'xanthan gum', 'carrageenan', 'cellulose', 'starch',
        'honey', 'vanilla', 'cinnamon', 'pepper', 'garlic', 'onion'
    ]
    
    return known_harmful_keywords, known_moderate_keywords, common_safe_ingredients


def classify_ingredient_heuristic(ingredient_name, known_harmful_keywords, 
                                 known_moderate_keywords, common_safe_ingredients):
    """Classify ingredient based on keywords if not in safety database"""
    if pd.isna(ingredient_name) or ingredient_name.strip() == '':
        return 'Unknown', 'No safety data available'

    ing_lower = ingredient_name.lower().strip()

    # Check for harmful keywords
    for keyword in known_harmful_keywords:
        if keyword in ing_lower:
            return 'Harmful', f'Contains {keyword} which may pose health risks'

    # Check for moderate keywords
    for keyword in known_moderate_keywords:
        if keyword in ing_lower:
            return 'Moderate', f'Contains {keyword} which is safe within limits'

    # Check for common safe ingredients
    for safe_ing in common_safe_ingredients:
        if safe_ing in ing_lower:
            return 'Safe', f'{ingredient_name} is generally recognized as safe'

    # Default to Moderate for unknown ingredients (conservative approach)
    return 'Moderate', f'{ingredient_name} classification based on conservative assumption'


def parse_ingredients_from_text(ingredients_text):
    """
    Parse individual ingredients from ingredients text
    """
    if pd.isna(ingredients_text) or ingredients_text.strip() == '':
        return []
    
    # Normalize the text
    text = ingredients_text.lower().strip()
    
    # Common separators for ingredients
    separators = [',', ';', '•', '\\n', '\\r', '\\t']
    
    # Replace separators with a common delimiter
    for sep in separators:
        text = text.replace(sep, '|')
    
    # Handle parentheses which often contain additional info
    # Remove content in parentheses but keep the main ingredient
    import re
    text = re.sub(r'\([^)]*\)', '', text)  # Remove content in parentheses
    
    # Split and clean ingredients
    potential_ingredients = [ing.strip() for ing in text.split('|') if ing.strip()]
    
    # Further split on 'and' and '&' which often separate ingredients
    ingredients = []
    for ingr in potential_ingredients:
        # Split on 'and' and '&'
        sub_ings = re.split(r'\band\b|&', ingr)
        for sub_ing in sub_ings:
            sub_ing = sub_ing.strip()
            if sub_ing:
                ingredients.append(sub_ing)
    
    # Clean up ingredients - remove extra spaces and common prefixes/suffixes
    cleaned_ingredients = []
    for ingr in ingredients:
        # Remove common prefixes/suffixes
        ingr = re.sub(r'^contains\s*', '', ingr)
        ingr = re.sub(r'\s*contains$', '', ingr)
        ingr = re.sub(r'^with\s*', '', ingr)
        ingr = re.sub(r'\s*added$', '', ingr)
        ingr = re.sub(r'\s*preserved with.*$', '', ingr)
        ingr = re.sub(r'\s*emulsified with.*$', '', ingr)
        
        # Remove extra whitespace
        ingr = ' '.join(ingr.split())
        
        if len(ingr) > 1:  # Only include if meaningful length
            cleaned_ingredients.append(ingr)
    
    return cleaned_ingredients


def process_openfoodfacts_with_fssai_matching():
    """
    Process Open Food Facts data and classify ingredients using FSSAI as reference
    """
    print("Processing Open Food Facts data with FSSAI-based classification...")
    
    # Load FSSAI safety data
    ingredient_to_safety = load_fssai_safety_data()
    
    # Create heuristic classification rules
    known_harmful_keywords, known_moderate_keywords, common_safe_ingredients = create_heuristic_classifications()
    
    # Path to Open Food Facts data
    csv_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\en.openfoodfacts.org.products.csv.gz'
    
    classified_ingredients = []
    processed_count = 0
    max_products = 10000  # Limit for initial processing
    
    print("Reading Open Food Facts data...")
    
    # Read the file in chunks to handle large size
    chunk_size = 5000
    
    try:
        # First, let's try to detect the delimiter by reading a small sample
        with gzip.open(csv_path, 'rt', encoding='utf-8', errors='replace') as f:
            # Read first few lines to understand structure
            sample_lines = []
            for i in range(5):
                line = f.readline()
                if line:
                    sample_lines.append(line.strip())
        
        # Determine delimiter (likely tab or comma)
        first_line = sample_lines[0] if sample_lines else ""
        if '\t' in first_line:
            delimiter = '\t'
        else:
            delimiter = ','
            
        print(f"Detected delimiter: {delimiter}")
        
        # Now process the file with proper delimiter
        chunk_list = pd.read_csv(
            csv_path, 
            compression='gzip', 
            sep=delimiter, 
            chunksize=chunk_size,
            usecols=['ingredients_text', 'product_name', 'categories_en', 'additives_en'],
            low_memory=False
        )
        
        print("Processing chunks...")
        
        for chunk_idx, chunk in enumerate(chunk_list):
            print(f"Processing chunk {chunk_idx + 1}...")
            
            # Process each row in the chunk
            for idx, row in chunk.iterrows():
                ingredients_text = row.get('ingredients_text', '')
                
                if pd.notna(ingredients_text) and ingredients_text.strip() != '' and ingredients_text.lower() != 'nan':
                    # Parse individual ingredients from the text
                    parsed_ingredients = parse_ingredients_from_text(str(ingredients_text))
                    
                    # Process each parsed ingredient
                    for ingr in parsed_ingredients:
                        # Clean the ingredient name
                        ingr_clean = re.sub(r'[^\w\s\-]', ' ', ingr).strip()
                        
                        if len(ingr_clean) > 2:  # Skip very short entries
                            # Check if in our FSSAI safety database
                            if ingr_clean in ingredient_to_safety:
                                safety_info = ingredient_to_safety[ingr_clean]
                                classified_ingredients.append({
                                    'ingredient_name': ingr.title(),
                                    'original_ingredients_text': ingredients_text,
                                    'product_name': row.get('product_name', ''),
                                    'ins_number': safety_info['ins_number'],
                                    'category': safety_info['category'],
                                    'safety_category': safety_info['safety_category'],
                                    'safety_description': safety_info['safety_description'],
                                    'source': 'FSSAI_Match'
                                })
                            else:
                                # Use heuristic classification for unmatched ingredients
                                safety_cat, safety_desc = classify_ingredient_heuristic(
                                    ingr_clean, 
                                    known_harmful_keywords, 
                                    known_moderate_keywords, 
                                    common_safe_ingredients
                                )
                                
                                classified_ingredients.append({
                                    'ingredient_name': ingr.title(),
                                    'original_ingredients_text': ingredients_text,
                                    'product_name': row.get('product_name', ''),
                                    'ins_number': 'Not in FSSAI',
                                    'category': 'General Food Ingredient',
                                    'safety_category': safety_cat,
                                    'safety_description': safety_desc,
                                    'source': 'Heuristic_Classification'
                                })
                
                processed_count += 1
                
                # Limit processing for initial run
                if processed_count >= max_products:
                    print(f"Reached processing limit of {max_products} products")
                    break
            
            if processed_count >= max_products:
                break
        
        print(f"Processed {processed_count} products")
        
    except Exception as e:
        print(f"Error processing Open Food Facts data: {e}")
        print("Attempting alternative processing method...")
        
        # Alternative: Try reading with different parameters
        try:
            # Read with pandas, limiting to first 1000 rows for testing
            df_sample = pd.read_csv(
                csv_path, 
                compression='gzip', 
                nrows=1000,
                low_memory=False
            )
            
            print(f"Successfully loaded sample of {len(df_sample)} rows")
            print("Columns:", df_sample.columns.tolist())
            
            # Find ingredient-related columns
            ingredient_cols = [col for col in df_sample.columns if 'ingredient' in col.lower()]
            additive_cols = [col for col in df_sample.columns if 'additive' in col.lower()]
            
            print(f"Found ingredient columns: {ingredient_cols}")
            print(f"Found additive columns: {additive_cols}")
            
            # Process using the found columns
            for idx, row in df_sample.iterrows():
                for col in ingredient_cols:
                    ingredients_text = row.get(col, '')
                    
                    if pd.notna(ingredients_text) and str(ingredients_text).strip() != '':
                        parsed_ingredients = parse_ingredients_from_text(str(ingredients_text))
                        
                        for ingr in parsed_ingredients:
                            ingr_clean = re.sub(r'[^\w\s\-]', ' ', ingr).strip()
                            
                            if len(ingr_clean) > 2:
                                if ingr_clean in ingredient_to_safety:
                                    safety_info = ingredient_to_safety[ingr_clean]
                                    classified_ingredients.append({
                                        'ingredient_name': ingr.title(),
                                        'original_ingredients_text': ingredients_text,
                                        'product_name': row.get('product_name', ''),
                                        'ins_number': safety_info['ins_number'],
                                        'category': safety_info['category'],
                                        'safety_category': safety_info['safety_category'],
                                        'safety_description': safety_info['safety_description'],
                                        'source': 'FSSAI_Match'
                                    })
                                else:
                                    safety_cat, safety_desc = classify_ingredient_heuristic(
                                        ingr_clean, 
                                        known_harmful_keywords, 
                                        known_moderate_keywords, 
                                        common_safe_ingredients
                                    )
                                    
                                    classified_ingredients.append({
                                        'ingredient_name': ingr.title(),
                                        'original_ingredients_text': ingredients_text,
                                        'product_name': row.get('product_name', ''),
                                        'ins_number': 'Not in FSSAI',
                                        'category': 'General Food Ingredient',
                                        'safety_category': safety_cat,
                                        'safety_description': safety_desc,
                                        'source': 'Heuristic_Classification'
                                    })
        
        except Exception as e2:
            print(f"Alternative processing also failed: {e2}")
            print("Creating dataset with just FSSAI data as fallback...")
            
            # Create a sample dataset with our FSSAI data
            safety_df = pd.read_csv(r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv')
            for _, row in safety_df.iterrows():
                classified_ingredients.append({
                    'ingredient_name': row['ingredient_name'],
                    'original_ingredients_text': f"Sample product containing {row['ingredient_name']}",
                    'product_name': f"Sample Product with {row['ingredient_name']}",
                    'ins_number': row['ins_number'],
                    'category': row['category'],
                    'safety_category': row['safety_category'],
                    'safety_description': row['safety_description'],
                    'source': 'FSSAI_Regulation'
                })

    # Create DataFrame from classified ingredients
    if classified_ingredients:
        classified_df = pd.DataFrame(classified_ingredients)
        
        # Remove exact duplicates based on ingredient name and safety category
        classified_df = classified_df.drop_duplicates(
            subset=['ingredient_name', 'safety_category'], 
            keep='first'
        )
        
        print(f"\nClassified {len(classified_df)} unique ingredients")
        print(f"Safety category distribution:")
        print(classified_df['safety_category'].value_counts())
        
        # Calculate statistics
        total_classified = len(classified_df)
        fssai_matches = len(classified_df[classified_df['source'] == 'FSSAI_Match'])
        heuristic_classifications = len(classified_df[classified_df['source'] == 'Heuristic_Classification'])
        
        print(f"\nClassification sources:")
        print(f"FSSAI matches: {fssai_matches} ({fssai_matches/total_classified*100:.1f}%)")
        print(f"Heuristic classifications: {heuristic_classifications} ({heuristic_classifications/total_classified*100:.1f}%)")
        
        # Save the classified dataset
        output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\openfoodfacts_classified_ingredients.csv'
        classified_df.to_csv(output_path, index=False)
        print(f"\nClassified ingredients saved to: {output_path}")
        
        # Create and save summary
        summary_stats = classified_df.groupby(['safety_category', 'source']).size().unstack(fill_value=0)
        summary_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\classification_summary_detailed.csv'
        summary_stats.to_csv(summary_path)
        print(f"Detailed classification summary saved to: {summary_path}")
        
        # Show sample of results
        print("\nSample of classified data:")
        print(classified_df[['ingredient_name', 'safety_category', 'safety_description', 'source']].head(15))
        
        return classified_df
    else:
        print("No ingredients were classified")
        return pd.DataFrame()


def expand_classification_with_additional_sources():
    """
    Expand the classification by adding more ingredients from other datasets
    """
    print("\nExpanding classification with additional sources...")
    
    # Load previously classified data if it exists
    output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\openfoodfacts_classified_ingredients.csv'
    
    if os.path.exists(output_path):
        main_df = pd.read_csv(output_path)
        print(f"Loaded existing classified data with {len(main_df)} entries")
    else:
        main_df = pd.DataFrame()
        print("No existing classified data found, starting fresh")
    
    # Load additional safety databases if available
    additional_sources = []
    
    # Check for comprehensive safety DB
    comp_db_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\comprehensive_ingredient_safety_db.csv'
    if os.path.exists(comp_db_path):
        comp_db = pd.read_csv(comp_db_path)
        print(f"Found comprehensive DB with {len(comp_db)} entries")
        
        # Format to match our structure
        comp_formatted = comp_db.rename(columns={
            'ingredient_name': 'ingredient_name',
            'ins_number': 'ins_number', 
            'category': 'category',
            'safety_category': 'safety_category',
            'safety_description': 'safety_description'
        })[['ingredient_name', 'ins_number', 'category', 'safety_category', 'safety_description']]
        
        comp_formatted['original_ingredients_text'] = 'From comprehensive safety database'
        comp_formatted['product_name'] = 'N/A'
        comp_formatted['source'] = 'Comprehensive_DB'
        
        additional_sources.append(comp_formatted)
    
    # Combine all sources
    if additional_sources:
        all_sources = [main_df] + additional_sources
        combined_df = pd.concat(all_sources, ignore_index=True, sort=False)
        
        # Remove duplicates keeping FSSAI matches when available
        combined_df = combined_df.sort_values('source')  # Sort to prioritize certain sources
        combined_df = combined_df.drop_duplicates(subset=['ingredient_name'], keep='first')
        
        # Save expanded dataset
        expanded_output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\expanded_ingredient_classification.csv'
        combined_df.to_csv(expanded_output_path, index=False)
        print(f"Expanded classification saved to: {expanded_output_path}")
        print(f"Total ingredients in expanded dataset: {len(combined_df)}")
        
        return combined_df
    else:
        return main_df


if __name__ == "__main__":
    # Process Open Food Facts with FSSAI matching
    classified_df = process_openfoodfacts_with_fssai_matching()
    
    # Expand with additional sources
    expanded_df = expand_classification_with_additional_sources()
    
    print("\nOpen Food Facts ingredient classification completed!")
    print(f"Final dataset contains {len(expanded_df)} classified ingredients")