import pandas as pd
import os

def create_ingredient_safety_dataset():
    print("Creating ingredient safety dataset...")
    
    # Load the FSSAI additives data we created
    fssai_df = pd.read_csv(r'C:\code\llm_project\Ingredient_decoder\data\processed\fssai_additives.csv')
    print(f"FSSAI data shape: {fssai_df.shape}")
    print("FSSAI columns:", fssai_df.columns.tolist())
    
    print("\nFSSAI data preview:")
    print(fssai_df.head())
    
    # Create a safety classification mapping based on the category and general knowledge
    # Since the FSSAI document doesn't provide explicit safety ratings, we'll create a 
    # basic classification system based on additive types
    def classify_safety_by_category(category, ingredient_name):
        if pd.isna(category):
            category = ""
        if pd.isna(ingredient_name):
            ingredient_name = ""
        
        category_lower = category.lower()
        name_lower = ingredient_name.lower()
        
        # Categories that are generally safe when used within limits
        safe_categories = ['food additive', 'emulsifier/stabilizer']
        
        # Some additives that are known to be safe
        safe_additives = [
            'citric acid', 'titanium dioxide', 'sodium benzoate', 'potassium nitrate',
            'sorbic acid', 'sodium propionate', 'sulphur dioxide', 'ascorbic acid',
            'sodium ascorbate', 'tocopherol', 'lecithin', 'guar gum', 'pectin'
        ]
        
        # Some additives that may have concerns if overused
        moderate_additives = [
            'bha', 'bht', 'propyl gallate', 'sodium nitrite', 'sulfites'
        ]
        
        if any(safe_add in name_lower for safe_add in safe_additives):
            return 'Safe'
        elif any(mod_add in name_lower for mod_add in moderate_additives):
            return 'Moderate'
        elif category_lower in [cat.lower() for cat in safe_categories]:
            return 'Safe'
        elif 'preserv' in name_lower or 'nitrate' in name_lower or 'nitrite' in name_lower:
            return 'Moderate'
        elif 'colour' in category_lower or 'color' in category_lower:
            return 'Moderate'  # Food colors are generally safe but some people are sensitive
        else:
            # Default to moderate for additives that are regulated but generally safe
            return 'Moderate'
    
    # Apply safety classification to FSSAI data
    fssai_df['safety_category'] = fssai_df.apply(
        lambda row: classify_safety_by_category(row['category'], row['ingredient_name']), axis=1
    )
    
    # Add safety descriptions
    def get_safety_description(safety_cat, ingredient_name):
        descriptions = {
            'Safe': 'Generally recognized as safe for consumption within recommended limits.',
            'Moderate': 'Safe when consumed within recommended limits; some individuals may be sensitive.',
            'Harmful': 'Should be avoided or consumed with caution; potential health risks.'
        }
        return descriptions.get(safety_cat, 'Safety classification not determined.')
    
    fssai_df['safety_description'] = fssai_df.apply(
        lambda row: get_safety_description(row['safety_category'], row['ingredient_name']), axis=1
    )
    
    print(f"\nDataset with safety classifications:")
    print(fssai_df[['ingredient_name', 'ins_number', 'category', 'safety_category']].head(15))
    
    # Select the required columns for the ingredient decoder
    final_columns = ['ingredient_name', 'ins_number', 'category', 'safety_category', 'safety_description']
    final_df = fssai_df[final_columns].copy()
    
    # Remove duplicates based on ingredient name
    final_df = final_df.drop_duplicates(subset=['ingredient_name'], keep='first')
    
    print(f"\nFinal dataset shape: {final_df.shape}")
    print(final_df.head(10))
    
    # Save the final dataset
    output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv'
    final_df.to_csv(output_path, index=False)
    print(f"\nSaved final ingredient safety dataset to: {output_path}")
    
    # Show summary statistics
    print(f"\nSafety category distribution:")
    print(final_df['safety_category'].value_counts())
    
    return final_df

def create_sample_ingredient_input():
    """Create a sample input file that demonstrates how the ingredient decoder would work"""
    sample_data = {
        'ingredient_text': [
            'Sugar, Milk Solids, Cocoa Butter, Emulsifiers (Soy Lecithin, INS 322), Natural Vanilla Flavouring',
            'Wheat Flour, Salt, Yeast, Preservatives (Sodium Benzoate, INS 211), Antioxidants (Ascorbic Acid)',
            'Tomato Puree, Salt, Sugar, Acidity Regulator (Citric Acid, INS 330), Preservative (Potassium Sorbate, INS 202)'
        ],
        'expected_warnings': [
            'Contains emulsifiers (INS 322) - Generally safe',
            'Contains preservative (INS 211) and antioxidant (Ascorbic Acid) - Safe within limits',
            'Contains acidity regulator (INS 330) and preservative (INS 202) - Safe within limits'
        ]
    }
    
    sample_df = pd.DataFrame(sample_data)
    sample_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\sample_ingredient_inputs.csv'
    sample_df.to_csv(sample_path, index=False)
    print(f"Created sample input file at: {sample_path}")

if __name__ == "__main__":
    df = create_ingredient_safety_dataset()
    create_sample_ingredient_input()
    print("\nIngredient decoder data preprocessing completed successfully!")