"""J20-JM: J19-1 with a looser square grip, 2.00 / 2.05 / 2.10 / 2.15 / 2.20.
Made in Jason's fork as "J20"; renamed because Austin's J20 is a different cap.
Jason, 2026-09-30, on his printer: the J19 plate (1.90 grip) will not start
over the stick in any rotation; his caliper reads the stick 1.8 across the
flats (J4: 1.86). So his printer prints the 1.90 hole under 1.8, and the step
starts above Austin's loosest tested grip (J14-3, 1.95). Only the grip
changes: depth 1.6 (J19-1), J17-B tabs, J16 mouth chamfer, dice dots 1-5.
Same depth and outside as J19-1, so the ride height and lid room are J19-1's.
Rows J20JM-* in MEASUREMENTS. Run: .venv/bin/python cad/joystick_j20jm.py
"""
import hashlib
import itertools
import json
from pathlib import Path
from build123d import Pos, Compound, export_step, import_step
import joystick_test as J
import joystick_j4 as J4
import joystick_j7 as J7
import joystick_j8 as J8
import joystick_j14 as J14
import joystick_j15 as J15
import joystick_j16 as J16
import joystick_j17 as J17
import joystick_j18 as J18
import joystick_j19_step as J19S

ROOT=J.ROOT
STL=ROOT/'stl/v1.4/joystick-j20jm'
OUT=ROOT/'renders/v1.4/joystick-j20jm'
SQUARES=[2.00,2.05,2.10,2.15,2.20]  # J20JM-GRIP, dots 1..5
DEPTH=1.6  # J20JM-KEEP: J19-1
TAB_SCALE=J18.TAB_SCALE  # J20JM-KEEP: J17-B
STEM=1.86  # J4, cal; Jason's caliper 1.8 (J4-JM)

def cavity(square,depth):
    """J17's square-only socket with grip `square`; roof at `depth` above the bed face."""
    roof=J.BOTTOM+depth;h=square/2;ch=J16.MOUTH_CH
    return (J.M.box(-h,h,-h,h,J.BOTTOM-J.P.TOOL_EXT,roof)+J7.frustum(square,0,roof,roof+square/2)
            +J7.frustum(square+2*ch,square,J.BOTTOM,J.BOTTOM+ch)
            +J.M.box(-h-ch,h+ch,-h-ch,h+ch,J.BOTTOM-J.P.TOOL_EXT,J.BOTTOM+J.P.EPS))

def cap(square,depth,n):
    """J17.cap with the grip as a parameter."""
    w,tip=J17.tab(TAB_SCALE)
    c=J15.cap()+(J8.cavity(J16.SQUARE,J16.LIFT) & J.cylinder(J.NECK,J.BOTTOM,J4.FLAT_Z))  # J15 with its socket filled
    fl=None
    for f in J16.flares(w,tip):fl=f if fl is None else fl+f
    c=c+(fl-J16.thin(J16.FLARE_T))-cavity(square,depth)
    for p in J17.pips(n):c-=p
    return c

def main():
    STL.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    def vol(s):return sum(x.volume for x in s.solids()) if s is not None else 0.
    checks={};parts={};caps={};outputs=[]
    j19=J18.cap(DEPTH,1)
    checks['J19_1_reproduced_at_1.90']=vol(cap(J16.SQUARE,DEPTH,1)-j19)<1e-6 and vol(j19-cap(J16.SQUARE,DEPTH,1))<1e-6
    roof=J.BOTTOM+DEPTH;ch=J16.MOUTH_CH
    for i,sq in enumerate(SQUARES):
        n=str(i+1);c=cap(sq,DEPTH,i+1);h=sq/2
        checks[n+'_valid_single_solid']=c.is_valid and len(c.solids())==1
        checks[n+'_no_flat_overhang_in_socket']=not J7.overhangs(c)
        checks[n+'_grip_is_'+f'{sq:.2f}']=vol(c & J.M.box(-h,h,-h,h,J.BOTTOM,roof-.01))<1e-6 and vol(c & J.M.box(h+.01,h+.1,-.1,.1,J.BOTTOM+ch+.05,roof-.05))>0
        checks[n+'_depth_is_'+str(DEPTH)]=vol(c & J.M.box(-.05,.05,-.05,.05,roof+h+.05,roof+h+.15))>0
        checks[n+'_wider_than_stem']=sq>STEM
        checks[n+'_lip_stop_kept']=sq+2*ch<2.94  # J4b
        checks[n+'_pips_inside_flat_top']=J17.PIP_STEP*2**.5+J17.PIP_D/2<2.5
        label=f'J20JM-{n} grip {sq:.2f}'
        parts[n]=J19S.labelled(Pos(0,0,-J.BOTTOM)*c,label)
        caps[label]=(c,J16.LIFT+J18.J16_DEPTH-DEPTH)
        path=STL/f'joystick-j20jm-{n}.stl';J.export(parts[n],path);outputs.append(path)
        path=STL/f'joystick-j20jm-{n}.step';export_step(parts[n],str(path));outputs.append(path)
        back=import_step(str(path)).solids()
        checks[n+'_step_matches_model']=len(back)==1 and J19S.same(back[0],parts[n])
    step=2*J17.tab(TAB_SCALE)[1]+J14.GAP
    placed=[Pos((i%3)*step,(i//3)*step,0)*p for i,p in enumerate(parts.values())]  # 3 x 2
    checks['plate_separate']=all(J.overlap(a,x)<1e-6 for a,x in itertools.combinations(placed,2))
    path=STL/'joystick-j20jm-plate.stl';J.export(Compound(children=placed),path);outputs.append(path)
    asm=J19S.fit(caps);asm.label='J20-JM fit, v1.7 lid'
    lid,hat,*placed_caps=asm.children
    for c in placed_caps:checks[c.label+'_clear_of_lid_and_stick_at_rest']=J.overlap(c,lid)<1e-6 and J.overlap(c,hat)<1e-6
    path=OUT/'fit.step';export_step(asm,str(path));outputs.append(path)
    report=dict(checks=checks,passed=all(checks.values()),grips={str(i+1):s for i,s in enumerate(SQUARES)},depth=DEPTH,tab_scale=TAB_SCALE,
        notes=['Only the grip changes from J19-1; ride height and lid room are J19-1s (model, if the stick tip seats on the roof).',
               'Dice dots 1-5 as J19: keep the sets apart.'])
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    src=[Path(__file__),*(ROOT/'cad'/n for n in ('joystick_j19_step.py','joystick_j18.py','joystick_j17.py','joystick_j16.py','joystick_j15.py','joystick_test.py'))]
    (OUT/'manifest.json').write_text(json.dumps(dict(revision='J20-JM',source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in src},
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(outputs)}),indent=2)+'\n')
    print(json.dumps(dict(checks=checks,passed=report['passed']),indent=2))
    if not report['passed']:raise SystemExit('Validation failed')

if __name__=='__main__':main()
