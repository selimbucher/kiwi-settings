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


def colors_kmeans(image_path, n_colors=16, min_saturation=0.4, min_lightness=0.3):
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

    if not result.stdout.strip():
        print("ERROR: magick produced no output", file=sys.stderr)
        return []

    all_colors = []
    unmatched = []

    for line in result.stdout.splitlines():
        m = re.match(r'\s*(\d+):.*\(\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*[\d.]+)?\)', line)
        if not m:
            unmatched.append(line)
            continue
        all_colors.append(Color(
            count=int(m.group(1)),
            r=float(m.group(2)),
            g=float(m.group(3)),
            b=float(m.group(4)),
        ))

    if unmatched:
        # print(f"WARNING: {len(unmatched)} lines didn't match the regex:", file=sys.stderr)
        for line in unmatched[:5]:
            print(f"  {repr(line)}", file=sys.stderr)

    candidates = [c for c in all_colors if c.s_hls >= min_saturation and c.l >= min_lightness]

    if candidates:
        candidates.sort(key=lambda c: c.count, reverse=True)
        return candidates

    # Fallback: return the brightest color from all kmeans results
    if all_colors:
        # print("WARNING: no colors passed filters, falling back to brightest", file=sys.stderr)
        return [max(all_colors, key=lambda c: c.v)]

    return []


def adjust_color(color: Color, min_saturation=0.18, max_saturation=0.64, min_value=0.85) -> Color:
    h, s, v = color.hsv
    s = max(min_saturation, min(max_saturation, s))
    v = max(min_value, v)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return Color(count=color.count, r=r * 255, g=g * 255, b=b * 255)


def get_color(image_path, fmt="hex"):
    colors = colors_kmeans(image_path)
    if not colors:
        return None
    best = adjust_color(colors[0])
    return best.to_css(fmt=fmt)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python colors.py <image_path>")
        sys.exit(1)
    print(get_color(sys.argv[1]))