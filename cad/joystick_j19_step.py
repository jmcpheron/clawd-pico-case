"""J19 as STEP, for editing in Onshape (or any B-rep CAD). No new geometry.
Each cap is joystick_j18.cap at the J19 depths, flange down at the origin,
the same frame as the J19 STLs. fit.step puts all five caps (one body each,
same spot; hide all but one) in the v1.7 lid at the ride height j10_tilt
uses, with the hat proxy. The proxy's stick is moved to the lid's hole centre
(the hole was moved to the real stem by fit, L3/L4/V1-JOY). That ride height
assumes the stick tip seats on the roof, which J18/J19-TILT doubt.
STEP is derived output: edits come back as numbers in a new J script.
Rows J19-* in MEASUREMENTS. Run: .venv/bin/python cad/joystick_j19_step.py
"""
import hashlib
import json
from pathlib import Path
from build123d import Pos, Compound, export_step, import_step
import joystick_j18 as J18
import joystick_j19 as J19
import j10_tilt as TILT

ROOT=J18.ROOT
J,J16,P=J18.J,J18.J16,J18.J.P
M,L1,L4,V,L7=TILT.M,TILT.L1,TILT.V.L4,TILT.V,TILT.L7
STL=ROOT/'stl/v1.4/joystick-j19'
OUT=ROOT/'renders/v1.4/joystick-j19'
TOL=1e-4  # re-import must match the in-memory solid to this (mm, mm^3)

def labelled(shape,label):
    shape.label=label
    return shape

def fit(caps):
    """v1.7 lid, hat proxy and caps in assembled position, as j10_tilt places them."""
    L7.W.shorten()
    lid,_=L7.lid()
    hx,hy=M.JOY_C[0]+L4.DX,M.JOY_C[1]+L4.DY+V.JOY_DY
    jx,jy=M.JOY_C;h=P.J4/2
    stick=M.box(jx-h,jx+h,jy-h,jy+h,P.J3,P.J6)  # model.hat's stick, at the original JOY_C
    hat=M.hat()-stick+Pos(hx-jx,hy-jy,0)*stick
    parts=[labelled(lid,'lid v1.7'),labelled(hat,'hat proxy, stick at lid hole')]
    for name,(c,lift) in caps.items():
        dz=L1.LIP_TOP+lift-J.BOTTOM-J.FLANGE_T
        parts.append(labelled(Pos(hx,hy,dz)*c,name))
    return Compound(children=parts,label='J19 fit, v1.7 lid')

def same(a,b):
    ba,bb=a.bounding_box(),b.bounding_box()
    return abs(a.volume-b.volume)<TOL and all(abs(x-y)<TOL for x,y in zip((*ba.min,*ba.max),(*bb.min,*bb.max)))

def main():
    checks={};caps={};outputs=[]
    for i,depth in enumerate(J19.DEPTHS):
        n=i+1;c=J18.cap(depth,n);name=f'J19-{n} depth {depth}'
        printed=labelled(Pos(0,0,-J.BOTTOM)*c,name)  # as the STL
        path=STL/f'joystick-j19-{n}.step';export_step(printed,str(path));outputs.append(path)
        back=import_step(str(path)).solids()
        checks[f'{n}_reimports_as_one_solid']=len(back)==1 and back[0].is_valid
        checks[f'{n}_reimport_matches_model']=len(back)==1 and same(back[0],printed)
        caps[name]=(c,J16.LIFT+J18.J16_DEPTH-depth)
    path=OUT/'fit.step';asm=fit(caps);export_step(asm,str(path));outputs.append(path)
    back=import_step(str(path)).solids()
    checks['fit_reimports_all_bodies']=len(back)==len(asm.children)
    report=dict(revision='J19-STEP',passed=all(checks.values()),checks=checks,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (Path(__file__),*(ROOT/'cad'/n for n in ('joystick_j19.py','joystick_j18.py','joystick_j17.py','j10_tilt.py')))},
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs})
    (OUT/'step-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(checks=checks,passed=report['passed']),indent=2))
    if not report['passed']:raise SystemExit('Validation failed')

if __name__=='__main__':main()
