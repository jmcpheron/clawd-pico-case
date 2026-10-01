"""V1.8: the v1.7 base with two cable slots in the non-USB end wall, for the
pigtail of an external I2C signing chip held by the I2C spacer
(cad/i2c_spacer.py). Jason, 2026-10-01. Slots sit wholly below the seam, in
line with the spacer's clips, 1.57 clear of the end catch on each side: no
catch, rib or lid change, so the v1.7 lid is reused unchanged.
Assembly and viewer show the stack held as v1.3 (pico_holes.held()), the J22
joystick (current), the S2 buttons, the spacer and a 4-wire proxy.
Rows V1.8-* and SP-* in MEASUREMENTS. Run: .venv/bin/python cad/v1_8_cable_slot.py
"""
import base64
import hashlib
import json
import tempfile
from pathlib import Path
from build123d import Pos, Compound, export_step, import_step
import i2c_spacer as SP
import pico_holes as H
import joystick_j16 as J16
import joystick_j18 as J18
import joystick_j22 as J22

L7=SP.L7
R,W,V,T,S,M,P,J,L1,T5=L7.R,L7.W,L7.V,L7.T,L7.S,L7.M,L7.P,L7.J,L7.L1,L7.T5
ROOT=L7.ROOT
REV='v1.8'
OUT=ROOT/'renders'/REV
STL=ROOT/'stl'/REV
SLOT_W=2*SP.WIRE+2*P.CAP_HOLE_CLEAR  # V1.8-SLOT: 2.5
SLOT_H=SP.WIRE+2*P.CAP_HOLE_CLEAR    # V1.8-SLOT: 1.5
COLORS={**{n:c for n,(f,c) in V.V.PARTS.items()},'i2c_spacer':'#3a9d5d','wires':'#cc3333'}

def slot_z():
    z0=SP.face()-P.CAP_HOLE_CLEAR  # V1.8-SLOT: from 0.25 below the Pico face
    return z0,z0+SLOT_H

def slots():
    z0,z1=slot_z();out=None
    for c in SP.clip_x():
        s=M.box(c-SLOT_W/2,c+SLOT_W/2,S.Y0-P.TOOL_EXT,M.IY0+.5,z0,z1)
        out=s if out is None else out+s
    return out

def base():
    b17,_=L7.base()
    return b17-slots(),b17

def joystick():
    """J22 at the lid's joystick hole, ride height as j10_tilt places caps."""
    hx,hy=M.JOY_C[0]+V.L4.DX,M.JOY_C[1]+V.L4.DY+V.JOY_DY
    lift=J16.LIFT+J18.J16_DEPTH-J22.DEPTH
    return Pos(hx,hy,L1.LIP_TOP+lift-J.BOTTOM-J.FLANGE_T)*J22.cap()

