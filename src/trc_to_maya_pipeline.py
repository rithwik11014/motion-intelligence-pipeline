import maya.cmds as cmds
import sys

DATA_FILE        =
DATA_SAMPLE_RATE = 1000
MAYA_FPS         = 30
SCALE            = 100

with open(DATA_FILE, 'r') as f:
    raw = f.readlines()

hi = next(i for i, l in enumerate(raw) if l.startswith("Sample #"))
headers = raw[hi].rstrip('\n').split('\t')
rows = [l.rstrip('\n').split('\t') for l in raw[hi+1:] if l.strip()]
col_idx = {h: i for i, h in enumerate(headers) if h}


SKIP = {'Sample #', 'Time', 'EMG', 'MOCAP_TRIGGER', 'LED_TRIGGER', ''}
seen, markers = set(), []
for col in headers:
    if col in SKIP: continue
    if col.endswith(('_X','_Y','_Z')):
        name = col[:-2]
        if name not in seen:
            seen.add(name)
            markers.append(name)

safe = lambda n: n.replace('.','_').replace(' ','_')


if cmds.objExists('mocap_grp'):
    cmds.delete('mocap_grp')

grp = cmds.group(empty=True, name='mocap_grp')
loc_map = {}
for name in markers:
    loc = cmds.spaceLocator(name=safe(name))[0]
    cmds.parent(loc, grp)
    loc_map[name] = loc

step = DATA_SAMPLE_RATE / MAYA_FPS
total = int(len(rows) / step)


for f in range(total):
    ri = int(f * step)
    if ri >= len(rows): break
    row = rows[ri]
    t = f + 1
    for name, loc in loc_map.items():
        try:
            x = float(row[col_idx[name+'_X']]) * SCALE
            y = float(row[col_idx[name+'_Y']]) * SCALE
            z = float(row[col_idx[name+'_Z']]) * SCALE
        except:
            x, y, z = 0.0, 0.0, 0.0
        cmds.setKeyframe(loc, at='translateX', v=x, t=t)
        cmds.setKeyframe(loc, at='translateY', v=y, t=t)
        cmds.setKeyframe(loc, at='translateZ', v=z, t=t)
    if f % 100 == 0:
        sys.stdout.write("\r  Frame {}/{}".format(f, total))

cmds.playbackOptions(minTime=1, maxTime=total, animationStartTime=1, animationEndTime=total)





# import maya.cmds as cmds

safe = lambda n: n.replace('.','_').replace(' ','_')

CONNECTIONS = [
    ("L.FootHeel","L.AnkleLateral"), ("L.AnkleLateral","L.KneeLateral"),
    ("L.KneeLateral","L.Thigh"),     ("L.Thigh","LASIS"),
    ("R.FootHeel","R.AnkleLateral"), ("R.AnkleLateral","R.KneeLateral"),
    ("R.KneeLateral","R.Thigh"),     ("R.Thigh","RASIS"),
    ("LASIS","RASIS"),   ("LASIS","LPSIS"),  ("RASIS","RPSIS"),
    ("LASIS","C7"),      ("RASIS","C7"),     ("C7","CLAV"),
    ("C7","Head_Top"),   ("CLAV","LACR"),    ("CLAV","RACR"),
    ("LACR","L.ShoulderFront"),  ("L.ShoulderFront","L.UpparArm"),
    ("L.UpparArm","L.LowerArmLateral"), ("L.LowerArmLateral","L.WristMedial"),
    ("RACR","R.ShoulderFront"),  ("R.ShoulderFront","R.UpparArm"),
    ("R.UpparArm","R.LowerArmLateral"), ("R.LowerArmLateral","R.WristMedial"),
]

if cmds.objExists('skeleton_grp'):
    cmds.delete('skeleton_grp')
skel_grp = cmds.group(empty=True, name='skeleton_grp')

for a, b in CONNECTIONS:
    la, lb = safe(a), safe(b)
    if not cmds.objExists(la) or not cmds.objExists(lb):
        continue
    pa = cmds.xform(la, q=True, ws=True, t=True)
    pb = cmds.xform(lb, q=True, ws=True, t=True)
    crv = cmds.curve(d=1, p=[pa, pb], n='bone_{}_{}'.format(la, lb))
    cl_a = cmds.cluster(crv+'.cv[0]', n='clA_{}_{}'.format(la,lb))[1]
    cl_b = cmds.cluster(crv+'.cv[1]', n='clB_{}_{}'.format(la,lb))[1]
    cmds.pointConstraint(la, cl_a, mo=False)
    cmds.pointConstraint(lb, cl_b, mo=False)
    cmds.setAttr(cl_a+'.visibility', 0)
    cmds.setAttr(cl_b+'.visibility', 0)
    cmds.parent(crv, cl_a, cl_b, skel_grp)
