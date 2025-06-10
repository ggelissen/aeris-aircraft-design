import openvsp as vsp
import numpy as np
from stl import mesh
import pyvista as pv
from design_variables import DesignParameters
from scipy.interpolate import interp1d
import os
import pandas as pd

def print_all_params(obj_id):
    parm_ids = vsp.GetGeomParmIDs(obj_id)
    for pid in parm_ids:
        pname = vsp.GetParmName(pid)
        group = vsp.GetParmGroupName(pid)
        val = vsp.GetParmVal(pid)
        print(f" Group: {group} / Parameter Name: {pname} / Value: {val}")

def plotSTL(file: str):
    # Load the STL file
    # Load STL


    your_mesh = mesh.Mesh.from_file(file)
    points = your_mesh.vectors.reshape(-1, 3)

    # Get unique points and triangle faces
    unique_points, idx = np.unique(points, axis=0, return_inverse=True)
    faces = idx.reshape(-1, 3)
    faces_with_size = np.hstack([np.full((faces.shape[0], 1), 3), faces])  # '3' means triangle

    # Convert to PyVista mesh
    pv_mesh = pv.PolyData(unique_points, faces_with_size)

    # Create a plotter with appropriate rendering mode
    plotter = pv.Plotter(off_screen=is_headless())
    plotter.add_mesh(pv_mesh, smooth_shading=True, color='lightgray', show_edges=False)

    # Show and optionally save screenshot
    plotter.show(screenshot="data/output.png")
    plotter = pv.Plotter()
    plotter.add_mesh(pv_mesh, smooth_shading=True, color='lightgray', show_edges=False)
    plotter.show()

def create_fuselage(designvars: DesignParameters = None):
    fuse_id = vsp.AddGeom("FUSELAGE", "")
    vsp.SetParmVal(fuse_id, "Length", "Design", designvars.fuselage.l_f)

    crosssections = designvars.fuselage.crosssections

    # Set the number of cross-sections to the number of crosssections from the designvars dictionary
    num_of_crosssections = len(crosssections)
    diff = num_of_crosssections - vsp.GetNumXSec(vsp.GetXSecSurf(fuse_id, 0))
    if diff > 0:
        for _ in range(diff):
            vsp.InsertXSec(fuse_id, vsp.GetNumXSec(vsp.GetXSecSurf(fuse_id, 0))-2)
        dist_between_crosssections_fraction = 1 / (num_of_crosssections - 1)
        for i in range(1, vsp.GetNumXSec(vsp.GetXSecSurf(fuse_id, 0))):
            vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), "XLocPercent"),
                           i * dist_between_crosssections_fraction)
    elif diff < 0:
        for _ in range(abs(diff)):
            vsp.CutXSec(fuse_id, 1)
        dist_between_crosssections_fraction = 1 / (num_of_crosssections - 1)
        for i in range(1, vsp.GetNumXSec(vsp.GetXSecSurf(fuse_id, 0))):
            vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), "XLocPercent"),
                           i * dist_between_crosssections_fraction)
    # Tip of the fuselage
    fuselage_tip = crosssections["fuselagetip1"]["Tan_Angles"]
    vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), 0), vsp.XSEC_BOTH_SIDES, fuselage_tip['top'] , fuselage_tip["right"], fuselage_tip["bottom"], fuselage_tip["left"])

    # Set middle crosssections
    for j, value in enumerate(list(crosssections.values())[1:-1]):
        i = j+1
        vsp.ChangeXSecShape(vsp.GetXSecSurf(fuse_id, 0), i, eval(value["Type"]))
        if value["Type"] == "vsp.XS_ROUNDED_RECTANGLE":
            vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), "RoundedRect_Width"), value["Dimensions"]["Width"])
            vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), "RoundedRect_Height"), value["Dimensions"]["Height"])
            vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), "RoundRect_Keystone"), value["Dimensions"]["Keystone"])
            vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), "RoundedRect_RadiusSymmetryType"), value["Dimensions"]["RadiusSymmetryType"])
            vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), "RoundRectXSec_Radius"), value["Dimensions"]["Radius"])
            if value["Dimensions"]["RadiusSymmetryType"] == 1.0:
                vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), "RoundRectXSec_RadiusBR"), value["Dimensions"]["RadiusBR"])
        cs_tan_angles = value["Tan_Angles"]
        vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), i), vsp.XSEC_BOTH_SIDES, cs_tan_angles["top"], cs_tan_angles["right"], cs_tan_angles["bottom"], cs_tan_angles["left"])

    # Fuselage end tip
    fuselage_tip2 = crosssections["fuselagetip2"]["Tan_Angles"]
    vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), 4), vsp.XSEC_BOTH_SIDES, fuselage_tip2['top'], fuselage_tip2["right"], fuselage_tip2["bottom"], fuselage_tip2["left"])
    designvars.fuselage.fuseid = fuse_id

    vsp.SetParmVal(fuse_id, "Tess_W", "Shape", 100)
    print(vsp.GetParmVal(fuse_id, "Tess_W", "Shape"))
    vsp.UpdateGeom(fuse_id)

