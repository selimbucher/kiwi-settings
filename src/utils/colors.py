import math
import subprocess
import colorsys
import re
import sys
from dataclasses import dataclass


@dataclass
class Color:
    count: int
    r: float
    g: float
    b: float

    @property
    def hls(self):
        return colorsys.rgb_to_hls(self.r / 255, self.g / 255, self.b / 255)

    @property
    def hsv(self):
        return colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)

    @property
    def h(self): return self.hls[0]
    @property
    def l(self): return self.hls[1]
    @property
    def s_hls(self): return self.hls[2]
    @property
    def s_hsv(self): return self.hsv[1]
    @property
    def v(self): return self.hsv[2]

    def to_hex(self):
        return f"#{int(self.r):02X}{int(self.g):02X}{int(self.b):02X}"

    def to_rgb(self):
        return f"rgb({int(self.r)}, {int(self.g)}, {int(self.b)})"

    def to_hsl(self):
        h, l, s = self.hls
        return f"hsl({h*360:.0f}, {s*100:.0f}%, {l*100:.0f}%)"

    def to_css(self, fmt="hex"):
        if fmt == "hex": return self.to_hex()
        if fmt == "rgb": return self.to_rgb()
        if fmt == "hsl": return self.to_hsl()
        raise ValueError(f"Unknown format: {fmt}")

    def __repr__(self):
        return f"Color({self.to_hex()}  count={self.count}  s={self.s_hsv:.2f}  v={self.v:.2f}  l={self.l:.2f})"


