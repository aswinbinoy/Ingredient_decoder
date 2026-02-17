"""
Multi-Source Ingredient Classification Analysis
================================================
This script analyzes whether combining FSSAI, WHO, and GRAS datasets 
can improve ingredient classification for Open Food Facts data.

Approach:
1. Create/load threshold data from FSSAI, WHO, and GRAS
2. Combine into unified safety thresholds
3. Test classification on sample Open Food Facts ingredients
4. Compare FSSAI-only vs. combined approach
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# ============================================================================
# STEP 1: Create WHO and GRAS threshold datasets (simulated based on real data)
# ============================================================================

def create_who_threshold_data():
    """
    Create WHO (World Health Organization) threshold data for food additives.
    Based on WHO/FAO Joint Expert Committee on Food Additives (JECFA) guidelines.
    """
    who_data = [
        # Nitrites/Nitrates
        ('Sodium nitrite', 0.07, 'High Concern', 'Can form carcinogenic nitrosamines; restricted in infant food'),
        ('Potassium nitrite', 0.07, 'High Concern', 'Can form carcinogenic nitrosamines; restricted in infant food'),
        ('Sodium nitrate', 3.7, 'Moderate Concern', 'Can form carcinogenic nitrosamines under certain conditions'),
        ('Potassium nitrate', 3.7, 'Moderate Concern', 'Can form carcinogenic nitrosamines under certain conditions'),
        # Sulfites
        ('Sulfur dioxide', 0.7, 'Moderate Concern', 'Can trigger asthma attacks in sensitive individuals'),
        ('Sodium sulfite', 0.7, 'Moderate Concern', 'Can trigger asthma attacks in sensitive individuals'),
        ('Sodium bisulfite', 0.7, 'Moderate Concern', 'Can trigger asthma attacks in sensitive individuals'),
        ('Potassium bisulfite', 0.7, 'Moderate Concern', 'Can trigger asthma attacks in sensitive individuals'),
        # Benzoates
        ('Sodium benzoate', 5.0, 'Low Concern', 'May form benzene with vitamin C; generally safe within limits'),
        ('Potassium benzoate', 5.0, 'Low Concern', 'May form benzene with vitamin C; generally safe within limits'),
        ('Benzoic acid', 5.0, 'Low Concern', 'May form benzene with vitamin C; generally safe within limits'),
        # Sorbates
        ('Sorbic acid', 25.0, 'Low Concern', 'Generally well tolerated; rare allergic reactions'),
        ('Potassium sorbate', 25.0, 'Low Concern', 'Generally well tolerated; rare allergic reactions'),
        ('Calcium sorbate', 25.0, 'Low Concern', 'Generally well tolerated; rare allergic reactions'),
        # Antioxidants
        ('BHA', 0.5, 'High Concern', 'Potential carcinogen in high doses; restricted in some countries'),
        ('BHT', 1.0, 'High Concern', 'Potential carcinogen in high doses; restricted in some countries'),
        ('TBHQ', 0.7, 'High Concern', 'Potential carcinogen; genotoxic concerns at high doses'),
        # Sweeteners
        ('Aspartame', 40.0, 'Moderate Concern', 'Safe for most; contraindicated for phenylketonurics'),
        ('Acesulfame potassium', 15.0, 'Moderate Concern', 'Safe within ADI; limited long-term data'),
        ('Saccharin', 5.0, 'Moderate Concern', 'Safe within ADI; possible bladder cancer concerns at very high doses'),
        # Food Colours
        ('Tartrazine', 7.5, 'Moderate Concern', 'May cause hyperactivity in children; allergic reactions'),
        ('Sunset Yellow FCF', 2.5, 'Moderate Concern', 'May cause hyperactivity in children; allergic reactions'),
        ('Allura Red AC', 7.0, 'Moderate Concern', 'May cause hyperactivity in children; allergic reactions'),
        ('Ponceau 4R', 7.0, 'Moderate Concern', 'May cause hyperactivity in children; allergic reactions'),
        # Caramel/Phosphates
        ('Caramel color', 300.0, 'Low Concern', 'Generally safe; Class I preferred'),
        ('Phosphoric acid', 70.0, 'Moderate Concern', 'May affect bone health with excessive consumption'),
        ('Sodium phosphate', 70.0, 'Low Concern', 'Generally safe within limits'),
        # Others
        ('Caffeine', 6.0, 'Moderate Concern', 'Safe in moderation; addictive; restricted in infant food'),
        # Contaminants (very low ADI = highly toxic)
        ('Lead', 0.0036, 'Very High Concern', 'Neurotoxic; no safe level; minimize exposure'),
        ('Cadmium', 0.0025, 'Very High Concern', 'Nephrotoxic; no safe level; minimize exposure'),
        ('Mercury', 0.004, 'Very High Concern', 'Neurotoxic; no safe level; minimize exposure'),
        ('Aflatoxin', 0.0002, 'Very High Concern', 'Hepatotoxic carcinogen; no safe level; minimize exposure'),
    ]
    
    df = pd.DataFrame(who_data, columns=['additive_name', 'adi_value', 'who_category', 'who_notes'])
    df['source'] = 'WHO/JECFA'
    return df


def create_gras_threshold_data():
    """
    Create GRAS (Generally Recognized As Safe) threshold data.
    Based on FDA GRAS notices and determinations.
    """
    gras_data = [
        # Acids
        ('Citric acid', 'GRAS', 'Acidulant', 'Naturally occurring; safe in normal food use'),
        ('Malic acid', 'GRAS', 'Acidulant', 'Naturally occurring; safe in normal food use'),
        ('Tartaric acid', 'GRAS', 'Acidulant', 'Naturally occurring; safe in normal food use'),
        ('Fumaric acid', 'GRAS', 'Acidulant', 'Naturally occurring; safe in normal food use'),
        # Seasonings
        ('Salt', 'GRAS', 'Seasoning', 'Essential nutrient; excessive intake linked to hypertension'),
        ('Potassium chloride', 'GRAS', 'Seasoning', 'Salt substitute; safe for most; caution for kidney patients'),
        # Sweeteners
        ('Sugar', 'GRAS', 'Sweetener', 'Safe in moderation; excessive intake linked to obesity/diabetes'),
        ('Glucose', 'GRAS', 'Sweetener', 'Natural sugar; safe'),
        ('Fructose', 'GRAS', 'Sweetener', 'Natural sugar; safe in moderation'),
        ('High fructose corn syrup', 'GRAS', 'Sweetener', 'Controversial; safe within limits but linked to metabolic issues'),
        # Antioxidants/Vitamins
        ('Ascorbic acid', 'GRAS', 'Antioxidant', 'Essential vitamin; antioxidant; safe'),
        ('Tocopherols', 'GRAS', 'Antioxidant', 'Essential vitamin; antioxidant; safe'),
        # Emulsifiers
        ('Lecithin', 'GRAS', 'Emulsifier', 'Natural emulsifier; safe; may be allergenic (soy)'),
        ('Mono- and diglycerides', 'GRAS', 'Emulsifier', 'Safe; derived from fats'),
        # Thickeners
        ('Xanthan gum', 'GRAS', 'Thickener', 'Fermentation-derived; safe; may cause digestive issues in excess'),
        ('Guar gum', 'GRAS', 'Thickener', 'Plant-derived; safe; may cause digestive issues in excess'),
        ('Pectin', 'GRAS', 'Thickener', 'Fruit-derived; safe'),
        ('Carrageenan', 'GRAS', 'Thickener', 'Seaweed-derived; safe; some controversy on degraded forms'),
        # Leavening/Firming
        ('Sodium bicarbonate', 'GRAS', 'Leavening Agent', 'Natural leavening; safe'),
        ('Calcium carbonate', 'GRAS', 'Firming Agent', 'Natural mineral; safe'),
        # Flavorings
        ('Vanilla extract', 'GRAS', 'Flavoring', 'Natural flavoring; safe'),
        ('Natural flavors', 'GRAS', 'Flavoring', 'Generally safe; may contain allergens'),
        # Other
        ('Yeast', 'GRAS', 'Leavening Agent', 'Natural leavening; safe'),
        ('Baking soda', 'GRAS', 'Leavening Agent', 'Natural leavening; safe'),
        ('Acetic acid', 'GRAS', 'Acidulant', 'Natural acid (vinegar); safe'),
        ('Lactic acid', 'GRAS', 'Acidulant', 'Natural acid (fermentation); safe'),
        ('Gelatin', 'GRAS', 'Gelling Agent', 'Animal-derived; safe; dietary restrictions apply'),
        ('Collagen', 'GRAS', 'Gelling Agent', 'Animal-derived; safe'),
        ('Starch', 'GRAS', 'Thickener', 'Plant-derived; safe'),
        ('Modified food starch', 'GRAS', 'Thickener', 'Modified from natural starch; safe'),
        ('Sodium acetate', 'GRAS', 'Preservative', 'Fermentation-derived; safe'),
        ('Calcium acetate', 'GRAS', 'Preservative', 'Safe; calcium source'),
        ('Rosemary extract', 'GRAS', 'Natural Antioxidant', 'Natural antioxidant; safe alternative to synthetic'),
        ('Green tea extract', 'GRAS', 'Natural Antioxidant', 'Natural antioxidant; safe alternative to synthetic'),
        # Additives with some concerns
        ('Sodium benzoate', 'GRAS', 'Preservative', 'Safe within limits; may form benzene with vitamin C'),
        ('Titanium dioxide', 'GRAS', 'Colorant', 'Generally safe; some recent concerns on nanoparticle forms'),
        ('MSG', 'GRAS', 'Flavor Enhancer', 'Safe for most; some individuals report sensitivity'),
    ]
    
    df = pd.DataFrame(gras_data, columns=['additive_name', 'gras_status', 'gras_category', 'gras_notes'])
    df['source'] = 'FDA_GRAS'
    return df


# ============================================================================
# STEP 2: Load existing FSSAI data
# ============================================================================

def load_fssai_data():
    """Load existing FSSAI safety data"""
    fssai_path = r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv'
    if os.path.exists(fssai_path):
        df = pd.read_csv(fssai_path)
        # Standardize column names for merging
        df = df.rename(columns={
            'ingredient_name': 'additive_name',
            'safety_description': 'fssai_notes'
        })
        df['source'] = 'FSSAI'
        return df
    else:
        print(f"FSSAI data not found at {fssai_path}")
        return pd.DataFrame()


# ============================================================================
# STEP 3: Combine datasets with unified classification rules
# ============================================================================

def create_unified_classification(fssai_df, who_df, gras_df):
    """
    Combine all three sources into a unified classification system.
    
    Classification Logic:
    - If ANY source says "Harmful/High Concern" -> classify as Harmful
    - If ANY source says "Moderate Concern" -> classify as Moderate
    - If ALL sources say "Safe/GRAS/Low Concern" -> classify as Safe
    - Use most restrictive classification (safety-first approach)
    """
    
    # Combine all dataframes into unified format
    all_ingredients = {}
    
    # Process FSSAI data
    if not fssai_df.empty:
        for _, row in fssai_df.iterrows():
            name = row['additive_name'].lower().strip()
            all_ingredients[name] = {
                'ingredient': name,
                'fssai_category': row.get('safety_category', 'Unknown'),
                'who_category': None,
                'gras_category': None,
                'fssai_notes': row.get('fssai_notes', ''),
                'who_notes': None,
                'gras_notes': None,
                'adi_value': None,
                'sources_available': 'FSSAI'
            }
    
    # Process WHO data - merge with existing or add new
    for _, row in who_df.iterrows():
        name = row['additive_name'].lower().strip()
        if name in all_ingredients:
            # Update existing entry
            all_ingredients[name]['who_category'] = row['who_category']
            all_ingredients[name]['who_notes'] = row['who_notes']
            all_ingredients[name]['adi_value'] = row['adi_value']
            all_ingredients[name]['sources_available'] += ',WHO'
        else:
            # Add new entry
            all_ingredients[name] = {
                'ingredient': name,
                'fssai_category': None,
                'who_category': row['who_category'],
                'gras_category': None,
                'fssai_notes': None,
                'who_notes': row['who_notes'],
                'gras_notes': None,
                'adi_value': row['adi_value'],
                'sources_available': 'WHO'
            }
    
    # Process GRAS data - merge with existing or add new
    for _, row in gras_df.iterrows():
        name = row['additive_name'].lower().strip()
        if name in all_ingredients:
            # Update existing entry
            all_ingredients[name]['gras_category'] = row['gras_category']
            all_ingredients[name]['gras_notes'] = row['gras_notes']
            all_ingredients[name]['sources_available'] += ',GRAS'
        else:
            # Add new entry
            all_ingredients[name] = {
                'ingredient': name,
                'fssai_category': None,
                'who_category': None,
                'gras_category': row['gras_category'],
                'fssai_notes': None,
                'who_notes': None,
                'gras_notes': row['gras_notes'],
                'adi_value': None,
                'sources_available': 'GRAS'
            }
    
    unified_df = pd.DataFrame(list(all_ingredients.values()))
    
    # Apply unified classification rules
    unified_df['unified_category'] = unified_df.apply(classify_unified, axis=1)
    unified_df['classification_rationale'] = unified_df.apply(get_classification_rationale, axis=1)
    
    return unified_df


def classify_unified(row):
    """
    Apply unified classification based on all available sources.
    Uses most restrictive classification (safety-first approach).
    """
    categories = []
    
    # Map FSSAI category
    if row['fssai_category']:
        cat = str(row['fssai_category'])
        if 'Safe' in cat:
            categories.append(('FSSAI', 3))
        elif 'Moderate' in cat:
            categories.append(('FSSAI', 2))
        elif 'Harmful' in cat:
            categories.append(('FSSAI', 1))
    
    # Map WHO category
    if row['who_category']:
        cat = str(row['who_category'])
        if 'Low Concern' in cat:
            categories.append(('WHO', 3))
        elif 'Moderate Concern' in cat:
            categories.append(('WHO', 2))
        elif 'High Concern' in cat:
            categories.append(('WHO', 1))
        elif 'Very High Concern' in cat:
            categories.append(('WHO', 0))
    
    # Map GRAS category
    if row['gras_category']:
        # GRAS is generally safe, but check notes for concerns
        categories.append(('GRAS', 3))
    
    if not categories:
        return 'Unknown'
    
    # Use minimum score (most restrictive)
    min_score = min([score for _, score in categories])
    
    if min_score >= 3:
        return 'Safe'
    elif min_score == 2:
        return 'Moderate'
    elif min_score == 1:
        return 'Harmful'
    else:
        return 'Very Harmful'


def get_classification_rationale(row):
    """Generate explanation for the unified classification"""
    reasons = []
    
    if row['fssai_category']:
        reasons.append(f"FSSAI: {row['fssai_category']}")
    if row['who_category']:
        reasons.append(f"WHO: {row['who_category']}")
    if row['gras_category']:
        reasons.append(f"GRAS: {row['gras_category']}")
    
    if row['unified_category'] in ['Harmful', 'Very Harmful']:
        return f"Restricted: {'; '.join(reasons)}"
    elif row['unified_category'] == 'Moderate':
        return f"Use with caution: {'; '.join(reasons)}"
    else:
        return f"Generally safe: {'; '.join(reasons)}"


# ============================================================================
# STEP 4: Create test dataset from Open Food Facts ingredients
# ============================================================================

def create_test_ingredients():
    """
    Create a sample of ingredients commonly found in Open Food Facts
    to test the classification system.
    """
    test_ingredients = [
        # Common additives
        {'name': 'Sodium benzoate', 'product': 'Soft Drink'},
        {'name': 'Potassium sorbate', 'product': 'Fruit Juice'},
        {'name': 'Sodium nitrite', 'product': 'Processed Meat'},
        {'name': 'BHA', 'product': 'Breakfast Cereal'},
        {'name': 'BHT', 'product': 'Snack Food'},
        {'name': 'TBHQ', 'product': 'Fried Snacks'},
        {'name': 'Aspartame', 'product': 'Diet Soda'},
        {'name': 'Tartrazine', 'product': 'Candy'},
        {'name': 'Caramel color', 'product': 'Cola'},
        {'name': 'Phosphoric acid', 'product': 'Cola'},
        
        # Generally safe ingredients
        {'name': 'Citric acid', 'product': 'Fruit Snacks'},
        {'name': 'Ascorbic acid', 'product': 'Juice'},
        {'name': 'Pectin', 'product': 'Jam'},
        {'name': 'Xanthan gum', 'product': 'Salad Dressing'},
        {'name': 'Lecithin', 'product': 'Chocolate'},
        {'name': 'Salt', 'product': 'Chips'},
        {'name': 'Sugar', 'product': 'Cookies'},
        
        # Borderline ingredients
        {'name': 'Caffeine', 'product': 'Energy Drink'},
        {'name': 'Sulfur dioxide', 'product': 'Dried Fruit'},
        {'name': 'Sodium nitrate', 'product': 'Bacon'},
        {'name': 'MSG', 'product': 'Instant Noodles'},
        {'name': 'High fructose corn syrup', 'product': 'Soda'},
        {'name': 'Modified food starch', 'product': 'Processed Cheese'},
        {'name': 'Carrageenan', 'product': 'Almond Milk'},
        {'name': 'Titanium dioxide', 'product': 'Candy Coating'},
    ]
    
    return pd.DataFrame(test_ingredients)


# ============================================================================
# STEP 5: Test classification and compare approaches
# ============================================================================

def classify_with_fssai_only(ingredient_name, fssai_df):
    """Classify ingredient using FSSAI data only"""
    if fssai_df.empty:
        return 'Unknown', 'No FSSAI data available'
    
    # Try exact match
    match = fssai_df[fssai_df['additive_name'].str.lower() == ingredient_name.lower().strip()]
    if not match.empty:
        row = match.iloc[0]
        return row.get('safety_category', 'Unknown'), row.get('fssai_notes', '')
    
    # Try partial match
    for _, row in fssai_df.iterrows():
        if ingredient_name.lower() in row['additive_name'].lower():
            return row.get('safety_category', 'Unknown'), row.get('fssai_notes', '')
    
    return 'Unknown', 'Not found in FSSAI database'


def classify_with_unified(ingredient_name, unified_df):
    """Classify ingredient using unified (FSSAI + WHO + GRAS) data"""
    # Try exact match
    match = unified_df[unified_df['ingredient'] == ingredient_name.lower().strip()]
    if not match.empty:
        row = match.iloc[0]
        return row['unified_category'], row['classification_rationale']
    
    # Try partial match
    for _, row in unified_df.iterrows():
        if ingredient_name.lower() in row['ingredient'].lower():
            return row['unified_category'], row['classification_rationale']
    
    return 'Unknown', 'Not found in any database'


def run_classification_comparison(test_df, fssai_df, unified_df):
    """
    Compare FSSAI-only vs. unified classification on test ingredients.
    """
    results = []
    
    for _, row in test_df.iterrows():
        ingredient = row['name']
        product = row['product']
        
        # FSSAI-only classification
        fssai_cat, fssai_reason = classify_with_fssai_only(ingredient, fssai_df)
        
        # Unified classification
        unified_cat, unified_reason = classify_with_unified(ingredient, unified_df)
        
        # Determine if classification changed
        change_status = 'No Change'
        if fssai_cat == 'Unknown' and unified_cat != 'Unknown':
            change_status = 'Improved Coverage'
        elif fssai_cat != unified_cat and unified_cat != 'Unknown':
            # Check if unified is more restrictive
            safety_order = {'Safe': 4, 'Moderate': 3, 'Harmful': 2, 'Very Harmful': 1, 'Unknown': 0}
            if safety_order.get(unified_cat, 0) < safety_order.get(fssai_cat, 0):
                change_status = 'More Restrictive (Safer)'
            else:
                change_status = 'Classification Changed'
        
        results.append({
            'ingredient': ingredient,
            'product': product,
            'fssai_category': fssai_cat,
            'fssai_rationale': fssai_reason,
            'unified_category': unified_cat,
            'unified_rationale': unified_reason,
            'change_status': change_status
        })
    
    return pd.DataFrame(results)


# ============================================================================
# STEP 6: Generate analysis report
# ============================================================================

def generate_analysis_report(comparison_df, unified_df):
    """Generate comprehensive analysis report"""
    
    report = []
    report.append("=" * 80)
    report.append("MULTI-SOURCE INGREDIENT CLASSIFICATION ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Unified database summary
    report.append("\n" + "=" * 80)
    report.append("UNIFIED DATABASE SUMMARY")
    report.append("=" * 80)
    report.append(f"Total unique ingredients in unified database: {len(unified_df)}")
    report.append(f"\nSources coverage:")
    report.append(f"  - FSSAI covered: {unified_df['fssai_category'].notna().sum()}")
    report.append(f"  - WHO covered: {unified_df['who_category'].notna().sum()}")
    report.append(f"  - GRAS covered: {unified_df['gras_category'].notna().sum()}")
    report.append(f"  - Multiple sources: {(unified_df['sources_available'].str.count(',') > 0).sum()}")
    report.append(f"\nUnified classification distribution:")
    report.append(unified_df['unified_category'].value_counts().to_string())
    
    # Classification comparison summary
    report.append("\n" + "=" * 80)
    report.append("CLASSIFICATION COMPARISON (FSSAI-only vs. Unified)")
    report.append("=" * 80)
    report.append(f"Test ingredients analyzed: {len(comparison_df)}")
    report.append(f"\nChange status distribution:")
    report.append(comparison_df['change_status'].value_counts().to_string())
    
    # Coverage improvement
    fssai_unknown = (comparison_df['fssai_category'] == 'Unknown').sum()
    unified_unknown = (comparison_df['unified_category'] == 'Unknown').sum()
    coverage_improvement = fssai_unknown - unified_unknown
    
    report.append(f"\nCoverage Analysis:")
    report.append(f"  - FSSAI unknown: {fssai_unknown} ({fssai_unknown/len(comparison_df)*100:.1f}%)")
    report.append(f"  - Unified unknown: {unified_unknown} ({unified_unknown/len(comparison_df)*100:.1f}%)")
    report.append(f"  - Coverage improvement: {coverage_improvement} ingredients")
    
    # Safety improvement
    more_restrictive = (comparison_df['change_status'] == 'More Restrictive (Safer)').sum()
    improved_coverage = (comparison_df['change_status'] == 'Improved Coverage').sum()
    report.append(f"\nSafety Analysis:")
    report.append(f"  - Classifications made more restrictive: {more_restrictive}")
    report.append(f"  - Percentage: {more_restrictive/len(comparison_df)*100:.1f}%")
    report.append(f"  - Ingredients with improved coverage: {improved_coverage}")
    
    # Detailed examples
    report.append("\n" + "=" * 80)
    report.append("DETAILED CLASSIFICATION EXAMPLES")
    report.append("=" * 80)
    
    # Show improved coverage examples
    improved = comparison_df[comparison_df['change_status'] == 'Improved Coverage']
    if not improved.empty:
        report.append("\n--- Improved Coverage (FSSAI had no data) ---")
        for _, row in improved.head(5).iterrows():
            report.append(f"\n  Ingredient: {row['ingredient']} (in {row['product']})")
            report.append(f"    FSSAI: {row['fssai_category']}")
            report.append(f"    Unified: {row['unified_category']}")
            report.append(f"    Rationale: {row['unified_rationale']}")
    
    # Show more restrictive examples
    restrictive = comparison_df[comparison_df['change_status'] == 'More Restrictive (Safer)']
    if not restrictive.empty:
        report.append("\n--- More Restrictive Classification (Safer) ---")
        for _, row in restrictive.head(5).iterrows():
            report.append(f"\n  Ingredient: {row['ingredient']} (in {row['product']})")
            report.append(f"    FSSAI: {row['fssai_category']} -> {row['fssai_rationale']}")
            report.append(f"    Unified: {row['unified_category']} -> {row['unified_rationale']}")
    
    # Show no change examples (for validation)
    no_change = comparison_df[comparison_df['change_status'] == 'No Change']
    if not no_change.empty:
        report.append("\n--- Consistent Classifications (Validated) ---")
        for _, row in no_change.head(5).iterrows():
            report.append(f"\n  Ingredient: {row['ingredient']} (in {row['product']})")
            report.append(f"    Both FSSAI and Unified: {row['fssai_category']}")
    
    # Recommendations
    report.append("\n" + "=" * 80)
    report.append("RECOMMENDATIONS")
    report.append("=" * 80)
    
    if coverage_improvement > 0:
        report.append(f"\n[YES] COMBINING DATASETS IS BENEFICIAL")
        report.append(f"  - {coverage_improvement} additional ingredients can be classified")
        report.append(f"  - WHO data provides ADI values for quantitative risk assessment")
        report.append(f"  - GRAS data confirms safety of common food ingredients")
    
    if more_restrictive > 0:
        report.append(f"\n[YES] SAFETY IMPROVEMENT")
        report.append(f"  - {more_restrictive} ingredients have more conservative classification")
        report.append(f"  - WHO health warnings add important context")
    
    if improved_coverage > 0:
        report.append(f"\n[YES] COVERAGE IMPROVEMENT")
        report.append(f"  - {improved_coverage} ingredients now have classification (was Unknown)")
    
    report.append(f"\n[RECOMMENDED APPROACH:]")
    report.append(f"  1. Use unified classification for Open Food Facts analysis")
    report.append(f"  2. Prioritize WHO ADI values for quantitative thresholds")
    report.append(f"  3. Use most restrictive classification (safety-first)")
    report.append(f"  4. Include source attribution in explanations")
    
    report.append("\n" + "=" * 80)
    
    return "\n".join(report)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("Starting Multi-Source Ingredient Classification Analysis...")
    print("=" * 60)
    
    # Step 1: Create/load datasets
    print("\n[1/5] Loading datasets...")
    fssai_df = load_fssai_data()
    print(f"  - FSSAI data: {len(fssai_df)} entries")
    
    who_df = create_who_threshold_data()
    print(f"  - WHO data: {len(who_df)} entries")
    
    gras_df = create_gras_threshold_data()
    print(f"  - GRAS data: {len(gras_df)} entries")
    
    # Step 2: Create unified classification
    print("\n[2/5] Creating unified classification system...")
    unified_df = create_unified_classification(fssai_df, who_df, gras_df)
    print(f"  - Unified database: {len(unified_df)} unique ingredients")
    
    # Step 3: Create test ingredients
    print("\n[3/5] Creating test ingredient dataset...")
    test_df = create_test_ingredients()
    print(f"  - Test ingredients: {len(test_df)}")
    
    # Step 4: Run classification comparison
    print("\n[4/5] Running classification comparison...")
    comparison_df = run_classification_comparison(test_df, fssai_df, unified_df)
    
    # Step 5: Generate report
    print("\n[5/5] Generating analysis report...")
    report = generate_analysis_report(comparison_df, unified_df)
    
    # Save outputs
    output_dir = r'C:\code\llm_project\Ingredient_decoder\data\processed'
    
    # Save unified database
    unified_df.to_csv(f'{output_dir}/unified_ingredient_database.csv', index=False)
    print(f"\n[OK] Unified database saved to: {output_dir}/unified_ingredient_database.csv")
    
    # Save comparison results
    comparison_df.to_csv(f'{output_dir}/classification_comparison_results.csv', index=False)
    print(f"[OK] Comparison results saved to: {output_dir}/classification_comparison_results.csv")
    
    # Save report
    report_path = f'{output_dir}/multi_source_analysis_report.txt'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"[OK] Analysis report saved to: {report_path}")
    
    # Print report
    print("\n")
    print(report)
    
    # Print sample comparison table
    print("\n" + "=" * 80)
    print("SAMPLE CLASSIFICATION COMPARISON TABLE")
    print("=" * 80)
    print(comparison_df[['ingredient', 'product', 'fssai_category', 'unified_category', 'change_status']].to_string(index=False))
    
    return comparison_df, unified_df


if __name__ == "__main__":
    comparison_df, unified_df = main()
    print("\n" + "=" * 60)
    print("Analysis completed successfully!")
    print("=" * 60)
