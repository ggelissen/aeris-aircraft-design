import matplotlib.pyplot as plt
import numpy as np

# INPUT VALUES - Class I Weight Breakdown
W_TO = 26872.60    # Take-off Weight (N)
W_E = 12030.16     # Empty Weight (N) 
W_F_total = 8958.44      # Total Fuel Weight (N)
W_PL = 5884.00     # Payload Weight (N)
M_res = 0.248      # Reserve fuel ratio (W_Fres/W_Fused)
W_tfo = 0          # Trapped fuel and oil (N) - assumed small/included elsewhere

def create_class_i_pie_chart():
    """
    Creates a pie chart showing the Class I weight breakdown with fuel split into used and reserve.
    """
    
    # Calculate fuel breakdown
    # From M_res = W_Fres/W_Fused, we get:
    # W_Fused = W_F_total / (1 + M_res)
    # W_Fres = M_res * W_Fused
    W_F_used = W_F_total / (1 + M_res)
    W_F_reserve = M_res * W_F_used
    
    # Calculate any remaining weight 
    W_other = W_TO - (W_E + W_F_total + W_PL + W_tfo)
    
    # Weight components for the pie chart
    weights = [W_E, W_F_used, W_F_reserve, W_PL]
    labels = ['Operating Empty\n Weight', 'Used Fuel', 'Reserve Fuel', 'Payload']
    colors = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#45B7D1', '#FFA07A']
    
    # Add other weight if significant
    if abs(W_other) > 10:  # More than 10N
        weights.append(W_other)
        labels.append('Other\n(TFO + misc)')
        colors.append('#FFCC99')
    
    # Create the pie chart
    plt.figure(figsize=(12, 8))
    
    # Create pie chart with percentages
    wedges, texts, autotexts = plt.pie(weights, 
                                      labels=labels, 
                                      colors=colors, 
                                      autopct='%1.1f%%',
                                      startangle=90,
                                      textprops={'fontsize': 11})
    
    # Enhance the appearance
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    
    # Add title
    plt.title('Class I Aircraft Weight Breakdown (W_TO)', fontsize=16, fontweight='bold', pad=20)
    
    # Add weight values as text
    info_text = f"""Class I Weight Analysis:

Take-off Weight: {W_TO:.0f} N ({W_TO/9.80665:.0f} kg)

Main Components:
• Empty Weight: {W_E:.0f} N ({100*W_E/W_TO:.1f}%)
• Total Fuel: {W_F_total:.0f} N ({100*W_F_total/W_TO:.1f}%)
  - Used Fuel: {W_F_used:.0f} N ({100*W_F_used/W_TO:.1f}%)
  - Reserve Fuel: {W_F_reserve:.0f} N ({100*W_F_reserve/W_TO:.1f}%)
• Payload: {W_PL:.0f} N ({100*W_PL/W_TO:.1f}%)

Fuel Breakdown:
• Reserve Ratio (M_res): {M_res:.3f}
• Used/Reserve Split: {100*W_F_used/W_F_total:.1f}% / {100*W_F_reserve/W_F_total:.1f}%"""
    
    plt.figtext(0.02, 0.02, info_text, fontsize=9, verticalalignment='bottom', 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.9))
    
    # Ensure the pie chart is circular
    plt.axis('equal')
    
    # Adjust layout to prevent text cutoff
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.4)  # Make room for the info text
    
    # Show the plot
    plt.show()
    
    # Print summary
    print("=== CLASS I WEIGHT BREAKDOWN SUMMARY ===")
    print(f"\nTake-off Weight (W_TO): {W_TO:.2f} N ({W_TO/9.80665:.2f} kg)")
    print(f"\nMain Components:")
    print(f"  Empty Weight (W_E): {W_E:.2f} N ({100*W_E/W_TO:.1f}%)")
    print(f"  Total Fuel Weight: {W_F_total:.2f} N ({100*W_F_total/W_TO:.1f}%)")
    print(f"    - Used Fuel: {W_F_used:.2f} N ({100*W_F_used/W_TO:.1f}%)")
    print(f"    - Reserve Fuel: {W_F_reserve:.2f} N ({100*W_F_reserve/W_TO:.1f}%)")
    print(f"  Payload Weight (W_PL): {W_PL:.2f} N ({100*W_PL/W_TO:.1f}%)")
    if abs(W_other) > 10:
        print(f"  Other (TFO + misc): {W_other:.2f} N ({100*W_other/W_TO:.1f}%)")
    
    print(f"\nFuel Analysis:")
    print(f"  Reserve Ratio (M_res): {M_res:.3f}")
    print(f"  Reserve fuel is {M_res*100:.1f}% of used fuel")
    print(f"  Used fuel is {100*W_F_used/W_F_total:.1f}% of total fuel")

if __name__ == "__main__":
    create_class_i_pie_chart()