import pandas as pd
import gzip
import os

def combine_datasets():
    print("Combining datasets...")
    
    # Load the FSSAI additives data we created
    fssai_df = pd.read_csv(r'C:\code\llm_project\Ingredient_decoder\data\processed\fssai_additives.csv')
    print(f"FSSAI data shape: {fssai_df.shape}")
    print("FSSAI columns:", fssai_df.columns.tolist())
    
    # Load the Open Food Facts data
    csv_path = r'C:\code\llm_project\Ingredient_decoder\data\raw\en.openfoodfacts.org.products.csv.gz'
    
    # Read first few lines to understand the structure
    with gzip.open(csv_path, 'rt', encoding='utf-8', errors='ignore') as f:
        # Read first 1000 lines to get an idea of the data
        lines = []
        for i, line in enumerate(f):
            lines.append(line)
            if i >= 1000:  # Just read first 1000 lines to understand structure
                break
    
    # Join the lines and create a DataFrame from a sample
    sample_text = ''.join(lines)
    with open('temp_sample.csv', 'w', encoding='utf-8') as temp_file:
        temp_file.write(sample_text)
    
    # Read the sample to understand column structure
    sample_df = pd.read_csv('temp_sample.csv', nrows=100)  # Read first 100 rows as sample
    print(f"Open Food Facts sample shape: {sample_df.shape}")
    print("Open Food Facts columns:", sample_df.columns.tolist())
    
    # Key columns we're interested in from Open Food Facts
    # The most relevant column for ingredients is 'ingredients_text'
    ingredients_col = 'ingredients_text'
    additives_col = 'additives_en'  # Contains additives in English
    
    if ingredients_col in sample_df.columns:
        print(f"\nSample ingredients from Open Food Facts:")
        sample_ingredients = sample_df[ingredients_col].dropna().head(10)
        for i, ingr in enumerate(sample_ingredients):
            print(f"{i+1}: {ingr[:100]}...")  # First 100 chars
    
    if additives_col in sample_df.columns:
        print(f"\nSample additives from Open Food Facts:")
        sample_additives = sample_df[additives_col].dropna().head(10)
        for i, add in enumerate(sample_additives):
            print(f"{i+1}: {add}")
    
    # Clean up temporary file
    os.remove('temp_sample.csv')
    
    # Create a safety classification mapping based on FSSAI data
    # Since we don't have explicit safety ratings in the FSSAI data, 
    # we'll create a basic classification system
    def classify_safety(ins_number):
        # This is a simplified classification - in a real system, 
        # you would have more detailed safety information
        if pd.isna(ins_number) or ins_number == '':
            return 'Unknown'
        # For now, we'll classify all listed additives as 'Moderate' (generally recognized as safe with limits)
        return 'Moderate'
    
    # Apply safety classification to FSSAI data
    fssai_df['safety_classification'] = fssai_df['ins_number'].apply(classify_safety)
    
    print(f"\nFSSAI data with safety classifications:")
    print(fssai_df[['ingredient_name', 'ins_number', 'category', 'safety_classification']].head(10))
    
    # Save the combined/processed data
    output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\merged_ingredient_data.csv'
    fssai_df.to_csv(output_path, index=False)
    print(f"\nSaved processed data to: {output_path}")
    
    # Also create a simplified version for the ingredient decoder model
    simplified_df = fssai_df[['ingredient_name', 'ins_number', 'category', 'safety_classification']].copy()
    simplified_df.columns = ['ingredient_name', 'ins_number', 'category', 'safety_category']
    
    # Add some example safety descriptions
    def get_safety_description(category):
        if category == 'Safe':
            return 'Generally recognized as safe for consumption'
        elif category == 'Moderate':
            return 'Safe when consumed within recommended limits'
        elif category == 'Harmful':
            return 'Should be avoided or consumed with caution'
        else:
            return 'Safety classification not determined'
    
    simplified_df['safety_description'] = simplified_df['safety_category'].apply(get_safety_description)
    
    # Save simplified dataset
    simple_output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv'
    simplified_df.to_csv(simple_output_path, index=False)
    print(f"Saved simplified safety data to: {simple_output_path}")
    
    print(f"\nFinal simplified dataset shape: {simplified_df.shape}")
    print(simplified_df.head(10))
    
    return simplified_df

if __name__ == "__main__":
    df = combine_datasets()