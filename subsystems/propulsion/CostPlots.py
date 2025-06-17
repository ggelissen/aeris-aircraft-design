import matplotlib.pyplot as plt

# Data extracted from the image
# Nm: Number of aircraft sold
# ACQ Cost (incl. Dev): Acquisition cost in Euros (including development)
num_aircraft_sold = [
    50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000, 2500
]

acquisition_cost_euros = [
    6264521.851, 4646840.137, 4006131.284, 3645018.973, 3407074.844,
    3235650.561, 3000739.672, 2843997.413, 2729987.679, 2642280.283,
    2572098.517, 2514278.388, 2465559.724, 2301274.556, 2203671.119,
    2136952.636
]

# Convert acquisition cost to million euros for plotting
acquisition_cost_million_euros = [cost / 1_000_000 for cost in acquisition_cost_euros]

# Create the plot
plt.figure(figsize=(10, 6)) # Set the figure size for better readability
plt.plot(num_aircraft_sold, acquisition_cost_million_euros, marker='o', linestyle='-', color='blue')

plt.xlabel('Number of Aircraft Sold', fontsize=12)
plt.ylabel('Acquisition Cost [Million Euros]', fontsize=12)

# Add grid for better readability
plt.grid(True, linestyle='--', alpha=0.7)

# Customize ticks for better readability
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

# Optional: Add data labels for specific points if needed (e.g., every 5th point)
# for i in range(0, len(num_aircraft_sold), 5):
#     plt.text(num_aircraft_sold[i], acquisition_cost_million_euros[i],
#              f'{acquisition_cost_million_euros[i]:.2f}M€',
#              fontsize=9, ha='right', va='bottom')

# Show the plot
plt.tight_layout() # Adjust layout to prevent labels from overlapping
plt.show()
# import matplotlib.pyplot as plt
# import numpy as np # Used for np.cos, np.sin, np.deg2rad

# # Data for the pie chart (DOC Category and Euros)
# categories = [
#     'Crew',
#     'Fuel',
#     'Insurance',
#     'Maintenance',
#     'Depreciation',
#     'Landing/Navigation',
#     'Finance'
# ]

# euros_values = [
#     315.42, # Crew
#     81.14,  # Fuel
#     4.10,   # Insurance
#     416.97, # Maintenance
#     124.12, # Depreciation
#     2.91,   # Landing/Navigation
#     49.72   # Finance
# ]

# # Combine categories and values into pairs, then sort them by value (descending)
# sorted_pairs = sorted(zip(categories, euros_values), key=lambda x: x[1], reverse=False)

# # Unpack the sorted pairs back into separate lists
# sorted_categories = [pair[0] for pair in sorted_pairs]
# sorted_euros_values = [pair[1] for pair in sorted_pairs]

# # Define custom shades of blue for the categories, matching the order of 'categories' list
# # The colors are chosen to provide visual distinction while staying within the blue palette,
# # inspired by 'lightcyan', 'cyan', 'royalblue', 'darkblue'.
# # We need to re-map these colors to the sorted categories for consistency.
# # Create a dictionary to map original categories to their colors, then apply to sorted categories
# original_colors_map = {
#     'Crew': '#4169E1',
#     'Fuel': '#6A5ACD',
#     'Insurance': '#E0FFFF',
#     'Maintenance': '#00008B',
#     'Depreciation': '#191970',
#     'Landing/Navigation': '#AFEEEE',
#     'Finance': '#00CED1'
# }

# # Apply colors based on the sorted categories
# sorted_custom_blue_colors = [original_colors_map[cat] for cat in sorted_categories]


# # Create the pie chart
# plt.figure(figsize=(14, 10)) # Increased figure size for better label placement

# # Use `autopct=None` for now, as we will manually place all labels.
# # `plt.pie` returns wedges, and if labels are passed, a list of Text objects for labels.
# # If autopct is not None, it also returns a list of Text objects for percentages.
# # In this setup, we'll explicitly manage all text placement to ensure no overlap.
# wedges, _ = plt.pie(
#     sorted_euros_values, # Use sorted values
#     autopct=None,           # No default percentages on the slices
#     startangle=90,          # Start the first slice at the top
#     colors=sorted_custom_blue_colors, # Use the sorted custom defined blue colors
#     wedgeprops={'edgecolor': 'black', 'linewidth': 0.5} # Add borders to slices
# )


