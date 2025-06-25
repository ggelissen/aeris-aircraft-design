from pyxdsm.XDSM import XDSM, OPT, SOLVER, FUNC, GROUP, IFUNC

# 1. Create a new XDSM instance
xdsm = XDSM(use_sfmath=True)

# 2. Add all the components to the XDSM
xdsm.add_system("opt", OPT, r"\text{0, 7-1: Optimizer}")
xdsm.add_system("iterator", SOLVER, r"\text{1, 5-2: Iterator}")
xdsm.add_system("class_i", FUNC, r"\text{2: Class I Estimations}")
xdsm.add_system("prelim_sizing", FUNC, r"\text{3: Preliminary Sizing}")
xdsm.add_system("class_ii", FUNC, r"\text{4: Class II Estimations}")
xdsm.add_system("constraints", IFUNC, r"\text{6: Constraints}")

# 3. Define the connections (data flow) between the components

# Above the diagonal 
xdsm.connect("iterator", "class_i", r"MTOW, OEW, C_{D0}", label_width=2)
xdsm.connect("class_i", "prelim_sizing", r"L/D, TSFC, W/S, T/W", label_width=2)
xdsm.connect("opt", "prelim_sizing", r"A_w, W/S, \Lambda_{0.25c}", label_width=2)
xdsm.connect("iterator", "prelim_sizing", r"A_w, S_w", label_width=2)
xdsm.connect("class_i", "class_ii", r"MTOW, OEW", label_width=2)
xdsm.connect("prelim_sizing", "class_ii", r"GEOM_c", label_width=2)
xdsm.connect("class_i", "constraints", r"W/S, T/W", label_width=2)
xdsm.connect("prelim_sizing", "constraints", r"A_w", label_width=2)

# Under the diagonal
xdsm.connect("class_ii", "iterator", r"MTOW, OEW", label_width=2)
xdsm.connect("prelim_sizing", "iterator", r"A_w, S_w, C_{D0}", label_width=2)

xdsm.connect("class_ii", "opt", r"m_{fuel}", label_width=2)
xdsm.connect("constraints", "opt", r"g", label_width=2)

# Inputs from outside the system
xdsm.add_input("opt", r"\mathbf{x^{(0)}}")
#xdsm.add_input("iterator", r"TLAR")
xdsm.add_input("class_i", r"R_{cr}, V_{cr}, h_{cr}, M_{ff}, L/D, TSFC, OEW/MTOW", label_width=3)
# xdsm.add_input("prelim_sizing", r"TLAR")
# xdsm.add_input("class_ii", r"TLAR")
# xdsm.add_input("constraints", r"TLAR")

# Outputs from the system
xdsm.add_output("opt", r"\mathbf{x^*}", side="left")

# 4. Group components to indicate a process
# Inner loop process
xdsm.add_process(
    [
        "iterator",
        "class_i", 
        "prelim_sizing",
        "iterator"
    ]
)

# Outer loop process
xdsm.add_process(
    [
        "opt",
        "iterator",
        "class_i",
        "prelim_sizing", 
        "class_ii",
        "constraints",
        "opt"
    ]
)

# 5. Write the XDSM diagram to a PDF file
xdsm.write("xdsm/simplified_aircraft_xdsm")
