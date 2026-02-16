import pandas as pd
import numpy as np

def validate_classification_results():
    """
    Validate the classification accuracy and completeness of the generated dataset
    """
    print("Validating classification results...")
    
    # Load the expanded dataset
    dataset_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\expanded_ingredient_classification.csv'
    df = pd.read_csv(dataset_path)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Total ingredients: {len(df)}")
    
    # Basic statistics
    print("\n=== BASIC STATISTICS ===")
    print(f"Unique ingredient names: {df['ingredient_name'].nunique()}")
    print(f"Missing values per column:")
    print(df.isnull().sum())
    
    # Safety category distribution
    print("\n=== SAFETY CATEGORY DISTRIBUTION ===")
    safety_dist = df['safety_category'].value_counts()
    print(safety_dist)
    
    print(f"\nSafety percentages:")
    for category, count in safety_dist.items():
        percentage = (count / len(df)) * 100
        print(f"  {category}: {count} ({percentage:.2f}%)")
    
    # Source distribution
    print("\n=== SOURCE DISTRIBUTION ===")
    if 'source' in df.columns:
        source_dist = df['source'].value_counts()
        print(source_dist)
        
        print(f"\nSource percentages:")
        for source, count in source_dist.items():
            percentage = (count / len(df)) * 100
            print(f"  {source}: {count} ({percentage:.2f}%)")
    
    # Quality checks
    print("\n=== QUALITY CHECKS ===")
    
    # Check for empty or invalid ingredient names
    empty_names = df[df['ingredient_name'].isna() | (df['ingredient_name'].str.strip() == '')]
    print(f"Empty ingredient names: {len(empty_names)}")
    
    # Check for unknown safety categories
    valid_categories = ['Safe', 'Moderate', 'Harmful']
    invalid_categories = df[~df['safety_category'].isin(valid_categories)]
    print(f"Invalid safety categories: {len(invalid_categories)}")
    
    # Check for ingredients with no safety description
    no_description = df[df['safety_description'].isna() | (df['safety_description'].str.strip() == '')]
    print(f"Ingredients with no safety description: {len(no_description)}")
    
    # Sample of each safety category
    print("\n=== SAMPLE INGREDIENTS BY CATEGORY ===")
    for category in ['Safe', 'Moderate', 'Harmful']:
        if category in df['safety_category'].values:
            sample_ingredients = df[df['safety_category'] == category]['ingredient_name'].head(5).tolist()
            print(f"{category}: {sample_ingredients}")
    
    # Check FSSAI matches vs heuristic classifications
    if 'source' in df.columns:
        print("\n=== FSSAI MATCHES ANALYSIS ===")
        fssai_matches = df[df['source'].str.contains('FSSAI', na=False)]
        heuristic_matches = df[df['source'].str.contains('Heuristic', na=False)]
        
        print(f"FSSAI-based classifications: {len(fssai_matches)} ({len(fssai_matches)/len(df)*100:.2f}%)")
        print(f"Heuristic-based classifications: {len(heuristic_matches)} ({len(heuristic_matches)/len(df)*100:.2f}%)")
        
        if len(fssai_matches) > 0:
            print(f"Sample FSSAI matches: {fssai_matches['ingredient_name'].head(5).tolist()}")
        if len(heuristic_matches) > 0:
            print(f"Sample heuristic matches: {heuristic_matches['ingredient_name'].head(5).tolist()}")
    
    # Completeness score
    print("\n=== COMPLETENESS ASSESSMENT ===")
    required_columns = ['ingredient_name', 'safety_category', 'safety_description']
    completeness_scores = {}
    
    for col in required_columns:
        if col in df.columns:
            non_null_count = df[col].notna().sum()
            completeness_scores[col] = (non_null_count / len(df)) * 100
            print(f"{col}: {completeness_scores[col]:.2f}% complete")
    
    overall_completeness = sum(completeness_scores.values()) / len(completeness_scores)
    print(f"Overall completeness: {overall_completeness:.2f}%")
    
    # Potential issues
    print("\n=== POTENTIAL ISSUES ===")
    potential_duplicates = df[df.duplicated(subset=['ingredient_name'], keep=False)]
    print(f"Potential duplicate ingredient names: {potential_duplicates['ingredient_name'].nunique()}")
    
    # Very short ingredient names (might be parsing errors)
    short_names = df[df['ingredient_name'].str.len() < 3]
    print(f"Very short ingredient names (<3 chars): {len(short_names)}")
    
    # Save validation report
    validation_report = {
        'total_ingredients': len(df),
        'unique_ingredients': df['ingredient_name'].nunique(),
        'safety_distribution': safety_dist.to_dict(),
        'source_distribution': source_dist.to_dict() if 'source' in df.columns else {},
        'completeness_scores': completeness_scores,
        'overall_completeness': overall_completeness,
        'empty_names': len(empty_names),
        'invalid_categories': len(invalid_categories),
        'no_description': len(no_description)
    }
    
    # Write validation report to file
    report_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\validation_report.txt'
    with open(report_path, 'w') as f:
        f.write("CLASSIFICATION VALIDATION REPORT\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total ingredients: {validation_report['total_ingredients']}\n")
        f.write(f"Unique ingredients: {validation_report['unique_ingredients']}\n\n")
        
        f.write("Safety Distribution:\n")
        for category, count in validation_report['safety_distribution'].items():
            percentage = (count / validation_report['total_ingredients']) * 100
            f.write(f"  {category}: {count} ({percentage:.2f}%)\n")
        f.write("\n")
        
        f.write("Completeness Scores:\n")
        for col, score in validation_report['completeness_scores'].items():
            f.write(f"  {col}: {score:.2f}%\n")
        f.write(f"\nOverall Completeness: {validation_report['overall_completeness']:.2f}%\n\n")
        
        f.write("Quality Issues:\n")
        f.write(f"  Empty names: {validation_report['empty_names']}\n")
        f.write(f"  Invalid categories: {validation_report['invalid_categories']}\n")
        f.write(f"  No description: {validation_report['no_description']}\n")
    
    print(f"\nValidation report saved to: {report_path}")
    
    return validation_report


