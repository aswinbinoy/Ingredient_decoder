from src.ingredient_decoder import IngredientDecoder
import pandas as pd

def test_ingredient_decoder():
    print("Testing Ingredient Decoder...")
    
    # Initialize the decoder
    decoder = IngredientDecoder()
    
    # Check the safety data
    print(f'Safety data shape: {decoder.safety_data.shape}')
    print('Sample safety data:')
    print(decoder.safety_data.head())
    
    print("\n" + "="*50)
    
    # Test with specific ingredients
    test_ingredients = ['Sodium benzoate', 'Citric Acid', 'Titanium dioxide', 'Sorbic acid']
    
    for ingr in test_ingredients:
        result = decoder.classify_ingredient(ingr)
        print(f'Classification for {ingr}:')
        print(f'  INS Number: {result["ins_number"]}')
        print(f'  Category: {result["category"]}')
        print(f'  Safety: {result["safety_category"]}')
        print(f'  Description: {result["safety_description"]}')
        print()
    
    print("="*50)
    
    # Test with full ingredient lists
    test_lists = [
        "Sugar, Milk Solids, Cocoa Butter, Emulsifiers (Soy Lecithin), Natural Vanilla Flavouring",
        "Wheat Flour, Salt, Yeast, Preservatives (Sodium Benzoate), Antioxidants (Ascorbic Acid)",
        "Tomato Puree, Salt, Sugar, Acidity Regulator (Citric Acid), Preservative (Potassium Sorbate)"
    ]
    
    for ingr_list in test_lists:
        print(f'Analyzing: {ingr_list}')
        result = decoder.analyze_ingredients(ingr_list)
        print(f'  Overall Assessment: {result["overall_assessment"]}')
        print(f'  Warnings: {result["warnings"]}')
        print(f'  Safety Summary: {result["safety_summary"]}')
        print()

if __name__ == "__main__":
    test_ingredient_decoder()