def create_wing(designvars: DesignParameters = None):
    wing_id = vsp.AddGeom("WING", "")
    print(f"wingid: {wing_id}")
    wing_model = vsp.AddFeaStruct(wing_id)
    wingpars = designvars.wing

    # Wing sizing
    vsp.SetParmVal(wing_id, "Span", "XSec_1", wingpars.b_w/2)
    vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", wingpars.root_chord)
    vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", wingpars.tip_chord)
    vsp.SetParmVal(wing_id, "Sweep_Location", "XSec_1", 0.25)
    vsp.SetParmVal(wing_id, "Sweep", "XSec_1", np.rad2deg(wingpars.Lambda_025c_w))

    # Set root airfoil, parametrised using Class-Shape Transformation (CST) coefficients, which are better for supercritical airfoils
    vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 0, vsp.XS_CST_AIRFOIL)
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "Camber"), wingpars.camber_r) # This is for NACA Four Series, not CST
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "CamberLoc"), wingpars.camber_loc_r) # This is for NACA Four Series, not CST
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "ThickChord"), wingpars.t_c_w_r) # This is for NACA Four Series, not CST
    vsp.SetUpperCST(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), len(wingpars.CST_uppersurf), wingpars.CST_uppersurf)
    vsp.SetLowerCST(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), len(wingpars.CST_lowersurf), wingpars.CST_lowersurf)
    # Scale root airfoil to required thickness to chord ratio
    vsp.UpdateGeom(wing_id)
    vsp.WriteSeligAirfoil("data/Airfoil.dat", wing_id, 0) # Write airfoil to file

    vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 0, vsp.XS_FILE_AIRFOIL)
    vsp.ReadFileAirfoil(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "data/Airfoil.dat") # Read airfoil from file
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "ThickChord"), wingpars.t_c_w_r) # After reimiport thickness can be set

    # Set tip airfoil, parametrised using Class-Shape Transformation (CST) coefficients, which are better for supercritical airfoils
    vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 1, vsp.XS_CST_AIRFOIL)
    # vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "Camber"), 0.05) # This is for NACA Four Series, not CST
    # vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "CamberLoc"), 0.2) # This is for NACA Four Series, not CST
    # vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "ThickChord"), 0.1) # This is for NACA Four Series, not CST
    vsp.SetUpperCST(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), len(wingpars.CST_uppersurf), wingpars.CST_uppersurf)
    vsp.SetLowerCST(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), len(wingpars.CST_lowersurf), wingpars.CST_lowersurf)
    # Scale tip airfoil to required thickness to chord ratio
    vsp.UpdateGeom(wing_id)
    vsp.WriteSeligAirfoil("data/Airfoil.dat", wing_id, 1)  # Write airfoil to file
    vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 1, vsp.XS_FILE_AIRFOIL)
    vsp.ReadFileAirfoil(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "data/Airfoil.dat")  # Read airfoil from file
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 1), 0), "ThickChord"), wingpars.t_c_w_t)  # After reimiport thickness can be set
    vsp.UpdateGeom(wing_id)

    # Position wing on fuselage
    vsp.WriteVSPFile('data/special.vsp3')
    wingpars.mac = vsp.GetParmVal(wing_id, "MAC", "WingGeom")  # Mean Aerodynamic Chord)
    tip_chord = vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),1), "Tip_Chord"))
    root_chord = vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),1), "Root_Chord"))
    wingpars.y_LEMAC = 0.5 * (wingpars.mac - root_chord) * vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),1), "Span")) / (tip_chord - root_chord)
    x_pos = wingpars.x_LEMAC - (np.tan(wingpars.Lambda_025c_w) * wingpars.y_LEMAC - 0.25 * wingpars.mac)
    vsp.SetParmVal(wing_id, "X_Rel_Location", "XForm", x_pos)
    vsp.SetParmVal(wing_id, "Z_Rel_Location", "XForm", -wingpars.z_LEMAC)

    # Add Incidence Angle
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "Theta"), wingpars.i_w )
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "Theta"), wingpars.i_w )

    # Add Dihedral
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "Dihedral"), np.rad2deg(wingpars.Gamma_w))

    # Add wing twist
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "Twist_Location"), 0.25)
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "Twist"), np.rad2deg(wingpars.epsilon_t_quarter_chord))

    planform_points = []
    for thing in vsp.GetFeatureLinePnts(wing_id):
        if np.isclose(thing.z(), 0.0, rtol=0, atol=1e-5):
            planform_points.append(np.array([thing.x(), thing.y()]))
    wingpars.planform_points = np.array(planform_points)


    wingpars.wingid = wing_id

    vsp.SetParmVal(wing_id, "Tess_W", "Shape", 200)
    # Add yehudi
    if wingpars.yehudi:
        vsp.SplitWingXSec(wing_id, 1)
        vsp.UpdateGeom(wing_id)
        vsp.SetDriverGroup(wing_id, 1, vsp.AREA_WSECT_DRIVER, vsp.SECSWEEP_WSECT_DRIVER, vsp.SPAN_WSECT_DRIVER)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Sec_Sweep_Location", "XSec_2", 0.0)
        vsp.UpdateGeom(wing_id)
        vsp.SetDriverGroup(wing_id, 2, vsp.AREA_WSECT_DRIVER, vsp.SECSWEEP_WSECT_DRIVER, vsp.AR_WSECT_DRIVER)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Span", "XSec_1", wingpars.b_w/2 * wingpars.yehudi_pos_frac)  # Set span again after split
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Area", "XSec_1", wingpars.yehudi_area / 2)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Area", "XSec_2", wingpars.S_w / 2 - wingpars.yehudi_area / 2)
        vsp.UpdateGeom(wing_id)
        taper_second_part_of_wing = vsp.GetParmVal(wing_id, "Taper", "XSec_2")
        LEsweep = np.rad2deg(np.arctan(((
                    2 * 0.25 * wingpars.tip_chord * (-1 + 1 / taper_second_part_of_wing) / vsp.GetParmVal(wing_id, 'Span', 'XSec_2') + np.tan(np.deg2rad(
                vsp.GetParmVal(wing_id, 'Sweep', 'XSec_2')))))))
        vsp.SetParmVal(wing_id, "Sec_Sweep_Location", "XSec_1", 0.0)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Sec_Sweep", "XSec_1", LEsweep)  # Set sweep again after split
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Sweep_Location", "XSec_1", 1.0)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Sweep", "XSec_1", 0.0)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Area", "XSec_1", wingpars.yehudi_area / 2)
        vsp.UpdateGeom(wing_id)

        vsp.SetParmVal(wing_id, "Area", "XSec_2", wingpars.S_w / 2 - wingpars.yehudi_area / 2)
        vsp.UpdateGeom(wing_id)
        taper_second_part_of_wing = vsp.GetParmVal(wing_id, "Taper", "XSec_2")
        LEsweep = np.rad2deg(np.arctan(((
                2 * 0.25 * wingpars.tip_chord * (-1 + 1 / taper_second_part_of_wing) / vsp.GetParmVal(wing_id, 'Span',
                                                                                                      'XSec_2') + np.tan(np.deg2rad(
            vsp.GetParmVal(wing_id, 'Sweep', 'XSec_2')))))))
        vsp.SetParmVal(wing_id, "Sec_Sweep_Location", "XSec_1", 0.0)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Sec_Sweep", "XSec_1", LEsweep)  # Set sweep again after split
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Sweep_Location", "XSec_1", 1.0)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Sweep", "XSec_1", 0.0)
        vsp.UpdateGeom(wing_id)
        vsp.SetParmVal(wing_id, "Area", "XSec_2", wingpars.S_w / 2 - wingpars.yehudi_area / 2)
        for i in range(5):
            vsp.SetParmVal(wing_id, "Area", "XSec_1", wingpars.yehudi_area / 2)
            vsp.UpdateGeom(wing_id)
            vsp.SetParmVal(wing_id, "Area", "XSec_2", wingpars.S_w / 2 - wingpars.yehudi_area / 2)
            vsp.UpdateGeom(wing_id)
        new_halfspan = vsp.GetParmVal(wing_id, "Span", "XSec_1") + vsp.GetParmVal(wing_id, "Span", "XSec_2")
        print(vsp.GetParmVal(wing_id, "Area", "XSec_1"), vsp.GetParmVal(wing_id, "Area", "XSec_2"), wingpars.S_w/2)
        wingpars.b_w = new_halfspan * 2
        mac = vsp.GetParmVal(wing_id, "MAC", "WingGeom")
        wingpars.mac = mac
        wingpars.yehudi_pos_frac = vsp.GetParmVal(wing_id, "Span", "XSec_1")/new_halfspan
        wingpars.Lambda_0_w = np.deg2rad(vsp.GetParmVal(wing_id, "Sec_Sweep", "XSec_1"))
        wingpars.Lambda_025c_w = np.arctan(np.tan(wingpars.Lambda_0_w)-2*0.25*vsp.GetParmVal(wing_id, "Tip_Chord", "XSec_2")*(-1+vsp.GetParmVal(wing_id, "Taper", "XSec_2"))/vsp.GetParmVal(wing_id, "Span", "XSec_2"))

        # Reposition wing with updated planform:
        # Position wing on fuselage
        wingpars.mac = vsp.GetParmVal(wing_id, "MAC", "WingGeom")  # Mean Aerodynamic Chord)

        if wingpars.mac < vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),2), "Root_Chord")):
            tip_chord = vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),2), "Tip_Chord"))
            root_chord = vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),2), "Root_Chord"))
            wingpars.y_LEMAC = 0.5 * (wingpars.mac - root_chord) * (vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),2), "Span"))) / (tip_chord - root_chord) + vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),1), "Span"))
        else:
            tip_chord = vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),1), "Tip_Chord"))
            root_chord = vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),1), "Root_Chord"))
            wingpars.y_LEMAC = 0.5 * (wingpars.mac - root_chord) * (vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id,0),1), "Span"))) / (tip_chord - root_chord)

        x_pos = wingpars.x_LEMAC - (np.tan(wingpars.Lambda_0_w) * wingpars.y_LEMAC)
        wingpars.xpos = x_pos
        vsp.SetParmVal(wing_id, "X_Rel_Location", "XForm", x_pos)
        vsp.SetParmVal(wing_id, "Z_Rel_Location", "XForm", -wingpars.z_LEMAC)
        vsp.UpdateGeom(wing_id)

