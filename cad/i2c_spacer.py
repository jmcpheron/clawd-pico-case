"""I2C spacer: a thin plate between the Pico and the LCD that holds the pigtail
for an external I2C signing chip (OPTIGA Trust M) where it leaves the non-USB
end. Jason, 2026-10-01: the wires are independent of the part (no pin routing),
the part sits between the boards with a strain-relief clip, and the cable is a
pigtail (plug outside). Two pegs locate it in the Pico's button-end holes
(cad/pico_holes.py, provisional until PINK-P20); two clips at the edge hold
2 wires each, in line with the v1.8 base slots (cad/v1_8_cable_slot.py).
It touches only the Pico, so the LCD cannot be lifted or shifted.
Case frame with the stack held as v1.3 (pico_holes.held()).
Rows SP-* in MEASUREMENTS. Run: .venv/bin/python cad/i2c_spacer.py
"""
import hashlib
import json
import math
from pathlib import Path
from build123d import Pos, Rot, Cone, export_step, import_step
import pico_holes as H

L7,M,P,J=H.L7,H.M,H.P,H.J
ROOT=H.ROOT
STL=ROOT/'stl/i2c-spacer'
OUT=ROOT/'renders/i2c-spacer'
STRIP_IN=P.P10/2-P.HEADER_W/2   # 7.62: header strip inner edge from the Pico centreline (P10, H1 envelope)
HALF_W=STRIP_IN-P.CLEAR         # SP-PLATE: 7.32
LENGTH=4.3                      # SP-PLATE: plate end past the inner end-wall face
T=1.4                           # SP-PLATE
PEG_D=H.HOLE_D-2*P.JOY_SOCKET_CLEAR  # SP-PEG: 1.8
PEG_L=P.P3+.4                   # SP-PEG: through the PCB (PINK-P3) and 0.4 past
PEG_CH=.3                       # SP-PEG: tip chamfer
WIRE=1.0                        # SP-WIRE: design envelope per wire, not a cable measurement
CLIP_W=2*WIRE+P.MATE_CLEAR      # SP-CLIP: 2.2, two wires
CLIP_L=1.2                      # SP-CLIP
LIP_H,MOUTH=.4,WIRE-.15         # SP-CLIP: lip 0.4 thick, mouth 0.85 (V1.4-RIB 0.15 interference)
CLIP_WALL=.4                    # SP-CLIP: wall to the plate edge

def face():
    return M.Z_PICO_TOP  # Pico's LCD-facing face

def slide(dy):
    """How far the held stack can still slide toward the button end (v1.3: 0.08)."""
    return dy-M.IY0

def y0(dy):
    return M.IY0+P.CLEAR+slide(dy)  # SP-PLATE: CLEAR from the wall even when slid

def clip_x():
    off=HALF_W-CLIP_WALL-CLIP_W/2  # 5.82
    return [M.PICO_CX-off,M.PICO_CX+off]

def wire_x():
    return [c+s*(CLIP_W/2-WIRE/2-P.MATE_CLEAR/4) for c in clip_x() for s in (-1,1)]

def spacer(dy=None):
    dy=H.held() if dy is None else dy
    z0=face();a=y0(dy);b=M.IY0+LENGTH;cx=M.PICO_CX
    s=M.box(cx-HALF_W,cx+HALF_W,a,b,z0,z0+T)
    for x,y in H.centres(dy)[:2]:  # button-end holes
        peg=J.cylinder(PEG_D,z0-PEG_L+PEG_CH,z0+P.EPS)
        tip=Pos(x,y,z0-PEG_L+PEG_CH/2)*Cone(PEG_D/2-PEG_CH,PEG_D/2,PEG_CH)
        s+=Pos(x,y,0)*peg+tip
    for c in clip_x():
        s-=M.box(c-CLIP_W/2,c+CLIP_W/2,a-P.TOOL_EXT,a+CLIP_L,z0-P.TOOL_EXT,z0+T-LIP_H)
        s-=M.box(c-MOUTH/2,c+MOUTH/2,a-P.TOOL_EXT,a+CLIP_L,z0+T-LIP_H-P.EPS,z0+T+P.TOOL_EXT)
    return s

def wires(dy=None,y_out=None):
    """Proxy: 4 x WIRE resting on the Pico face in the clips, out past the end wall."""
    dy=H.held() if dy is None else dy
    y_out=M.IY0-6 if y_out is None else y_out
    a=y0(dy)+CLIP_L-.01;z=face()+WIRE/2;d=WIRE-.02  # 0.01 shy all round: tests fit, not tangency
    out=None
    for x in wire_x():
        w=Pos(x,(a+y_out)/2,z)*Rot(90,0,0)*J.cylinder(d,-(a-y_out)/2,(a-y_out)/2)
        out=w if out is None else out+w
    return out

