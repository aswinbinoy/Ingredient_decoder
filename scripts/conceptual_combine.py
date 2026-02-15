import pandas as pd
import os

def create_combined_dataset_concept():
    """
    Create a conceptual combined dataset showing how FSSAI and Open Food Facts
    data could be integrated in the future
    """
    print("Creating conceptual combined dataset...")
    
    # Load our FSSAI-based safety data
    safety_df = pd.read_csv(r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv')
    print(f"FSSAI safety data shape: {safety_df.shape}")
    
    # Create a mapping of ingredients to safety info
    ingredient_to_safety = {}
    for _, row in safety_df.iterrows():
        ingredient_name = row['ingredient_name'].lower().strip()
        ingredient_to_safety[ingredient_name] = {
            'ins_number': row['ins_number'],
            'category': row['category'],
            'safety_category': row['safety_category'],
            'safety_description': row['safety_description']
        }
    
    # Create a sample of how Open Food Facts data might be processed
    # (In reality, this would require processing the full large dataset)
    sample_ingredients = [
        'sugar', 'salt', 'wheat flour', 'milk', 'egg', 'soy lecithin',
        'citric acid', 'sodium benzoate', 'titanium dioxide', 'vanilla extract'
    ]
    
    # Match sample ingredients with safety info
    matched_data = []
    for ingr in sample_ingredients:
        safety_info = ingredient_to_safety.get(ingr, {
            'ins_number': 'Unknown',
            'category': 'Unknown', 
            'safety_category': 'Unknown',
            'safety_description': 'No safety data available'
        })
        
        matched_data.append({
            'ingredient_name': ingr.title(),
            'ins_number': safety_info['ins_number'],
            'category': safety_info['category'],
            'safety_category': safety_info['safety_category'],
            'safety_description': safety_info['safety_description'],
            'source': 'Matched_FSSAI' if safety_info['ins_number'] != 'Unknown' else 'Not_found_in_FSSAI'
        })
    
    # Convert to DataFrame
    matched_df = pd.DataFrame(matched_data)
    
    # Combine with our existing FSSAI data
    combined_df = pd.concat([safety_df, matched_df], ignore_index=True)
    
    # Remove duplicates keeping the original FSSAI data
    combined_df = combined_df.drop_duplicates(subset=['ingredient_name'], keep='first')
    
    # Save the combined dataset
    output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\final_combined_ingredient_data.csv'
    combined_df.to_csv(output_path, index=False)
    
    print(f"Combined dataset shape: {combined_df.shape}")
    print("Sample of combined data:")
    print(combined_df.head(10))
    
    print(f"\nDataset saved to: {output_path}")
    
    # Show summary
    print(f"\nSafety category distribution:")
    print(combined_df['safety_category'].value_counts())
    
    return combined_df

if __name__ == "__main__":
    df = create_combined_dataset_concept()
    print("\nConceptual dataset combination completed!")
    print("This shows how FSSAI safety data could be matched with ingredients from other sources.")