def create_V_tail(designvars: DesignParameters = None):
    hstab_id = vsp.AddGeom("WING")
    vsp.SetGeomName(hstab_id, "Horizontal_Stabilizer")
    tailpars = designvars.empennage

    # Position it at the tail (move along X and Z)
    vsp.SetParmVal(hstab_id, "X_Rel_Location", "XForm", tailpars.x_t)  # Tail of the fuselage
    vsp.SetParmVal(hstab_id, "Z_Rel_Location", "XForm", -tailpars.z_t)  # Slight vertical offset

    # Set orientation (v-tail, so dihedral = 40)
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(hstab_id, 0), 1), "Dihedral"), np.rad2deg(tailpars.vtail_dihedral))

    # Symmetry around XZ plane (so it spans both sides)
    vsp.SetParmVal(hstab_id, "Sym_Planar_Flag", "Sym", vsp.SYM_XZ)

    # Size V-Tail
    vsp.SetParmVal(hstab_id, "Span", "XSec_1", tailpars.b_v/2)  # Half span
    vsp.SetParmVal(hstab_id, "Tip_Chord", "XSec_1", tailpars.c_t)
    vsp.SetParmVal(hstab_id, "Root_Chord", "XSec_1", tailpars.c_r)

def create_engines(designvars: DesignParameters = None):
    proppars = designvars.engine
    pod_id = vsp.AddGeom("STACK")
    # print_all_params(pod_id)  # Print all parameters for the engine pod
    vsp.SetGeomName(pod_id, "Fuselage_Engine")
    vsp.SetParmVal(pod_id, "OrderPolicy", "Design", 1)  # Set order policy to "Loop" for engine pod to enable flowthrough
    vsp.ChangeXSecShape(vsp.GetXSecSurf(pod_id, 0), 0, vsp.XS_SUPER_ELLIPSE)
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 0), "Super_Width"), proppars.nacelle_diameter)  # Width of the engine pod
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 0), "Super_Height"), proppars.nacelle_diameter)  # Height of the engine pod
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 0), "Super_MaxWidthLoc"), proppars.nacelle_blend_par)  # Deform the superellipse
    vsp.CutXSec(pod_id, 3)
    vsp.CutXSec(pod_id, 3)
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 1), "XDelta"), proppars.nacelle_length) # Length of the engine pod
    vsp.ChangeXSecShape(vsp.GetXSecSurf(pod_id, 0), 1, vsp.XS_SUPER_ELLIPSE)
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 1), "Super_Width"), proppars.engine_diameter)  # Width of the engine pod
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 1), "Super_Height"), proppars.engine_diameter)  # Height of the engine pod
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 1), "Super_MaxWidthLoc"), proppars.nacelle_blend_par)  # Deform the superellipse
    nita = np.rad2deg(proppars.nacelle_inlet_tan_angles)
    nota = np.rad2deg(proppars.nacelle_outlet_tan_angles)
    vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 0), vsp.XSEC_BOTH_SIDES, nita[0], nita[1], nita[2], nita[3])  # Set tangent angles for the first cross-section
    vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 1), vsp.XSEC_BOTH_SIDES, nota[0], nota[1], nota[2], nota[3])  # Set tangent angles for the second cross-section
    vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 2), vsp.XSEC_BOTH_SIDES, nita[0], nita[1], nita[2], nita[3])  # Set tangent angles for the third cross-section

    vsp.SetParmVal(pod_id, "X_Rel_Location", "XForm", -proppars.engine_x_pos)  # Longitudinal position
    vsp.SetParmVal(pod_id, "Y_Rel_Location", "XForm", proppars.engine_y_pos)  # Side offset (0 = centerline)
    vsp.SetParmVal(pod_id, "Z_Rel_Location", "XForm", -proppars.engine_z_pos)  # Vertical offset (on top of fuselage)

