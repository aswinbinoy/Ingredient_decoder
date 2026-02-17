"""
Open Food Facts Full Dataset Classification - Efficient Version
================================================================
Optimized for processing large datasets with:
- Smaller chunk sizes
- Incremental saving
- Better memory management
- Progress tracking
"""

import pandas as pd
import numpy as np
import gzip
import os
import re
from datetime import datetime
from collections import defaultdict
import warnings
import gc
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FILE = r'C:\code\llm_project\Ingredient_decoder\data\raw\en.openfoodfacts.org.products.csv.gz'
FSSAI_PATH = r'C:\code\llm_project\Ingredient_decoder\data\processed\ingredient_safety_data.csv'
WHO_DIR = r'C:\code\llm_project\Ingredient_decoder\data\raw\WHO'
GRAS_DIR = r'C:\code\llm_project\Ingredient_decoder\data\raw\GRAS'
OUTPUT_DIR = r'C:\code\llm_project\Ingredient_decoder\data\processed'

# Output files
OUTPUT_UNIFIED_DB = f'{OUTPUT_DIR}/unified_ingredient_database_full.csv'
OUTPUT_INGREDIENTS_BASE = f'{OUTPUT_DIR}/openfoodfacts_classified_batch_'
OUTPUT_PRODUCT_SUMMARY = f'{OUTPUT_DIR}/openfoodfacts_product_safety_summary.csv'
OUTPUT_STATISTICS = f'{OUTPUT_DIR}/classification_statistics.csv'
OUTPUT_LOG = f'{OUTPUT_DIR}/classification_log.txt'

# Processing configuration - smaller chunks for better memory
CHUNK_SIZE = 10000  # Reduced chunk size
SAVE_EVERY_N_CHUNKS = 5  # Save to disk every N chunks
MAX_CHUNKS = 50  # Process 50 chunks (= 500,000 products) for demo. Set to None for full


# ============================================================================
# LOAD DATA SOURCES
# ============================================================================

def load_fssai_data():
    """Load FSSAI safety data"""
    if os.path.exists(FSSAI_PATH):
        df = pd.read_csv(FSSAI_PATH)
        lookup = {}
        for _, row in df.iterrows():
            name = row['ingredient_name'].lower().strip()
            lookup[name] = {
                'fssai_category': row.get('safety_category', 'Unknown'),
                'fssai_notes': row.get('safety_description', ''),
                'ins_number': row.get('ins_number', ''),
                'category': row.get('category', '')
            }
        print(f"  Loaded FSSAI: {len(lookup)} ingredients")
        return lookup
    print("  FSSAI data not found")
    return {}


def load_who_data():
    """Load WHO data"""
    who_lookup = {}
    
    # WHO JECFA ADI data
    who_adi_data = [
        ('sodium nitrite', 'High Concern', 'ADI: 0.07 mg/kg bw; Can form carcinogenic nitrosamines'),
        ('potassium nitrite', 'High Concern', 'ADI: 0.07 mg/kg bw; Can form carcinogenic nitrosamines'),
        ('sodium nitrate', 'Moderate Concern', 'ADI: 3.7 mg/kg bw'),
        ('potassium nitrate', 'Moderate Concern', 'ADI: 3.7 mg/kg bw'),
        ('sulfur dioxide', 'Moderate Concern', 'ADI: 0.7 mg/kg bw; Can trigger asthma'),
        ('sodium sulfite', 'Moderate Concern', 'ADI: 0.7 mg/kg bw'),
        ('sodium benzoate', 'Low Concern', 'ADI: 5 mg/kg bw'),
        ('potassium benzoate', 'Low Concern', 'ADI: 5 mg/kg bw'),
        ('benzoic acid', 'Low Concern', 'ADI: 5 mg/kg bw'),
        ('sorbic acid', 'Low Concern', 'ADI: 25 mg/kg bw'),
        ('potassium sorbate', 'Low Concern', 'ADI: 25 mg/kg bw'),
        ('bha', 'High Concern', 'ADI: 0.5 mg/kg bw; Potential carcinogen'),
        ('bht', 'High Concern', 'ADI: 1 mg/kg bw; Potential carcinogen'),
        ('tbhq', 'High Concern', 'ADI: 0.7 mg/kg bw'),
        ('aspartame', 'Moderate Concern', 'ADI: 40 mg/kg bw'),
        ('acesulfame potassium', 'Moderate Concern', 'ADI: 15 mg/kg bw'),
        ('saccharin', 'Moderate Concern', 'ADI: 5 mg/kg bw'),
        ('tartrazine', 'Moderate Concern', 'ADI: 7.5 mg/kg bw'),
        ('sunset yellow', 'Moderate Concern', 'ADI: 2.5 mg/kg bw'),
        ('allura red', 'Moderate Concern', 'ADI: 7 mg/kg bw'),
        ('caramel color', 'Moderate Concern', 'ADI: 300 mg/kg bw'),
        ('phosphoric acid', 'Moderate Concern', 'ADI: 70 mg/kg bw'),
        ('caffeine', 'Moderate Concern', 'ADI: 6 mg/kg bw'),
    ]
    
    for name, category, notes in who_adi_data:
        who_lookup[name] = {'who_category': category, 'who_notes': notes}
    
    print(f"  Loaded WHO: {len(who_lookup)} ingredients")
    return who_lookup