def compare_with_original_fssai():
    """
    Compare the expanded dataset with the original FSSAI dataset to assess coverage
    """
    print("\n=== COMPARISON WITH ORIGINAL FSSAI DATA ===")
    
    # Load original FSSAI data
    original_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv'
    original_df = pd.read_csv(original_path)
    
    # Load expanded dataset
    expanded_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\expanded_ingredient_classification.csv'
    expanded_df = pd.read_csv(expanded_path)
    
    print(f"Original FSSAI dataset: {len(original_df)} ingredients")
    print(f"Expanded dataset: {len(expanded_df)} ingredients")
    print(f"Expansion factor: {len(expanded_df)/len(original_df):.2f}x")
    
    # Count how many original ingredients are preserved in expanded dataset
    original_ingredients = set(original_df['ingredient_name'].str.lower().str.strip())
    expanded_ingredients = set(expanded_df['ingredient_name'].str.lower().str.strip())
    
    overlap = original_ingredients.intersection(expanded_ingredients)
    print(f"Original ingredients preserved: {len(overlap)}/{len(original_ingredients)} ({len(overlap)/len(original_ingredients)*100:.2f}%)")
    
    # New ingredients added
    new_ingredients = expanded_ingredients - original_ingredients
    print(f"New ingredients added: {len(new_ingredients)}")
    
    print(f"\nSample of new ingredients: {list(new_ingredients)[:10]}")
    
    return {
        'original_count': len(original_df),
        'expanded_count': len(expanded_df),
        'expansion_factor': len(expanded_df)/len(original_df),
        'preserved_count': len(overlap),
        'new_count': len(new_ingredients)
    }


if __name__ == "__main__":
    # Run validation
    validation_results = validate_classification_results()
    
    # Run comparison with original
    comparison_results = compare_with_original_fssai()
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Dataset successfully expanded from {comparison_results['original_count']} to {comparison_results['expanded_count']} ingredients")
    print(f"Expansion factor: {comparison_results['expansion_factor']:.2f}x")
    print(f"Original ingredients preserved: {comparison_results['preserved_count']}/{comparison_results['original_count']} ({comparison_results['preserved_count']/comparison_results['original_count']*100:.2f}%)")
    print(f"New ingredients added: {comparison_results['new_count']}")
    print(f"Overall data completeness: {validation_results['overall_completeness']:.2f}%")
    print("\nValidation completed successfully!")