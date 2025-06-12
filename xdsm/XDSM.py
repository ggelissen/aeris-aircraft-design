from pyxdsm.XDSM import XDSM, OPT, SOLVER, FUNC, GROUP

# 1. Create a new XDSM instance
# We can specify if we want to use LaTeX's sans-serif fonts
xdsm = XDSM(use_sfmath=True)

# 2. Add all the components to the XDSM
# The arguments are: name (str), type (str), and label (str)
# The name is a unique ID. The label is what is displayed in the diagram.
xdsm.add_system("opt", OPT, r"\text{0, 11-1: Optimizer}")
xdsm.add_system("iterator", SOLVER, r"\text{1, 7-2: Iterator}")
xdsm.add_system("prelim_design", FUNC, r"\text{2: Preliminary Design}")
xdsm.add_system("aero", FUNC, r"\text{3: Aerodynamics}")
xdsm.add_system("structures", FUNC, r"\text{4: Structures}")
xdsm.add_system("propulsion", FUNC, r"\text{5: Propulsion}")
xdsm.add_system("flight_perf", FUNC, r"\text{6: Flight Performance}")
xdsm.add_system("climate", FUNC, r"\text{8: Climate}")
xdsm.add_system("cost", FUNC, r"\text{9: Cost}")
xdsm.add_system("constraints", FUNC, r"\text{10: Constraints}")             # TODO: Add stability and control subsystem

# 3. Define the connections (data flow) between the components

# Above the diagonal 
xdsm.connect("opt", "prelim_design", r"M_{cr}, h_{cr}, A_w", label_width=2)                 # TODO: Might want to add more inputs (sweep, t/c etc.)
xdsm.connect("iterator", "prelim_design", r"C_{L,max}, OEW, MTOW, TSFC", label_width=2)

xdsm.connect("iterator", "aero", r"MTOW", label_width=2)
xdsm.connect("prelim_design", "aero", r"C_{D0}, S_w", label_width=2)

xdsm.connect("iterator", "structures", r"GEOM_{CS}", label_width=2)
xdsm.connect("prelim_design", "structures", r"n_{ult}, GEOM_c, W_c, X_c", label_width=2)
xdsm.connect("aero", "structures", r"C_L, C_D, C_M, GEOM_{HLD}", label_width=2)

xdsm.connect("opt", "propulsion", r"M_{cr}, h_{cr}", label_width=2)
xdsm.connect("iterator", "propulsion", r"MTOW", label_width=2)
xdsm.connect("prelim_design", "propulsion", r"T_{TO}", label_width=2)
xdsm.connect("aero", "propulsion", r"L/D", label_width=2)

xdsm.connect("iterator", "flight_perf", r"MTOW", label_width=2)
xdsm.connect("structures", "flight_perf", r"OEW", label_width=2)
xdsm.connect("propulsion", "flight_perf", r"TSFC", label_width=2)

xdsm.connect("prelim_design", "climate", r"T_{TO}", label_width=2)
xdsm.connect("structures", "climate", r"OEW", label_width=2)                # TODO: Reconsider this connection
xdsm.connect("flight_perf", "climate", r"m_{fuel}", label_width=2)

xdsm.connect("structures", "cost", r"OEW", label_width=2)                   # TODO: Reconsider this connection
xdsm.connect("flight_perf", "cost", r"m_{fuel}, t_{bl}", label_width=2)

xdsm.connect("propulsion", "constraints", r"dBN", label_width=2)
xdsm.connect("climate", "constraints", r"ATR_{100}", label_width=2)
xdsm.connect("cost", "constraints", r"DOC", label_width=2)


# Under the diagonal
xdsm.connect("aero", "iterator", r"C_{L,max}, L/D", label_width=2)
xdsm.connect("structures", "iterator", r"OEW", label_width=2)
xdsm.connect("propulsion", "iterator", r"TSFC, m_{eng}", label_width=2)
xdsm.connect("flight_perf", "iterator", r"m_{fuel}, GEOM_{cs}", label_width=2)

xdsm.connect("flight_perf", "opt", r"m_{fuel}", label_width=2)
xdsm.connect("climate", "opt", r"ATR_{100}", label_width=2)
xdsm.connect("cost", "opt", r"DOC", label_width=2)
xdsm.connect("constraints", "opt", r"g", label_width=2)


# Inputs from outside the system
xdsm.add_input("opt", r"\mathbf{x^{(0)}}")
xdsm.add_input("iterator", r"TLAR")
xdsm.add_input("prelim_design", r"TLAR")
xdsm.add_input("structures", r"TRB")
xdsm.add_input("propulsion", r"TRB")
xdsm.add_input("flight_perf", r"TLAR")
#xdsm.add_input("climate", r"m_{fuel}")
xdsm.add_input("constraints", r"TLAR")

# Outputs from the system
xdsm.add_output("opt", r"\mathbf{x^*}", side="left")


# 4. Group components to indicate a process
# This will draw a box around the specified components
xdsm.add_process(
    [
        "prelim_design",
        "aero",
        "structures",
        "propulsion",
        "flight_perf",
        "climate",
        "cost",
        "constraints",
    ]
)

# 5. Write the XDSM diagram to a PDF file
# This will create "aircraft_xdsm.pdf" and the associated TeX files.
xdsm.write("xdsm/aircraft_xdsm")
