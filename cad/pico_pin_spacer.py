"""Pico pin spacer: Jason's design (inputs/2026-10-01-jason-pico-spacer.step),
rebuilt here so every number traces to a row, plus an I2C variant.
A 1.0 plate between the header rows on the header (LCD) side of the Pico, with
square-holed tabs that slip over chosen header pins. Jason's file has tabs on
the corner pins 1, 20, 21, 40 at his caliper positions; this script
reproduces that file exactly (checked), then builds two printable parts on the
datasheet grid (JS-SNAP):
  corners: pins 1, 20, 21, 40
  i2c:     corners + pins 6 (GP4), 7 (GP5), 36 (3V3), 38 (GND), with a pin-1
           dot and an arrow to the USB end on the top face
Frame: centred on the Pico, +y toward USB, +z toward the LCD, z 0 on the Pico
side; seen from +z, pin 1 is top-right (PICO-PINOUT).
Rows JS-*, PICO-PINOUT, P9, P10 in MEASUREMENTS. Run: .venv/bin/python cad/pico_pin_spacer.py
"""
import hashlib
import json
import math
from pathlib import Path
from build123d import Pos, Plane, Polygon, extrude, fillet, export_step, import_step, GeomType
import joystick_test as J

M,P=J.M,J.P
ROOT=J.ROOT
STL=ROOT/'stl/pico-spacer'
OUT=ROOT/'renders/pico-spacer'
SOURCE=ROOT/'inputs/2026-10-01-jason-pico-spacer.step'  # JS-SOURCE
SOURCE_SHA='8319309b4b510ec4128f9be43da630fcca887caee2540161a71941140802430e'
PAD=3.3     # JS-PAD: tab, square, centred on its pin
R=1.0       # JS-PAD: tab corner and junction fillets
R_TIGHT=.8  # JS-TIGHT: junction fillets facing a 1.78 gap between tabs
HOLE=1.3    # JS-HOLE: square through hole
T=1.0       # JS-T
PITCH=2.54            # P9, ds Pico 2 W: header pitch
ROW_X=P.P10/2         # JS-SNAP: 8.89
PIN_Y=19*PITCH/2      # JS-SNAP: 24.13, corner pins
CAL_ROW_X,CAL_PIN_Y=8.85,24.1  # JS-PINS-CAL: Jason's file, reproduction check only
CORNERS=[1,20,21,40]
I2C=CORNERS+[6,7,36,38]  # JS-I2C
DOT_D,MARK_DEPTH=1.0,.3  # JS-MARK
ARROW=3.0                # JS-MARK: width and length
SVG_NAMES={1:'GP0',6:'GP4',7:'GP5',36:'3V3',38:'GND'}  # PICO-PINOUT, JS-I2C

def pin_xy(n,row_x=ROW_X,pin_y=PIN_Y):
    """PICO-PINOUT: 1-20 down the +x side from the USB end, 21-40 up the -x side."""
    pitch=2*pin_y/19  # P9 on the datasheet grid
    if 1<=n<=20:return row_x,pin_y-(n-1)*pitch
    if 21<=n<=40:return -row_x,-pin_y+(n-21)*pitch
    raise ValueError(n)

def tabs(pins,row_x,pin_y):
    """One rectangle per run of pins on a side whose tabs would overlap: (x_in, x_out, y_lo, y_hi)."""
    out=[]
    for sgn in (1,-1):
        ys=sorted(pin_xy(n,row_x,pin_y)[1] for n in pins if math.copysign(1,pin_xy(n,row_x,pin_y)[0])==sgn)
        groups=[]
        for y in ys:
            if groups and y-groups[-1][-1]<PAD:groups[-1].append(y)
            else:groups.append([y])
        for g in groups:out.append((sgn*(row_x-PAD/2),sgn*(row_x+PAD/2),g[0]-PAD/2,g[-1]+PAD/2))
    return out

def spacer(pins,row_x=ROW_X,pin_y=PIN_Y,mark=False,t=T):
    xi=row_x-PAD/2
    s=M.box(-xi,xi,-pin_y,pin_y,0,t)
    full,tight=[],[]
    tb=tabs(pins,row_x,pin_y)
    for x_in,x_out,lo,hi in tb:
        s+=M.box(min(x_in,x_out),max(x_in,x_out),lo,hi,0,t)
        full+=[(x_out,lo),(x_out,hi)]
        for y,other in ((lo,[h for a,_,_,h in tb if a==x_in and h<=lo]),(hi,[l for a,_,l,_ in tb if a==x_in and l>=hi])):
            near=any(abs(y-o)<2*R for o in other)  # JS-TIGHT: neighbour too close for two R junction fillets
            (tight if near else full).append((x_in,y))  # inner corner: convex past the plate end, concave junction otherwise
    def at(e,pts):
        a,b=e.start_point(),e.end_point()
        return e.geom_type==GeomType.LINE and abs(a.X-b.X)<1e-9 and abs(a.Y-b.Y)<1e-9 and any(abs(a.X-x)<1e-6 and abs(a.Y-y)<1e-6 for x,y in pts)
    s=fillet([e for e in s.edges() if at(e,full)],R)
    if tight:s=fillet([e for e in s.edges() if at(e,tight)],R_TIGHT)
    for n in pins:
        x,y=pin_xy(n,row_x,pin_y)
        s-=M.box(x-HOLE/2,x+HOLE/2,y-HOLE/2,y+HOLE/2,-P.TOOL_EXT,t+P.TOOL_EXT)
    if mark:
        dx,dy=xi-DOT_D,pin_y-DOT_D  # JS-MARK: dot 1.0 in from the plate's pin-1 corner
        s-=Pos(dx,dy,0)*J.cylinder(DOT_D,t-MARK_DEPTH,t+P.TOOL_EXT)
        tip=pin_y-4*DOT_D  # JS-MARK: arrow on the centreline, tip toward USB
        tri=Plane.XY.offset(t-MARK_DEPTH)*Polygon((-ARROW/2,tip-ARROW),(ARROW/2,tip-ARROW),(0,tip),align=None)
        s-=extrude(tri,MARK_DEPTH+P.TOOL_EXT)
    return s

