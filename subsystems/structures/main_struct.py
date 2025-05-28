## Requirments:
# python=3.11
# numpy!=1.19.4

# Before running, make sure to run:
# pip install -r requirements.txt

from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits import mplot3d
import matplotlib
import pyvista as pv
import numpy as np

from vspfunctions import print_all_params

matplotlib.use('Qt5Agg')
import openvsp as vsp
import vspfunctions

# Step 1: Loading analysis
import loading

# Step 2 Import geometric variables from Class I/II methods
# span =
# root_chord =
# tip_chord =
# sweep =

# Step 3: Create a VSP model using the imported geometric variables
vsp.ClearVSPModel()

#### Add fuselage and change fuselage shape to make room for payload. This is done by changing the cross-sections of the fuselage.
fuse_id = vsp.AddGeom("FUSELAGE", "")
vsp.SetParmVal(fuse_id, "Length", "Design", 15.0)

# Tip of the fuselage
vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), 0), vsp.XSEC_BOTH_SIDES, 21.32, 45, 21.32, 45)

# Fuselage cross section 1
vsp.ChangeXSecShape(vsp.GetXSecSurf(fuse_id, 0), 1, vsp.XS_ROUNDED_RECTANGLE)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),1), "RoundedRect_Width"), 2.24490)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),1), "RoundedRect_Height"), 1.85714)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),1), "RoundRect_Keystone"), 0.57143)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),1), "RoundedRect_RadiusSymmetryType"), 1.0)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),1), "RoundRectXSec_Radius"), 0.71812)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),1), "RoundRectXSec_RadiusBR"), 0.18898)
vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), 1), vsp.XSEC_BOTH_SIDES, 7.11, 0, 7.11, 0)

# Fuselage cross section 2
vsp.ChangeXSecShape(vsp.GetXSecSurf(fuse_id, 0), 2, vsp.XS_ROUNDED_RECTANGLE)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),2), "RoundedRect_Width"), 2.50000)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),2), "RoundedRect_Height"), 2.17551)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),2), "RoundRect_Keystone"), 0.58929)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),2), "RoundedRect_RadiusSymmetryType"), 3.0)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),2), "RoundRectXSec_Radius"), 0.76500)
vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), 2), vsp.XSEC_BOTH_SIDES, 0, 0, 0, 0)

# Fuselage cross section 3
vsp.ChangeXSecShape(vsp.GetXSecSurf(fuse_id, 0), 3, vsp.XS_ROUNDED_RECTANGLE)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),3), "RoundedRect_Width"), 2.50000)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),3), "RoundedRect_Height"), 1.96327)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),3), "RoundRect_Keystone"), 0.60357)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),3), "RoundedRect_RadiusSymmetryType"), 3.0)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0),3), "RoundRectXSec_Radius"), 0.76500)
vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), 3), vsp.XSEC_BOTH_SIDES, 0, 0, 0, 0)

# Fuselage end tip
vsp.SetXSecTanAngles(vsp.GetXSec(vsp.GetXSecSurf(fuse_id, 0), 4), vsp.XSEC_BOTH_SIDES, -26.05, -45, -26.05, -45)



### Add wing
wing_id = vsp.AddGeom("WING", "")
wing_model = vsp.AddFeaStruct(wing_id)

# Wing sizing
vsp.SetParmVal(wing_id, "Span", "XSec_1", 10.0)
vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", 3.0)
vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", 1.5)
vsp.SetParmVal(wing_id, "Sweep", "XSec_1", 30.0)

# Set airfoil (both at root and tip)
vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 0, vsp.XS_FOUR_SERIES)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "Camber"), 0.02)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "CamberLoc"), 0.4)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 0), "ThickChord"), 0.12)
vsp.ChangeXSecShape(vsp.GetXSecSurf(wing_id, 0), 1, vsp.XS_FOUR_SERIES)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "Camber"), 0.02)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "CamberLoc"), 0.4)
vsp.SetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(wing_id, 0), 1), "ThickChord"), 0.12)

# Position wing on fuselage
vsp.SetParmVal(wing_id, "X_Rel_Location", "XForm", 5.0)
vsp.SetParmVal(wing_id, "Z_Rel_Location", "XForm", 0)

# Add wingribs
num_wingribs = 10 # in total
ribs = []
for i in range(num_wingribs):
    ribs.append(vsp.AddFeaPart(wing_id, wing_model, vsp.FEA_RIB))



### Add v_tail
hstab_id = vsp.AddGeom("WING")
vsp.SetGeomName(hstab_id, "Horizontal_Stabilizer")

# Position it at the tail (move along X and Z)
vsp.SetParmVal(hstab_id, "X_Rel_Location", "XForm", 10.0)  # Tail of the fuselage
vsp.SetParmVal(hstab_id, "Z_Rel_Location", "XForm", 0.5)   # Slight vertical offset

# Set orientation (v-tail, so dihedral = 40)
vsp.SetParmVal(hstab_id, "Dihedral", "XSec_1", 40.0)

# Symmetry around XZ plane (so it spans both sides)
vsp.SetParmVal(hstab_id, "Sym_Planar_Flag", "Sym", vsp.SYM_XZ)

# Size V-Tail
vsp.SetParmVal(hstab_id, "Span", "XSec_1", 5.0)
vsp.SetParmVal(hstab_id, "Tip_Chord", "XSec_1", 1.0)
vsp.SetParmVal(hstab_id, "Root_Chord", "XSec_0", 1.5)



### Add engines
pod_id = vsp.AddGeom("POD")
#print_all_params(pod_id)  # Print all parameters for the engine pod
vsp.SetGeomName(pod_id, "Fuselage_Engine")
vsp.SetParmVal(pod_id, "Length", "Design", 4.0)     # Length of the engine pod
vsp.SetParmVal(pod_id, "FineRatio", "Design", 6)     # Radius to Length ratio
vsp.SetParmVal(pod_id, "X_Rel_Location", "XForm", 8.50)   # Longitudinal position
vsp.SetParmVal(pod_id, "Y_Rel_Location", "XForm", 0.0)    # Side offset (0 = centerline)
vsp.SetParmVal(pod_id, "Z_Rel_Location", "XForm", 1.5)   # Vertical offset (on top of fuselage)




# Step 4: Simulate aircraft with loads

# Step 5: Change Structural variables to optimise for mass

# Step 6: Save progress and share optimised variables to other subsystems. Share aircraft 3D model to aerodynamics.

vsp.Update()

# Save as VSP3 file
vsp.WriteVSPFile("aircraft_model.vsp3")

# Export to STL or other formats
vsp.ExportFile("aircraft_model.stl", vsp.SET_ALL, vsp.EXPORT_STL)

# PLOTTING
# Load the STL file
# Load STL
your_mesh = mesh.Mesh.from_file('aircraft_model.stl')
points = your_mesh.vectors.reshape(-1, 3)

# Unique points and triangle faces
unique_points, idx = np.unique(points, axis=0, return_inverse=True)
faces = idx.reshape(-1, 3)

# Convert to pyvista format
faces_with_size = np.hstack([np.full((faces.shape[0], 1), 3), faces])  # '3' means triangle
pv_mesh = pv.PolyData(unique_points, faces_with_size)

# Plot with smooth shading
pv_mesh.plot(smooth_shading=True, color='lightgray', show_edges=False)