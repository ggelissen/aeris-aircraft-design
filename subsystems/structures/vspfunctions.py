import openvsp as vsp

def print_all_params(obj_id):
    parm_ids = vsp.GetGeomParmIDs(obj_id)
    for pid in parm_ids:
        pname = vsp.GetParmName(pid)
        group = vsp.GetParmGroupName(pid)
        val = vsp.GetParmVal(pid)
        print(f" Group: {group} / Parameter Name: {pname} / Value: {val}")