def vol(s):return sum(x.volume for x in s.solids()) if s is not None else 0.

def symdiff(a,b):return vol(a-b)+vol(b-a)

def hole_ok(s,n,row_x=ROW_X,pin_y=PIN_Y,t=T):
    """Square hole of side HOLE centred on the pin: void inside, solid just outside on all four sides."""
    x,y=pin_xy(n,row_x,pin_y);h=HOLE/2
    void=vol(s & M.box(x-h+1e-4,x+h-1e-4,y-h+1e-4,y+h-1e-4,.1,t-.1))<1e-9
    ring=all(vol(s & M.box(x+a-.02,x+a+.02,y+b-.02,y+b+.02,.1,t-.1))>0 for a,b in ((h+.03,0),(-h-.03,0),(0,h+.03),(0,-h-.03)))
    return void and ring

def svg(s,pins,path):
    """Top view from the LCD side: outline, all 40 pins numbered, spacer holes highlighted."""
    k,m=12,40;bb=s.bounding_box();W,H=(bb.size.X+2*6)*k+2*m,(bb.size.Y+2*4)*k+2*m+30
    X=lambda x:m+(x-bb.min.X+6)*k;Y=lambda y:m+30+(bb.max.Y+4-y)*k
    top=max((f for f in s.faces() if f.geom_type==GeomType.PLANE and f.normal_at().Z>.99),key=lambda f:f.area)
    def poly(w):
        pts=[]
        for e in w.order_edges():
            for i in range(12):pts.append(e.position_at(i/12))
        return ' '.join(f'{X(p.X):.1f},{Y(p.Y):.1f}' for p in pts)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" font-family="Helvetica,Arial,sans-serif">',
         '<rect width="100%" height="100%" fill="#fff"/>',
         f'<text x="{W/2:.0f}" y="24" text-anchor="middle" font-size="16" font-weight="bold">USB end ↑ — seen from the LCD (header) side</text>',
         f'<polygon points="{poly(top.outer_wire())}" fill="#3a9d5d" fill-opacity=".35" stroke="#1e6b3c" stroke-width="1.5"/>']
    for w in top.inner_wires():out.append(f'<polygon points="{poly(w)}" fill="#fff" stroke="#1e6b3c" stroke-width="1"/>')
    for n in range(1,41):
        x,y=pin_xy(n);on=n in pins
        out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{3.5 if on else 2.5}" fill="{"#cc3333" if on else "#999"}"/>')
        lx=X(x)+(26 if x>0 else -26)
        label=f'{n} {SVG_NAMES[n]}' if n in SVG_NAMES else str(n)
        out.append(f'<text x="{lx:.1f}" y="{Y(y)+4:.1f}" text-anchor="{"start" if x>0 else "end"}" font-size="{12 if on else 10}" fill="{"#000" if on else "#777"}" font-weight="{"bold" if on else "normal"}">{label}</text>')
    out.append('</svg>')
    path.write_text('\n'.join(out)+'\n')

