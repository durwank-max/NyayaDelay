from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import os

app = Flask(__name__)
CORS(app)

MODEL_PATH = 'nyayadelay_model.joblib'

# Attempt to load the model. If it doesn't exist, we will handle it in the endpoint.
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None
    print(f"Warning: {MODEL_PATH} not found. Please ensure the model is trained and saved.")

import random

# Mock database simulating an external API (like NJDG)
STATE_DATABASE = {
    'up': {'budget': 104, 'shortfall': 25.4, 'pop_lower': 93021, 'pop_hc': 2332970, 'hc_ccr': 96},
    'delhi': {'budget': 581, 'shortfall': 32.5, 'pop_lower': 30695, 'pop_hc': 465889, 'hc_ccr': 88},
    'bihar': {'budget': 83, 'shortfall': 20.2, 'pop_lower': 92259, 'pop_hc': 3674088, 'hc_ccr': 113},
    'mh': {'budget': 172, 'shortfall': 17.6, 'pop_lower': 64645, 'pop_hc': 1941636, 'hc_ccr': 72},
    'wb': {'budget': 75, 'shortfall': 17.6, 'pop_lower': 107412, 'pop_hc': 1833444, 'hc_ccr': 121},
    'goa': {'budget': 498, 'shortfall': 17.6, 'pop_lower': 39175, 'pop_hc': 1941636, 'hc_ccr': 72}
}

@app.route('/api/metrics/<state_id>', methods=['GET'])
def get_live_metrics(state_id):
    """Simulates fetching live data from an external dashboard like NJDG."""
    if state_id not in STATE_DATABASE:
        return jsonify({"error": "State not found"}), 404
        
    base_data = STATE_DATABASE[state_id].copy()
    
    # Introduce slight random noise (±2%) to simulate "live" fluctuating metrics for the demo
    base_data['hc_ccr'] = round(base_data['hc_ccr'] * random.uniform(0.98, 1.02), 1)
    base_data['shortfall'] = round(base_data['shortfall'] * random.uniform(0.98, 1.02), 1)
    
    return jsonify(base_data)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    try:
        # Extract features ensuring correct types and order
        budget = float(data.get('budget', 0))
        shortfall = float(data.get('shortfall', 0))
        pop_lower = float(data.get('pop_lower', 0))
        pop_hc = float(data.get('pop_hc', 0))
        hc_ccr = float(data.get('hc_ccr', 0))
        
        features = {
            'budget_per_capita_judiciary': [budget],
            'population_per_high_court_judge': [pop_hc],
            'population_per_lower_court_judge': [pop_lower],
            'courthall_shortfall_pct': [shortfall],
            'high_court_case_clearance_rate': [hc_ccr]
        }
        
        df = pd.DataFrame(features)
        
        if model:
            prediction = int(model.predict(df)[0])
            probabilities = model.predict_proba(df)[0]
            confidence = round(float(max(probabilities)) * 100, 2)
        else:
            # Fallback logic if model is missing to prevent backend crash during demo
            is_growing = hc_ccr < 100 or shortfall > 18
            prediction = 0 if is_growing else 1
            confidence = 85.5  # Dummy confidence
        
        # 0: High Risk (Backlog Growing), 1: Low Risk (Backlog Clearing)
        if prediction == 0:
            label = "Backlog growing (High Pendency Risk)"
            advisory = "Critical pendency bottleneck detected. Shortfall and judge ratios are expanding backlogs."
        else:
            label = "Clearing backlog (Low Risk)"
            advisory = "District bench pacing is clearing historical caseload."
            
        return jsonify({
            "backlog_status": prediction,
            "label": label,
            "confidence": confidence,
            "advisory": advisory
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
