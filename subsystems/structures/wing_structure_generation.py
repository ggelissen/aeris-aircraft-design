import numpy as np
from ezdxf.addons.r12writer import dxf_attribs

import openvsp as vsp
import os
from design_variables import *
from vspfunctions import *
import scipy
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay



def wing_structure_generation(designvars: DesignParameters = None):
    """
    Generates the wing structure for the aircraft model using VSP.

    Parameters:
    - designvars: DesignParameters object containing design variables.
    - NCell: Number of cells for the wing structure.
    """


    # Freeze geometry:
    vsp.SetComputationFileName(vsp.DEGEN_GEOM_CSV_TYPE, "data/DegenGeom.csv")
    vsp.SetSetFlag(designvars.wing.wingid, 8, True)
    vsp.ComputeDegenGeom(8, vsp.DEGEN_GEOM_CSV_TYPE)
    print("here")
    data = pd.read_csv("data/DegenGeom.csv", header=None, skiprows=10, nrows=2211)
    datanp = data.to_numpy()
    designvars.structurecoords = datanp

    cross_sectional_structure_along_span(designvars, 0)
    cross_sectional_structure_along_span(designvars, 0.871)
    cross_sectional_structure_along_span(designvars, 0.9)
    cross_sectional_structure_along_span(designvars, 0.95)

    generate_wing_structure_3D(designvars, num_spanwise_points=1001)