def main():
    STL.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    checks={}
    def check(n,ok):checks[n]=bool(ok)
    # 1. Jason's file, reproduced from the rows.
    check('source_file_unchanged',hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA)
    src=import_step(str(SOURCE));jo=Pos(0,0,25)*spacer(CORNERS,CAL_ROW_X,CAL_PIN_Y)  # his file sits at z 25-26
    check('rebuild_matches_jason_step',len(src.solids())==1 and symdiff(jo,src)<1e-3)
    check('rebuild_same_bbox',all(abs(a-b)<1e-6 for a,b in zip((*jo.bounding_box().min,*jo.bounding_box().max),(*src.bounding_box().min,*src.bounding_box().max))))
    # 2. Printable parts on the datasheet grid.
    parts={'corners':(spacer(CORNERS),CORNERS),'i2c':(spacer(I2C,mark=True),I2C)}
    for name,(s,pins) in parts.items():
        check(name+'_valid_single_solid',s.is_valid and len(s.solids())==1)
        check(name+'_holes_on_grid',all(hole_ok(s,n) for n in pins))
        check(name+'_no_extra_holes',len(max((f for f in s.faces() if f.geom_type==GeomType.PLANE and f.normal_at().Z<-.99),key=lambda f:f.area).inner_wires())==len(pins))
        check(name+'_flat_on_bed',abs(s.bounding_box().min.Z)<1e-9 and abs(s.bounding_box().max.Z-T)<1e-9)
    i2c=parts['i2c'][0];tb=tabs(I2C,ROW_X,PIN_Y)
    side=sorted((lo,hi) for x_in,x_out,lo,hi in tb if x_in<0)  # pins 36, 38, 40 run
    check('pins_6_7_share_one_tab',any(lo<pin_xy(7)[1]<pin_xy(6)[1]<hi and x_in>0 for x_in,x_out,lo,hi in tb))
    check('tabs_36_38_40_separate_1_78',[round(b[0]-a[1],2) for a,b in zip(side,side[1:]) if a[1]>0]==[1.78,1.78])
    plain=spacer(I2C)
    marks=math.pi*(DOT_D/2)**2*MARK_DEPTH+ARROW*ARROW/2*MARK_DEPTH
    check('mark_wholly_in_plate_0_7_floor',T-MARK_DEPTH>=.7-1e-9 and abs(vol(plain)-vol(i2c)-marks)<1e-3)
    tighter=(R**2-R_TIGHT**2)*(1-math.pi/4)*T  # pin 40's junction now faces pin 38's tab (JS-TIGHT)
    check('i2c_contains_corners_but_pin_40_junction',abs(vol(parts['corners'][0]-plain)-tighter)<1e-4)
    # 3. Fit in the v1.7 case: the footprint over the Pico, through the whole gap under the LCD sockets.
    import v1_7_lock as L7
    L7.W.shorten();held=M.IY1-P.L1-.02  # v1.3 hold, as v1_3_short_end
    lid,_=L7.lid();base,_=L7.base()
    gap=M.Z_LCD_BACK-P.L7-M.Z_PICO_TOP  # 3.6: header plastic + free pin (PINK-P18b unmeasured)
    tall=Pos(M.PICO_CX,M.PICO_CY+held,M.Z_PICO_TOP)*spacer(I2C,t=gap)
    check('footprint_clear_of_v1_7_case',J.overlap(tall,base+lid)<1e-6)
    rail=P.P2/2+P.CLEAR  # rail inner faces from the Pico centreline (S1 rails)
    report=dict(passed=all(checks.values()),checks=checks,
        source=dict(file=str(SOURCE.relative_to(ROOT)),sha256=SOURCE_SHA,onshape='Part Studio 1 - Part 6, 2026-10-01T20:06:14Z',author='Jason McPheron'),
        grid=dict(row_x=ROW_X,corner_pin_y=round(PIN_Y,3),pitch=PITCH,jason_cal=dict(row_x=CAL_ROW_X,corner_pin_y=CAL_PIN_Y)),
        pins={name:{str(n):[round(v,3) for v in pin_xy(n)] for n in pins} for name,(s,pins) in parts.items()},
        size_mm={name:[round(v,3) for v in s.bounding_box().size] for name,(s,pins) in parts.items()},
        case_fit=dict(clear_to_rails=round(rail-ROW_X-PAD/2,3),gap_header_side_mm=round(gap,2),
            needs='at least 1.0 free between the header plastic top and the LCD socket bottoms, or the LCD rises by the shortfall (PINK-P18b unmeasured)'),
        notes=['Holes snapped to the datasheet grid (JS-SNAP); Jason measured 17.70 x 48.20 (JS-PINS-CAL).',
               'Pin numbering from Jason looking at his board (PICO-PINOUT). Check top-view.svg against the board before printing.'])
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(checks=checks,passed=report['passed'],size_mm=report['size_mm'],case_fit=report['case_fit']),indent=2))
    if not report['passed']:raise SystemExit('Validation failed')
    outputs=[]
    for name,(s,pins) in parts.items():
        stl=STL/f'pico-spacer-{name}.stl';J.export(s,stl);outputs.append(stl)
        s.label=f'Pico pin spacer, {name}';step=OUT/f'pico-spacer-{name}.step';export_step(s,str(step));outputs.append(step)
        back=import_step(str(step)).solids()
        if len(back)!=1 or abs(back[0].volume-s.volume)>1e-6:raise SystemExit(f'STEP re-import mismatch: {name}')
    svg(i2c,I2C,OUT/'top-view.svg');outputs+=[OUT/'top-view.svg',OUT/'validation.json']
    srcs=[Path(__file__),SOURCE,*(ROOT/'cad'/n for n in ('model.py','params.py','v1_7_lock.py'))]
    (OUT/'manifest.json').write_text(json.dumps(dict(revision='pico-spacer',supports=False,raft=False,slice_verified=False,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in srcs},
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}),indent=2)+'\n')

if __name__=='__main__':main()
