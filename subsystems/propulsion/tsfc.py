import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Data extracted from the provided image
# Engine Model | Bypass Ratio (TO) | SFC (TO) | SFC (CRUISE)
engine_data = {
    'CFM56_3C1': {'bypass_ratio': 4.80, 'sfc_to': 0.33, 'sfc_cruise': 0.667},
    'CFM56_5A1': {'bypass_ratio': 6.00, 'sfc_to': 0.33, 'sfc_cruise': 0.596},
    'CFM56_5C2': {'bypass_ratio': 6.40, 'sfc_to': 0.32, 'sfc_cruise': 0.545},
    # 'CFM56_7B20': {'sfc_to': 0.36}, # Missing Bypass Ratio and Cruise SFC
    'V2500_A1':  {'bypass_ratio': 5.40, 'sfc_to': 0.35, 'sfc_cruise': 0.581},
    'V2522_A5':  {'bypass_ratio': 5.00, 'sfc_to': 0.34, 'sfc_cruise': 0.574},
    'V2533_A5':  {'bypass_ratio': 4.60, 'sfc_to': 0.37, 'sfc_cruise': 0.574},
    'V2525_D5':  {'bypass_ratio': 4.80, 'sfc_to': 0.36, 'sfc_cruise': 0.574},
}

# Prepare data for regression
bypass_ratios = []
sfc_ratios_cruise_to_to = []

print("Engine Data and Calculated SFC Ratios:")
print("-" * 50)
print(f"{'Engine':<12} | {'BPR':<5} | {'SFC TO':<6} | {'SFC CR':<6} | {'SFC Ratio (CR/TO)':<18}")
print("-" * 50)

for engine, data in engine_data.items():
    if 'bypass_ratio' in data and 'sfc_to' in data and 'sfc_cruise' in data:
        sfc_to = data['sfc_to']
        sfc_cruise = data['sfc_cruise']
        bpr = data['bypass_ratio']

        if sfc_to > 0: # Avoid division by zero
            sfc_ratio = sfc_cruise / sfc_to
            bypass_ratios.append(bpr)
            sfc_ratios_cruise_to_to.append(sfc_ratio)
            print(f"{engine:<12} | {bpr:<5.2f} | {sfc_to:<6.2f} | {sfc_cruise:<6.3f} | {sfc_ratio:<18.4f}")
        else:
            print(f"Skipping {engine} due to SFC TO being zero or invalid.")
    else:
        print(f"Skipping {engine} due to missing data.")
print("-" * 50)

# Convert lists to numpy arrays for scikit-learn
X = np.array(bypass_ratios).reshape(-1, 1)  # Feature: Bypass Ratio
y = np.array(sfc_ratios_cruise_to_to)       # Target: SFC Ratio (Cruise/TO)

# Perform linear regression
model = LinearRegression()
model.fit(X, y)

# Get the model coefficients
slope = model.coef_[0]
intercept = model.intercept_

print(f"\nLinear Regression Model:")
print(f"Equation: SFC_Ratio = {slope:.4f} * Bypass_Ratio + {intercept:.4f}")
print(f"R-squared: {model.score(X, y):.4f}") # R-squared value to check goodness of fit

# Predict SFC ratio for FJ44-1AP (Bypass Ratio = 2.6)
fj44_1ap_bpr = 2.6
predicted_sfc_ratio_fj44 = model.predict(np.array([[fj44_1ap_bpr]]))[0]

print(f"\nPrediction for FJ44-1AP (Bypass Ratio = {fj44_1ap_bpr}):")
print(f"Predicted SFC Ratio (Cruise/TO): {predicted_sfc_ratio_fj44:.4f}")

# Plotting the results
plt.figure(figsize=(10, 6))
plt.scatter(X, y, color='blue', label='Engine Data Points')
plt.plot(X, model.predict(X), color='red', linewidth=2, label='Linear Regression Line')

# Plot the prediction for FJ44-1AP
plt.scatter([fj44_1ap_bpr], [predicted_sfc_ratio_fj44], color='green', s=100, zorder=5, edgecolor='black', label=f'FJ44-1AP Prediction (BPR={fj44_1ap_bpr})')

plt.xlabel('Bypass Ratio (TO)')
plt.ylabel('SFC Ratio (Cruise SFC / TO SFC)')
plt.title('SFC Ratio vs. Bypass Ratio for Turbofan Engines')
plt.legend()
plt.grid(True)
plt.figtext(0.5, 0.01, f"Regression Equation: y = {slope:.4f}x + {intercept:.4f}\nR-squared: {model.score(X, y):.4f}", ha="center", fontsize=10, bbox={"facecolor":"lightgray", "alpha":0.5, "pad":5})
plt.tight_layout(rect=[0, 0.05, 1, 1]) # Adjust layout to make space for figtext
plt.show()