def cross_sectional_structure_along_span(designvars: DesignParameters = None, spanwise_position: float = 0.0, plot: bool = True):
    """
    Generates the cross-sectional structure along the span of the wing.

    Parameters:
    - designvars: DesignParameters object containing design variables.
    - NCell: Number of cells for the wing structure.
    - spanwise_position: Position along the span where the cross-section is generated as a fraction of the total span (0.0 to 1.0).
    """
    outline, chord_length, x_displacement = cross_section(designvars, spanwise_position)
    split_index = np.argmin(outline[:, 0])
    upper_airfoil = outline[:split_index]
    lower_airfoil = outline[split_index:]

    spar_points_array = []
    for i in range(designvars.wing.wingsection.num_spars):
        spar_pos = designvars.wing.wingsection.spars[f"Spar{i+1}"]["x_pos_frac"] * chord_length + x_displacement
        y_0 = scipy.interpolate.interp1d(upper_airfoil[:, 0], upper_airfoil[:, 1], kind='linear')(spar_pos)
        y_1 = scipy.interpolate.interp1d(lower_airfoil[:, 0], lower_airfoil[:, 1], kind='linear')(spar_pos)
        spar_points = np.array([[spar_pos, y_0], [spar_pos, y_1]])
        spar_points_array.append(spar_points)
        # t_flange_1 = designvars.wing.wingsection.spars[f"Spar{i+1}"]["t_flange_1_mm"] # in mm
        # t_flange_2 = designvars.wing.wingsection.spars[f"Spar{i+1}"]["t_flange_2_mm"]
        # t_web = designvars.wing.wingsection.spars[f"Spar{i+1}"]["t_web_mm"]
        # t_flange_width = designvars.wing.wingsection.spars[f"Spar{i+1}"]["flange_width_mm"]

    stringer_array = []
    for i in range(designvars.wing.wingsection.num_stringers):
        string_pos = designvars.wing.wingsection.stringers[f"Stringer{i+1}"]["pos_along_airfoil_side"]
        top_or_bottom = designvars.wing.wingsection.stringers[f"Stringer{i+1}"]['top_or_bottom_side']
        string_CS_area = designvars.wing.wingsection.stringers[f"Stringer{i+1}"]['crosssectionalarea_mm2']
        if top_or_bottom == "top":
            string_x = upper_airfoil[np.argmin(np.abs(upper_airfoil[:, 0]-string_pos*chord_length-x_displacement))][0]
            string_y = scipy.interpolate.interp1d(upper_airfoil[:, 0], upper_airfoil[:, 1], kind='linear')(string_x)
        elif top_or_bottom == "bottom":
            string_x = lower_airfoil[np.argmin(np.abs(lower_airfoil[:, 0] - string_pos * chord_length-x_displacement))][0]
            string_y = scipy.interpolate.interp1d(lower_airfoil[:, 0], lower_airfoil[:, 1], kind='linear')(string_x)
        stringer_array.append(np.array([string_x, string_y]))



    # make room for ailerons:
    if spanwise_position*designvars.wing.b_w/2 - designvars.control_surface.x_a_inboard > 0.0 and spanwise_position*designvars.wing.b_w/2 - designvars.control_surface.x_a_outboard < 0.0:
        trailing_edge_position = outline[np.argmax(outline[:, 0])][0]
        cut_out_length_from_trailing_edge = designvars.control_surface.aileron_width
        cut_out_position_x = trailing_edge_position -  cut_out_length_from_trailing_edge
        # Filter out all elements with x positions behind cut_out_position_x
        # wingskin:
        wingskin_removal_array = []
        for indexx, point in enumerate(outline):
            if point[0] > cut_out_position_x:
                wingskin_removal_array.append(indexx)
        outline2 = outline.copy()
        for indexx in reversed(wingskin_removal_array):
            outline2 = np.delete(outline2, indexx, axis=0)
        split_index2 = np.argmin(outline2[:, 0])
        xmax = np.maximum(np.max(outline2[:split_index2], axis=0)[0], np.max(outline2[split_index2:], axis=0)[0])
        lower_airfoil_sticks_out = ( np.max(outline2[:split_index2], axis=0)[0] <  np.max(outline2[split_index2:], axis=0)[0])
        if lower_airfoil_sticks_out:
            y_xmax = np.float64((scipy.interpolate.interp1d(upper_airfoil[:,0], upper_airfoil[:,1], kind='linear')(xmax)))
        else:
            y_xmax = np.float64((scipy.interpolate.interp1d(lower_airfoil[:,0], lower_airfoil[:,1], kind='linear')(xmax)))
        outline2 = np.vstack((outline2, np.array([xmax, y_xmax])))
        outline = outline2.copy()
        split_index3 = np.argmin(outline[:, 0])
        upper_airfoil = outline[:split_index3]
        lower_airfoil = outline[split_index3:]
        # spars:
        spar_removal_array = []
        for i in range(len(spar_points_array)):
            if spar_points_array[i][0, 0] > cut_out_position_x:
                spar_removal_array.append(i)
        for indexx in reversed(spar_removal_array):
            spar_points_array.pop(indexx)
        # stringers:
        stringer_removal_array = []
        for i in range(len(stringer_array)):
            if stringer_array[i][0] > cut_out_position_x:
                stringer_removal_array.append(i)
        for indexx in reversed(stringer_removal_array):
            stringer_array.pop(indexx)

    # make room for flaps:
    for flapgroup in designvars.wing.flapgroups:
        if spanwise_position - flapgroup.spanwise_pos_frac_inbound > 0.0 and spanwise_position - flapgroup.spanwise_pos_frac_outbound < 0.0:
            trailing_edge_position = outline[np.argmax(outline[:, 0])][0]
            cut_out_length_from_trailing_edge = flapgroup.flapwidth
            cut_out_position_x = trailing_edge_position -  cut_out_length_from_trailing_edge
            # Filter out all elements with x positions behind cut_out_position_x
            # wingskin:
            wingskin_removal_array = []
            for indexx, point in enumerate(outline):
                if point[0] > cut_out_position_x:
                    wingskin_removal_array.append(indexx)
            outline2 = outline.copy()
            for indexx in reversed(wingskin_removal_array):
                outline2 = np.delete(outline2, indexx, axis=0)
            split_index2 = np.argmin(outline2[:, 0])
            xmax = np.maximum(np.max(outline2[:split_index2], axis=0)[0], np.max(outline2[split_index2:], axis=0)[0])
            lower_airfoil_sticks_out = ( np.max(outline2[:split_index2], axis=0)[0] <  np.max(outline2[split_index2:], axis=0)[0])
            if lower_airfoil_sticks_out:
                y_xmax = np.float64((scipy.interpolate.interp1d(upper_airfoil[:,0], upper_airfoil[:,1], kind='linear')(xmax)))
            else:
                y_xmax = np.float64((scipy.interpolate.interp1d(lower_airfoil[:,0], lower_airfoil[:,1], kind='linear')(xmax)))
            outline2 = np.vstack((outline2, np.array([xmax, y_xmax])))
            outline = outline2.copy()
            split_index3 = np.argmin(outline[:, 0])
            upper_airfoil = outline[:split_index3]
            lower_airfoil = outline[split_index3:]
            # spars:
            spar_removal_array = []
            for i in range(len(spar_points_array)):
                if spar_points_array[i][0, 0] > cut_out_position_x:
                    spar_removal_array.append(i)
            for indexx in reversed(spar_removal_array):
                spar_points_array.pop(indexx)
            # stringers:
            stringer_removal_array = []
            for i in range(len(stringer_array)):
                if stringer_array[i][0] > cut_out_position_x:
                    stringer_removal_array.append(i)
            for indexx in reversed(stringer_removal_array):
                stringer_array.pop(indexx)


    if plot:
        plt.plot(outline[:, 0], outline[:, 1])
        for stringer in stringer_array:
            plt.scatter(stringer[0], stringer[1], marker='o', color='r')
        for spar in spar_points_array:
            plt.plot(spar[:, 0], spar[:, 1])
        plt.show()
        plt.savefig('data/wing_structure.png', dpi=300, bbox_inches='tight')
    return spar_points_array, stringer_array, outline, chord_length, lower_airfoil, upper_airfoil

