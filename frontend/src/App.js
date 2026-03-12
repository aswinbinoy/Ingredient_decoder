import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [ingredients, setIngredients] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeIngredients = async () => {
    if (!ingredients.trim()) {
      setError('Please enter some ingredients to analyze');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_URL}/analyze`, {
        ingredients: ingredients
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to analyze ingredients. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadSample = (sampleText) => {
    setIngredients(sampleText);
    setResult(null);
    setError(null);
  };

  const sampleIngredients = [
    "Sugar, Milk Solids, Cocoa Butter, Emulsifiers (Soy Lecithin, INS 322), Natural Vanilla Flavouring",
    "Wheat Flour, Salt, Yeast, Preservatives (Sodium Benzoate, INS 211), Antioxidants (Ascorbic Acid)",
    "Tomato Puree, Salt, Sugar, Acidity Regulator (Citric Acid, INS 330), Preservative (Potassium Sorbate, INS 202)",
    "Water, High Fructose Corn Syrup, Caramel Color, Phosphoric Acid, Natural Flavors, Caffeine",
    "Maida (Refined Wheat Flour), Palm Oil, Sugar, Artificial Flavors (Strawberry), Red Color (INS 124), Preservative (Sodium Metabisulphite, INS 223), Antioxidant (BHA, INS 320)",
    "Carbonated Water, Sugar, Caramel Color (INS 150d), Phosphoric Acid (INS 338), Artificial Sweetener (Aspartame, INS 951), Caffeine, Sodium Benzoate (INS 211)",
    "Potato Chips: Potatoes, Vegetable Oil (Palm Oil), Salt, Sugar, Monosodium Glutamate (INS 621), Artificial Flavors, Yellow Color (Tartrazine, INS 102), Disodium Inosinate (INS 631), Disodium Guanylate (INS 627)",
    "Instant Noodles: Wheat Flour, Palm Oil, Salt, Thickeners (INS 401, INS 415), Acidity Regulator (INS 501), Flavor Enhancers (MSG INS 621, IMP INS 631, GMP INS 627), Artificial Colors (INS 102, INS 110), Preservative (INS 220), Antioxidant (TBHQ)"
  ];

  const getAssessmentClass = (assessment) => {
    if (!assessment) return '';
    const lower = assessment.toLowerCase();
    if (lower.includes('safe')) return 'safe';
    if (lower.includes('moderate')) return 'moderate';
    if (lower.includes('harmful')) return 'harmful';
    if (lower.includes('mixed')) return 'mixed';
    return 'unknown';
  };

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <header className="header">
          <h1>🔍 Ingredient Decoder</h1>
          <p>AI-Powered Food Ingredient Transparency System</p>
        </header>

        {/* Main Card */}
        <div className="main-card">
          {/* Input Section */}
          <div className="input-section">
            <label htmlFor="ingredients">
              Enter Food Ingredients:
            </label>
            <textarea
              id="ingredients"
              className="textarea"
              placeholder="Paste the ingredient list from a food product package here..."
              value={ingredients}
              onChange={(e) => setIngredients(e.target.value)}
              rows={6}
            />
            <button
              className="analyze-btn"
              onClick={analyzeIngredients}
              disabled={loading}
            >
              {loading ? 'Analyzing...' : 'Analyze Ingredients'}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          {/* Loading Spinner */}
          {loading && (
            <div className="loading">
              <div className="spinner"></div>
            </div>
          )}

          {/* Results Section */}
          {result && !loading && (
            <div className="results-section">
              <h2>Analysis Results</h2>

              {/* Overall Assessment */}
              <div className={`assessment-card ${getAssessmentClass(result.overall_assessment)}`}>
                <div className="assessment-title">
                  {result.overall_assessment === 'Safe' && '✅ Safe to Consume'}
                  {result.overall_assessment === 'Moderate' && '⚠️ Consume in Moderation'}
                  {result.overall_assessment === 'Harmful' && '🚫 Potentially Harmful'}
                  {result.overall_assessment === 'Mixed' && '❓ Mixed Safety Profile'}
                  {result.overall_assessment === 'Unknown' && '❓ Unknown Assessment'}
                </div>
                <p className="assessment-explanation">{result.explanation}</p>
              </div>

              {/* Safety Summary */}
              {result.safety_summary && (
                <div className="safety-summary">
                  <div className="summary-item safe">
                    <span className="summary-count">{result.safety_summary.Safe || 0}</span>
                    <span className="summary-label">Safe</span>
                  </div>
                  <div className="summary-item moderate">
                    <span className="summary-count">{result.safety_summary.Moderate || 0}</span>
                    <span className="summary-label">Moderate</span>
                  </div>
                  <div className="summary-item harmful">
                    <span className="summary-count">{result.safety_summary.Harmful || 0}</span>
                    <span className="summary-label">Harmful</span>
                  </div>
                  <div className="summary-item unknown">
                    <span className="summary-count">{result.safety_summary.Unknown || 0}</span>
                    <span className="summary-label">Unknown</span>
                  </div>
                </div>
              )}

              {/* Extracted Ingredients */}
              {result.extracted_ingredients && result.extracted_ingredients.length > 0 && (
                <div className="ingredients-list">
                  <h3>📋 Ingredient Breakdown</h3>
                  {result.extracted_ingredients.map((item, index) => (
                    <div
                      key={index}
                      className={`ingredient-item ${item.classification?.safety_category?.toLowerCase() || 'unknown'}`}
                    >
                      <div className="ingredient-name">{item.name}</div>
                      <div className="ingredient-details">
                        <span className={`ingredient-category ${item.classification?.safety_category?.toLowerCase() || 'unknown'}`}>
                          {item.classification?.safety_category || 'Unknown'}
                        </span>
                        {item.classification?.category && item.classification.category !== 'Unknown' && (
                          <span style={{ color: '#666', fontSize: '0.85rem' }}>
                            • {item.classification.category}
                          </span>
                        )}
                        {item.classification?.ins_number && item.classification.ins_number !== 'Unknown' && (
                          <span style={{ color: '#666', fontSize: '0.85rem', marginLeft: '0.5rem' }}>
                            (INS {item.classification.ins_number})
                          </span>
                        )}
                      </div>
                      {item.classification?.safety_description && (
                        <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
                          {item.classification.safety_description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Warnings */}
              {result.warnings && result.warnings.length > 0 && (
                <div className="warnings-section">
                  <h3>⚠️ Health Warnings</h3>
                  {result.warnings.map((warning, index) => (
                    <div key={index} className="warning-item">
                      <div className="warning-ingredient">
                        {warning.ingredient || warning.name}
                      </div>
                      <div className="warning-description">
                        {warning.description || warning.health_impact}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Health Recommendations */}
              {result.health_recommendations && result.health_recommendations.length > 0 && (
                <div className="recommendations-section">
                  <h3>💡 Health Recommendations</h3>
                  {result.health_recommendations.map((rec, index) => (
                    <div key={index} className="recommendation-item">
                      {rec}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Sample Ingredients */}
          <div className="sample-section">
            <h3>🧪 Try with sample ingredients:</h3>
            <div className="sample-buttons">
              {sampleIngredients.map((sample, index) => (
                <button
                  key={index}
                  className="sample-btn"
                  onClick={() => loadSample(sample)}
                >
                  Sample {index + 1}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
