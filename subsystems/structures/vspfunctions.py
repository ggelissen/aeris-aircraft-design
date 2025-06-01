import openvsp as vsp
import numpy as np
from stl import mesh
import pyvista as pv
from design_variables import DesignParameters

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

    # Unique points and triangle faces
    unique_points, idx = np.unique(points, axis=0, return_inverse=True)
    faces = idx.reshape(-1, 3)

    # Convert to pyvista format
    faces_with_size = np.hstack([np.full((faces.shape[0], 1), 3), faces])  # '3' means triangle
    pv_mesh = pv.PolyData(unique_points, faces_with_size)

    # Plot with smooth shading
    pv_mesh.plot(smooth_shading=True, color='lightgray', show_edges=False)


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

def create_wing(designvars: DesignParameters = None):
    wing_id = vsp.AddGeom("WING", "")
    wing_model = vsp.AddFeaStruct(wing_id)
    wingpars = designvars.wing

    # Wing sizing
    vsp.SetParmVal(wing_id, "Span", "XSec_1", wingpars.b_w/2)
    vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", wingpars.root_chord)
    vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", wingpars.tip_chord)
    vsp.SetParmVal(wing_id, "Sweep_Location", "XSec_1", 0.25)
    vsp.SetParmVal(wing_id, "Sweep", "XSec_1", np.rad2deg(wingpars.Lambda_w_quarter))

    # Set root airfoil, parametrised using Class-Shape Transformation (CST) coefficients, which are better for supercritical airfoils
    vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 0, vsp.XS_CST_AIRFOIL)
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "Camber"), wingpars.camber_r) # This is for NACA Four Series, not CST
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "CamberLoc"), wingpars.camber_loc_r) # This is for NACA Four Series, not CST
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "ThickChord"), wingpars.t_c_w_r) # This is for NACA Four Series, not CST
    vsp.SetUpperCST(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), len(wingpars.CST_uppersurf), wingpars.CST_uppersurf)
    vsp.SetLowerCST(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), len(wingpars.CST_lowersurf), wingpars.CST_lowersurf)
    # Scale root airfoil to required thickness to chord ratio
    vsp.WriteSeligAirfoil("data/Airfoil.dat", wing_id, 0) # Write airfoil to file
    vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 0, vsp.XS_FILE_AIRFOIL)
    vsp.ReadFileAirfoil(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "data/Airfoil.dat") # Read airfoil from file
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "ThickChord"), wingpars.t_c_w_r) # After reimiport thickness can be set

    # Set tip airfoil, parametrised using Class-Shape Transformation (CST) coefficients, which are better for supercritical airfoils
    vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 1, vsp.XS_CST_AIRFOIL)
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "Camber"), wingpars.camber_t) # This is for NACA Four Series, not CST
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "CamberLoc"), wingpars.camber_loc_t) # This is for NACA Four Series, not CST
    #vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "ThickChord"), wingpars.t_c_w_t) # This is for NACA Four Series, not CST
    vsp.SetUpperCST(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), len(wingpars.CST_uppersurf), wingpars.CST_uppersurf)
    vsp.SetLowerCST(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), len(wingpars.CST_lowersurf), wingpars.CST_lowersurf)
    # Scale tip airfoil to required thickness to chord ratio
    vsp.WriteSeligAirfoil("data/Airfoil.dat", wing_id, 0)  # Write airfoil to file
    vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 1, vsp.XS_FILE_AIRFOIL)
    vsp.ReadFileAirfoil(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "data/Airfoil.dat")  # Read airfoil from file
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 1), 0), "ThickChord"), wingpars.t_c_w_t)  # After reimiport thickness can be set

    # Position wing on fuselage
    x_pos = wingpars.x_LEMAC - (np.tan(wingpars.Lambda_w_quarter) * wingpars.y_LEMAC - 0.25 * wingpars.mac)
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

    # Add wingribs
    num_wingribs = 10  # in total
    ribs = []
    for i in range(num_wingribs):
        ribs.append(vsp.AddFeaPart(wing_id, wing_model, vsp.FEA_RIB))


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
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 0), "Super_Width"), proppars.engine_diameter)  # Width of the engine pod
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 0), "Super_Height"), proppars.engine_diameter)  # Height of the engine pod
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 0), "Super_MaxWidthLoc"), proppars.nacelle_blend_par)  # Deform the superellipse
    vsp.CutXSec(pod_id, 3)
    vsp.CutXSec(pod_id, 3)
    vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(pod_id, 0), 1), "XDelta"), proppars.engine_length) # Length of the engine pod
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