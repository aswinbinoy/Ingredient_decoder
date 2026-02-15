import pandas as pd
import re
from typing import List, Dict, Tuple

class IngredientDecoder:
    """
    An ingredient decoder that analyzes food ingredient lists and classifies them as Safe, Moderate, or Harmful.
    """
    
    def __init__(self, safety_data_path: str = None):
        """
        Initialize the ingredient decoder with safety data.
        
        Args:
            safety_data_path: Path to the CSV file containing ingredient safety information
        """
        if safety_data_path:
            self.safety_data = pd.read_csv(safety_data_path)
        else:
            # Default to the comprehensive safety database
            self.safety_data = pd.read_csv(r'C:\code\llm_project\Ingredient_decoder\data\processed\comprehensive_ingredient_safety_db.csv')
        
        # Create a lookup dictionary for faster access
        self.ingredient_lookup = {}
        for _, row in self.safety_data.iterrows():
            ingredient_name = row['ingredient_name'].lower().strip()
            self.ingredient_lookup[ingredient_name] = {
                'ins_number': row['ins_number'],
                'category': row['category'],
                'safety_category': row['safety_category'],
                'safety_description': row['safety_description']
            }
    
    def extract_ingredients(self, ingredient_text: str) -> List[str]:
        """
        Extract individual ingredients from an ingredient text.
        
        Args:
            ingredient_text: Raw ingredient text from food packaging
            
        Returns:
            List of individual ingredients
        """
        # Remove common separators and split
        # Handle various separators like commas, parentheses, colons
        text = ingredient_text.lower()
        
        # Remove common descriptors that aren't ingredients
        text = re.sub(r'\([^)]*\)', '', text)  # Remove parentheses content
        text = re.sub(r'\d+%', '', text)       # Remove percentages
        text = re.sub(r'contains?:?', '', text)  # Remove "contains" phrases
        
        # Split by common separators
        separators = [',', ';', ':', 'and', '&']
        for sep in separators:
            text = text.replace(sep, '|')
        
        # Split and clean ingredients
        ingredients = [ingr.strip() for ingr in text.split('|') if ingr.strip()]
        
        # Filter out very short entries that are likely not ingredients
        ingredients = [ingr for ingr in ingredients if len(ingr) > 2]
        
        return ingredients
    
    def classify_ingredient(self, ingredient: str) -> Dict:
        """
        Classify a single ingredient based on safety data.
        
        Args:
            ingredient: Individual ingredient name
            
        Returns:
            Dictionary with classification information
        """
        ingredient_lower = ingredient.lower().strip()
        
        # Direct match
        if ingredient_lower in self.ingredient_lookup:
            return self.ingredient_lookup[ingredient_lower]
        
        # Partial match - look for the ingredient in the safety data
        for idx, row in self.safety_data.iterrows():
            if ingredient_lower in row['ingredient_name'].lower():
                return {
                    'ins_number': row['ins_number'],
                    'category': row['category'],
                    'safety_category': row['safety_category'],
                    'safety_description': row['safety_description']
                }
        
        # If no match found, return unknown
        return {
            'ins_number': 'Unknown',
            'category': 'Unknown',
            'safety_category': 'Unknown',
            'safety_description': 'Safety classification not available for this ingredient.'
        }
    
    def analyze_ingredients(self, ingredient_text: str) -> Dict:
        """
        Analyze a full ingredient list and return safety assessment.
        
        Args:
            ingredient_text: Full ingredient list from food product
            
        Returns:
            Dictionary with analysis results
        """
        extracted_ingredients = self.extract_ingredients(ingredient_text)
        
        results = {
            'input_text': ingredient_text,
            'extracted_ingredients': [],
            'safety_summary': {'Safe': 0, 'Moderate': 0, 'Harmful': 0, 'Unknown': 0},
            'warnings': [],
            'overall_assessment': 'Unknown'
        }
        
        for ingr in extracted_ingredients:
            classification = self.classify_ingredient(ingr)
            
            ingredient_result = {
                'name': ingr,
                'classification': classification
            }
            
            results['extracted_ingredients'].append(ingredient_result)
            results['safety_summary'][classification['safety_category']] += 1
            
            # Add warnings for moderate or harmful ingredients
            if classification['safety_category'] in ['Moderate', 'Harmful']:
                warning = f"{ingr}: {classification['safety_description']}"
                results['warnings'].append(warning)
        
        # Determine overall assessment
        safe_count = results['safety_summary']['Safe']
        moderate_count = results['safety_summary']['Moderate']
        harmful_count = results['safety_summary']['Harmful']
        unknown_count = results['safety_summary']['Unknown']
        
        if harmful_count > 0:
            results['overall_assessment'] = 'Harmful'
        elif moderate_count > 0:
            results['overall_assessment'] = 'Moderate'
        elif unknown_count > 0:
            results['overall_assessment'] = 'Mixed (some unknown ingredients)'
        else:
            results['overall_assessment'] = 'Safe'
        
        return results

# Example usage
if __name__ == "__main__":
    # Initialize the decoder
    decoder = IngredientDecoder()
    
    # Test with sample ingredient lists
    test_ingredients = [
        "Sugar, Milk Solids, Cocoa Butter, Emulsifiers (Soy Lecithin, INS 322), Natural Vanilla Flavouring",
        "Wheat Flour, Salt, Yeast, Preservatives (Sodium Benzoate, INS 211), Antioxidants (Ascorbic Acid)",
        "Tomato Puree, Salt, Sugar, Acidity Regulator (Citric Acid, INS 330), Preservative (Potassium Sorbate, INS 202)"
    ]
    
    for ingr_text in test_ingredients:
        print(f"\nAnalyzing: {ingr_text}")
        result = decoder.analyze_ingredients(ingr_text)
        print(f"Overall Assessment: {result['overall_assessment']}")
        print(f"Warnings: {result['warnings']}")
        print(f"Safety Summary: {result['safety_summary']}")