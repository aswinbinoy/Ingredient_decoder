"""
Convert Final Classified Dataset to Instruction Format (JSONL)
================================================================
This script converts the classified dataset into JSONL format suitable for 
LLM fine-tuning. Each entry contains:
- instruction: The task description
- input: The ingredient name
- output: Risk level and explanation

Output formats:
1. Full dataset with all samples
2. Deduplicated dataset (unique ingredients only)
3. Balanced dataset (equal samples per category)
"""

import pandas as pd
import json
import os
from datetime import datetime
from collections import defaultdict

# Paths
INPUT_FILE = r'C:\code\llm_project\Ingredient_decoder\data\processed\final_classified_dataset.csv'
OUTPUT_DIR = r'C:\code\llm_project\Ingredient_decoder\data\instruction_data'

# Output files
OUTPUT_JSONL_FULL = f'{OUTPUT_DIR}/ingredient_safety_full.jsonl'
OUTPUT_JSONL_UNIQUE = f'{OUTPUT_DIR}/ingredient_safety_unique.jsonl'
OUTPUT_JSONL_BALANCED = f'{OUTPUT_DIR}/ingredient_safety_balanced.jsonl'
OUTPUT_STATS = f'{OUTPUT_DIR}/conversion_statistics.json'
OUTPUT_REPORT = f'{OUTPUT_DIR}/instruction_dataset_report.txt'


def generate_explanation(row):
    """Generate a natural language explanation for the ingredient"""
    ingredient = row['ingredient_name']
    risk = row['simplified_category']
    rationale = row.get('classification_rationale', '')
    sources = row.get('sources_available', '')
    
    # Risk level descriptions
    risk_descriptions = {
        'Safe': 'generally recognized as safe for consumption',
        'Moderate': 'safe when consumed within recommended limits, but some individuals may be sensitive',
        'Harmful': 'may pose health risks and should be avoided or consumed with caution'
    }
    
    # Build explanation
    explanation_parts = []
    
    # Base risk statement
    base_risk = risk_descriptions.get(risk, 'classification uncertain')
    explanation_parts.append(f"This ingredient is {base_risk}.")
    
    # Add source-based information
    if 'FSSAI' in sources:
        if 'Safe' in str(row.get('fssai_category', '')):
            explanation_parts.append("Approved as safe by FSSAI (Indian food safety standards).")
        elif 'Moderate' in str(row.get('fssai_category', '')):
            explanation_parts.append("FSSAI recommends consumption within specified limits.")
    
    if 'WHO' in sources:
        who_cat = str(row.get('who_category', ''))
        if 'Low Concern' in who_cat:
            explanation_parts.append("WHO considers this additive low concern.")
        elif 'Moderate Concern' in who_cat:
            explanation_parts.append("WHO advises moderate consumption based on JECFA evaluation.")
        elif 'High Concern' in who_cat:
            explanation_parts.append("WHO has flagged potential health concerns with this substance.")
    
    if 'GRAS' in sources:
        gras_cat = str(row.get('gras_category', ''))
        if gras_cat == 'Safe':
            explanation_parts.append("FDA GRAS (Generally Recognized As Safe) certified.")
        elif gras_cat == 'Moderate':
            explanation_parts.append("FDA GRAS with some usage restrictions.")
    
    # Add specific warnings for harmful ingredients
    if risk == 'Harmful':
        harmful_warnings = {
            'red 40': 'This artificial food dye has been linked to hyperactivity in children.',
            'yellow 5': 'This artificial dye may cause allergic reactions and hyperactivity.',
            'sodium nitrite': 'Can form carcinogenic compounds; linked to increased cancer risk.',
            'bht': 'Synthetic antioxidant with potential carcinogenic properties.',
            'bha': 'Preservative classified as potentially carcinogenic.',
            'tbhq': 'Synthetic preservative with genotoxicity concerns.',
        }
        
        ing_lower = ingredient.lower()
        for keyword, warning in harmful_warnings.items():
            if keyword in ing_lower:
                explanation_parts.append(warning)
                break
    
    # Combine explanation
    explanation = ' '.join(explanation_parts)
    
    # Ensure explanation is not too long
    if len(explanation) > 300:
        explanation = explanation[:297] + '...'
    
    return explanation


def create_instruction_entry(ingredient, risk, explanation, instruction_type='standard'):
    """Create a single instruction-format entry"""
    
    # Different instruction templates for variety
    instructions = {
        'standard': "Analyze this food ingredient and classify its safety level as Safe, Moderate, or Harmful. Provide a brief explanation.",
        'simple': "Is this ingredient safe to consume? Classify as Safe, Moderate, or Harmful with explanation.",
        'detailed': "Evaluate the health risk of this food ingredient. Consider regulatory approvals (FSSAI, FDA GRAS, WHO) and potential health effects. Output: Safe, Moderate, or Harmful with explanation.",
        'consumer': "As a food safety expert, tell me if this ingredient is safe. Use categories: Safe, Moderate, or Harmful. Explain your reasoning.",
        'technical': "Classify this food additive/ingredient based on toxicological data and regulatory status. Categories: Safe (no known risks), Moderate (safe within limits), Harmful (potential health risks). Provide scientific rationale."
    }
    
    instruction = instructions.get(instruction_type, instructions['standard'])
    
    output = f"Risk Level: {risk}\n\nExplanation: {explanation}"
    
    return {
        'instruction': instruction,
        'input': ingredient,
        'output': output
    }


