# Python script to generate a flowchart for the Transonic Wing Design Algorithm
# Requires the 'graphviz' Python package and the Graphviz C library installed.
# To install the Python package: pip install graphviz
# To install Graphviz (software): https://graphviz.org/download/

from graphviz import Digraph

def generate_flowchart():
    """
    Generates a flowchart for the Transonic Wing Design Algorithm.
    """
    dot = Digraph(comment='Transonic Wing Design Algorithm Flowchart', engine='dot')
    dot.attr(rankdir='TD', labelloc='t', label='Transonic Wing Design Algorithm', fontsize='20')

    # Define node styles based on Mermaid classes (approximated)
    # Start/End nodes
    start_end_attrs = {'shape': 'box', 'style': 'filled', 'fillcolor': '#cff', 'fontname': 'Helvetica'}
    # Input/Output nodes
    io_attrs = {'shape': 'parallelogram', 'style': 'filled', 'fillcolor': '#cfc', 'fontname': 'Helvetica'} # Parallelogram for I/O
    # Process nodes
    process_attrs = {'shape': 'box', 'style': 'filled', 'fillcolor': '#ccf', 'fontname': 'Helvetica'}
    # Decision nodes
    decision_attrs = {'shape': 'diamond', 'style': 'filled', 'fillcolor': '#fcf', 'fontname': 'Helvetica'}

    # Define nodes
    dot.node('A', 'Start: Transonic Wing Design Algorithm', **start_end_attrs)
    dot.node('B', 'Define Inputs & Requirements', **io_attrs)
    dot.node('C', 'Define Design Variables', **io_attrs)
    dot.node('D', 'Initialize Optimization Loop / Select Design Point', **process_attrs)

    # Subgraph for Iteration / Design Point Evaluation
    with dot.subgraph(name='cluster_iteration') as sub:
        sub.attr(label='Iteration / Design Point Evaluation', style='filled', color='lightgrey', fontname='Helvetica', fontsize='16')
        sub.node_attr.update(style='filled', fontname='Helvetica')

        # Nodes within the subgraph
        sub.node('E', 'Calculate Wing Thickness Ratio (t/c)_w ?', **decision_attrs) # Mermaid {} implies decision
        sub.node('F', 'Is (t/c)_w Valid?', **decision_attrs)
        sub.node('G', 'Estimate/Iterate MTOW for current point', **process_attrs)
        sub.node('H', 'Calculate Wing Geometry: S_w, b_w', **process_attrs)
        sub.node('I', 'Calculate Aerodynamic Drag Components:\nC_D_profile,wing, C_D_induced, C_D_compressibility, C_D_total', **process_attrs)
        sub.node('J', 'Calculate Propulsion Function: F_prop', **process_attrs)
        sub.node('K', 'Calculate Wing Structural Weight Parameters: Λ2, Λ3', **process_attrs)
        sub.node('L', 'Calculate Wing Penalty Function (WPF)', **process_attrs)
        sub.node('M', 'Calculate Figure of Merit (FOM)?', **decision_attrs) # Mermaid {} implies decision
        sub.node('N', 'Evaluate Constraints', **process_attrs)
        sub.node('O', 'Is Design Feasible?\n(All Constraints Met)', **decision_attrs)
        sub.node('P', 'Is Current FOM better than Best FOM?', **decision_attrs)
        sub.node('Q', 'Update Best FOM & Store Optimal Design Parameters', **process_attrs)

        # Edges within the subgraph
        sub.edge('D', 'E')
        sub.edge('E', 'F', label='Calculation Done') # E is calculation leading to F's decision
        sub.edge('F', 'D', label='No, Invalid (t/c)_w\n(Next Point/Stop)')
        sub.edge('F', 'G', label='Yes')
        sub.edge('G', 'H')
        sub.edge('H', 'I')
        sub.edge('I', 'J')
        sub.edge('J', 'K')
        sub.edge('K', 'L')
        sub.edge('L', 'M')
        sub.edge('M', 'N', label='Calculation Done') # M is calculation leading to N
        sub.edge('N', 'O')
        sub.edge('O', 'D', label='No, Infeasible\n(Next Point)')
        sub.edge('O', 'P', label='Yes')
        sub.edge('P', 'D', label='No\n(Next Point)')
        sub.edge('P', 'Q', label='Yes')
        sub.edge('Q', 'D', label='Continue Loop\n(Next Point)')

    dot.node('R', 'Optimization Loop Ends / All Points Evaluated', **process_attrs)
    dot.node('S', 'Output: Optimal Wing Design Parameters & FOM Value', **io_attrs)
    dot.node('T', 'End', **start_end_attrs)

    # Define top-level edges
    dot.edge('A', 'B')
    dot.edge('B', 'C')
    dot.edge('C', 'D')
    dot.edge('D', 'R', label='Loop Exit Condition Met\n(e.g., Converged or All Points Done)') # Edge to exit loop
    dot.edge('R', 'S')
    dot.edge('S', 'T')

    # Render the flowchart
    # You can change the format to 'png', 'svg', etc.
    # The output file will be named 'transonic_wing_design_flowchart.pdf'
    try:
        dot.render('transonic_wing_design_flowchart', view=False, format='pdf')
        print("Flowchart 'transonic_wing_design_flowchart.pdf' generated successfully.")
        print("You might need to install Graphviz (https://graphviz.org/download/) if you haven't already.")
    except Exception as e:
        print(f"Error rendering flowchart: {e}")
        print("Please ensure Graphviz is installed and in your system's PATH.")
        print("You can download it from https://graphviz.org/download/")

if __name__ == '__main__':
    generate_flowchart()