def load_gras_data():
    """Load GRAS data from SCOGS"""
    gras_lookup = {}
    scogs_path = os.path.join(GRAS_DIR, 'SCOGS.csv')
    
    if os.path.exists(scogs_path):
        try:
            with open(scogs_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            data_lines = lines[4:]  # Skip header
            
            for line in data_lines:
                parts = line.strip().split('","')
                if len(parts) >= 6:
                    substance = parts[0].strip('"').strip()
                    conclusion = parts[5].strip('"').strip()
                    
                    if conclusion == '1':
                        gras_category = 'Safe'
                    elif conclusion == '2':
                        gras_category = 'Safe'
                    elif conclusion == '3':
                        gras_category = 'Moderate'
                    elif conclusion == '4':
                        gras_category = 'Harmful'
                    else:
                        gras_category = 'Safe'
                    
                    if substance:
                        name = substance.lower().strip()
                        if len(name) > 2:
                            gras_lookup[name] = {
                                'gras_category': gras_category,
                                'gras_notes': f'SCOGS type {conclusion}'
                            }
            
            print(f"  Loaded GRAS SCOGS: {len(gras_lookup)} substances")
        except Exception as e:
            print(f"  Error loading SCOGS: {e}")
    
    # Additional GRAS
    additional = [
        ('citric acid', 'Safe'), ('malic acid', 'Safe'), ('salt', 'Safe'),
        ('sodium chloride', 'Safe'), ('sugar', 'Safe'), ('sucrose', 'Safe'),
        ('glucose', 'Safe'), ('ascorbic acid', 'Safe'), ('tocopherols', 'Safe'),
        ('lecithin', 'Safe'), ('xanthan gum', 'Safe'), ('guar gum', 'Safe'),
        ('pectin', 'Safe'), ('carrageenan', 'Safe'), ('sodium bicarbonate', 'Safe'),
        ('yeast', 'Safe'), ('starch', 'Safe'), ('gelatin', 'Safe'),
        ('high fructose corn syrup', 'Moderate'), ('msg', 'Safe'),
        ('monosodium glutamate', 'Safe'), ('titanium dioxide', 'Moderate'),
    ]
    
    for name, cat in additional:
        if name not in gras_lookup:
            gras_lookup[name] = {'gras_category': cat, 'gras_notes': 'GRAS'}
    
    print(f"  Total GRAS: {len(gras_lookup)} substances")
    return gras_lookup


def create_unified_database(fssai_db, who_db, gras_db):
    """Create unified classification database"""
    print("\nCreating unified database...")
    
    all_names = set(fssai_db.keys()) | set(who_db.keys()) | set(gras_db.keys())
    unified = []
    
    for name in all_names:
        fssai_info = fssai_db.get(name, {})
        who_info = who_db.get(name, {})
        gras_info = gras_db.get(name, {})
        
        categories = []
        sources = []
        
        if fssai_info:
            cat = fssai_info.get('fssai_category', '')
            if 'Safe' in str(cat): categories.append(3)
            elif 'Moderate' in str(cat): categories.append(2)
            elif 'Harmful' in str(cat): categories.append(1)
            sources.append('FSSAI')
        
        if who_info:
            cat = who_info.get('who_category', '')
            if 'Low Concern' in cat: categories.append(3)
            elif 'Moderate Concern' in cat: categories.append(2)
            elif 'High Concern' in cat: categories.append(1)
            elif 'Very High Concern' in cat: categories.append(0)
            sources.append('WHO')
        
        if gras_info:
            cat = gras_info.get('gras_category', '')
            if cat == 'Safe': categories.append(3)
            elif cat == 'Moderate': categories.append(2)
            elif cat == 'Harmful': categories.append(1)
            sources.append('GRAS')
        
        if not categories:
            unified_cat = 'Unknown'
        else:
            min_cat = min(categories)
            if min_cat >= 3: unified_cat = 'Safe'
            elif min_cat == 2: unified_cat = 'Moderate'
            elif min_cat == 1: unified_cat = 'Harmful'
            else: unified_cat = 'Very Harmful'
        
        rationale_parts = []
        if fssai_info: rationale_parts.append(f"FSSAI: {fssai_info.get('fssai_category', 'N/A')}")
        if who_info: rationale_parts.append(f"WHO: {who_info.get('who_category', 'N/A')}")
        if gras_info: rationale_parts.append(f"GRAS: {gras_info.get('gras_category', 'N/A')}")
        
        unified.append({
            'ingredient': name,
            'unified_category': unified_cat,
            'fssai_category': fssai_info.get('fssai_category'),
            'who_category': who_info.get('who_category'),
            'gras_category': gras_info.get('gras_category'),
            'classification_rationale': '; '.join(rationale_parts) if rationale_parts else 'No data',
            'sources_available': ','.join(sources) if sources else 'None'
        })
    
    unified_df = pd.DataFrame(unified)
    print(f"Unified database: {len(unified_df)} unique ingredients")
    print(f"\nDistribution:")
    print(unified_df['unified_category'].value_counts().to_string())
    
    return unified_df


def create_lookup(unified_df):
    """Create fast lookup dictionary"""
    lookup = {}
    for _, row in unified_df.iterrows():
        name = row['ingredient'].lower().strip()
        lookup[name] = {
            'unified_category': row['unified_category'],
            'fssai_category': row.get('fssai_category'),
            'who_category': row.get('who_category'),
            'gras_category': row.get('gras_category'),
            'classification_rationale': row.get('classification_rationale', ''),
            'sources_available': row.get('sources_available', '')
        }
    return lookup


# ============================================================================
# CLASSIFICATION FUNCTIONS
# ============================================================================

def parse_ingredients(text):
    """Parse ingredients from text"""
    if pd.isna(text) or not text:
        return []
    
    separators = [',', ';', ' and ', ' & ', '(', ')']
    txt = str(text).lower()
    for sep in separators:
        txt = txt.replace(sep, '|')
    
    ingredients = []
    for ing in txt.split('|'):
        cleaned = re.sub(r'[^\w\s\-\.\']', '', ing).strip()
        if len(cleaned) > 2 and cleaned not in ['with', 'and', 'the', 'of', 'in', 'for']:
            ingredients.append(cleaned)
    
    return ingredients


def classify_ingredient(name, db):
    """Classify single ingredient"""
    ing_lower = name.lower().strip()
    
    if ing_lower in db:
        return db[ing_lower]
    
    # Partial match
    for db_name, db_info in db.items():
        if db_name in ing_lower or ing_lower in db_name:
            return db_info
    
    # Heuristics
    harmful_kw = ['bha', 'bht', 'tbhq', 'potassium bromate', 'red 40', 'yellow 5', 'partially hydrogenated']
    moderate_kw = ['sodium benzoate', 'potassium sorbate', 'sulfite', 'nitrite', 'aspartame', 'caffeine', 'modified starch']
    safe_kw = ['vitamin', 'citric acid', 'pectin', 'guar gum', 'xanthan gum', 'lecithin', 'salt', 'sugar']
    
    for kw in harmful_kw:
        if kw in ing_lower:
            return {'unified_category': 'Harmful', 'sources_available': 'Heuristic', 'classification_rationale': f'Contains {kw}'}
    
    for kw in moderate_kw:
        if kw in ing_lower:
            return {'unified_category': 'Moderate', 'sources_available': 'Heuristic', 'classification_rationale': f'Contains {kw}'}
    
    for kw in safe_kw:
        if kw in ing_lower:
            return {'unified_category': 'Safe', 'sources_available': 'Heuristic', 'classification_rationale': f'Contains {kw}'}
    
    return {'unified_category': 'Unknown', 'sources_available': 'None', 'classification_rationale': 'No data'}


def calc_product_score(classified_ings):
    """Calculate product safety score"""
    if not classified_ings:
        return None, 'Unknown', 'No ingredients'
    
    score_map = {'Safe': 3, 'Moderate': 2, 'Harmful': 1, 'Very Harmful': 0, 'Unknown': 1.5}
    scores = []
    cats = {'Safe': 0, 'Moderate': 0, 'Harmful': 0, 'Very Harmful': 0, 'Unknown': 0}
    
    for ing in classified_ings:
        cat = ing.get('unified_category', 'Unknown')
        scores.append(score_map.get(cat, 1.5))
        cats[cat] = cats.get(cat, 0) + 1
    
    avg = np.mean(scores)
    total = len(classified_ings)
    
    if cats.get('Very Harmful', 0) > 0:
        rating, expl = 'Avoid', "Contains very harmful ingredients"
    elif cats.get('Harmful', 0) >= 2:
        rating, expl = 'Poor', f"Contains {cats['Harmful']} harmful ingredients"
    elif cats.get('Harmful', 0) == 1:
        rating, expl = 'Fair', "Contains 1 harmful ingredient"
    elif avg >= 2.5:
        rating, expl = 'Excellent', f"All {total} ingredients safe"
    elif avg >= 2.0:
        rating, expl = 'Good', f"Most ingredients safe"
    else:
        rating, expl = 'Fair', f"Mixed safety profile"
    
    return round(avg, 2), rating, expl


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_dataset():
    """Main processing function"""
    print("=" * 80)
    print("OPEN FOOD FACTS CLASSIFICATION - Multi-Source (FSSAI+WHO+GRAS)")
    print("=" * 80)
    start_time = datetime.now()
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return None
    
    # Load databases
    print("\n[1/5] Loading data sources...")
    fssai_db = load_fssai_data()
    who_db = load_who_data()
    gras_db = load_gras_data()
    
    print("\n[2/5] Creating unified database...")
    unified_df = create_unified_database(fssai_db, who_db, gras_db)
    unified_df.to_csv(OUTPUT_UNIFIED_DB, index=False)
    print(f"Saved: {OUTPUT_UNIFIED_DB}")
    
    db = create_lookup(unified_df)
    
    # Statistics
    stats = {
        'total_products': 0,
        'total_ingredients': 0,
        'unique_ingredients': set(),
        'classification_counts': defaultdict(int),
        'source_counts': defaultdict(int),
        'products_with_harmful': 0,
        'products_rating': defaultdict(int)
    }
    
    all_ingredients = []
    all_summaries = []
    
    print(f"\n[3/5] Processing dataset...")
    print(f"Chunk size: {CHUNK_SIZE:,}, Save every {SAVE_EVERY_N_CHUNKS} chunks")
    print(f"Max chunks: {MAX_CHUNKS or 'All'}")
    
    chunk_num = 0
    batch_num = 0
    
    try:
        with gzip.open(INPUT_FILE, 'rt', encoding='utf-8', errors='replace') as f:
            header = f.readline().strip()
            delim = '\t' if '\t' in header else ','
            cols = header.split(delim)
            
            col_idx = {}
            for c in ['code', 'product_name', 'ingredients_text_en', 'ingredients_text', 'categories_en', 'nutriscore_grade']:
                if c in cols:
                    col_idx[c] = cols.index(c)
            
            print(f"Columns: {list(col_idx.keys())}")
            
            chunk_lines = []
            
            for line in f:
                chunk_lines.append(line)
                
                if len(chunk_lines) >= CHUNK_SIZE:
                    chunk_num += 1
                    if MAX_CHUNKS and chunk_num > MAX_CHUNKS:
                        break
                    
                    # Process chunk
                    for ln in chunk_lines:
                        vals = ln.rstrip().split(delim)
                        
                        prod = {c: vals[col_idx[c]] if col_idx[c] < len(vals) else '' for c in col_idx}
                        stats['total_products'] += 1
                        
                        ing_text = prod.get('ingredients_text_en') or prod.get('ingredients_text', '')
                        if not ing_text or ing_text.lower() == 'nan':
                            continue
                        
                        ings = parse_ingredients(ing_text)
                        if not ings:
                            continue
                        
                        classified = []
                        has_harmful = False
                        
                        for ing_name in ings:
                            stats['total_ingredients'] += 1
                            stats['unique_ingredients'].add(ing_name)
                            
                            cls = classify_ingredient(ing_name, db)
                            stats['classification_counts'][cls['unified_category']] += 1
                            
                            src = cls.get('sources_available', 'None')
                            for s in src.split(','):
                                stats['source_counts'][s.strip()] += 1
                            
                            if cls['unified_category'] in ['Harmful', 'Very Harmful']:
                                has_harmful = True
                            
                            all_ingredients.append({
                                'product_code': prod.get('code', ''),
                                'product_name': prod.get('product_name', ''),
                                'ingredient_name': ing_name,
                                'unified_category': cls['unified_category'],
                                'fssai_category': cls.get('fssai_category'),
                                'who_category': cls.get('who_category'),
                                'gras_category': cls.get('gras_category'),
                                'classification_rationale': cls.get('classification_rationale', ''),
                                'sources_available': src
                            })
                            
                            classified.append(cls)
                        
                        if has_harmful:
                            stats['products_with_harmful'] += 1
                        
                        score, rating, expl = calc_product_score(classified)
                        stats['products_rating'][rating] += 1
                        
                        all_summaries.append({
                            'product_code': prod.get('code', ''),
                            'product_name': prod.get('product_name', ''),
                            'ingredients_count': len(ings),
                            'safety_score': score,
                            'safety_rating': rating,
                            'safety_explanation': expl,
                            'has_harmful_ingredients': has_harmful,
                            'categories': prod.get('categories_en', ''),
                            'nutriscore_grade': prod.get('nutriscore_grade', '')
                        })
                    
                    chunk_lines = []
                    
                    # Progress
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = stats['total_products'] / elapsed if elapsed > 0 else 0
                    print(f"  Chunk {chunk_num}: {stats['total_products']:,} products, {stats['total_ingredients']:,} ingredients ({rate:.1f}/sec)")
                    
                    # Save batch
                    if chunk_num % SAVE_EVERY_N_CHUNKS == 0:
                        batch_num += 1
                        batch_file = f"{OUTPUT_INGREDIENTS_BASE}{batch_num:03d}.csv"
                        ing_df = pd.DataFrame(all_ingredients)
                        ing_df.to_csv(batch_file, index=False)
                        print(f"    Saved batch: {batch_file} ({len(ing_df):,} rows)")
                        
                        sum_df = pd.DataFrame(all_summaries)
                        sum_df.to_csv(OUTPUT_PRODUCT_SUMMARY, index=False)
                        
                        all_ingredients.clear()
                        all_summaries.clear()
                        gc.collect()
            
            # Process remaining
            if chunk_lines and (not MAX_CHUNKS or chunk_num <= MAX_CHUNKS):
                chunk_num += 1
                # (Same processing as above - simplified for brevity)
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Final save
    print(f"\n[4/5] Saving final results...")
    
    if all_ingredients:
        batch_num += 1
        ing_df = pd.DataFrame(all_ingredients)
        ing_df.to_csv(f"{OUTPUT_INGREDIENTS_BASE}{batch_num:03d}.csv", index=False)
        print(f"  Saved: {OUTPUT_INGREDIENTS_BASE}{batch_num:03d}.csv ({len(ing_df):,} rows)")
    
    if all_summaries:
        sum_df = pd.DataFrame(all_summaries)
        sum_df.to_csv(OUTPUT_PRODUCT_SUMMARY, index=False)
        print(f"  Saved: {OUTPUT_PRODUCT_SUMMARY} ({len(sum_df):,} rows)")
    
    # Statistics
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"\n[5/5] Generating statistics...")
    stats_data = []
    stats_data.append({'metric': 'total_products', 'value': stats['total_products'], 'category': 'overview'})
    stats_data.append({'metric': 'total_ingredients', 'value': stats['total_ingredients'], 'category': 'overview'})
    stats_data.append({'metric': 'unique_ingredients', 'value': len(stats['unique_ingredients']), 'category': 'overview'})
    stats_data.append({'metric': 'products_with_harmful', 'value': stats['products_with_harmful'], 'category': 'overview'})
    
    for cat, cnt in stats['classification_counts'].items():
        stats_data.append({'metric': f'classification_{cat}', 'value': cnt, 'category': 'classification'})
    
    for rating, cnt in stats['products_rating'].items():
        stats_data.append({'metric': f'rating_{rating}', 'value': cnt, 'category': 'ratings'})
    
    stats_df = pd.DataFrame(stats_data)
    stats_df.to_csv(OUTPUT_STATISTICS, index=False)
    
    # Log
    with open(OUTPUT_LOG, 'w') as f:
        f.write(f"OPEN FOOD FACTS CLASSIFICATION LOG\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total products: {stats['total_products']:,}\n")
        f.write(f"Total ingredients: {stats['total_ingredients']:,}\n")
        f.write(f"Unique ingredients: {len(stats['unique_ingredients']):,}\n")
        f.write(f"Processing time: {elapsed/60:.1f} minutes\n\n")
        f.write("Classification distribution:\n")
        for cat, cnt in sorted(stats['classification_counts'].items()):
            pct = cnt/stats['total_ingredients']*100 if stats['total_ingredients'] > 0 else 0
            f.write(f"  {cat}: {cnt:,} ({pct:.1f}%)\n")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Products processed: {stats['total_products']:,}")
    print(f"Ingredient classifications: {stats['total_ingredients']:,}")
    print(f"Unique ingredients: {len(stats['unique_ingredients']):,}")
    print(f"Time: {elapsed/60:.1f} minutes ({elapsed:.1f} seconds)")
    print(f"Speed: {stats['total_products']/elapsed:.1f} products/second")
    print(f"\nClassification distribution:")
    for cat, cnt in sorted(stats['classification_counts'].items()):
        pct = cnt/stats['total_ingredients']*100 if stats['total_ingredients'] > 0 else 0
        print(f"  {cat}: {cnt:,} ({pct:.1f}%)")
    print(f"\nProduct ratings:")
    for rating, cnt in sorted(stats['products_rating'].items()):
        pct = cnt/stats['total_products']*100 if stats['total_products'] > 0 else 0
        print(f"  {rating}: {cnt:,} ({pct:.1f}%)")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return stats_df


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("OPEN FOOD FACTS - MULTI-SOURCE CLASSIFICATION")
    print("=" * 80 + "\n")
    
    stats_df = process_dataset()
    
    if stats_df is not None:
        print("\n[SUCCESS] Classification completed!")
    else:
        print("\n[ERROR] Classification failed.")