def calculate_cg(designvars: DesignParameters = None):
    """
    Calculate the center of gravity (CG) of the aircraft based on the design parameters.
    This function assumes that the CG is calculated based on the fuselage, wing, empennage, and engines.
    OpenVSP options for analysis 'MassProp' are:
    [input_name]                  [type]       	[doc]
   DegenSet                      integer      	Degenerate geometry Set for analysis.
   MassSliceDir                  integer      	Direction for mass property slicing.
   ModeID                        string       	ID for Mode to use for analysis.
   NumMassSlices                 integer      	Number of slices.
   Set                           integer      	Geometry Set for analysis.
   UseModeFlag                   integer      	Flag to control whether Modes are used instead of Sets.
    """
    # Execute Mass Analysis
    result = vsp.ExecAnalysis("MassProp")
    #vsp.PrintResults(result)

    # CG Coordinates:
    CG_Coords_Vec = vsp.GetVec3dResults(result, "Total_CG")[0]
    CG_Coords = np.array([CG_Coords_Vec.x(), CG_Coords_Vec.y(), CG_Coords_Vec.z()])

    # Inertia:
    I = {}
    for sub in ["xx", "xy", "xz", "yy", "yz", "zz"]:
        I[sub] = vsp.GetDoubleResults(result, f"Total_I{sub}")

    # Total Mass:
    total_mass = vsp.GetDoubleResults(result, "Total_Mass")[0]

    designvars.inertia_matrix = np.array([[I["xx"], I["xy"], I["xz"]],
                                             [I["xy"], I["yy"], I["yz"]],
                                             [I["xz"], I["yz"], I["zz"]]])
    designvars.cg.cg_vector_from_3Dmodel = CG_Coords
    designvars.cg.total_mass_from_3Dmodel = total_mass
    vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0)) # Delete slices
    for geom in vsp.FindGeoms():
        vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown") , True)

