"""Pico mounting holes in the v1.7 case frame. PROVISIONAL until measured.
Jason, 2026-10-01: wants the Pico's four corner holes as mounting points for a
new part that holds the wires and the signing chip. The PINK board's holes are
not measured yet, so this uses the official Pico 2 W datasheet rows (P4, P7,
P8) centred on the PINK outline, with the Pico centred under the hat (A3
assumption; L8 unmeasured). The stack sits as v1.3 holds it: against the
shortened USB-end wall, 0.02 clear (play to the other wall is reported).
Writes renders/pico-holes/: assembly.step (v1.7 base and lid, hat proxy, Pico
proxy with holes), pico.step, validation.json (hole centres and room around
them), manifest.json. Same frame as renders/v1.7/assembly.step: LCD PCB front
face at z 0, hat corner at x 0, y 0 before the hold shift.
Row PICO-HOLES-PROV in MEASUREMENTS. Run: .venv/bin/python cad/pico_holes.py
"""
import hashlib
import json
import math
from pathlib import Path
from build123d import Pos, Compound, export_step, import_step
import v1_7_lock as L7

M,P,J=L7.M,L7.P,L7.J
ROOT=L7.ROOT
OUT=ROOT/'renders/pico-holes'
HOLE_D=2.1     # P4, ds Pico 2 W; PINK-P20 pending
PITCH_L=47.0   # P7, ds Pico 2 W, hole centres along the length; PINK-P20 pending
PITCH_W=11.4   # P8, ds Pico 2 W, hole centres across the width; PINK-P20 pending

def held():
    """y shift of the stack in the v1.3+ case: against the USB-end wall, 0.02 clear (v1_3_short_end)."""
    return M.IY1-P.L1-.02

def centres(dy=0.):
    """Hole centres (x, y) in the case frame, Pico centred on PICO_CX/CY (A3 assumption)."""
    return [(M.PICO_CX+sx*PITCH_W/2,M.PICO_CY+dy+sy*PITCH_L/2) for sy in (-1,1) for sx in (-1,1)]

def drills(dy=0.):
    return [Pos(x,y,0)*J.cylinder(HOLE_D,M.Z_PICO_BOT-P.TOOL_EXT,M.Z_PICO_TOP+P.TOOL_EXT) for x,y in centres(dy)]

def pico():
    """model.pico with the four holes, at the model datum."""
    p=M.pico()
    for d in drills():p-=d
    return p

def labelled(shape,label):
    shape.label=label
    return shape

def room(solid,x,y,z0,z1,d=HOLE_D):
    """Free height in a column of diameter d at (x, y) from z0 toward z1 before `solid` (z1 if none)."""
    col=Pos(x,y,0)*J.cylinder(d,min(z0,z1),max(z0,z1))
    hit=solid & col
    if hit is None or not hit.solids():return round(abs(z1-z0),3)
    bb=hit.bounding_box()
    return round(bb.min.Z-z0 if z1>z0 else z0-bb.max.Z,3)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    L7.W.shorten()
    lid,_=L7.lid();base,_=L7.base()
    dy=held();shift=Pos(0,dy,0)
    hat=shift*M.hat();pc=shift*pico()
    def vol(s):return sum(x.volume for x in s.solids()) if s is not None else 0.
    pcb_cut=4*math.pi*(HOLE_D/2)**2*P.P3
    checks=dict(
        pico_valid=pc.is_valid,
        holes_cut_only_the_pcb=abs(vol(M.pico())-vol(pico())-pcb_cut)<1e-3,  # clear of the USB shell and button proxy
        holes_inside_outline=PITCH_L/2+HOLE_D/2<P.P1/2 and PITCH_W/2+HOLE_D/2<P.P2/2,
        holes_inside_header_rows=PITCH_W/2+HOLE_D/2<P.P10/2-P.HEADER_W/2,  # clear of the header strips
        pico_clear_of_case=J.overlap(base+lid,pc)<1e-5)
    hat_graze=round(J.overlap(lid,hat),4)  # held stack: the joystick body proxy (J3, a render guess) grazes the lid; reported only
    holes=[]
    for (x,y),name in zip(centres(dy),('button end, left','button end, right','USB end, left','USB end, right')):
        holes.append(dict(name=name,x=round(x,3),y=round(y,3),
            below_to_base=room(base,x,y,M.Z_PICO_BOT,M.Z_BOTTOM-1),   # Pico component face down to the base
            above_to_hat=room(hat+lid,x,y,M.Z_PICO_TOP,0.)))          # Pico header face up to the LCD board
    asm=Compound(children=[labelled(base,'base v1.7'),labelled(lid,'lid v1.7'),labelled(hat,'LCD hat proxy'),
        labelled(pc,'Pico PINK proxy, holes PROVISIONAL')],label='Pico holes, v1.7 case')
    paths=[OUT/'assembly.step',OUT/'pico.step']
    export_step(asm,str(paths[0]));export_step(labelled(shift*pico(),'Pico PINK proxy, holes PROVISIONAL'),str(paths[1]))  # own copy: pc now has a parent
    back=import_step(str(paths[0])).solids()
    checks['assembly_reimports_four_bodies']=len(back)==4
    report=dict(passed=all(checks.values()),checks=checks,provisional=True,
        sources=dict(hole_d='P4 2.1 (ds Pico 2 W)',pitch_length='P7 47.0 (ds)',pitch_width='P8 11.4 (ds)',
            pico_position='centred under the hat (A3 assumption, L8 unmeasured)',
            stack_y=f'held {dy:.2f} (v1.3: against the USB-end wall, 0.02 clear); can slide {dy-M.IY0:.2f} toward the button end'),
        frame='case: LCD PCB front face z 0, +y toward the USB-C/joystick end; mm',
        pico_faces_z=dict(header_face=round(M.Z_PICO_TOP,3),component_face=round(M.Z_PICO_BOT,3)),
        hole_d=HOLE_D,holes=holes,
        notes=['below_to_base: free height under each hole from the Pico component face to the first base material.',
               'above_to_hat: free height above each hole from the Pico header face to the hat proxy or lid.',
               'Replace P4/P7/P8 with PINK caliper rows (PINK-P20) and L8 before designing to these.',
               f'Hat proxy overlaps the lid by {hat_graze} mm3 at the held position: the joystick body proxy, whose height J3 is a render guess. Not the Pico.'])
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    src=[Path(__file__),*(ROOT/'cad'/n for n in ('model.py','params.py','v1_7_lock.py'))]
    (OUT/'manifest.json').write_text(json.dumps(dict(revision='pico-holes (provisional)',
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in src},
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*paths,OUT/'validation.json']}),indent=2)+'\n')
    print(json.dumps(dict(checks=checks,passed=report['passed'],holes=holes),indent=2))
    if not report['passed']:raise SystemExit('Validation failed')

if __name__=='__main__':main()
