"""
Flask API Backend for Ingredient Decoder
Integrates the fine-tuned LLaMA-3 model for ingredient classification
"""

import os
import zipfile
import shutil
import tempfile
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import re
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend


class IngredientDecoder:
    """
    Ingredient decoder using the fine-tuned LLaMA-3 model.
    Falls back to rule-based classification if model is unavailable.
    """

    def __init__(self, model_zip_path: str = None, safety_data_path: str = None):
        """
        Initialize the ingredient decoder.

        Args:
            model_zip_path: Path to the zipped fine-tuned model
            safety_data_path: Path to the CSV file containing ingredient safety information
        """
        self.model = None
        self.tokenizer = None
        self.model_dir = None
        self.safety_data = None
        self.ingredient_lookup = {}
        
        # Add common basic ingredients as fallback
        self._add_common_ingredients()

        # Try to load the fine-tuned model
        if model_zip_path and os.path.exists(model_zip_path):
            self._load_model(model_zip_path)

        # Load safety data for fallback
        if safety_data_path and os.path.exists(safety_data_path):
            self._load_safety_data(safety_data_path)
        else:
            # Default paths - prioritize unified database
            default_paths = [
                r'data\processed\unified_ingredient_database_full.csv',
                r'data\processed\comprehensive_ingredient_safety_db.csv',
                r'data\processed\ingredient_safety_data.csv'
            ]
            for path in default_paths:
                if os.path.exists(path):
                    self._load_safety_data(path)
                    break
    
    def _add_common_ingredients(self):
        """Add common basic ingredients as fallback."""
        common_ingredients = {
            'sugar': {'ins_number': 'Unknown', 'category': 'Sweetener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Consume in moderation.', 'health_impact': 'Safe when consumed in moderation'},
            'milk': {'ins_number': 'Unknown', 'category': 'Dairy', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common allergen.', 'health_impact': 'Safe. May cause allergic reactions in some individuals.'},
            'milk solids': {'ins_number': 'Unknown', 'category': 'Dairy', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common allergen.', 'health_impact': 'Safe. May cause allergic reactions in some individuals.'},
            'water': {'ins_number': 'Unknown', 'category': 'Base', 'safety_category': 'Safe', 'safety_description': 'Essential for life. Generally recognized as safe.', 'health_impact': 'Safe'},
            'salt': {'ins_number': 'Unknown', 'category': 'Seasoning', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Consume in moderation.', 'health_impact': 'Safe when consumed in moderation'},
            'cocoa butter': {'ins_number': 'Unknown', 'category': 'Fat', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'cocoa': {'ins_number': 'Unknown', 'category': 'Flavoring', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'wheat': {'ins_number': 'Unknown', 'category': 'Grain', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common allergen (gluten).', 'health_impact': 'Safe. May cause allergic reactions in individuals with celiac disease or gluten sensitivity.'},
            'wheat flour': {'ins_number': 'Unknown', 'category': 'Grain', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Contains gluten.', 'health_impact': 'Safe. May cause allergic reactions in individuals with celiac disease or gluten sensitivity.'},
            'flour': {'ins_number': 'Unknown', 'category': 'Grain', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'eggs': {'ins_number': 'Unknown', 'category': 'Protein', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common allergen.', 'health_impact': 'Safe. May cause allergic reactions in some individuals.'},
            'egg': {'ins_number': 'Unknown', 'category': 'Protein', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common allergen.', 'health_impact': 'Safe. May cause allergic reactions in some individuals.'},
            'butter': {'ins_number': 'Unknown', 'category': 'Dairy', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe when consumed in moderation'},
            'oil': {'ins_number': 'Unknown', 'category': 'Fat', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe when consumed in moderation'},
            'vegetable oil': {'ins_number': 'Unknown', 'category': 'Fat', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe when consumed in moderation'},
            'yeast': {'ins_number': 'Unknown', 'category': 'Leavening', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'baking powder': {'ins_number': 'Unknown', 'category': 'Leavening', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'baking soda': {'ins_number': 'Unknown', 'category': 'Leavening', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'vanilla': {'ins_number': 'Unknown', 'category': 'Flavoring', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'vanilla extract': {'ins_number': 'Unknown', 'category': 'Flavoring', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'chocolate': {'ins_number': 'Unknown', 'category': 'Flavoring', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe when consumed in moderation'},
            'honey': {'ins_number': 'Unknown', 'category': 'Sweetener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'cream': {'ins_number': 'Unknown', 'category': 'Dairy', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe when consumed in moderation'},
            'cheese': {'ins_number': 'Unknown', 'category': 'Dairy', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'soy': {'ins_number': 'Unknown', 'category': 'Protein', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common allergen.', 'health_impact': 'Safe. May cause allergic reactions in some individuals.'},
            'soy lecithin': {'ins_number': 'INS 322', 'category': 'Emulsifier', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common allergen.', 'health_impact': 'Safe. May cause allergic reactions in some individuals.'},
            'lecithin': {'ins_number': 'INS 322', 'category': 'Emulsifier', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            # Add more common additives
            'corn syrup': {'ins_number': 'Unknown', 'category': 'Sweetener', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe but high in fructose. Consume in moderation.', 'health_impact': 'Moderate - high sugar content'},
            'high fructose corn syrup': {'ins_number': 'Unknown', 'category': 'Sweetener', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe but high in fructose. Consume in moderation.', 'health_impact': 'Moderate - high sugar content, may contribute to metabolic issues'},
            'caramel color': {'ins_number': 'INS 150', 'category': 'Color', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe. Some types may contain 4-MEI.', 'health_impact': 'Moderate - generally safe but some concerns about byproducts'},
            'phosphoric acid': {'ins_number': 'INS 338', 'category': 'Acidulant', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe. Excessive consumption may affect bone health.', 'health_impact': 'Moderate - may interfere with calcium absorption'},
            'natural flavors': {'ins_number': 'Unknown', 'category': 'Flavoring', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Derived from natural sources.', 'health_impact': 'Safe'},
            'natural flavor': {'ins_number': 'Unknown', 'category': 'Flavoring', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Derived from natural sources.', 'health_impact': 'Safe'},
            'caffeine': {'ins_number': 'Unknown', 'category': 'Stimulant', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe in moderation. May cause jitters or sleep disturbances.', 'health_impact': 'Moderate - stimulant, consume in moderation'},
            'sodium benzoate': {'ins_number': 'INS 211', 'category': 'Preservative', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common food preservative.', 'health_impact': 'Safe when consumed within limits'},
            'benzoic acid': {'ins_number': 'INS 210', 'category': 'Preservative', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common food preservative.', 'health_impact': 'Safe when consumed within limits'},
            'citric acid': {'ins_number': 'INS 330', 'category': 'Acidulant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common food additive.', 'health_impact': 'Safe'},
            'ascorbic acid': {'ins_number': 'INS 300', 'category': 'Antioxidant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Vitamin C.', 'health_impact': 'Safe - essential vitamin'},
            'guar gum': {'ins_number': 'INS 412', 'category': 'Thickener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Plant-based thickener.', 'health_impact': 'Safe'},
            'xanthan gum': {'ins_number': 'INS 415', 'category': 'Thickener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common food thickener.', 'health_impact': 'Safe'},
            'carrageenan': {'ins_number': 'INS 407', 'category': 'Thickener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Derived from seaweed.', 'health_impact': 'Safe'},
            'pectin': {'ins_number': 'INS 440', 'category': 'Thickener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Derived from fruit.', 'health_impact': 'Safe'},
            'glucose syrup': {'ins_number': 'Unknown', 'category': 'Sweetener', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe. High in sugar.', 'health_impact': 'Moderate - high sugar content'},
            'fructose': {'ins_number': 'Unknown', 'category': 'Sweetener', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe. Fruit sugar.', 'health_impact': 'Moderate - consume in moderation'},
            'dextrose': {'ins_number': 'Unknown', 'category': 'Sweetener', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe. Simple sugar.', 'health_impact': 'Moderate - high glycemic index'},
            'maltodextrin': {'ins_number': 'Unknown', 'category': 'Thickener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Derived from starch.', 'health_impact': 'Safe'},
            'modified food starch': {'ins_number': 'Unknown', 'category': 'Thickener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'modified corn starch': {'ins_number': 'Unknown', 'category': 'Thickener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'gelatin': {'ins_number': 'Unknown', 'category': 'Gelling Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Derived from animal collagen.', 'health_impact': 'Safe'},
            'agar': {'ins_number': 'INS 406', 'category': 'Gelling Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Plant-based gelling agent.', 'health_impact': 'Safe'},
            'sorbitol': {'ins_number': 'INS 420', 'category': 'Sweetener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Sugar alcohol.', 'health_impact': 'Safe - may cause digestive issues in large amounts'},
            'mannitol': {'ins_number': 'INS 421', 'category': 'Sweetener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Sugar alcohol.', 'health_impact': 'Safe'},
            'sucralose': {'ins_number': 'INS 955', 'category': 'Sweetener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Artificial sweetener.', 'health_impact': 'Safe'},
            'aspartame': {'ins_number': 'INS 951', 'category': 'Sweetener', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe. Artificial sweetener. Not for phenylketonurics.', 'health_impact': 'Moderate - contains phenylalanine'},
            'acesulfame potassium': {'ins_number': 'INS 950', 'category': 'Sweetener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Artificial sweetener.', 'health_impact': 'Safe'},
            'stevia': {'ins_number': 'INS 960', 'category': 'Sweetener', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Natural sweetener.', 'health_impact': 'Safe'},
            'monosodium glutamate': {'ins_number': 'INS 621', 'category': 'Flavor Enhancer', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. May cause sensitivity in some individuals.', 'health_impact': 'Safe - some individuals may be sensitive'},
            'msg': {'ins_number': 'INS 621', 'category': 'Flavor Enhancer', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. May cause sensitivity in some individuals.', 'health_impact': 'Safe - some individuals may be sensitive'},
            'disodium inosinate': {'ins_number': 'INS 631', 'category': 'Flavor Enhancer', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'disodium guanylate': {'ins_number': 'INS 627', 'category': 'Flavor Enhancer', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'potassium sorbate': {'ins_number': 'INS 202', 'category': 'Preservative', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common preservative.', 'health_impact': 'Safe'},
            'calcium propionate': {'ins_number': 'INS 282', 'category': 'Preservative', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Common bread preservative.', 'health_impact': 'Safe'},
            'sodium nitrite': {'ins_number': 'INS 250', 'category': 'Preservative', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe in small amounts. Used in cured meats.', 'health_impact': 'Moderate - consume in moderation'},
            'sodium nitrate': {'ins_number': 'INS 251', 'category': 'Preservative', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe in small amounts. Used in cured meats.', 'health_impact': 'Moderate - consume in moderation'},
            'titanium dioxide': {'ins_number': 'INS 171', 'category': 'Color', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe. White colorant.', 'health_impact': 'Moderate - some concerns about nanoparticle forms'},
            'red 40': {'ins_number': 'Unknown', 'category': 'Color', 'safety_category': 'Moderate', 'safety_description': 'Artificial color. May cause hyperactivity in sensitive children.', 'health_impact': 'Moderate - may affect sensitive individuals'},
            'yellow 5': {'ins_number': 'INS 102', 'category': 'Color', 'safety_category': 'Moderate', 'safety_description': 'Artificial color. May cause allergic reactions in some individuals.', 'health_impact': 'Moderate - may cause allergies'},
            'blue 1': {'ins_number': 'INS 133', 'category': 'Color', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Artificial color.', 'health_impact': 'Safe'},
            'green 3': {'ins_number': 'INS 143', 'category': 'Color', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Artificial color.', 'health_impact': 'Safe'},
            'tartrazine': {'ins_number': 'INS 102', 'category': 'Color', 'safety_category': 'Moderate', 'safety_description': 'Artificial color. May cause allergic reactions.', 'health_impact': 'Moderate - may cause allergies'},
            'sunflower lecithin': {'ins_number': 'INS 322', 'category': 'Emulsifier', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'calcium carbonate': {'ins_number': 'INS 170', 'category': 'Anticaking Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'silicon dioxide': {'ins_number': 'INS 551', 'category': 'Anticaking Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Anti-caking agent.', 'health_impact': 'Safe'},
            'calcium phosphate': {'ins_number': 'INS 341', 'category': 'Anticaking Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'magnesium stearate': {'ins_number': 'INS 470', 'category': 'Anti-caking Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'stearic acid': {'ins_number': 'INS 570', 'category': 'Emulsifier', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'glycerin': {'ins_number': 'INS 422', 'category': 'Humectant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'glycerol': {'ins_number': 'INS 422', 'category': 'Humectant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'propylene glycol': {'ins_number': 'INS 1520', 'category': 'Humectant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'lactic acid': {'ins_number': 'INS 270', 'category': 'Acidulant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'malic acid': {'ins_number': 'INS 296', 'category': 'Acidulant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'tartaric acid': {'ins_number': 'INS 334', 'category': 'Acidulant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'fumaric acid': {'ins_number': 'INS 297', 'category': 'Acidulant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'sodium citrate': {'ins_number': 'INS 331', 'category': 'Emulsifier', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'potassium citrate': {'ins_number': 'INS 332', 'category': 'Emulsifier', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'calcium citrate': {'ins_number': 'INS 333', 'category': 'Firming Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'sodium bicarbonate': {'ins_number': 'INS 500', 'category': 'Leavening', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Baking soda.', 'health_impact': 'Safe'},
            'potassium bicarbonate': {'ins_number': 'INS 501', 'category': 'Leavening', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'ammonium bicarbonate': {'ins_number': 'INS 503', 'category': 'Leavening', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'calcium chloride': {'ins_number': 'INS 509', 'category': 'Firming Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'potassium chloride': {'ins_number': 'INS 508', 'category': 'Gelling Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'magnesium chloride': {'ins_number': 'INS 511', 'category': 'Firming Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'iron': {'ins_number': 'Unknown', 'category': 'Mineral', 'safety_category': 'Safe', 'safety_description': 'Essential mineral.', 'health_impact': 'Safe - essential nutrient'},
            'zinc': {'ins_number': 'Unknown', 'category': 'Mineral', 'safety_category': 'Safe', 'safety_description': 'Essential mineral.', 'health_impact': 'Safe - essential nutrient'},
            'calcium': {'ins_number': 'Unknown', 'category': 'Mineral', 'safety_category': 'Safe', 'safety_description': 'Essential mineral.', 'health_impact': 'Safe - essential nutrient'},
            'vitamin a': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'vitamin c': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'vitamin d': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'vitamin e': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'vitamin b': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'folic acid': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'niacin': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'riboflavin': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'thiamine': {'ins_number': 'Unknown', 'category': 'Vitamin', 'safety_category': 'Safe', 'safety_description': 'Essential vitamin.', 'health_impact': 'Safe - essential nutrient'},
            'beta carotene': {'ins_number': 'INS 160a', 'category': 'Color', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Natural color and vitamin A precursor.', 'health_impact': 'Safe'},
            'annatto': {'ins_number': 'INS 160b', 'category': 'Color', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Natural color.', 'health_impact': 'Safe'},
            'turmeric': {'ins_number': 'INS 100', 'category': 'Color', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Natural spice and color.', 'health_impact': 'Safe'},
            'paprika': {'ins_number': 'INS 160c', 'category': 'Color', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Natural spice and color.', 'health_impact': 'Safe'},
            'rosemary extract': {'ins_number': 'Unknown', 'category': 'Antioxidant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Natural antioxidant.', 'health_impact': 'Safe'},
            'tocopherols': {'ins_number': 'INS 306', 'category': 'Antioxidant', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Vitamin E.', 'health_impact': 'Safe'},
            'bha': {'ins_number': 'INS 320', 'category': 'Antioxidant', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe in limited amounts. Synthetic antioxidant.', 'health_impact': 'Moderate - some concerns at high doses'},
            'bht': {'ins_number': 'INS 321', 'category': 'Antioxidant', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe in limited amounts. Synthetic antioxidant.', 'health_impact': 'Moderate - some concerns at high doses'},
            'tbhq': {'ins_number': 'INS 319', 'category': 'Antioxidant', 'safety_category': 'Moderate', 'safety_description': 'Generally recognized as safe in limited amounts.', 'health_impact': 'Moderate - consume in moderation'},
            'shellac': {'ins_number': 'INS 904', 'category': 'Glazing Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Resinous glaze.', 'health_impact': 'Safe'},
            'beeswax': {'ins_number': 'INS 901', 'category': 'Glazing Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe.', 'health_impact': 'Safe'},
            'carnauba wax': {'ins_number': 'INS 903', 'category': 'Glazing Agent', 'safety_category': 'Safe', 'safety_description': 'Generally recognized as safe. Plant-based wax.', 'health_impact': 'Safe'},
        }
        
        for name, data in common_ingredients.items():
            if name not in self.ingredient_lookup:
                self.ingredient_lookup[name] = data

    def _load_model(self, model_zip_path: str):
        """Extract and load the fine-tuned PEFT/LoRA model."""
        try:
            logger.info(f"Loading model from {model_zip_path}")
            
            # Check if path is a directory (already extracted) or zip file
            if os.path.isdir(model_zip_path):
                # Model is already extracted
                adapter_path = model_zip_path
                logger.info(f"Using extracted model directory: {adapter_path}")
            else:
                # Extract from zip file
                self.model_dir = tempfile.mkdtemp(prefix='ingredient_model_')
                with zipfile.ZipFile(model_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.model_dir)
                
                # Find the adapter directory
                extracted_files = os.listdir(self.model_dir)
                logger.info(f"Extracted files: {extracted_files}")
                
                adapter_path = self.model_dir
                if 'final_model' in extracted_files:
                    adapter_path = os.path.join(self.model_dir, 'final_model')
            
            # Read adapter config to get base model
            adapter_config_path = os.path.join(adapter_path, 'adapter_config.json')
            if not os.path.exists(adapter_config_path):
                logger.warning(f"adapter_config.json not found at {adapter_config_path}")
                return

            with open(adapter_config_path, 'r') as f:
                adapter_config = json.load(f)

            base_model_name = adapter_config.get('base_model_name_or_path',
                                                  'unsloth/Llama-3-8B-Instruct-bnb-4bit')
            logger.info(f"Base model: {base_model_name}")
            logger.info(f"Adapter path: {adapter_path}")

            # Load base model and adapter using PEFT
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer
                from peft import PeftModel

                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(adapter_path)
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token

                # Load base model (4-bit quantized for memory efficiency)
                logger.info("Loading base LLaMA-3 model...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    base_model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map='auto' if torch.cuda.is_available() else None,
                    load_in_4bit=True if torch.cuda.is_available() else False,
                )

                # Load LoRA adapter
                logger.info("Loading LoRA adapter weights...")
                self.model = PeftModel.from_pretrained(self.model, adapter_path)

                # Merge adapter weights for faster inference
                self.model = self.model.merge_and_unload()

                self.model.eval()
                logger.info("Model loaded successfully!")

            except ImportError as e:
                logger.warning(f"Required libraries not available: {e}")
                logger.info("Install with: pip install peft accelerate bitsandbytes")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")
                logger.info("Will use rule-based fallback")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.info("Using rule-based fallback")

    def _load_safety_data(self, safety_data_path: str):
        """Load safety data for rule-based classification."""
        try:
            logger.info(f"Loading safety data from {safety_data_path}")
            self.safety_data = pd.read_csv(safety_data_path)

            # Create lookup dictionary
            for _, row in self.safety_data.iterrows():
                # Try both 'ingredient' and 'ingredient_name' columns
                ingredient_name = str(row.get('ingredient', row.get('ingredient_name', ''))).lower().strip()
                if ingredient_name:
                    # Get safety category from various possible columns
                    gras_cat = row.get('gras_category', '')
                    fssai_cat = row.get('fssai_category', '')
                    who_cat = row.get('who_category', '')
                    
                    # Determine overall safety category
                    safety_category = 'Safe'  # Default
                    if gras_cat and isinstance(gras_cat, str):
                        gras_cat = str(gras_cat).strip()
                        if 'Moderate' in gras_cat:
                            safety_category = 'Moderate'
                        elif 'Harmful' in gras_cat or 'High Concern' in gras_cat:
                            safety_category = 'Harmful'
                    if who_cat and isinstance(who_cat, str):
                        who_cat = str(who_cat).strip()
                        if 'High Concern' in who_cat:
                            safety_category = 'Harmful'
                        elif 'Moderate Concern' in who_cat and safety_category != 'Harmful':
                            safety_category = 'Moderate'
                    
                    # Build description from available fields
                    description_parts = []
                    if pd.notna(row.get('gras_category')) and row.get('gras_category'):
                        description_parts.append(f"GRAS: {row['gras_category']}")
                    if pd.notna(row.get('fssai_category')) and row.get('fssai_category'):
                        description_parts.append(f"FSSAI: {row['fssai_category']}")
                    if pd.notna(row.get('who_category')) and row.get('who_category'):
                        description_parts.append(f"WHO: {row['who_category']}")
                    if pd.notna(row.get('classification_rationale')) and row.get('classification_rationale'):
                        description_parts.append(str(row['classification_rationale']))
                    
                    self.ingredient_lookup[ingredient_name] = {
                        'ins_number': row.get('ins_number', 'Unknown'),
                        'category': row.get('unified_category', row.get('category', 'Unknown')),
                        'safety_category': safety_category,
                        'safety_description': ' | '.join(description_parts) if description_parts else 'Generally recognized as safe',
                        'health_impact': ' | '.join(description_parts) if description_parts else 'Generally recognized as safe'
                    }
            logger.info(f"Loaded {len(self.ingredient_lookup)} ingredients to lookup")
        except Exception as e:
            logger.error(f"Error loading safety data: {e}")

    def _predict_with_model(self, ingredient_text: str) -> Dict:
        """Use the fine-tuned LLaMA-3 model for prediction."""
        if self.model is None or self.tokenizer is None:
            return None

        try:
            import torch
            
            # Format input using the same template as training
            prompt = f"""### Instruction:
Analyze the ingredient and classify it as Safe, Moderate, or Harmful.

### Input:
{ingredient_text}

### Output:
"""

            # Tokenize and generate
            inputs = self.tokenizer(prompt, return_tensors='pt')
            
            # Move to GPU if available
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.95,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            # Decode response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract only the generated part (after ### Output:)
            response = full_response.replace(prompt, '').strip()
            
            return self._parse_model_response(response, ingredient_text)

        except Exception as e:
            logger.error(f"Model prediction error: {e}")
            return None

    def _parse_model_response(self, response: str, original_text: str) -> Dict:
        """Parse the model's response into structured output."""
        import re
        
        # Extract key information from model response
        result = {
            'input_text': original_text,
            'overall_assessment': 'Unknown',
            'health_recommendation': '',
            'explanation': response,
            'ingredients': [],
            'warnings': [],
            'health_recommendations': []
        }

        # Try to extract safety category (handles formats like "Risk Level: Safe" or "Safe")
        response_upper = response.upper()
        
        # Check for Risk Level pattern
        risk_match = re.search(r'Risk\s*Level:\s*(Safe|Moderate|Harmful)', response, re.IGNORECASE)
        if risk_match:
            result['overall_assessment'] = risk_match.group(1).capitalize()
        elif 'HARMFUL' in response_upper or 'HARMFUL' in response.upper():
            result['overall_assessment'] = 'Harmful'
        elif 'MODERATE' in response_upper:
            result['overall_assessment'] = 'Moderate'
        elif 'SAFE' in response_upper:
            result['overall_assessment'] = 'Safe'

        # Extract explanation (text after Explanation: or the full response)
        exp_match = re.search(r'Explanation:\s*(.+)', response, re.DOTALL)
        if exp_match:
            result['explanation'] = exp_match.group(1).strip()
        
        # Generate health recommendation based on assessment
        if result['overall_assessment'] == 'Harmful':
            result['health_recommendations'].append('Avoid or minimize consumption of this product.')
            result['warnings'].append({'ingredient': 'Product', 'description': 'Contains potentially harmful ingredients'})
        elif result['overall_assessment'] == 'Moderate':
            result['health_recommendations'].append('Consume in moderation as part of a balanced diet.')
        elif result['overall_assessment'] == 'Safe':
            result['health_recommendations'].append('This product appears to contain safe ingredients.')

        return result

    def _classify_with_safety_data(self, ingredient: str) -> Dict:
        """Classify ingredient using safety data lookup."""
        ingredient_lower = ingredient.lower().strip()
        
        # Direct match
        if ingredient_lower in self.ingredient_lookup:
            return self.ingredient_lookup[ingredient_lower]
        
        # Try removing parentheses content
        ingr_no_paren = re.sub(r'\([^)]*\)', '', ingredient_lower).strip()
        if ingr_no_paren and ingr_no_paren in self.ingredient_lookup:
            return self.ingredient_lookup[ingr_no_paren]
        
        # Try extracting just the main ingredient name (before commas, etc.)
        ingr_main = ingredient_lower.split(',')[0].strip()
        if ingr_main in self.ingredient_lookup:
            return self.ingredient_lookup[ingr_main]
        
        # Partial match - check if ingredient contains a known ingredient
        for ingr_name, data in self.ingredient_lookup.items():
            if ingr_name in ingredient_lower or ingredient_lower in ingr_name:
                return data
        
        # Check for INS numbers
        ins_match = re.search(r'INS\s*(\d+)|E(\d+)', ingredient, re.IGNORECASE)
        if ins_match:
            ins_number = ins_match.group(1) if ins_match.group(1) else f"E{ins_match.group(2)}"
            for ingr_name, data in self.ingredient_lookup.items():
                if str(data.get('ins_number', '')).replace('INS ', '') == ins_number:
                    return data
        
        # Try matching with common variations
        variations = {
            'high fructose corn syrup': 'corn syrup',
            'corn syrup': 'high fructose corn syrup',
            'phosphoric acid': 'phosphoric acid',
            'caramel color': 'caramel color',
            'natural flavors': 'natural flavor',
            'natural flavor': 'natural flavors',
            'caffeine': 'caffeine',
            'sodium benzoate': 'sodium benzoate',
            'benzoic acid': 'benzoic acid',
        }
        
        for var, lookup_term in variations.items():
            if var in ingredient_lower:
                if lookup_term in self.ingredient_lookup:
                    return self.ingredient_lookup[lookup_term]
        
        # Unknown ingredient
        return {
            'ins_number': 'Unknown',
            'category': 'Unknown',
            'safety_category': 'Unknown',
            'safety_description': 'Safety classification not available for this ingredient.',
            'health_impact': 'Unknown - consider researching this ingredient'
        }

    def extract_ingredients(self, ingredient_text: str) -> List[str]:
        """Extract individual ingredients from text."""
        text = ingredient_text.lower()

        # Remove parentheses content (often contains INS numbers)
        paren_content = re.findall(r'\(([^)]*)\)', text)
        text = re.sub(r'\([^)]*\)', '', text)

        # Extract INS numbers before removing
        ins_numbers = []
        for content in paren_content:
            ins_matches = re.findall(r'INS\s*(\d+)', content, re.IGNORECASE)
            ins_numbers.extend(ins_matches)

        # Remove percentages
        text = re.sub(r'\d+%', '', text)
        text = re.sub(r'contains?:?', '', text)

        # Split by separators
        separators = [',', ';', ':', 'and', '&']
        for sep in separators:
            text = text.replace(sep, '|')

        # Split and clean
        ingredients = [ingr.strip() for ingr in text.split('|') if ingr.strip()]
        ingredients = [ingr for ingr in ingredients if len(ingr) > 2]

        # Add back INS numbers to ingredient list
        for ins in ins_numbers:
            ingredients.append(f"INS {ins}")

        return ingredients

    def analyze_ingredients(self, ingredient_text: str) -> Dict:
        """
        Analyze ingredient list and return comprehensive assessment.

        Args:
            ingredient_text: Full ingredient list from food product

        Returns:
            Dictionary with analysis results
        """
        # Try model-based analysis first
        if self.model is not None:
            model_result = self._predict_with_model(ingredient_text)
            if model_result:
                return model_result

        # Fallback to rule-based analysis
        extracted_ingredients = self.extract_ingredients(ingredient_text)

        results = {
            'input_text': ingredient_text,
            'extracted_ingredients': [],
            'safety_summary': {'Safe': 0, 'Moderate': 0, 'Harmful': 0, 'Unknown': 0},
            'warnings': [],
            'health_recommendations': [],
            'overall_assessment': 'Unknown',
            'explanation': ''
        }

        for ingr in extracted_ingredients:
            classification = self._classify_with_safety_data(ingr)

            ingredient_result = {
                'name': ingr,
                'classification': classification
            }

            results['extracted_ingredients'].append(ingredient_result)

            safety_cat = classification.get('safety_category', 'Unknown')
            if safety_cat in results['safety_summary']:
                results['safety_summary'][safety_cat] += 1
            else:
                results['safety_summary']['Unknown'] += 1

            # Add warnings and recommendations
            if safety_cat in ['Moderate', 'Harmful']:
                warning = {
                    'ingredient': ingr,
                    'category': safety_cat,
                    'description': classification.get('safety_description', 'No description available'),
                    'health_impact': classification.get('health_impact', '')
                }
                results['warnings'].append(warning)
                results['health_recommendations'].append(
                    f"Limit consumption of {ingr} - {classification.get('health_impact', '')}"
                )
            elif safety_cat == 'Safe':
                results['health_recommendations'].append(
                    f"{ingr} is generally considered safe."
                )

        # Determine overall assessment
        safe_count = results['safety_summary']['Safe']
        moderate_count = results['safety_summary']['Moderate']
        harmful_count = results['safety_summary']['Harmful']
        unknown_count = results['safety_summary']['Unknown']

        if harmful_count > 0:
            results['overall_assessment'] = 'Harmful'
            results['explanation'] = (
                f"This product contains {harmful_count} potentially harmful ingredient(s). "
                f"Consider alternative products with safer ingredients."
            )
        elif moderate_count > 0:
            results['overall_assessment'] = 'Moderate'
            results['explanation'] = (
                f"This product contains {moderate_count} ingredient(s) that should be consumed in moderation. "
                f"{safe_count} ingredient(s) are considered safe."
            )
        elif unknown_count > 0:
            results['overall_assessment'] = 'Mixed'
            results['explanation'] = (
                f"This product has {safe_count} safe ingredient(s) but {unknown_count} unknown ingredient(s). "
                f"Research the unknown ingredients for complete safety assessment."
            )
        else:
            results['overall_assessment'] = 'Safe'
            results['explanation'] = (
                f"All {safe_count} ingredients in this product are generally considered safe."
            )

        return results

    def __del__(self):
        """Cleanup temporary model directory."""
        if self.model_dir and os.path.exists(self.model_dir):
            try:
                shutil.rmtree(self.model_dir)
            except:
                pass


# Global decoder instance
decoder = None


def get_decoder():
    """Get or create the decoder instance."""
    global decoder
    if decoder is None:
        # Find the model - use extracted model directory first, then zip file
        model_paths = [
            r'models\final_model',
            'models/final_model',
            r'models\final_model-20260228T144312Z-1-001.zip',
            'models/final_model-20260228T144312Z-1-001.zip'
        ]
        model_path = None
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                logger.info(f"Found model at: {path}")
                break
        
        if model_path:
            decoder = IngredientDecoder(model_zip_path=model_path)
        else:
            logger.warning("No model found, using rule-based fallback only")
            decoder = IngredientDecoder()
    return decoder


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Ingredient Decoder API is running'})


@app.route('/api/analyze', methods=['POST'])
def analyze_ingredients():
    """
    Analyze food ingredients and return safety classification.

    Expected JSON body:
    {
        "ingredients": "Sugar, Milk Solids, Cocoa Butter, Emulsifiers (Soy Lecithin)"
    }
    """
    try:
        data = request.get_json()

        if not data or 'ingredients' not in data:
            return jsonify({
                'error': 'Missing ingredients field',
                'message': 'Please provide ingredient text in the request body'
            }), 400

        ingredient_text = data['ingredients'].strip()
        if not ingredient_text:
            return jsonify({
                'error': 'Empty ingredients',
                'message': 'Please provide non-empty ingredient text'
            }), 400

        # Analyze ingredients
        decoder_instance = get_decoder()
        result = decoder_instance.analyze_ingredients(ingredient_text)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error analyzing ingredients: {e}")
        return jsonify({
            'error': 'Analysis failed',
            'message': str(e)
        }), 500


@app.route('/api/batch-analyze', methods=['POST'])
def batch_analyze():
    """
    Analyze multiple ingredient lists.

    Expected JSON body:
    {
        "ingredients_list": [
            "Sugar, Milk, Cocoa",
            "Wheat Flour, Salt, Yeast"
        ]
    }
    """
    try:
        data = request.get_json()

        if not data or 'ingredients_list' not in data:
            return jsonify({
                'error': 'Missing ingredients_list field'
            }), 400

        ingredients_list = data['ingredients_list']
        if not isinstance(ingredients_list, list):
            return jsonify({
                'error': 'Invalid format',
                'message': 'ingredients_list must be an array'
            }), 400

        decoder_instance = get_decoder()
        results = []

        for ingredient_text in ingredients_list:
            if ingredient_text.strip():
                result = decoder_instance.analyze_ingredients(ingredient_text)
                results.append(result)

        return jsonify({'results': results})

    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({
            'error': 'Batch analysis failed',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # Initialize decoder on startup
    logger.info("Initializing Ingredient Decoder...")
    get_decoder()

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