def calculate_wet_areas(designvars: DesignParameters = None):
    """
    Calculate the wetted areas of the aircraft components, taking into account parts of the aircraft being partly inside of other
    aircraft components, and therefore not being exposed.
    This function assumes that the wetted areas are calculated based on the fuselage, wing, empennage, and engines.
    OpenVSP options for analysis 'CompGeom' are:
       [input_name]                  [type]       	[doc]
   DegenSet                      integer      	Degenerate geometry Set for analysis.
   HalfMeshFlag                  integer      	Flag to control whether Y >= 0 half mesh is generated.
   ModeID                        string       	ID for Mode to use for analysis.
   Set                           integer      	Normal geometry Set for analysis.
   SubSurfFlag                   integer      	Flag to control whether subsurfaces are used in analysis.
   UseModeFlag                   integer      	Flag to control whether Modes are used instead of Sets.
   WriteCSVFlag                  integer      	Flag to control whether CSV file is written.
    """
    vsp.SetAnalysisInputDefaults("CompGeom")
    #result = vsp.ExecAnalysis("CompGeom")
    output_mesh = vsp.ComputeCompGeom(vsp.SET_SHOWN, False, 0)
    result = vsp.FindLatestResultsID("Comp_Geom")
    #vsp.PrintResults(result)


    wet_areas = {}
    wet_areas["fuselage"] = vsp.GetDoubleResults(result, "Wet_Area")[0]
    wet_areas["wing"] = vsp.GetDoubleResults(result, "Wet_Area")[1]
    wet_areas["empennage"] = vsp.GetDoubleResults(result, "Wet_Area")[2]
    wet_areas["engines"] = vsp.GetDoubleResults(result, "Wet_Area")[3]
    wet_areas["total"] = vsp.GetDoubleResults(result, "Total_Wet_Area")[0]
    designvars.wing.wetted_area = wet_areas

    vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0))  # Delete slices
    for geom in vsp.FindGeoms():
        vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown"), True)

