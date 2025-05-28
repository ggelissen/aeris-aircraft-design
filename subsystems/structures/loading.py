# Make V-n diagram, taking into account loads from the wake of the previous aircraft
# make use of https://ntrs.nasa.gov/api/citations/20140000839/downloads/20140000839.pdf page 280 and further
# as well as https://ntrs.nasa.gov/api/citations/20160010341/downloads/20160010341.pdf


import design_variables



# Step n: Create V-n digram from STANAG-4671

def vn_diagram():
    """
    Create a V-n diagram based on the STANAG-4671 standard.
    This function will use the aircraft model created in the previous steps
    and simulate the loads to generate the V-n diagram.
    """


    weight = design_variables.get_weight()
    print(weight)


    print("Generating V-n diagram... (this is a placeholder)")
    # Actual implementation would go here