def generate_wing_structure_3D(designvars: DesignParameters = None, num_spanwise_points: int = 1001):
    halfspan = designvars.wing.b_w / 2
    plotter = pv.Plotter()


    # Add stringers, spars and ribs
    spars = {}
    for spar_index in range(designvars.wing.wingsection.num_spars):
        spars[f'spar{spar_index+1}'] = {"spar_points": [], "top_flange": [], "bottom_flange": []}
    stringers = {}
    for stringer_index in range(designvars.wing.wingsection.num_stringers):
        stringers[f'stringer{stringer_index+1}'] = {"stringer_points": []}
    wingskin = []
    dx = halfspan/num_spanwise_points
    for x in np.linspace(0, halfspan, num_spanwise_points):
        spar_points_array, stringer_array, _, chord_length, lower_airfoil, upper_airfoil = cross_sectional_structure_along_span(designvars, x / halfspan, plot=False)
        for index, spar_points in enumerate(spar_points_array):
            spars[f'spar{index+1}']['spar_points'].append(np.array([spar_points[0][0], spar_points[0][1], x]))
            spars[f'spar{index+1}']['top_flange'].append(np.array([spar_points[0][0], spar_points[0][1], x]))
            spars[f'spar{index + 1}']['spar_points'].append(np.array([spar_points[1][0], spar_points[1][1], x]))
            spars[f'spar{index+1}']['bottom_flange'].append(np.array([spar_points[1][0], spar_points[1][1], x]))
        for index, stringer in enumerate(stringer_array):
            stringers[f'stringer{index+1}']['stringer_points'].append(np.array([stringer[0], stringer[1], x]))
        if x < halfspan:
            _, _, _, _, lower_airfoil2, upper_airfoil2 = cross_sectional_structure_along_span(designvars, (x + dx) / halfspan, plot=False)
            for ind, point in enumerate(upper_airfoil):
                if ind < len(upper_airfoil)-1 and ind < len(upper_airfoil2)-1:
                    wingskin.append([np.array([point[0], point[1], x]), np.array([upper_airfoil2[ind][0], upper_airfoil2[ind][1], x + dx]),
                                         np.array([upper_airfoil[ind+1][0], upper_airfoil[ind+1][1], x]), np.array([upper_airfoil2[ind+1][0], upper_airfoil2[ind+1][1], x+dx])])
                else:
                    wingskin.append([np.array([upper_airfoil[-1][0], upper_airfoil[-1][1], x]),
                                             np.array([upper_airfoil2[-1][0], upper_airfoil2[-1][1], x + dx]),
                                             np.array([lower_airfoil[-1][0], lower_airfoil[-1][1], x]),
                                             np.array([lower_airfoil2[-1][0], lower_airfoil2[-1][1], x + dx])])
            for ind, point in enumerate(lower_airfoil):
                if ind < len(lower_airfoil)-1 and ind < len(lower_airfoil2)-1:
                    wingskin.append([np.array([point[0], point[1], x]),
                                             np.array([lower_airfoil2[ind][0], lower_airfoil2[ind][1], x + dx]),
                                             np.array([lower_airfoil[ind + 1][0], lower_airfoil[ind + 1][1], x]),
                                             np.array([lower_airfoil2[ind + 1][0], lower_airfoil2[ind + 1][1], x + dx])])
            wingskin.append([np.array([upper_airfoil[0][0], upper_airfoil[0][1], x]),
                             np.array([upper_airfoil2[0][0], upper_airfoil2[0][1], x + dx]),
                             np.array([lower_airfoil[0][0], lower_airfoil[0][1], x]),
                             np.array([lower_airfoil2[0][0], lower_airfoil2[0][1], x + dx])])



    # Draw spars
    for spar_index in range(designvars.wing.wingsection.num_spars):

        topflange = spars[f'spar{spar_index + 1}']['top_flange']
        bottomflange = spars[f'spar{spar_index + 1}']['bottom_flange']
        quad_faces = []
        for indexx, point in enumerate(topflange):
            if not indexx == len(topflange) - 1:
                new_vertex = [
                    [point[0], point[1], point[2]],  # x, y, z coordinates
                    [topflange[indexx+1][0], topflange[indexx+1][1], topflange[indexx+1][2]],
                    [bottomflange[indexx+1][0], bottomflange[indexx+1][1], bottomflange[indexx+1][2]],
                    [bottomflange[indexx][0], bottomflange[indexx][1], bottomflange[indexx][2]]
                ]
                quad_faces.append(new_vertex)
        vertex_list = []
        index_map = {}
        faces = []

        for quad in quad_faces:
            face_indices = []
            for pt in quad:
                key = tuple(pt)
                if key not in index_map:
                    index_map[key] = len(vertex_list)
                    vertex_list.append(pt)
                face_indices.append(index_map[key])
            faces.append([4] + face_indices)




        vertices = np.array(vertex_list)
        faces = np.hstack(faces)
        mesh = pv.PolyData(vertices, faces)
        plotter.add_mesh(mesh, show_edges=False, color="lightblue", opacity=0.5)

        #spar_flanges
        spars[f'spar{spar_index+1}']['top_flange'] = np.array(spars[f'spar{spar_index+1}']['top_flange'])
        spars[f'spar{spar_index+1}']['bottom_flange'] = np.array(spars[f'spar{spar_index+1}']['bottom_flange'])
        lines = np.hstack([[len(spars[f'spar{spar_index+1}']['top_flange'])] + list(range(len(spars[f'spar{spar_index+1}']['top_flange'])))])
        lines_2= np.hstack([[len(spars[f'spar{spar_index+1}']['bottom_flange'])] + list(range(len(spars[f'spar{spar_index+1}']['bottom_flange'])))])
        curve = pv.PolyData(spars[f'spar{spar_index+1}']['top_flange'])
        curve.lines = lines
        curve2 = pv.PolyData(spars[f'spar{spar_index + 1}']['bottom_flange'])
        curve2.lines = lines_2
        plotter.add_mesh(curve, color='blue', line_width=3, opacity=0.2)
        plotter.add_mesh(curve2, color='blue', line_width=3, opacity=0.2)

    # Draw stringers
    for stringer_index in range(designvars.wing.wingsection.num_stringers):
        stringer_points = np.array(stringers[f'stringer{stringer_index + 1}']['stringer_points'])
        lines = np.hstack([[len(stringer_points)] + list(range(len(stringer_points)))])
        curve = pv.PolyData(stringer_points)
        curve.lines = lines
        plotter.add_mesh(curve, color='red', line_width=0.5, opacity=0.2)

    # Draw wingskin
    vertex_list_wingskin = []
    index_map_wingskin = {}
    faces_wingskin = []
    for quad in wingskin:
        face_indices = []
        for pt in quad:
            key = tuple(pt)
            if key not in index_map_wingskin:
                index_map_wingskin[key] = len(vertex_list_wingskin)
                vertex_list_wingskin.append(pt)
            face_indices.append(index_map_wingskin[key])
        faces_wingskin.append([4] + face_indices)
    vertices_wingskin = np.array(vertex_list_wingskin)
    faces_wingskin = np.hstack(faces_wingskin)
    mesh_wingskin = pv.PolyData(vertices_wingskin, faces_wingskin)
    plotter.add_mesh(mesh_wingskin, show_edges=False, color="grey", opacity=0.1)

    # Draw ribs
    for rib in range(len(designvars.wing.wingribs.ribs)):
        spanwise_pos = designvars.wing.wingribs.ribs[f"Rib{rib+1}"]["x_pos_frac"]
        _, _, outline, chord_length, _, _  = cross_sectional_structure_along_span(designvars, spanwise_pos, plot=False)
        tri = Delaunay(outline)
        faces = tri.simplices
        faces_pv = np.hstack([[3, *face] for face in faces])
        # Create 3D PolyData
        rib_points = [np.array([outlinepoint[0], outlinepoint[1], spanwise_pos * halfspan]) for outlinepoint in outline]
        rib_points = np.array(rib_points)
        rib_mesh = pv.PolyData(rib_points, faces_pv)

        plotter.add_mesh(rib_mesh, color='skyblue', show_edges=False)
    # Draw fuselage
    vsp.SetSetFlag(designvars.fuselage.fuseid, 6, True)
    vsp.ExportFile('data/fuselage.stl', 6 , vsp.EXPORT_STL)
    vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0))  # Delete NewGeom which gets added after an export
    for geom in vsp.FindGeoms():
        vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown"), True)
    fuselage_mesh = pv.read('data/fuselage.stl')
    fuselage_mesh.translate([-designvars.wing.xpos, 0, 0], inplace=True)
    plotter.add_mesh(fuselage_mesh, color='brown', show_edges=False, opacity=0.2)



    plotter.show()

