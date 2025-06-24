import matplotlib.pyplot as plt
import numpy as np

# INPUT VALUES - Class II Weight Breakdown
W_TO = 29794       # Take-off Weight (N)
W_OE = 14110       # Operating Empty Weight (N)
W_F_total = 9799   # Total Fuel Weight (N)
W_F_used = 7821    # Used Fuel Weight (N) - given directly
W_PL = 5884        # Payload Weight (N)

# Calculate reserve fuel
W_F_reserve = W_F_total - W_F_used  # Reserve Fuel Weight (N)

# Detailed Component Weights (part of W_OE)
W_wing = 2739.59          # Wing Weight (N)
W_fuselage = 4236.50      # Fuselage Weight (N)
W_landing_gear = 1191.75  # Landing Gear Weight (N)
W_empennage = 465.13      # Empennage Weight (N)
W_fixed_equipment = 884.45 # Fixed Equipment Weight (N)
W_propulsion = 4598.38    # Propulsion Weight (N)

def create_weight_breakdown_pie_chart():
    """
    Creates pie charts showing the Class II weight breakdown with fuel split into used and reserve.
    Includes both top-level breakdown and detailed component breakdown.
    """
    
    # Calculate any remaining weight 
    W_other = W_TO - (W_OE + W_F_total + W_PL)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    
    # TOP-LEVEL BREAKDOWN (Left chart) - with fuel split
    weights_top = [W_OE, W_F_used, W_F_reserve, W_PL]
    labels_top = ['Operating Empty\nWeight', 'Used Fuel', 'Reserve Fuel', 'Payload']
    colors_top = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#45B7D1']
    
    # Add other weight if significant
    if abs(W_other) > 10:  # More than 10N difference
        weights_top.append(W_other)
        labels_top.append('Other')
        colors_top.append('#FFA07A')
    
    wedges1, texts1, autotexts1 = ax1.pie(weights_top, 
                                          labels=labels_top, 
                                          colors=colors_top, 
                                          autopct='%1.1f%%',
                                          startangle=90,
                                          textprops={'fontsize': 10})
    
    for autotext in autotexts1:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)
    
    ax1.set_title('Take-off Weight Breakdown\n(W_TO)', fontsize=14, fontweight='bold', pad=20)
    
    # DETAILED COMPONENT BREAKDOWN (Right chart)
    weights_components = [W_wing, W_fuselage, W_landing_gear, W_empennage, W_fixed_equipment, W_propulsion]
    labels_components = ['Wing', 'Fuselage', 'Landing Gear', 'Empennage', 'Fixed Equipment', 'Propulsion']
    colors_components = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99CCFF']
    
    wedges2, texts2, autotexts2 = ax2.pie(weights_components, 
                                          labels=labels_components, 
                                          colors=colors_components, 
                                          autopct='%1.1f%%',
                                          startangle=90,
                                          textprops={'fontsize': 10})
    
    for autotext in autotexts2:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)
    
    ax2.set_title('Operating Empty Weight Breakdown\n(W_OE Components)', fontsize=14, fontweight='bold', pad=20)
    
    # Add comprehensive weight information
    M_res = W_F_reserve / W_F_used if W_F_used > 0 else 0
    
    info_text = f"""Class II Weight Analysis:
    
Take-off Weight: {W_TO:.0f} N ({W_TO/9.80665:.0f} kg)

Main Components:
• Operating Empty: {W_OE:.0f} N ({100*W_OE/W_TO:.1f}%)
• Total Fuel: {W_F_total:.0f} N ({100*W_F_total/W_TO:.1f}%)
  - Used Fuel: {W_F_used:.0f} N ({100*W_F_used/W_TO:.1f}%)
  - Reserve Fuel: {W_F_reserve:.0f} N ({100*W_F_reserve/W_TO:.1f}%)
• Payload: {W_PL:.0f} N ({100*W_PL/W_TO:.1f}%)

Fuel Analysis:
• Reserve Ratio (M_res): {M_res:.3f}
• Used/Reserve Split: {100*W_F_used/W_F_total:.1f}% / {100*W_F_reserve/W_F_total:.1f}%

OE Component Details:
• Wing: {W_wing:.0f} N ({100*W_wing/W_OE:.1f}% of OE)
• Fuselage: {W_fuselage:.0f} N ({100*W_fuselage/W_OE:.1f}% of OE)
• Propulsion: {W_propulsion:.0f} N ({100*W_propulsion/W_OE:.1f}% of OE)
• Landing Gear: {W_landing_gear:.0f} N ({100*W_landing_gear/W_OE:.1f}% of OE)
• Fixed Equipment: {W_fixed_equipment:.0f} N ({100*W_fixed_equipment/W_OE:.1f}% of OE)
• Empennage: {W_empennage:.0f} N ({100*W_empennage/W_OE:.1f}% of OE)"""
    
    plt.figtext(0.02, 0.02, info_text, fontsize=9, verticalalignment='bottom', 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.9))
    
    # Ensure both pie charts are circular
    ax1.axis('equal')
    ax2.axis('equal')
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.4)  # Make room for the info text
    
    # Show the plot
    plt.show()
    
    # Print detailed summary
    print("=== CLASS II WEIGHT BREAKDOWN SUMMARY ===")
    print(f"\nTake-off Weight (W_TO): {W_TO:.0f} N ({W_TO/9.80665:.0f} kg)")
    print(f"\nMain Components:")
    print(f"  Operating Empty (W_OE): {W_OE:.0f} N ({100*W_OE/W_TO:.1f}%)")
    print(f"  Total Fuel Weight: {W_F_total:.0f} N ({100*W_F_total/W_TO:.1f}%)")
    print(f"    - Used Fuel: {W_F_used:.0f} N ({100*W_F_used/W_TO:.1f}%)")
    print(f"    - Reserve Fuel: {W_F_reserve:.0f} N ({100*W_F_reserve/W_TO:.1f}%)")
    print(f"  Payload Weight (W_PL): {W_PL:.0f} N ({100*W_PL/W_TO:.1f}%)")
    
    print(f"\nFuel Analysis:")
    print(f"  Reserve Ratio (M_res): {M_res:.3f}")
    print(f"  Reserve fuel is {M_res*100:.1f}% of used fuel")
    print(f"  Used fuel is {100*W_F_used/W_F_total:.1f}% of total fuel")
    
    print(f"\nOperating Empty Weight Components:")
    components = [
        ("Wing", W_wing),
        ("Fuselage", W_fuselage), 
        ("Propulsion", W_propulsion),
        ("Landing Gear", W_landing_gear),
        ("Fixed Equipment", W_fixed_equipment),
        ("Empennage", W_empennage)
    ]
    
    # Sort by weight (heaviest first)
    components.sort(key=lambda x: x[1], reverse=True)
    
    for name, weight in components:
        print(f"  {name}: {weight:.0f} N ({100*weight/W_OE:.1f}% of OE, {100*weight/W_TO:.1f}% of TO)")
    
    print(f"\nTotal OE Components: {sum(w for _, w in components):.0f} N")
    print(f"OE from input: {W_OE:.0f} N")
    print(f"Difference: {W_OE - sum(w for _, w in components):.0f} N")

if __name__ == "__main__":
    create_weight_breakdown_pie_chart()