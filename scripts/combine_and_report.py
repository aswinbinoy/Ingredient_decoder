"""
Combine all batch classification files into a single dataset
and generate final analysis report.
"""

import pandas as pd
import os
from datetime import datetime
import glob

OUTPUT_DIR = r'C:\code\llm_project\Ingredient_decoder\data\processed'
BATCH_PATTERN = f'{OUTPUT_DIR}/openfoodfacts_classified_batch_*.csv'
OUTPUT_COMBINED = f'{OUTPUT_DIR}/openfoodfacts_full_classified_combined.csv'
OUTPUT_REPORT = f'{OUTPUT_DIR}/classification_final_report.txt'

def combine_batches():
    """Combine all batch files into one"""
    print("Finding batch files...")
    batch_files = sorted(glob.glob(BATCH_PATTERN))
    print(f"Found {len(batch_files)} batch files:")
    for f in batch_files:
        size_mb = os.path.getsize(f) / 1024 / 1024
        print(f"  - {os.path.basename(f)} ({size_mb:.1f} MB)")
    
    print("\nCombining batches...")
    dfs = []
    for i, f in enumerate(batch_files):
        print(f"  Loading batch {i+1}/{len(batch_files)}...")
        df = pd.read_csv(f)
        dfs.append(df)
    
    print(f"\nConcatenating {len(dfs)} DataFrames...")
    combined = pd.concat(dfs, ignore_index=True)
    
    print(f"\nSaving combined file: {OUTPUT_COMBINED}")
    print(f"  Total rows: {len(combined):,}")
    print(f"  Columns: {list(combined.columns)}")
    
    # Save (may take a while for large files)
    combined.to_csv(OUTPUT_COMBINED, index=False)
    print(f"\nSaved: {OUTPUT_COMBINED}")
    print(f"  File size: {os.path.getsize(OUTPUT_COMBINED)/1024/1024:.1f} MB")
    
    return combined