def cross_section(designvars: DesignParameters = None, spanwise_pos_frac = 0.0, return_xdis = True):
    # points = []

    wingid = "CTELRBUKYF" # designvars.wing.wingid
    yehudi_frac = designvars.wing.yehudi_pos_frac
    if spanwise_pos_frac < yehudi_frac:
        local_chord_length = vsp.GetParmVal(wingid, "Root_Chord", "XSec_1") * (1 - np.abs(spanwise_pos_frac/yehudi_frac)) + vsp.GetParmVal(wingid, "Tip_Chord", "XSec_1") * np.abs(spanwise_pos_frac/yehudi_frac)
    else:
        local_chord_length = vsp.GetParmVal(wingid, "Root_Chord", "XSec_2") * (1 - np.abs((spanwise_pos_frac-yehudi_frac)/(1-yehudi_frac))) + vsp.GetParmVal(wingid, "Tip_Chord", "XSec_2") * np.abs((spanwise_pos_frac-yehudi_frac)/(1-yehudi_frac))


    # for vec in vsp.GetAirfoilCoordinates(designvars.wing.wingid, abs(spanwise_pos_frac)):
    #     points.append(np.array([vec.x(), vec.y()]))

    vsp.UpdateGeom(wingid)
    halfspann = vsp.GetParmVal(wingid, "TotalSpan", "WingGeom")/2
    pos_index = np.argmin(np.abs(designvars.structurecoords[:,1] - spanwise_pos_frac*halfspann))
    if designvars.structurecoords[pos_index, 1] < spanwise_pos_frac*halfspann:
        ycoord = designvars.structurecoords[pos_index, 1]
        uniquelist = np.unique(designvars.structurecoords[:,1])
        pos_index_in_unique = np.where(np.isclose(uniquelist , ycoord))[0]
        try:
            ycoord2 = uniquelist[pos_index_in_unique+1]
        except:
            ycoord2 = ycoord

        indices = np.where(np.isclose(designvars.structurecoords[:, 1], ycoord))[0]
        indices2 = np.where(np.isclose(designvars.structurecoords[:,1] , ycoord2))[0]
        wing_points = designvars.structurecoords[indices][:, [0, 2]]
        wing_points2 = designvars.structurecoords[indices2][:,[0,2]]
        if not np.equal(ycoord, ycoord2):
            interpolation_frac = (spanwise_pos_frac * halfspann - ycoord) / (ycoord2 - ycoord)
            wing_points = (1 - interpolation_frac) * wing_points + interpolation_frac * wing_points2
    else:
        ycoord2 = designvars.structurecoords[pos_index, 1]
        uniquelist = np.unique(designvars.structurecoords[:, 1])
        pos_index_in_unique = np.where(np.isclose(uniquelist, ycoord2))[0]
        try:
            ycoord = uniquelist[pos_index_in_unique - 1]
        except:
            ycoord = ycoord2

        indices = np.where(np.isclose(designvars.structurecoords[:, 1], ycoord))[0]
        indices2 = np.where(np.isclose(designvars.structurecoords[:, 1], ycoord2))[0]
        wing_points = designvars.structurecoords[indices][:, [0, 2]]
        wing_points2 = designvars.structurecoords[indices2][:, [0, 2]]
        if not np.equal(ycoord, ycoord2):
            interpolation_frac = (spanwise_pos_frac * halfspann - ycoord) / (ycoord2 - ycoord)
            wing_points = (1 - interpolation_frac) * wing_points + interpolation_frac * wing_points2



    # points = np.array(points)
    if return_xdis:
        x_displacement =  np.min(wing_points[:,0]) # - np.min(cross_section(designvars, 0.0, return_xdis=False)[0][:,0])  #np.tan(designvars.wing.Lambda_0_w) * spanwise_pos_frac * designvars.wing.b_w/2
    else:
        x_displacement = 0
    local_chord_length = np.max(wing_points[:,0]) - np.min(wing_points[:,0])
    # points[:, 0] *= local_chord_length  # Scale X coordinates by local chord length
    # points[:, 0] += x_displacement
    # points[:, 1] *= local_chord_length

    return wing_points , local_chord_length, x_displacement