def strips(dy):
    """Header plastic envelope: H1 width and length, the full 3.6 under the LCD sockets (PINK-STRIP pending)."""
    out=None
    for sx in (-1,1):
        x=M.PICO_CX+sx*P.P10/2
        s=M.box(x-P.HEADER_W/2,x+P.HEADER_W/2,M.PICO_CY+dy-P.HEADER_L/2,M.PICO_CY+dy+P.HEADER_L/2,face(),M.Z_LCD_BACK-P.L7)
        out=s if out is None else out+s
    return out

def overhangs(shape):
    """Downward faces steeper than 45 deg above the bed (shape in print orientation)."""
    bad=[]
    for f in shape.faces():
        for u in (.1,.5,.9):
            for v in (.1,.5,.9):
                try:pt=f.position_at(u,v);n=f.normal_at(pt)
                except Exception:continue
                if n.Z<-math.cos(math.radians(45))-1e-3 and pt.Z>1e-3:bad.append((round(pt.X,2),round(pt.Y,2),round(pt.Z,2)))
    return sorted(set(bad))

def printed(s):
    return L7.V.origin(Rot(180,0,0)*s)  # SP-PRINT: top face down, pegs up

def main():
    STL.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    L7.W.shorten()
    dy=H.held();s=spacer(dy);z0=face()
    lid,_=L7.lid();base,_=L7.base()
    hat=Pos(0,dy,0)*M.hat();pc=Pos(0,dy,0)*H.pico();wr=wires(dy)
    def vol(x):return sum(q.volume for q in x.solids()) if x is not None else 0.
    big=M.box(-10,40,-10,60,z0-.05,z0)
    peg_band=2*math.pi*(PEG_D/2)**2*.05
    pr=printed(s);bad=overhangs(pr)
    checks=dict(
        valid_single_solid=s.is_valid and len(s.solids())==1,
        pegs_in_pico_holes=all(vol(s & Pos(x,y,0)*J.cylinder(PEG_D+.02,z0-P.P3,z0))>.99*math.pi*(PEG_D/2)**2*P.P3 for x,y in H.centres(dy)[:2]),
        clear_of_pico=J.overlap(s,pc)<1e-5,
        flat_on_pico_face=abs(vol(s & big)-peg_band)<1e-4,  # only the pegs go below the face
        clear_of_header_strips=J.overlap(s,strips(dy))<1e-6,
        clear_of_hat=J.overlap(s,hat)<1e-6,
        clear_of_v1_7_case=J.overlap(s,base+lid)<1e-6,
        clear_of_wall_when_slid=y0(dy)-slide(dy)-M.IY0>=P.CLEAR-1e-9,
        wires_fit_clips=J.overlap(s,wr)<1e-6,
        lip_retains_one_wire=MOUTH<WIRE,
        no_overhangs_printed=not bad,
        printed_flat_on_bed=abs(pr.bounding_box().min.Z)<1e-6)
    bb=s.bounding_box()
    report=dict(passed=all(checks.values()),checks=checks,provisional=True,
        size_mm=[round(bb.size.X,2),round(bb.size.Y,2),round(T,2)],peg_d=PEG_D,peg_l=round(PEG_L,2),
        clip_x=[round(c,3) for c in clip_x()],wire_x=[round(x,3) for x in wire_x()],wire_envelope=WIRE,mouth=round(MOUTH,2),
        top_z=round(z0+T,3),room_to_lcd_back=round(M.Z_LCD_BACK-z0-T,2),room_to_socket_bottoms=round(M.Z_LCD_BACK-P.L7-z0-T,2),
        overhangs=bad,
        notes=['Provisional: peg positions and hole size are PICO-HOLES-PROV (datasheet), strips are the H1 envelope.',
               'Wires reach the clips over the 1.4 plate (a 1.4 step down into the channel); where they are soldered is independent of the part.',
               'Pigtail: thread the bare end in through a v1.8 slot, solder, then press the wires into the clips.'])
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(checks=checks,passed=report['passed'],size_mm=report['size_mm'],clip_x=report['clip_x'],overhangs=bad),indent=2))
    if not report['passed']:raise SystemExit('Validation failed')
    paths=[STL/'i2c-spacer-top-down.stl',OUT/'part.step']
    J.export(pr,paths[0])
    s.label='I2C spacer (case frame, provisional)';export_step(s,str(paths[1]))
    back=import_step(str(paths[1])).solids()
    if len(back)!=1 or abs(back[0].volume-s.volume)>1e-4:raise SystemExit('STEP re-import mismatch')
    src=[Path(__file__),*(ROOT/'cad'/n for n in ('pico_holes.py','model.py','params.py','v1_7_lock.py'))]
    (OUT/'manifest.json').write_text(json.dumps(dict(revision='i2c-spacer (provisional)',supports=False,raft=False,slice_verified=False,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in src},
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*paths,OUT/'validation.json']}),indent=2)+'\n')

if __name__=='__main__':main()
