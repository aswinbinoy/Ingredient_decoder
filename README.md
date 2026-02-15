# Ingredient Decoder – AI-Based Food Ingredient Transparency System

## Overview
Ingredient Decoder is an NLP-powered system that analyzes packaged food ingredient labels and classifies them as Safe, Moderate, or Harmful.

## Data Created
- `data/processed/fssai_additives.csv`: Extracted additive information from FSSAI regulations
- `data/processed/ingredient_safety_data.csv`: Final safety classification dataset
- `data/processed/comprehensive_ingredient_safety_db.csv`: Comprehensive database with Safe/Moderate/Harmful classifications
- `data/processed/final_combined_ingredient_data.csv`: Combined dataset with FSSAI and matched ingredient data
- `data/processed/sample_ingredient_classifications.csv`: Sample ingredient classifications from product data
- `data/processed/sample_ingredient_inputs.csv`: Sample inputs for testing
- `data/processed/classification_summary.csv`: Summary of safety classifications

## Model
Base Model: LLaMA-3-8B-Instruct
Fine-tuning Framework: Unsloth
Quantization: 4-bit for Google Colab compatibility

## Pipeline
Data Collection → Preprocessing → Safety Mapping → Instruction Dataset Creation → LLM Fine-Tuning → Risk Classification

## Output
- Ingredient Safety Category
- Allergen Detection
- Plain-English Health Explanation
- Color-coded Risk Levels

## Files Created
- `src/ingredient_decoder.py`: Main ingredient analysis class
- `requirements.txt`: Project dependencies

## Run Analysis
```bash
python src/ingredient_decoder.py
```

# File Structure
```
ingredient-decoder/
│
├── data/
│   ├── raw/
│   │   ├── en.openfoodfacts.org.products.csv.gz
│   │   ├── Chapter 3_Substances added to food(1).pdf
│   │   └── Ingredient_Decoder_Abstract_UPDATED.pdf
│   └── processed/
│       ├── fssai_additives.csv
│       ├── ingredient_safety_data.csv
│       └── sample_ingredient_inputs.csv
├── src/
│   └── ingredient_decoder.py
├── scripts/
│   ├── extract_pdfs.py
│   ├── parse_additives.py
│   ├── parse_additives_fixed.py
│   ├── create_additives_csv.py
│   ├── extract_specific_additives.py
│   ├── check_second_pdf.py
│   ├── combine_datasets.py
│   ├── create_final_dataset.py
│   ├── test_decoder.py
│   └── project_summary.py
├── notebooks/
├── models/
├── README.md
├── requirements.txt
└── .gitignore
```