def is_headless():
    return os.environ.get("DISPLAY", "") == ""

def fuselage_cross_section(designvars: DesignParameters = None, lengthwise_pos_frac = 0.0):
    if designvars.fuselage.coordinates_have_been_loaded == False:
        vsp.UpdateGeom(designvars.fuselage.fuseid)
        vsp.SetComputationFileName(vsp.DEGEN_GEOM_CSV_TYPE, "data/DegenGeom2.csv")
        vsp.SetSetFlag(designvars.fuselage.fuseid, 9, True)
        vsp.ComputeDegenGeom(9, vsp.DEGEN_GEOM_CSV_TYPE)
        data = pd.read_csv("data/DegenGeom2.csv", header=None, skiprows=10, nrows=357)
        datanp = data.to_numpy()
        designvars.fuselage.fuselage_coords = np.round(datanp, decimals=6)
        designvars.fuselage.coordinates_have_been_loaded = True

    vsp.UpdateGeom(designvars.fuselage.fuseid)
    length = designvars.fuselage.l_f
    pos_index = np.argmin(np.abs(designvars.fuselage.fuselage_coords[:, 0] - lengthwise_pos_frac * length))
    if designvars.fuselage.fuselage_coords[pos_index, 0] < lengthwise_pos_frac * length:
        xcoord = designvars.fuselage.fuselage_coords[pos_index, 0]
        uniquelist = np.unique(designvars.fuselage.fuselage_coords[:, 0])
        pos_index_in_unique = np.where(np.isclose(uniquelist, xcoord))[0]
        try:
            xcoord2 = uniquelist[pos_index_in_unique + 1]
        except:
            xcoord2 = xcoord

        indices = np.where(np.isclose(designvars.fuselage.fuselage_coords[:, 0], xcoord))[0]
        indices2 = np.where(np.isclose(designvars.fuselage.fuselage_coords[:, 0], xcoord2))[0]
        fuselage_points = designvars.fuselage.fuselage_coords[indices][:, [1, 2]]
        fuselage_points2 = designvars.fuselage.fuselage_coords[indices2][:, [1, 2]]
        if not np.equal(xcoord, xcoord2):
            interpolation_frac = (lengthwise_pos_frac * length - xcoord) / (xcoord2 - xcoord)
            fuselage_points = (1 - interpolation_frac) * fuselage_points + interpolation_frac * fuselage_points2
    else:
        xcoord2 = designvars.fuselage.fuselage_coords[pos_index, 0]
        uniquelist = np.unique(designvars.fuselage.fuselage_coords[:, 0])
        pos_index_in_unique = np.where(np.isclose(uniquelist, xcoord2))[0]
        try:
            xcoord = uniquelist[pos_index_in_unique + 1]
        except:
            xcoord = xcoord2

        indices = np.where(np.isclose(designvars.fuselage.fuselage_coords[:, 0], xcoord))[0]
        indices2 = np.where(np.isclose(designvars.fuselage.fuselage_coords[:, 0], xcoord2))[0]
        fuselage_points = designvars.fuselage.fuselage_coords[indices][:, [1, 2]]
        fuselage_points2 = designvars.fuselage.fuselage_coords[indices2][:, [1, 2]]
        if not np.equal(xcoord, xcoord2):
            interpolation_frac = (lengthwise_pos_frac * length - xcoord) / (xcoord2 - xcoord)
            fuselage_points = (1 - interpolation_frac) * fuselage_points + interpolation_frac * fuselage_points2



    import matplotlib.pyplot as plt
    plt.plot(fuselage_points[:, 0], fuselage_points[:, 1], label=f"Fuselage Cross Section at {lengthwise_pos_frac*100:.1f}%")
    plt.show()


    return fuselage_points

