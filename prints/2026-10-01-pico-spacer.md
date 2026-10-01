# Pico pin spacer — corners and I2C versions

Jason's spacer on the datasheet pin grid. Sits on the header side of the Pico
(toward the LCD) and slips over the pins through 1.3 mm square holes.

- `stl/pico-spacer/pico-spacer-corners.stl` (pins 1, 20, 21, 40), SHA256 `877b27ca257e21082cb70e80f18671b639bcdd7e03f121281bd80db3ca17d7fe`.
- `stl/pico-spacer/pico-spacer-i2c.stl` (+ pins 6, 7, 36, 38), SHA256 `96093fd7afd302894a48cc4968a5d5e7937cf30e24a2287faa25ecc7ca7f8538`.

Flat as exported (Pico side on the bed, dot and arrow up), no supports.
Printer, material and settings: to be filled in by Jason.

Check:
- the I2C version against `renders/pico-spacer/top-view.svg` before fitting:
  dot by pin 1 (GP0), arrow toward USB;
- it drops over all its pins without forcing;
- the LCD still plugs fully onto the Pico (the spacer needs 1.0 free between
  the header plastic and the LCD sockets);
- the case still closes.

## Result

(pending)
