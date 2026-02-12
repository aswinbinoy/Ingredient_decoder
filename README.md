# Ingredient Decoder – AI-Based Food Ingredient Transparency System

## Overview
Ingredient Decoder is an NLP-powered system that analyzes packaged food ingredient labels and classifies them as Safe, Moderate, or Harmful.

## Model
Base Model: LLaMA-3-8B-Instruct  
Fine-tuning Framework: Unsloth  
Quantization: 4-bit for Google Colab compatibility  

## Dataset Sources
- FSSAI Additive Regulations
- Open Food Facts Dataset
- WHO & FDA Safety References

## Pipeline
Data Collection → Preprocessing → Safety Mapping → Instruction Dataset Creation → LLM Fine-Tuning → Risk Classification

## Output
- Ingredient Safety Category
- Allergen Detection
- Plain-English Health Explanation
- Color-coded Risk Levels

## Run Training
```bash
python src/data_preprocessing.py
python src/create_instruction_dataset.py
python src/train_unsloth.py



#file structure

ingredient-decoder/
│
├── data/
│   ├── raw/
│   │   ├── openfoodfacts_raw.csv
│   │   ├── fssai_raw.csv
│   │
│   ├── processed/
│   │   ├── merged_cleaned.csv
│   │   ├── instruction_dataset.jsonl
│
├── src/
│   ├── data_preprocessing.py
│   ├── safety_dictionary.py
│   ├── create_instruction_dataset.py
│   ├── train_unsloth.py
│   ├── inference.py
│
├── notebooks/
│   ├── colab_training.ipynb
│
├── models/
│   ├── finetuned_model/
│
├── README.md
├── requirements.txt
└── .gitignore
