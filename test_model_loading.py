"""
Diagnostic script to verify if the model is loading correctly
"""

import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_model_loading():
    print("="*60)
    print("MODEL LOADING DIAGNOSTIC")
    print("="*60)
    
    # Test 1: Check if model files exist
    print("\n[1] Checking model files...")
    model_path = r'models\final_model'
    if os.path.exists(model_path):
        print(f"✓ Model directory found: {model_path}")
        files = os.listdir(model_path)
        print(f"  Files: {files}")
    else:
        print(f"✗ Model directory NOT found: {model_path}")
        return False
    
    # Test 2: Check if dependencies are installed
    print("\n[2] Checking dependencies...")
    deps = {
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'peft': 'PEFT',
        'pandas': 'Pandas',
        'flask': 'Flask'
    }
    
    missing = []
    for module, name in deps.items():
        try:
            __import__(module)
            print(f"✓ {name} installed")
        except ImportError as e:
            print(f"✗ {name} NOT installed: {e}")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        return False
    
    # Test 3: Try to load the model
    print("\n[3] Attempting to load model...")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import json
        
        adapter_path = model_path
        adapter_config_path = os.path.join(adapter_path, 'adapter_config.json')
        
        if not os.path.exists(adapter_config_path):
            print(f"✗ adapter_config.json NOT found at {adapter_config_path}")
            return False
        
        print(f"✓ Loading adapter config...")
        with open(adapter_config_path, 'r') as f:
            adapter_config = json.load(f)
        
        base_model = adapter_config.get('base_model_name_or_path', 'unsloth/Llama-3-8B-Instruct-bnb-4bit')
        print(f"✓ Base model: {base_model}")
        
        print(f"✓ Loading tokenizer from {adapter_path}...")
        tokenizer = AutoTokenizer.from_pretrained(adapter_path)
        print(f"✓ Tokenizer loaded successfully")
        
        print(f"✓ Loading base model (this may take a while)...")
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map='auto' if torch.cuda.is_available() else None,
            load_in_4bit=True if torch.cuda.is_available() else False,
        )
        print(f"✓ Base model loaded")
        
        print(f"✓ Loading LoRA adapter...")
        model = PeftModel.from_pretrained(model, adapter_path)
        print(f"✓ LoRA adapter loaded")
        
        print(f"✓ Merging adapter weights...")
        model = model.merge_and_unload()
        print(f"✓ Model merged and ready")
        
        print("\n" + "="*60)
        print("✓✓✓ MODEL LOADING SUCCESSFUL ✓✓✓")
        print("="*60)
        print("\nYour model should be working correctly!")
        print("The project is using the fine-tuned LLaMA-3 model.")
        return True
        
    except Exception as e:
        print(f"\n✗ Model loading failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        print("✗✗✗ MODEL LOADING FAILED ✗✗✗")
        print("="*60)
        print("\nYour project is falling back to database-only mode!")
        print("The analysis is using the safety database, NOT the trained model.")
        return False

def check_backend():
    print("\n\n" + "="*60)
    print("BACKEND INITIALIZATION TEST")
    print("="*60)
    
    try:
        sys.path.insert(0, r'c:\code\llm_project\Ingredient_decoder\backend')
        from app import IngredientDecoder, get_decoder
        
        print("\n[1] Creating decoder instance...")
        decoder = get_decoder()
        
        if decoder.model is not None:
            print("\n✓ Model loaded in IngredientDecoder!")
            print("  The system is using the TRAINED LLaMA-3 MODEL")
        else:
            print("\n✗ Model is NULL in IngredientDecoder!")
            print("  The system is using DATABASE FALLBACK only")
            print("  ↓ Check the output above for model loading errors ↓")
        
        # Test analysis
        print("\n[2] Testing ingredient analysis...")
        test_ingredient = "Sodium benzoate (INS 211)"
        result = decoder.analyze_ingredients(test_ingredient)
        
        print(f"\nInput: {test_ingredient}")
        print(f"Overall Assessment: {result['overall_assessment']}")
        print(f"Explanation: {result['explanation']}")
        
        if 'model_prediction' in result:
            print("✓ Result came from MODEL prediction")
        else:
            print("✓ Result came from DATABASE lookup")
        
    except Exception as e:
        print(f"\n✗ Backend test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    model_ok = test_model_loading()
    check_backend()