# # Manually place category name, value, and percentage labels outside the pie chart
# # Refined bbox_props to be slightly smaller and less opaque
# bbox_props = dict(boxstyle="round,pad=0.2", fc="w", ec="0.5", lw=0.5, alpha=0.8) # Smaller padding, less opaque
# arrow_props = dict(arrowstyle="-", color="0.5", connectionstyle="arc3,rad=0")

# # Calculate total sum for percentages
# total_value = sum(sorted_euros_values)

# for i, wedge in enumerate(wedges):
#     # Calculate the angle of the middle of the wedge
#     angle = (wedge.theta2 + wedge.theta1) / 2.0
#     x_center, y_center = wedge.center
#     radius = wedge.r
    
#     # Determine the radial distance for the label.
#     # We need a more aggressive offset for very small slices.
#     # The smallest slices were "Landing/Navigation" (€2.91) and "Insurance" (€4.10)
#     # The next small one is Finance (€49.72)
#     # Define thresholds and corresponding multipliers.
#     if sorted_euros_values[i] / total_value < 0.005: # For very very small slices (e.g., < 0.5%)
#         label_radius_multiplier = 1.7
#     elif sorted_euros_values[i] / total_value < 0.05: # For small slices (e.g., < 5%)
#         label_radius_multiplier = 1.6
#     elif sorted_euros_values[i] / total_value < 0.10: # For medium-small slices (e.g., < 10%)
#         label_radius_multiplier = 1.35
#     else: # For larger slices
#         label_radius_multiplier = 1.2


#     x_text_pos = x_center + radius * label_radius_multiplier * np.cos(np.deg2rad(angle))
#     y_text_pos = y_center + radius * label_radius_multiplier * np.sin(np.deg2rad(angle))

#     # Determine horizontal alignment based on angle for better text placement
#     # Also adjust for specific quadrants for better visual appeal.
#     ha = 'center' # Default to center, then adjust.
#     if angle > 90 and angle < 270: # Left half of the circle
#         ha = 'right'
#     elif angle <= 90 or angle >= 270: # Right half of the circle
#         ha = 'left'

#     # Special adjustments for very small slices that might still overlap with neighbors
#     # This might require manual fine-tuning based on actual output.
#     # For "Landing/Navigation" and "Insurance" which are very close and small.
#     # In a sorted list, they are at the end.
#     if sorted_categories[i] == 'Landing/Navigation':
#         y_text_pos -= 0.05 # Slightly nudge down
#         if ha == 'left': # If on the right side, shift right more
#              x_text_pos += 0.05
#         else: # If on the left side, shift left more
#              x_text_pos -= 0.05
#     elif sorted_categories[i] == 'Insurance':
#         y_text_pos += 0.05 # Slightly nudge up
#         if ha == 'left': # If on the right side, shift right more
#             x_text_pos += 0.05
#         else: # If on the left side, shift left more
#             x_text_pos -= 0.05
#     elif sorted_categories[i] == 'Finance': # Another small slice that might be problematic
#         if ha == 'left':
#             x_text_pos += 0.02
#         else:
#             x_text_pos -= 0.02

#     # Calculate percentage for the label
#     percentage = (sorted_euros_values[i] / total_value) * 100
    
#     # Create the label string with Category, Value, and Percentage
#     label_string = f'{sorted_categories[i]}\n{sorted_euros_values[i]:.2f}€ ({percentage:.1f}%)'
    
#     # Add text label
#     plt.text(x_text_pos, y_text_pos, label_string,
#              ha=ha, va='center', fontsize=9, bbox=bbox_props)

#     # Add connecting arrow/line for clarity
#     plt.annotate('', xy=(x_center + radius * np.cos(np.deg2rad(angle)),
#                          y_center + radius * np.sin(np.deg2rad(angle))), # Start point at wedge edge
#                  xytext=(x_text_pos, y_text_pos), # End point at label
#                  arrowprops=arrow_props,
#                  horizontalalignment=ha,
#                  verticalalignment='center')


# # Ensure the pie chart is drawn as a perfect circle
# plt.axis('equal')

# # Remove the legend as requested
# # plt.legend(...)

# # Adjust layout to prevent labels from overlapping with the plot or figure edges
# plt.tight_layout()
# plt.show()