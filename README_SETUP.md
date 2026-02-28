# Ingredient Decoder - Setup Guide

## Overview
This guide will help you set up and run the Ingredient Decoder application with both the Flask API backend and React frontend.

## Architecture

The application uses a **hybrid approach**:
1. **Primary**: Fine-tuned LLaMA-3 8B model (LoRA adapter) for intelligent ingredient analysis
2. **Fallback**: Rule-based classification using safety databases when model is unavailable

### Model Details
- **Base Model**: `unsloth/Llama-3-8B-Instruct-bnb-4bit` (4-bit quantized)
- **Adapter**: LoRA weights stored in `models/final_model-*.zip`
- **Framework**: PEFT (Parameter-Efficient Fine-Tuning)
- **Training**: Instruction-tuned for ingredient safety classification

## Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- **GPU recommended** for model inference (CPU fallback available but slower)

## Project Structure
```
Ingredient_decoder/
├── backend/
│   ├── app.py              # Flask API server
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── index.js       # React entry point
│   │   └── index.css      # Styles
│   ├── public/
│   │   └── index.html     # HTML template
│   └── package.json       # Node dependencies
├── models/
│   └── final_model-*.zip  # Fine-tuned LLaMA-3 model
├── data/
│   └── processed/         # Safety classification data
└── README_SETUP.md        # This file
```

## Installation

### 1. Backend Setup

#### Step 1: Create a virtual environment (recommended)
```bash
cd C:\code\llm_project\Ingredient_decoder
python -m venv venv
```

#### Step 2: Activate the virtual environment
**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

#### Step 3: Install Python dependencies
```bash
pip install -r requirements.txt
```

Or install backend-specific dependencies:
```bash
pip install -r backend\requirements.txt
```

### 2. Frontend Setup

#### Step 1: Navigate to frontend directory
```bash
cd frontend
```

#### Step 2: Install Node dependencies
```bash
npm install
```

## Running the Application

### Option 1: Run Backend and Frontend Separately

#### Start the Flask Backend
```bash
# From the project root directory
cd backend
python app.py
```

The API server will start at: `http://localhost:5000`

Available endpoints:
- `GET /api/health` - Health check
- `POST /api/analyze` - Analyze single ingredient list
- `POST /api/batch-analyze` - Analyze multiple ingredient lists

#### Start the React Frontend (in a new terminal)
```bash
# From the frontend directory
cd frontend
npm start
```

The React app will open at: `http://localhost:3000`

### Option 2: Quick Start Script

**Windows (PowerShell):**
```powershell
# Start backend in background
Start-Process python -ArgumentList "backend\app.py" -WindowStyle Normal

# Wait for backend to start
Start-Sleep -Seconds 5

# Start frontend
cd frontend
npm start
```

## API Usage

### Analyze Single Ingredient List

**Request:**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{\"ingredients\": \"Sugar, Milk Solids, Cocoa Butter, Emulsifiers (Soy Lecithin)\"}"
```

**Response:**
```json
{
  "input_text": "Sugar, Milk Solids, Cocoa Butter...",
  "overall_assessment": "Safe",
  "explanation": "All ingredients in this product are generally considered safe.",
  "extracted_ingredients": [
    {
      "name": "sugar",
      "classification": {
        "safety_category": "Safe",
        "category": "Sweetener",
        "safety_description": "Generally recognized as safe"
      }
    }
  ],
  "safety_summary": {
    "Safe": 5,
    "Moderate": 0,
    "Harmful": 0,
    "Unknown": 0
  },
  "warnings": [],
  "health_recommendations": [...]
}
```

### Batch Analysis

**Request:**
```bash
curl -X POST http://localhost:5000/api/batch-analyze \
  -H "Content-Type: application/json" \
  -d "{\"ingredients_list\": [\"Sugar, Milk\", \"Wheat Flour, Salt\"]}"
```

## Features

### Backend Features
- ✅ Fine-tuned LLaMA-3 model integration (when available)
- ✅ Rule-based fallback classification system
- ✅ RESTful API with CORS support
- ✅ Ingredient extraction and normalization
- ✅ Safety classification (Safe/Moderate/Harmful)
- ✅ Health recommendations generation
- ✅ Batch processing support

### Frontend Features
- ✅ Clean, modern UI with gradient design
- ✅ Real-time ingredient analysis
- ✅ Color-coded risk levels (Green/Yellow/Red)
- ✅ Detailed ingredient breakdown
- ✅ Health warnings and recommendations
- ✅ Sample ingredient presets
- ✅ Responsive design for mobile/desktop

## Color Coding System

| Category | Color | Meaning |
|----------|-------|---------|
| Safe | 🟢 Green | Generally safe for consumption |
| Moderate | 🟡 Yellow | Consume in moderation |
| Harmful | 🔴 Red | Potentially harmful, avoid if possible |
| Unknown | ⚪ Gray | Insufficient data available |

## Troubleshooting

### Backend Issues

**Error: "Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Error: "Model not found"**
- Ensure the model zip file exists in `models/` folder
- The app will use rule-based fallback if model loading fails

**Error: "Port 5000 already in use"**
```bash
# Change port in backend/app.py
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Frontend Issues

**Error: "npm not found"**
- Install Node.js from https://nodejs.org/

**Error: "Cannot connect to API"**
- Ensure backend is running on port 5000
- Check CORS settings in `backend/app.py`

**Build fails**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Development Tips

### Backend Development
- Enable debug mode: `app.run(debug=True)`
- View logs in the terminal where Flask is running
- Test API with Postman or curl

### Frontend Development
- Hot reload is enabled by default
- Check browser console for errors
- Use React DevTools for debugging

## Production Deployment

### Backend (Flask)
```bash
# Use a production server like gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Frontend (React)
```bash
# Create production build
npm run build

# Serve with a static file server
npm install -g serve
serve -s build -l 3000
```

## Security Notes

⚠️ **Important for Production:**
- Disable Flask debug mode
- Set proper CORS origins
- Use environment variables for sensitive data
- Implement rate limiting
- Add authentication if needed

## License
This project is for educational and research purposes.

## Support
For issues or questions, please refer to the main README.md or contact the development team.