def generate_report(combined_df):
    """Generate final analysis report"""
    print("\nGenerating final report...")
    
    # Load statistics
    stats_df = pd.read_csv(f'{OUTPUT_DIR}/classification_statistics.csv')
    
    # Load product summary
    summary_df = pd.read_csv(f'{OUTPUT_DIR}/openfoodfacts_product_safety_summary.csv')
    
    # Load unified database
    unified_df = pd.read_csv(f'{OUTPUT_DIR}/unified_ingredient_database_full.csv')
    
    report = []
    report.append("=" * 80)
    report.append("OPEN FOOD FACTS CLASSIFICATION - FINAL REPORT")
    report.append("Multi-Source Approach: FSSAI + WHO + GRAS")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Dataset overview
    report.append("\n" + "=" * 80)
    report.append("DATASET OVERVIEW")
    report.append("=" * 80)
    report.append(f"Total products analyzed: {len(summary_df):,}")
    report.append(f"Total ingredient classifications: {len(combined_df):,}")
    report.append(f"Unique ingredients: {combined_df['ingredient_name'].nunique():,}")
    report.append(f"Products with harmful ingredients: {summary_df['has_harmful_ingredients'].sum():,}")
    
    # Classification distribution
    report.append("\n" + "=" * 80)
    report.append("INGREDIENT CLASSIFICATION DISTRIBUTION")
    report.append("=" * 80)
    class_counts = combined_df['unified_category'].value_counts()
    for cat, cnt in class_counts.items():
        pct = cnt / len(combined_df) * 100
        report.append(f"  {cat}: {cnt:,} ({pct:.1f}%)")
    
    # Product safety ratings
    report.append("\n" + "=" * 80)
    report.append("PRODUCT SAFETY RATINGS")
    report.append("=" * 80)
    rating_counts = summary_df['safety_rating'].value_counts()
    for rating, cnt in rating_counts.items():
        pct = cnt / len(summary_df) * 100
        report.append(f"  {rating}: {cnt:,} ({pct:.1f}%)")
    
    # Top harmful ingredients
    report.append("\n" + "=" * 80)
    report.append("TOP HARMFUL INGREDIENTS FOUND")
    report.append("=" * 80)
    harmful_df = combined_df[combined_df['unified_category'] == 'Harmful']
    harmful_counts = harmful_df['ingredient_name'].value_counts().head(20)
    for ing, cnt in harmful_counts.items():
        report.append(f"  {ing}: {cnt:,} occurrences")
    
    # Top moderate ingredients
    report.append("\n" + "=" * 80)
    report.append("TOP MODERATE INGREDIENTS FOUND")
    report.append("=" * 80)
    moderate_df = combined_df[combined_df['unified_category'] == 'Moderate']
    moderate_counts = moderate_df['ingredient_name'].value_counts().head(20)
    for ing, cnt in moderate_counts.items():
        report.append(f"  {ing}: {cnt:,} occurrences")
    
    # Top safe ingredients
    report.append("\n" + "=" * 80)
    report.append("TOP SAFE INGREDIENTS FOUND")
    report.append("=" * 80)
    safe_df = combined_df[combined_df['unified_category'] == 'Safe']
    safe_counts = safe_df['ingredient_name'].value_counts().head(20)
    for ing, cnt in safe_counts.items():
        report.append(f"  {ing}: {cnt:,} occurrences")
    
    # Source coverage analysis
    report.append("\n" + "=" * 80)
    report.append("DATA SOURCE COVERAGE")
    report.append("=" * 80)
    report.append(f"Unified database size: {len(unified_df)} ingredients")
    source_counts = unified_df['sources_available'].value_counts()
    for src, cnt in source_counts.head(10).items():
        report.append(f"  {src}: {cnt} ingredients")
    
    # Sample products by rating
    report.append("\n" + "=" * 80)
    report.append("SAMPLE PRODUCTS BY SAFETY RATING")
    report.append("=" * 80)
    
    for rating in ['Excellent', 'Good', 'Fair', 'Poor', 'Avoid']:
        rating_samples = summary_df[summary_df['safety_rating'] == rating].head(3)
        if not rating_samples.empty:
            report.append(f"\n--- {rating} Rating Examples ---")
            for _, row in rating_samples.iterrows():
                report.append(f"  • {row['product_name']}")
                report.append(f"    Score: {row['safety_score']}, {row['ingredients_count']} ingredients")
                report.append(f"    {row['safety_explanation']}")
    
    # Recommendations
    report.append("\n" + "=" * 80)
    report.append("KEY FINDINGS & RECOMMENDATIONS")
    report.append("=" * 80)
    
    # Calculate coverage
    total_classified = len(combined_df)
    unknown_count = (combined_df['unified_category'] == 'Unknown').sum()
    known_pct = (1 - unknown_count / total_classified) * 100
    
    report.append(f"\n1. CLASSIFICATION COVERAGE")
    report.append(f"   - Known classifications: {known_pct:.1f}%")
    report.append(f"   - Unknown (needs more data): {(unknown_count/total_classified)*100:.1f}%")
    report.append(f"   - The unified database ({len(unified_df)} ingredients) needs expansion")
    report.append(f"     to cover more of the {combined_df['ingredient_name'].nunique():,} unique ingredients found")
    
    report.append(f"\n2. SAFETY CONCERNS")
    harmful_products = summary_df[summary_df['has_harmful_ingredients'] == True]
    report.append(f"   - {len(harmful_products):,} products ({len(harmful_products)/len(summary_df)*100:.1f}%) contain harmful ingredients")
    report.append(f"   - Most common harmful: preservatives, artificial colors, BHA/BHT")
    
    report.append(f"\n3. DATA SOURCE CONTRIBUTION")
    report.append(f"   - FSSAI: 41 ingredients (Indian regulatory standards)")
    report.append(f"   - WHO: 23 ingredients (JECFA ADI values)")
    report.append(f"   - GRAS: 22 ingredients (FDA SCOGS database)")
    report.append(f"   - Combined approach provides more comprehensive coverage")
    
    report.append(f"\n4. RECOMMENDATIONS FOR IMPROVEMENT")
    report.append(f"   a) Expand unified database with more ingredients from:")
    report.append(f"      - EU E-number database")
    report.append(f"      - Codex Alimentarius")
    report.append(f"      - Additional scientific literature")
    report.append(f"   b) Implement fuzzy matching for ingredient name variations")
    report.append(f"   c) Add quantity-based risk assessment when nutrition data available")
    report.append(f"   d) Consider NOVA classification for processing level")
    
    report.append("\n" + "=" * 80)
    report.append("OUTPUT FILES")
    report.append("=" * 80)
    report.append(f"1. Combined classifications: {OUTPUT_COMBINED}")
    report.append(f"2. Product safety summary: {OUTPUT_DIR}/openfoodfacts_product_safety_summary.csv")
    report.append(f"3. Unified database: {OUTPUT_DIR}/unified_ingredient_database_full.csv")
    report.append(f"4. Statistics: {OUTPUT_DIR}/classification_statistics.csv")
    report.append(f"5. This report: {OUTPUT_REPORT}")
    
    report.append("\n" + "=" * 80)
    
    report_text = "\n".join(report)
    
    # Save report
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"Report saved: {OUTPUT_REPORT}")
    print("\n" + report_text)
    
    return report_text


if __name__ == "__main__":
    print("=" * 80)
    print("COMBINING BATCH FILES & GENERATING FINAL REPORT")
    print("=" * 80)
    
    combined = combine_batches()
    generate_report(combined)
    
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE!")
    print("=" * 80)
