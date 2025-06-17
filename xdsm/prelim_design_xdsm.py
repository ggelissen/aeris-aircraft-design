from pyxdsm.XDSM import XDSM, OPT, SOLVER, FUNC, GROUP

# XDSM setup
x = XDSM()

# 1. Add systems, starting from top-left
# Note: Special LaTeX characters like '&' must be escaped with a backslash, e.g., '\&'.
# Subscripts can be created using math mode, e.g., '$n_{ult}$'.
x.add_system("opt", OPT, r"\text{0, 8-1: Optimizer}")
x.add_system("iterator", SOLVER, r"\text{1, 6-2: Iterator}")
x.add_system("class1", FUNC, r"\text{2: Class I Estimations}")
x.add_system("prelim_sizing", FUNC, r"\text{3: Preliminary Sizing}")
x.add_system("class2", FUNC, r"\text{4: Class II Estimations}")
x.add_system("prelim_positioning", FUNC, r"\text{5: Prelim. Positioning}")
x.add_system("constraints", FUNC, r"\text{7: Constraints}")

# 2. Add connections
# Connections from the outside to the first block\
x.add_input("opt", r"\mathbf{x^{(0)}}") 
x.add_input("iterator", r"TLAR")
x.add_input("class1", r"\text{Mission definition, fuel fractions}, L/D, TSFC, OEW/MTOW")

# Connections from 'sizing' to other blocks
x.add_output("sizing", r"\text{OEW, MTOW, W}_{F}", side="right")
x.connect("class1", "prelim_sizing", "L/D, TSFC")
x.connect("class1", "class2", "OEW")
x.connect("class1", "prelim_positioning", "L/D")

# Connections from 'multidisciplinary' to other blocks
x.add_output("prelim_sizing", r"3D views, $n_{ult}$", side="right")
x.connect("multidisciplinary", "sizing", "OEW")


# Connections from 'structures' to other blocks
x.add_output("structures", "OEW, c.g. range", side="right")
x.connect("structures", "multidisciplinary", "OEW")


# Connections from 'aero'
x.connect("aero", "structures", "Tail size and position, Wing position, Landing gear position")

# 3. Add process flow
x.add_process(["sizing", "multidisciplinary", "structures", "aero"], arrow=True)


# 4. Generate the diagram
# Note: The 'build=True' flag requires a LaTeX distribution (like MiKTeX or TeX Live) to be installed.
# Also ensure that the output directory exists if you specify one.
x.write("xdsm/prelim_design_xdsm", build=False)