def convert_to_jsonl(df, output_file, deduplicate=False, balance=False, max_per_category=None):
    """Convert DataFrame to JSONL format"""
    
    print(f"\nConverting to JSONL...")
    print(f"  Input rows: {len(df):,}")
    
    # Remove rows with unknown category
    df_clean = df[df['simplified_category'] != 'Unknown'].copy()
    print(f"  After removing Unknown: {len(df_clean):,}")
    
    if deduplicate:
        # Keep unique ingredients only
        df_clean = df_clean.drop_duplicates(subset=['ingredient_name'], keep='first')
        print(f"  After deduplication: {len(df_clean):,}")
    
    if balance and not deduplicate:
        # Balance categories
        category_counts = df_clean['simplified_category'].value_counts()
        min_count = category_counts.min()
        
        if max_per_category:
            target_count = min(min_count, max_per_category)
        else:
            target_count = min_count
        
        print(f"  Balancing categories (target: {target_count} per category)...")
        
        balanced_dfs = []
        for category in df_clean['simplified_category'].unique():
            cat_df = df_clean[df_clean['simplified_category'] == category].sample(n=target_count, random_state=42)
            balanced_dfs.append(cat_df)
        
        df_clean = pd.concat(balanced_dfs, ignore_index=True)
        df_clean = df_clean.sample(frac=1, random_state=42).reset_index(drop=True)  # Shuffle
        print(f"  Balanced dataset size: {len(df_clean):,}")
    
    # Generate explanations and create entries
    print(f"  Generating explanations...")
    entries = []
    
    # Use different instruction types for variety
    instruction_types = ['standard', 'simple', 'detailed', 'consumer', 'technical']
    
    for idx, row in df_clean.iterrows():
        explanation = generate_explanation(row)
        instruction_type = instruction_types[idx % len(instruction_types)]  # Rotate through types
        
        entry = create_instruction_entry(
            ingredient=row['ingredient_name'],
            risk=row['simplified_category'],
            explanation=explanation,
            instruction_type=instruction_type
        )
        entries.append(entry)
    
    # Save to JSONL
    print(f"  Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"  Saved {len(entries):,} entries")
    
    return entries


def generate_statistics(df, entries_full, entries_unique):
    """Generate conversion statistics"""
    
    stats = {
        'conversion_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'input_dataset': {
            'total_rows': len(df),
            'unique_ingredients': df['ingredient_name'].nunique(),
            'categories': df['simplified_category'].value_counts().to_dict()
        },
        'output_datasets': {
            'full_jsonl': {
                'entries': len(entries_full),
                'file': OUTPUT_JSONL_FULL
            },
            'unique_jsonl': {
                'entries': len(entries_unique),
                'file': OUTPUT_JSONL_UNIQUE
            }
        },
        'category_distribution_full': {},
        'category_distribution_unique': {}
    }
    
    # Category distribution for full dataset
    for cat in ['Safe', 'Moderate', 'Harmful']:
        count = sum(1 for e in entries_full if f"Risk Level: {cat}" in e['output'])
        stats['category_distribution_full'][cat] = count
    
    # Category distribution for unique dataset
    for cat in ['Safe', 'Moderate', 'Harmful']:
        count = sum(1 for e in entries_unique if f"Risk Level: {cat}" in e['output'])
        stats['category_distribution_unique'][cat] = count
    
    # Save statistics
    with open(OUTPUT_STATS, 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats


def generate_report(stats):
    """Generate human-readable report"""
    
    report = []
    report.append("=" * 80)
    report.append("INSTRUCTION DATASET CONVERSION REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {stats['conversion_date']}")
    report.append("")
    
    report.append("\n" + "=" * 80)
    report.append("INPUT DATASET")
    report.append("=" * 80)
    report.append(f"Source file: {INPUT_FILE}")
    report.append(f"Total rows: {stats['input_dataset']['total_rows']:,}")
    report.append(f"Unique ingredients: {stats['input_dataset']['unique_ingredients']:,}")
    report.append("\nCategory distribution:")
    for cat, count in stats['input_dataset']['categories'].items():
        pct = count / stats['input_dataset']['total_rows'] * 100
        report.append(f"  {cat}: {count:,} ({pct:.1f}%)")
    
    report.append("\n" + "=" * 80)
    report.append("OUTPUT DATASETS")
    report.append("=" * 80)
    
    report.append(f"\n1. Full Dataset (all samples)")
    report.append(f"   File: {OUTPUT_JSONL_FULL}")
    report.append(f"   Entries: {stats['output_datasets']['full_jsonl']['entries']:,}")
    report.append(f"   Category distribution:")
    for cat, count in stats['category_distribution_full'].items():
        pct = count / stats['output_datasets']['full_jsonl']['entries'] * 100
        report.append(f"     {cat}: {count:,} ({pct:.1f}%)")
    
    report.append(f"\n2. Unique Dataset (deduplicated)")
    report.append(f"   File: {OUTPUT_JSONL_UNIQUE}")
    report.append(f"   Entries: {stats['output_datasets']['unique_jsonl']['entries']:,}")
    report.append(f"   Category distribution:")
    for cat, count in stats['category_distribution_unique'].items():
        pct = count / stats['output_datasets']['unique_jsonl']['entries'] * 100
        report.append(f"     {cat}: {count:,} ({pct:.1f}%)")
    
    report.append(f"\n3. Balanced Dataset (equal samples per category)")
    report.append(f"   File: {OUTPUT_JSONL_BALANCED}")
    report.append(f"   Note: Created for balanced training")
    
    report.append("\n" + "=" * 80)
    report.append("JSONL FORMAT EXAMPLE")
    report.append("=" * 80)
    report.append("""
{
  "instruction": "Analyze this food ingredient and classify its safety level as Safe, Moderate, or Harmful. Provide a brief explanation.",
  "input": "citric acid",
  "output": "Risk Level: Safe\\n\\nExplanation: This ingredient is generally recognized as safe for consumption. Approved as safe by FSSAI (Indian food safety standards). FDA GRAS (Generally Recognized As Safe) certified."
}
""")
    
    report.append("\n" + "=" * 80)
    report.append("USAGE INSTRUCTIONS")
    report.append("=" * 80)
    report.append("For LLM Fine-tuning:")
    report.append("  1. Use 'unique_jsonl' for efficient training (no duplicates)")
    report.append("  2. Use 'full_jsonl' for maximum data augmentation")
    report.append("  3. Use 'balanced_jsonl' for balanced category representation")
    report.append("")
    report.append("Recommended training split:")
    report.append("  - Training: 80%")
    report.append("  - Validation: 10%")
    report.append("  - Test: 10%")
    report.append("")
    report.append("Compatible frameworks:")
    report.append("  - HuggingFace Transformers")
    report.append("  - Unsloth (for LLaMA fine-tuning)")
    report.append("  - OpenAI fine-tuning API")
    report.append("  - Any JSONL-compatible LLM training pipeline")
    
    report.append("\n" + "=" * 80)
    
    report_text = "\n".join(report)
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print("\n" + report_text)
    
    return report_text


def main():
    """Main conversion function"""
    print("=" * 80)
    print("CONVERTING TO INSTRUCTION FORMAT (JSONL)")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load dataset
    print(f"\n[1/5] Loading dataset...")
    df = pd.read_csv(INPUT_FILE)
    print(f"  Loaded {len(df):,} rows")
    
    # Create full JSONL
    print(f"\n[2/5] Creating full JSONL dataset...")
    entries_full = convert_to_jsonl(df, OUTPUT_JSONL_FULL, deduplicate=False)
    
    # Create unique JSONL (deduplicated)
    print(f"\n[3/5] Creating unique JSONL dataset...")
    entries_unique = convert_to_jsonl(df, OUTPUT_JSONL_UNIQUE, deduplicate=True)
    
    # Create balanced JSONL
    print(f"\n[4/5] Creating balanced JSONL dataset...")
    df_clean = df[df['simplified_category'] != 'Unknown'].copy()
    entries_balanced = convert_to_jsonl(df_clean, OUTPUT_JSONL_BALANCED, 
                                         deduplicate=True, balance=True, max_per_category=500)
    
    # Generate statistics
    print(f"\n[5/5] Generating statistics and report...")
    stats = generate_statistics(df, entries_full, entries_unique)
    generate_report(stats)
    
    print(f"\n" + "=" * 80)
    print("CONVERSION COMPLETE!")
    print("=" * 80)
    print(f"\nOutput files:")
    print(f"  1. {OUTPUT_JSONL_FULL} ({os.path.getsize(OUTPUT_JSONL_FULL)/1024/1024:.1f} MB)")
    print(f"  2. {OUTPUT_JSONL_UNIQUE} ({os.path.getsize(OUTPUT_JSONL_UNIQUE)/1024/1024:.1f} MB)")
    print(f"  3. {OUTPUT_JSONL_BALANCED} ({os.path.getsize(OUTPUT_JSONL_BALANCED)/1024/1024:.1f} MB)")
    print(f"  4. {OUTPUT_STATS}")
    print(f"  5. {OUTPUT_REPORT}")
    
    return stats


if __name__ == "__main__":
    stats = main()