def colors_kmeans(image_path, n_colors=16):
    """The image's dominant colors, most common first."""
    result = subprocess.run(
        ["magick", image_path,
         "-alpha", "off",
         "-resize", "200x200",
         "-kmeans", str(n_colors),
         "-format", "%c", "histogram:info:-"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"ERROR: magick failed (exit {result.returncode}):\n{result.stderr}", file=sys.stderr)
        return []

    colors = []
    for line in result.stdout.splitlines():
        m = re.match(r'\s*(\d+):.*\(\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*[\d.]+)?\)', line)
        if m:
            colors.append(Color(
                count=int(m.group(1)),
                r=float(m.group(2)),
                g=float(m.group(3)),
                b=float(m.group(4)),
            ))

    if not colors:
        print("ERROR: magick produced no colors", file=sys.stderr)
    return sorted(colors, key=lambda c: c.count, reverse=True)


# Accent colors are adjusted in OKHSV (Björn Ottosson). Each hue is most
# colorful at its own lightness: yellow and cyan near white, orange and pink in
# the middle, blue and violet dark. OKHSV measures saturation and value against
# that per hue, so one range looks equally strong on every hue, where a fixed
# lightness or chroma made cyan neon and forced violet into lavender.
ACCENT_SATURATION = (0.45, 0.62)
ACCENT_VALUE = (0.88, 0.97)
# what counts as a color worth taking from the wallpaper (OKLab)
MIN_SOURCE_CHROMA = 0.07
MIN_SOURCE_LIGHTNESS = 0.35


def _to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _linear_srgb_to_oklab(r, g, b):
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def _oklab_to_linear_srgb(lightness, a, b):
    l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def rgb_to_oklch(r, g, b):
    """sRGB in [0, 1] -> (lightness, chroma, hue in radians)"""
    lightness, a, b_ = _linear_srgb_to_oklab(*(_to_linear(x) for x in (r, g, b)))
    return lightness, math.hypot(a, b_), math.atan2(b_, a)


def _in_gamut(rgb):
    return all(-1e-6 <= x <= 1 + 1e-6 for x in rgb)


def _max_chroma(lightness, a_, b_):
    low, high = 0.0, 0.6
    for _ in range(40):
        mid = (low + high) / 2
        if _in_gamut(_oklab_to_linear_srgb(lightness, mid * a_, mid * b_)):
            low = mid
        else:
            high = mid
    return low


def _find_cusp(a_, b_):
    """(lightness, chroma) where this hue is most colorful in sRGB.

    Found numerically rather than with Ottosson's fitted polynomials; chroma
    over lightness has a single peak, so a golden-section search is enough.
    """
    low, high = 0.0, 1.0
    ratio = (math.sqrt(5) - 1) / 2
    x1, x2 = high - ratio * (high - low), low + ratio * (high - low)
    f1, f2 = _max_chroma(x1, a_, b_), _max_chroma(x2, a_, b_)
    for _ in range(40):
        if f1 < f2:
            low, x1, f1 = x1, x2, f2
            x2 = low + ratio * (high - low)
            f2 = _max_chroma(x2, a_, b_)
        else:
            high, x2, f2 = x2, x1, f1
            x1 = high - ratio * (high - low)
            f1 = _max_chroma(x1, a_, b_)
    lightness = (low + high) / 2
    return lightness, _max_chroma(lightness, a_, b_)


_K1, _K2 = 0.206, 0.03
_K3 = (1 + _K1) / (1 + _K2)


def _toe(x):
    return 0.5 * (_K3 * x - _K1 + math.sqrt((_K3 * x - _K1) ** 2 + 4 * _K2 * _K3 * x))


def _toe_inv(x):
    return (x * x + _K1 * x) / (_K3 * (x + _K2))


def srgb_to_okhsv(r, g, b):
    """sRGB in [0, 1] -> (hue in degrees, saturation, value)"""
    lightness, a, b_ = _linear_srgb_to_oklab(*(_to_linear(x) for x in (r, g, b)))
    chroma = math.hypot(a, b_)
    if chroma < 1e-9:
        return 0.0, 0.0, _toe(lightness)
    a_, b_n = a / chroma, b_ / chroma
    hue = math.degrees(math.atan2(b_, a)) % 360
    cusp_l, cusp_c = _find_cusp(a_, b_n)
    s_max, t_max = cusp_c / cusp_l, cusp_c / (1 - cusp_l)
    s_0 = 0.5
    k = 1 - s_0 / s_max
    t = t_max / (chroma + lightness * t_max)
    l_v, c_v = t * lightness, t * chroma
    l_vt = _toe_inv(l_v)
    c_vt = c_v * l_vt / l_v
    rgb_scale = _oklab_to_linear_srgb(l_vt, a_ * c_vt, b_n * c_vt)
    scale = (1 / max(*rgb_scale, 0)) ** (1 / 3)
    lightness, chroma = lightness / scale, chroma / scale
    lightness = _toe(lightness)
    value = lightness / l_v
    saturation = (s_0 + t_max) * c_v / (t_max * s_0 + t_max * k * c_v)
    return hue, saturation, value


def okhsv_to_srgb(hue, saturation, value):
    """(hue in degrees, saturation, value) -> sRGB in [0, 1]"""
    a_, b_ = math.cos(math.radians(hue)), math.sin(math.radians(hue))
    cusp_l, cusp_c = _find_cusp(a_, b_)
    s_max, t_max = cusp_c / cusp_l, cusp_c / (1 - cusp_l)
    s_0 = 0.5
    k = 1 - s_0 / s_max
    l_v = 1 - saturation * s_0 / (s_0 + t_max - t_max * k * saturation)
    c_v = saturation * t_max * s_0 / (s_0 + t_max - t_max * k * saturation)
    lightness, chroma = value * l_v, value * c_v
    l_vt = _toe_inv(l_v)
    c_vt = c_v * l_vt / l_v
    new_lightness = _toe_inv(lightness)
    chroma = chroma * new_lightness / lightness if lightness > 0 else 0
    lightness = new_lightness
    rgb_scale = _oklab_to_linear_srgb(l_vt, a_ * c_vt, b_ * c_vt)
    scale = (1 / max(*rgb_scale, 0)) ** (1 / 3)
    lightness, chroma = lightness * scale, chroma * scale
    rgb = _oklab_to_linear_srgb(lightness, chroma * a_, chroma * b_)
    return tuple(min(max(_to_srgb(x), 0.0), 1.0) for x in rgb)


def adjust_color(color: Color) -> Color:
    """Move a color into the accent's saturation and value ranges, keeping its hue."""
    hue, saturation, value = srgb_to_okhsv(color.r / 255, color.g / 255, color.b / 255)
    saturation = min(max(saturation, ACCENT_SATURATION[0]), ACCENT_SATURATION[1])
    value = min(max(value, ACCENT_VALUE[0]), ACCENT_VALUE[1])
    r, g, b = (round(x * 255) for x in okhsv_to_srgb(hue, saturation, value))
    return Color(count=color.count, r=r, g=g, b=b)


def get_color(image_path, fmt="hex"):
    colors = colors_kmeans(image_path)
    if not colors:
        return None
    # the most common clearly colored area; failing that, the most colorful one
    chroma = {id(c): rgb_to_oklch(c.r / 255, c.g / 255, c.b / 255) for c in colors}
    usable = [
        c for c in colors
        if chroma[id(c)][1] >= MIN_SOURCE_CHROMA and chroma[id(c)][0] >= MIN_SOURCE_LIGHTNESS
    ]
    source = usable[0] if usable else max(colors, key=lambda c: chroma[id(c)][1])
    return adjust_color(source).to_css(fmt=fmt)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python colors.py <image_path>")
        sys.exit(1)
    print(get_color(sys.argv[1]))
