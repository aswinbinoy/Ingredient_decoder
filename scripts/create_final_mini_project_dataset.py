"""
Create Final Classified Dataset for Mini Project
=================================================
This script creates a clean, simplified dataset containing only products
that can be confidently classified using our FSSAI + WHO + GRAS database.

Filters:
- Only products where at least 50% of ingredients have known classifications
- Removes products with too many unknown ingredients
- Creates a manageable dataset for the mini project
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

OUTPUT_DIR = r'C:\code\llm_project\Ingredient_decoder\data\processed'

# Input files
PRODUCT_SUMMARY = f'{OUTPUT_DIR}/openfoodfacts_product_safety_summary.csv'
CLASSIFIED_BATCHES = f'{OUTPUT_DIR}/openfoodfacts_classified_batch_*.csv'
UNIFIED_DB = f'{OUTPUT_DIR}/unified_ingredient_database_full.csv'

# Output files
OUTPUT_FINAL_DATASET = f'{OUTPUT_DIR}/final_classified_dataset.csv'
OUTPUT_SUMMARY = f'{OUTPUT_DIR}/final_dataset_summary.csv'
OUTPUT_REPORT = f'{OUTPUT_DIR}/mini_project_summary.txt'


def create_final_dataset():
    """Create final simplified dataset"""
    print("=" * 80)
    print("CREATING FINAL CLASSIFIED DATASET FOR MINI PROJECT")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load product summary
    print("\n[1/4] Loading product summary...")
    summary_df = pd.read_csv(PRODUCT_SUMMARY)
    print(f"  Total products: {len(summary_df):,}")
    
    # Load unified database for reference
    print("\n[2/4] Loading unified database...")
    unified_df = pd.read_csv(UNIFIED_DB)
    print(f"  Database size: {len(unified_df)} ingredients")
    
    # Load all classified ingredients from batches
    print("\n[3/4] Loading and combining classified ingredients...")
    import glob
    batch_files = sorted(glob.glob(f'{OUTPUT_DIR}/openfoodfacts_classified_batch_*.csv'))
    
    all_ingredients = []
    for i, batch_file in enumerate(batch_files):
        print(f"  Loading batch {i+1}/{len(batch_files)}...")
        df = pd.read_csv(batch_file)
        all_ingredients.append(df)
    
    classified_df = pd.concat(all_ingredients, ignore_index=True)
    print(f"  Total ingredient classifications: {len(classified_df):,}")
    
    # Filter: Keep only products with known classifications
    print("\n[4/4] Filtering and creating final dataset...")
    
    # Calculate known vs unknown for each product
    classified_df['is_known'] = classified_df['unified_category'] != 'Unknown'
    
    # Group by product
    product_stats = classified_df.groupby(['product_code', 'product_name']).agg({
        'ingredient_name': 'count',
        'is_known': 'sum',
        'unified_category': lambda x: (x == 'Harmful').sum()
    }).reset_index()
    product_stats.columns = ['product_code', 'product_name', 'total_ingredients', 
                             'known_ingredients', 'harmful_count']
    product_stats['known_percentage'] = (product_stats['known_ingredients'] / 
                                         product_stats['total_ingredients'] * 100)
    
    # Filter: Keep products with at least 50% known ingredients
    filtered_products = product_stats[product_stats['known_percentage'] >= 50].copy()
    print(f"\n  Products with >=50% known ingredients: {len(filtered_products):,}")
    
    # Merge back with summary to get safety ratings
    final_df = filtered_products.merge(
        summary_df[['product_code', 'safety_score', 'safety_rating', 
                    'safety_explanation', 'categories', 'nutriscore_grade']],
        on='product_code',
        how='left'
    )
    
    # Get ingredient details for final products
    final_products_codes = set(filtered_products['product_code'])
    final_ingredients = classified_df[classified_df['product_code'].isin(final_products_codes)]
    final_ingredients = final_ingredients[final_ingredients['unified_category'] != 'Unknown']
    
    # Create final ingredient-level dataset
    final_dataset = final_ingredients.merge(
        filtered_products[['product_code', 'known_percentage']],
        on='product_code',
        how='left'
    )
    
    # Add simplified safety score
    def simplify_category(cat):
        if cat in ['Safe']:
            return 'Safe'
        elif cat in ['Moderate']:
            return 'Moderate'
        elif cat in ['Harmful', 'Very Harmful']:
            return 'Harmful'
        else:
            return 'Unknown'
    
    final_dataset['simplified_category'] = final_dataset['unified_category'].apply(simplify_category)
    
    print(f"\n  Final dataset size: {len(final_dataset):,} ingredient classifications")
    print(f"  Unique products: {final_dataset['product_code'].nunique():,}")
    print(f"  Unique ingredients: {final_dataset['ingredient_name'].nunique():,}")
    
    # Save final dataset
    print(f"\nSaving final dataset: {OUTPUT_FINAL_DATASET}")
    final_dataset.to_csv(OUTPUT_FINAL_DATASET, index=False)
    
    # Create summary statistics
    summary_stats = {
        'metric': [
            'total_products',
            'total_ingredient_classifications',
            'unique_ingredients',
            'safe_ingredients',
            'moderate_ingredients',
            'harmful_ingredients',
            'products_excellent',
            'products_good',
            'products_fair',
            'products_poor'
        ],
        'value': [
            len(final_dataset['product_code'].unique()),
            len(final_dataset),
            final_dataset['ingredient_name'].nunique(),
            (final_dataset['simplified_category'] == 'Safe').sum(),
            (final_dataset['simplified_category'] == 'Moderate').sum(),
            (final_dataset['simplified_category'] == 'Harmful').sum(),
            (final_df['safety_rating'] == 'Excellent').sum(),
            (final_df['safety_rating'] == 'Good').sum(),
            (final_df['safety_rating'] == 'Fair').sum(),
            (final_df['safety_rating'] == 'Poor').sum()
        ]
    }
    summary_df_out = pd.DataFrame(summary_stats)
    summary_df_out.to_csv(OUTPUT_SUMMARY, index=False)
    print(f"Saved summary: {OUTPUT_SUMMARY}")
    
    # Generate report
    generate_report(final_dataset, final_df, unified_df)
    
    print(f"\n" + "=" * 80)
    print("FINAL DATASET CREATED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\nOutput files:")
    print(f"  1. {OUTPUT_FINAL_DATASET}")
    print(f"  2. {OUTPUT_SUMMARY}")
    print(f"  3. {OUTPUT_REPORT}")
    
    return final_dataset


def generate_report(final_df, product_df, unified_db):
    """Generate summary report"""
    report = []
    report.append("=" * 80)
    report.append("MINI PROJECT - FINAL CLASSIFIED DATASET SUMMARY")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    report.append("\n" + "=" * 80)
    report.append("DATASET OVERVIEW")
    report.append("=" * 80)
    report.append(f"Total products: {len(product_df):,}")
    report.append(f"Total ingredient classifications: {len(final_df):,}")
    report.append(f"Unique ingredients: {final_df['ingredient_name'].nunique():,}")
    report.append(f"Average ingredients per product: {len(final_df)/len(product_df):.1f}")
    
    report.append("\n" + "=" * 80)
    report.append("INGREDIENT CLASSIFICATION (SIMPLIFIED)")
    report.append("=" * 80)
    class_counts = final_df['simplified_category'].value_counts()
    for cat, cnt in class_counts.items():
        pct = cnt / len(final_df) * 100
        report.append(f"  {cat}: {cnt:,} ({pct:.1f}%)")
    
    report.append("\n" + "=" * 80)
    report.append("PRODUCT SAFETY DISTRIBUTION")
    report.append("=" * 80)
    rating_counts = product_df['safety_rating'].value_counts()
    for rating, cnt in rating_counts.items():
        pct = cnt / len(product_df) * 100
        report.append(f"  {rating}: {cnt:,} ({pct:.1f}%)")
    
    report.append("\n" + "=" * 80)
    report.append("TOP 10 SAFE INGREDIENTS")
    report.append("=" * 80)
    safe_df = final_df[final_df['simplified_category'] == 'Safe']
    safe_top = safe_df['ingredient_name'].value_counts().head(10)
    for i, (ing, cnt) in enumerate(safe_top.items(), 1):
        report.append(f"  {i}. {ing}: {cnt:,} occurrences")
    
    report.append("\n" + "=" * 80)
    report.append("TOP 10 MODERATE INGREDIENTS")
    report.append("=" * 80)
    moderate_df = final_df[final_df['simplified_category'] == 'Moderate']
    moderate_top = moderate_df['ingredient_name'].value_counts().head(10)
    for i, (ing, cnt) in enumerate(moderate_top.items(), 1):
        report.append(f"  {i}. {ing}: {cnt:,} occurrences")
    
    report.append("\n" + "=" * 80)
    report.append("TOP 10 HARMFUL INGREDIENTS")
    report.append("=" * 80)
    harmful_df = final_df[final_df['simplified_category'] == 'Harmful']
    harmful_top = harmful_df['ingredient_name'].value_counts().head(10)
    for i, (ing, cnt) in enumerate(harmful_top.items(), 1):
        report.append(f"  {i}. {ing}: {cnt:,} occurrences")
    
    report.append("\n" + "=" * 80)
    report.append("DATA SOURCES USED")
    report.append("=" * 80)
    report.append(f"Unified database size: {len(unified_db)} ingredients")
    sources = unified_db['sources_available'].value_counts()
    for src, cnt in sources.items():
        report.append(f"  {src}: {cnt} ingredients")
    
    report.append("\n" + "=" * 80)
    report.append("SAMPLE PRODUCTS")
    report.append("=" * 80)
    
    # Show one example from each rating
    for rating in ['Excellent', 'Good', 'Fair', 'Poor']:
        sample = product_df[product_df['safety_rating'] == rating].head(1)
        if not sample.empty:
            row = sample.iloc[0]
            report.append(f"\n  {rating}:")
            report.append(f"    Product: {row['product_name']}")
            report.append(f"    Score: {row.get('safety_score', 'N/A')}")
            report.append(f"    {row.get('safety_explanation', 'N/A')}")
    
    report.append("\n" + "=" * 80)
    report.append("USAGE RECOMMENDATIONS")
    report.append("=" * 80)
    report.append("This dataset is suitable for:")
    report.append("  - Training machine learning models for ingredient classification")
    report.append("  - Building ingredient safety prediction systems")
    report.append("  - Analyzing food product safety patterns")
    report.append("  - Creating food safety awareness applications")
    report.append("")
    report.append("Dataset structure:")
    report.append("  - product_code: Unique product identifier")
    report.append("  - product_name: Name of the product")
    report.append("  - ingredient_name: Individual ingredient")
    report.append("  - unified_category: Safe/Moderate/Harmful/Unknown")
    report.append("  - simplified_category: Safe/Moderate/Harmful (for ML)")
    report.append("  - fssai_category: FSSAI classification (if available)")
    report.append("  - who_category: WHO classification (if available)")
    report.append("  - gras_category: GRAS classification (if available)")
    report.append("  - classification_rationale: Explanation of classification")
    report.append("  - sources_available: Which databases provided data")
    report.append("")
    report.append("Next steps for your mini project:")
    report.append("  1. Load this dataset for training/testing")
    report.append("  2. Use 'simplified_category' for 3-class classification")
    report.append("  3. Use 'unified_category' for more granular analysis")
    report.append("  4. Merge with product summary for product-level predictions")
    
    report.append("\n" + "=" * 80)
    
    report_text = "\n".join(report)
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"\nReport saved: {OUTPUT_REPORT}")
    print("\n" + report_text)


if __name__ == "__main__":
    final_dataset = create_final_dataset()
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE!")
    print("=" * 80)
