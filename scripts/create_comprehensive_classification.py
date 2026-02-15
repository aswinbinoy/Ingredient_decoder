import pandas as pd
import os

def create_comprehensive_classification():
    """
    Create a comprehensive ingredient classification system by combining
    FSSAI data with heuristic classifications for broader coverage
    """
    print("Creating comprehensive ingredient classification system...")
    
    # Load our FSSAI safety data
    safety_df = pd.read_csv(r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv')
    print(f"FSSAI safety data shape: {safety_df.shape}")
    
    # Create a comprehensive ingredient safety database
    # This combines our FSSAI data with expanded classifications
    
    # Known harmful ingredients (beyond FSSAI data)
    harmful_ingredients = {
        'bha': {'ins_number': 'INS 320', 'category': 'Antioxidant', 'description': 'Butylated Hydroxyanisole - potential carcinogen'},
        'bht': {'ins_number': 'INS 321', 'category': 'Antioxidant', 'description': 'Butylated Hydroxytoluene - potential carcinogen'},
        'tbhq': {'ins_number': 'INS 319', 'category': 'Antioxidant', 'description': 'Tertiary Butylhydroquinone - potential carcinogen'},
        'potassium bromate': {'ins_number': 'INS 924', 'category': 'Flour Treatment Agent', 'description': 'Potential carcinogen'},
        'sodium nitrite': {'ins_number': 'INS 250', 'category': 'Preservative', 'description': 'Can form carcinogenic nitrosamines'},
        'fd&c red no. 40': {'ins_number': 'INS 129', 'category': 'Food Colour', 'description': 'May cause hyperactivity in children'},
        'fd&c yellow no. 5': {'ins_number': 'INS 102', 'category': 'Food Colour', 'description': 'May cause allergic reactions'},
        'fd&c blue no. 1': {'ins_number': 'INS 133', 'category': 'Food Colour', 'description': 'May cause allergic reactions'}
    }
    
    # Known moderate ingredients (with some concerns)
    moderate_ingredients = {
        'sodium benzoate': {'ins_number': 'INS 211', 'category': 'Preservative', 'description': 'Safe within limits, may react with vitamin C'},
        'potassium sorbate': {'ins_number': 'INS 202', 'category': 'Preservative', 'description': 'Generally safe but some people may be sensitive'},
        'sulfur dioxide': {'ins_number': 'INS 220', 'category': 'Preservative', 'description': 'Safe for most people but can cause reactions in asthmatics'},
        'tartrazine': {'ins_number': 'INS 102', 'category': 'Food Colour', 'description': 'Can cause allergic reactions and hyperactivity in some children'},
        'sunset yellow': {'ins_number': 'INS 155', 'category': 'Food Colour', 'description': 'May cause allergic reactions and hyperactivity in some children'},
        'allura red': {'ins_number': 'INS 129', 'category': 'Food Colour', 'description': 'May cause allergic reactions and hyperactivity in some children'},
        'acesulfame potassium': {'ins_number': 'INS 950', 'category': 'Sweetener', 'description': 'Safe within acceptable daily intake levels'},
        'aspartame': {'ins_number': 'INS 951', 'category': 'Sweetener', 'description': 'Safe for most people but contraindicated for phenylketonurics'},
        'saccharin': {'ins_number': 'INS 954', 'category': 'Sweetener', 'description': 'Safe within limits, was once linked to bladder cancer in rats'},
        'neotame': {'ins_number': 'INS 961', 'category': 'Sweetener', 'description': 'Newer sweetener, considered safe but less long-term data'},
        'acesulfame k': {'ins_number': 'INS 950', 'category': 'Sweetener', 'description': 'Safe within acceptable daily intake levels'}
    }
    
    # Common safe ingredients (beyond FSSAI data)
    safe_ingredients = {
        'sugar': {'ins_number': 'None', 'category': 'Sweetener', 'description': 'Natural sweetener, safe in moderation'},
        'salt': {'ins_number': 'None', 'category': 'Seasoning', 'description': 'Essential nutrient, safe in moderation'},
        'water': {'ins_number': 'None', 'category': 'Solvent', 'description': 'Essential for life, safe'},
        'oil': {'ins_number': 'None', 'category': 'Fat', 'description': 'Essential fat, safe in moderation'},
        'butter': {'ins_number': 'None', 'category': 'Fat', 'description': 'Natural dairy fat, safe in moderation'},
        'milk': {'ins_number': 'None', 'category': 'Dairy', 'description': 'Nutritious dairy product, safe for most'},
        'egg': {'ins_number': 'None', 'category': 'Protein', 'description': 'High-quality protein, safe for most'},
        'flour': {'ins_number': 'None', 'category': 'Grain', 'description': 'Basic ingredient, safe for most'},
        'citric acid': {'ins_number': 'INS 330', 'category': 'Acidulant', 'description': 'Natural acid, generally safe'},
        'ascorbic acid': {'ins_number': 'INS 300', 'category': 'Antioxidant', 'description': 'Vitamin C, beneficial antioxidant'},
        'tocopherol': {'ins_number': 'INS 306', 'category': 'Antioxidant', 'description': 'Vitamin E, beneficial antioxidant'},
        'lecithin': {'ins_number': 'INS 322', 'category': 'Emulsifier', 'description': 'Natural emulsifier, generally safe'},
        'pectin': {'ins_number': 'INS 440', 'category': 'Thickener', 'description': 'Natural thickener, generally safe'},
        'guar gum': {'ins_number': 'INS 412', 'category': 'Thickener', 'description': 'Natural thickener, generally safe'},
        'xanthan gum': {'ins_number': 'INS 415', 'category': 'Thickener', 'description': 'Natural thickener, generally safe'},
        'carrageenan': {'ins_number': 'INS 407', 'category': 'Thickener', 'description': 'Natural thickener, generally safe'}
    }
    
    # Combine all ingredients into a comprehensive database
    all_ingredients = []
    
    # Add FSSAI data
    for _, row in safety_df.iterrows():
        all_ingredients.append({
            'ingredient_name': row['ingredient_name'].lower().strip(),
            'ins_number': row['ins_number'],
            'category': row['category'],
            'safety_category': row['safety_category'],
            'safety_description': row['safety_description'],
            'source': 'FSSAI_Regulation'
        })
    
    # Add harmful ingredients
    for name, info in harmful_ingredients.items():
        all_ingredients.append({
            'ingredient_name': name,
            'ins_number': info['ins_number'],
            'category': info['category'],
            'safety_category': 'Harmful',
            'safety_description': info['description'],
            'source': 'Expert_Knowledge'
        })
    
    # Add moderate ingredients
    for name, info in moderate_ingredients.items():
        all_ingredients.append({
            'ingredient_name': name,
            'ins_number': info['ins_number'],
            'category': info['category'],
            'safety_category': 'Moderate',
            'safety_description': info['description'],
            'source': 'Expert_Knowledge'
        })
    
    # Add safe ingredients
    for name, info in safe_ingredients.items():
        all_ingredients.append({
            'ingredient_name': name,
            'ins_number': info['ins_number'],
            'category': info['category'],
            'safety_category': 'Safe',
            'safety_description': info['description'],
            'source': 'Expert_Knowledge'
        })
    
    # Create DataFrame
    comprehensive_df = pd.DataFrame(all_ingredients)
    
    # Remove duplicates, keeping FSSAI regulation data when available
    comprehensive_df = comprehensive_df.drop_duplicates(subset=['ingredient_name'], keep='first')
    
    print(f"Comprehensive database created with {len(comprehensive_df)} ingredients")
    print(f"Safety category distribution:")
    print(comprehensive_df['safety_category'].value_counts())
    
    # Save the comprehensive database
    output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\comprehensive_ingredient_safety_db.csv'
    comprehensive_df.to_csv(output_path, index=False)
    print(f"Comprehensive safety database saved to: {output_path}")
    
    # Create a sample classification based on common ingredient patterns
    # This simulates how we would classify ingredients from Open Food Facts
    sample_products = [
        {
            'product_name': 'Chocolate Bar',
            'ingredients': 'Sugar, Cocoa Butter, Whole Milk Powder, Soy Lecithin, Vanilla Extract'
        },
        {
            'product_name': 'Soda Drink',
            'ingredients': 'Carbonated Water, High Fructose Corn Syrup, Caramel Color, Phosphoric Acid, Caffeine, Sodium Benzoate'
        },
        {
            'product_name': 'Candy',
            'ingredients': 'Sugar, Corn Syrup, FD&C Red No. 40, Artificial Flavor, Citric Acid, Sodium Benzoate'
        },
        {
            'product_name': 'Bread',
            'ingredients': 'Wheat Flour, Water, Yeast, Salt, Sugar, Soy Lecithin, Calcium Propionate'
        },
        {
            'product_name': 'Jam',
            'ingredients': 'Strawberries, Sugar, Pectin, Citric Acid, Potassium Sorbate'
        }
    ]
    
    # Classify ingredients in sample products
    classified_samples = []
    for product in sample_products:
        ingredients_list = [ing.strip() for ing in product['ingredients'].split(',')]
        for ingredient in ingredients_list:
            ingredient_lower = ingredient.lower().strip()
            
            # Find matching safety info
            match = comprehensive_df[comprehensive_df['ingredient_name'] == ingredient_lower]
            if not match.empty:
                row = match.iloc[0]
                classified_samples.append({
                    'product_name': product['product_name'],
                    'ingredient_name': ingredient,
                    'ins_number': row['ins_number'],
                    'category': row['category'],
                    'safety_category': row['safety_category'],
                    'safety_description': row['safety_description'],
                    'source': row['source']
                })
            else:
                # If not found, use a conservative approach
                classified_samples.append({
                    'product_name': product['product_name'],
                    'ingredient_name': ingredient,
                    'ins_number': 'Not Found',
                    'category': 'Unknown',
                    'safety_category': 'Moderate',  # Conservative default
                    'safety_description': 'Safety classification not available, assumed moderate risk',
                    'source': 'Default_Classification'
                })
    
    # Create sample classification DataFrame
    sample_classification_df = pd.DataFrame(classified_samples)
    
    # Save sample classifications
    sample_output_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\sample_ingredient_classifications.csv'
    sample_classification_df.to_csv(sample_output_path, index=False)
    print(f"Sample ingredient classifications saved to: {sample_output_path}")
    
    print("\nSample of classified ingredients:")
    print(sample_classification_df.head(10))
    
    # Create a summary of the comprehensive database
    summary = comprehensive_df.groupby('safety_category').agg({
        'ingredient_name': 'count',
        'category': lambda x: x.value_counts().index[0] if not x.value_counts().empty else 'Unknown'
    }).rename(columns={'ingredient_name': 'count'})
    
    summary_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\classification_summary.csv'
    summary.to_csv(summary_path)
    print(f"Classification summary saved to: {summary_path}")
    
    print(f"\nSummary of comprehensive database:")
    print(summary)
    
    return comprehensive_df, sample_classification_df

if __name__ == "__main__":
    comprehensive_db, sample_classifications = create_comprehensive_classification()
    print("\nComprehensive ingredient classification system created successfully!")