def calculate_fuel_capacity(designvars: DesignParameters = None):
    #for both wings together
    fuel_id = vsp.AddGeom("CONFORMAL", designvars.wing.wingid)
    vsp.SetParmVal(fuel_id, "Offset", "Design", designvars.fueltank.dist_from_wingskin)
    vsp.SetParmVal(fuel_id, "UTrimFlag", "Design", 1.0)
    vsp.SetParmVal(fuel_id, "ChordTrimFlag", "Design", 1.0)
    vsp.SetParmVal(fuel_id, "ChordTrimMin", "Design", designvars.fueltank.frac_pos_chord_min)
    vsp.SetParmVal(fuel_id, "ChordTrimMax", "Design", designvars.fueltank.frac_pos_chord_max)
    vsp.SetParmVal(fuel_id, "UMaxTrimTypeFalg", "Design", 2.0)
    vsp.SetParmVal(fuel_id, "UMinTrimTypeFalg", "Design", 2.0)

    vsp.SetParmVal(fuel_id, "EtaTrimMin", "Design", designvars.fueltank.frac_pos_along_span_inboard)
    vsp.SetParmVal(fuel_id, "EtaTrimMax", "Design", designvars.fueltank.frac_pos_along_span_outboard)

    #calculate volume:
    vsp.SetSetFlag(fuel_id, 11, True)
    vsp.SetAnalysisInputDefaults("CompGeom")
    # result = vsp.ExecAnalysis("CompGeom")
    output_mesh = vsp.ComputeCompGeom(11, False, 0)
    result = vsp.FindLatestResultsID("Comp_Geom")

    vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0))  # Delete slices
    for geom in vsp.FindGeoms():
        vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown"), True)

    middle_wing_t_over_c = vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(designvars.wing.wingid, 0), 1), "ThickChord"))
    fuel_tank_thickness = middle_wing_t_over_c * designvars.wing.mac

    designvars.fueltank.fuel_tank_wing_volume = vsp.GetDoubleResults(result, "Total_Theo_Area", 0)[0] * fuel_tank_thickness