def main():
    OUT.mkdir(parents=True,exist_ok=True);STL.mkdir(parents=True,exist_ok=True)
    W.shorten()
    b,b17=base();l,_=L7.lid();dy=H.held()
    hat=Pos(0,dy,0)*M.hat();pc=Pos(0,dy,0)*H.pico()
    sp=SP.spacer(dy);wr=SP.wires(dy,S.Y0-5)
    cat=L7.catches();cut=slots()
    def vol(s):return sum(x.volume for x in s.solids()) if s is not None else 0.
    def diff(a,c):return a-c if a.solids() else a
    z0,z1=slot_z();catch=(M.CX-S.SNAP_W/2,M.CX+S.SNAP_W/2)
    checks={}
    def check(n,ok):checks[n]=bool(ok)
    check('base_valid_single_solid',b.is_valid and len(b.solids())==1)
    check('base_changed_only_at_slots',vol(diff(b17-b,cut))<1e-4 and vol(diff(b-b17,cut))<1e-6)
    check('slots_through_wall',all(vol(b & M.box(c-.5,c+.5,S.Y0+.2,M.IY0-.2,(z0+z1)/2-.3,(z0+z1)/2+.3))<1e-6 for c in SP.clip_x()))
    check('slot_roof_0_6_below_seam',S.SEAM-z1>=.6-1e-9)
    check('slots_1_5_clear_of_end_catch',min(min(abs(c-SLOT_W/2-catch[1]),abs(catch[0]-(c+SLOT_W/2))) for c in SP.clip_x())>=1.5)
    check('every_wire_inside_a_slot',all(any(abs(x-c)+SP.WIRE/2<=SLOT_W/2 for c in SP.clip_x()) for x in SP.wire_x()) and z0<SP.face() and z1>SP.face()+SP.WIRE)
    check('catches_unchanged',vol(diff(cat-b,cut))<1e-6)
    check('closed_contact_only_at_ribs',J.overlap(b,l-R.ribs())<1e-5)
    check('catches_seated_clear',J.overlap(cat,l)<1e-5)
    check('hardware_clear_of_base',J.overlap(b,hat+pc)<1e-5)
    check('spacer_clear_of_case',J.overlap(sp,b+l)<1e-6)
    check('wires_pass_slots',J.overlap(wr,b+l)<1e-6 and wr.bounding_box().min.Y<S.Y0)
    check('wires_clear_of_spacer',J.overlap(wr,sp)<1e-6)
    report=dict(revision=REV,checks=checks,passed=all(checks.values()),physical_fit_confirmed=False,provisional=True,
        slot_mm=dict(width=SLOT_W,height=SLOT_H,z=[round(z0,3),round(z1,3)],x=[[round(c-SLOT_W/2,3),round(c+SLOT_W/2,3)] for c in SP.clip_x()],
            roof_below_seam=round(S.SEAM-z1,3),clear_of_end_catch=round(min(catch[0]-(SP.clip_x()[0]+SLOT_W/2),SP.clip_x()[1]-SLOT_W/2-catch[1]),3)),
        pairs_with='v1.7 lid (unchanged)',
        notes=['Base only, below the seam: catches, ribs and lid unchanged (checked).','Thread the pigtail\'s bare end in through a slot, 2 wires per slot.',
               'Slot roof prints as a 2.5 mm bridge, floor down.','Spacer pegs and hole positions are provisional (PICO-HOLES-PROV).'])
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
    if not report['passed']:raise SystemExit('Validation failed')
    J.export(V.origin(b),STL/'base-floor-down.stl')
    view=dict(hat=hat,pico=pc,base=b,lid=l,button_caps=T.buttons(),joystick_cap=joystick(),i2c_spacer=sp,wires=wr)
    labels=dict(hat='LCD hat proxy',pico='Pico PINK proxy, holes PROVISIONAL',base='base v1.8',lid='lid v1.7',button_caps='button caps S2',
        joystick_cap='joystick J22',i2c_spacer='I2C spacer (provisional)',wires='pigtail wires (1.0 envelope proxy)')
    for n,s in view.items():s.label=labels[n]
    asm=Compound(children=list(view.values()),label='v1.8 cable slots + I2C spacer')
    export_step(asm,str(OUT/'assembly.step'))
    text=(OUT/'assembly.step').read_text()  # the importer rewrites labels, so check the file's own PRODUCT names
    if len(import_step(str(OUT/'assembly.step')).children)!=len(view) or not all(f"PRODUCT('{n}'" in text for n in labels.values()):
        raise SystemExit('STEP re-import: bodies or labels missing')
    packed=[]
    with tempfile.TemporaryDirectory() as tmp:
        for name,s in view.items():
            path=Path(tmp)/(name+'.stl');J.export(s,path);bb=s.bounding_box()
            packed.append(dict(name=name,color=COLORS[name],stl=base64.b64encode(path.read_bytes()).decode(),bbox=[*tuple(bb.min),*tuple(bb.max)]))
    info=dict(commit=REV+' cable slots + I2C spacer',case_mm=[round(S.X1-S.X0,2),round(S.Y1-S.Y0,2),round(S.TOP+T5.RAISE-M.Z_BOTTOM,2)],split_z=S.SEAM,
        assumptions=['Two 2.5 x 1.5 slots in the non-USB end, below the seam; v1.7 lid unchanged.','I2C spacer pegs in the Pico holes (provisional datasheet positions).',
                     'Wires are a 1.0 mm envelope proxy, not the real cable.','Stack held as v1.3; J22 joystick.'])
    html=((ROOT/'cad/viewer_template.html').read_text().replace('/*__PARTS__*/','const PARTS = '+json.dumps(packed)+';').replace('/*__INFO__*/','const INFO = '+json.dumps(info)+';')
        .replace('V3 review · NOT APPROVED FOR PRINT','V1.8 · CABLE SLOTS + I2C SPACER').replace('V3 Case Review — Not Approved for Print','V1.8 cable slots + I2C spacer')
        .replace('joystick_cap:1.1};','joystick_cap:1.1,i2c_spacer:-0.15,wires:-0.15};'))
    (OUT/'viewer.html').write_text(html);(ROOT/'renders/viewer.html').write_text(html)
    sources=[Path(__file__),*[ROOT/'cad'/n for n in ('i2c_spacer.py','pico_holes.py','v1_7_lock.py','joystick_j22.py','model.py','params.py')]]
    outputs=[STL/'base-floor-down.stl',OUT/'assembly.step',OUT/'validation.json',OUT/'viewer.html']
    (OUT/'manifest.json').write_text(json.dumps(dict(revision=REV,supports=False,raft=False,slice_verified=False,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}),indent=2)+'\n')

if __name__=='__main__':main()
