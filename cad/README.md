Original build123d CAD. Read `../CLAUDE.md` and `../PROCESS.md` first.
Hardware inputs and R4 choices cite `../MEASUREMENTS.md`; reasons in DESIGN.md.

From repository root: `.venv/bin/python cad/build.py`.
`params.py` defines hardware/choices; `model.py` constructs parts;
`validate.py` checks collision/motion scenarios; `render.py` produces a static
preview from CAD tessellation; `build.py` audits then exports all outputs.
Dependencies are pinned in requirements.txt. Validation is conditional on the
recorded measurements and explicit assumptions; see REPORT.md before printing.

## Editing in Onshape (round trip)

STEP files are exact solids exported from this source; edit them anywhere, but
the Python stays the source of truth.

1. Import `stl/v1.4/joystick-j19/joystick-j19-N.step` (flange down at the
   origin, mm). For fit, import `renders/v1.4/joystick-j19/fit.step`: v1.7 lid,
   hat proxy and all five caps in the same spot (hide all but one).
2. Edit. Note what you changed and why (a sketch dimension, a measurement).
3. Export STEP to `onshape/YYYY-MM-DD-<what>.step` on a branch and open a PR.
   Say where each number came from (caliper, fit test, guess).
4. Claude compares it with the original STEP (volume, bounding box, sections
   through socket and tabs), writes the changed numbers as `MEASUREMENTS.md`
   rows citing the file and its hash, logs `PROVENANCE.md`, writes the next J
   script in build123d, regenerates STL/STEP, and checks the result against
   the Onshape STEP.

Regenerate the STEPs: `.venv/bin/python cad/joystick_j19_step.py`.
Pico mounting holes (provisional, datasheet numbers): `renders/pico-holes/assembly.step`
(v1.7 base and lid, hat, Pico with holes, in the case frame) and `pico.step`;
hole centres and free room in `validation.json`. `.venv/bin/python cad/pico_holes.py`.
Documents on Onshape's free plan are public; use a private plan for this design.

I2C signing-chip wiring (provisional): `cad/i2c_spacer.py` (spacer on the Pico,
pegs in its button-end holes, two edge clips) and `cad/v1_8_cable_slot.py`
(v1.7 base + two non-USB end slots; viewer, assembly). Report:
`reports/2026-10-01-i2c-spacer-v1.8.md`.
