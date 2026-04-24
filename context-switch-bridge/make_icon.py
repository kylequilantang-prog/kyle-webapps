"""Generate Context Switch Bridge icons for PWA.

Metaphor: Two contexts (amber = current/scattered, green = next/focused)
connected by a glowing lavender bridge arc with a traveler dot mid-crossing.
Scattered dots evoke ADHD neural activity being gathered into intentional transition.
"""
from PIL import Image, ImageDraw, ImageFilter
import math, os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SIZE = 1024

BG = (10, 15, 31)          # #0A0F1F navy
BG_INNER = (17, 26, 46)    # #111A2E slightly lighter
AMBER = (245, 158, 11)     # #F59E0B
GREEN = (16, 185, 129)     # #10B981
LAV = (233, 228, 245)      # #E9E4F5
MUTED = (154, 168, 199)    # #9AA8C7


def rounded_rect_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def glow_circle(img, cx, cy, radius, color, glow_layers=6):
    """Draw a filled circle with a soft outer glow."""
    for i in range(glow_layers, 0, -1):
        alpha = int(40 * (i / glow_layers) * 0.35)
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        r = radius + i * (radius * 0.25)
        ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha))
        layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.35))
        img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(*color, 255))


def draw_bridge_arc(img, start, end, peak_y, color, thickness, samples=160):
    """Draw a quadratic bezier arc between start and end with given peak y."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    (x0, y0), (x2, y2) = start, end
    x1 = (x0 + x2) / 2
    y1 = peak_y
    pts = []
    for i in range(samples + 1):
        t = i / samples
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t ** 2 * x2
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t ** 2 * y2
        pts.append((x, y))
    d.line(pts, fill=(*color, 230), width=thickness, joint="curve")
    # soft glow
    glow = layer.filter(ImageFilter.GaussianBlur(thickness * 0.9))
    img.alpha_composite(glow)
    img.alpha_composite(layer)
    return pts


def scattered_dots(img, seed_points, color, base_radius):
    """Small dots suggesting ADHD-style thought scatter around the amber side,
    gathered into a focused stream around the green side."""
    d = ImageDraw.Draw(img)
    for (x, y, rmul, alpha) in seed_points:
        r = base_radius * rmul
        d.ellipse([x - r, y - r, x + r, y + r], fill=(*color, alpha))


def build_icon(size=SIZE):
    # Background with rounded corners (iOS will also mask, but this helps previews)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # gradient-ish background by compositing two layers
    bg = Image.new("RGBA", (size, size), (*BG, 255))
    # Subtle radial lighten toward center
    radial = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(radial)
    for i in range(60, 0, -1):
        a = int(3)
        r = size * 0.75 * (i / 60)
        rd.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r],
                   fill=(*BG_INNER, a))
    radial = radial.filter(ImageFilter.GaussianBlur(size * 0.05))
    bg.alpha_composite(radial)
    img.alpha_composite(bg)

    # Coordinates
    cy = size * 0.58
    left = (size * 0.22, cy)
    right = (size * 0.78, cy)
    peak_y = size * 0.30
    orb_r = size * 0.085

    # Scatter dots around the amber (left) side — representing unfocused thought
    import random
    random.seed(7)
    scatter_left = []
    for _ in range(14):
        angle = random.uniform(-math.pi, math.pi)
        dist = random.uniform(orb_r * 1.6, orb_r * 3.0)
        x = left[0] + math.cos(angle) * dist
        y = left[1] + math.sin(angle) * dist * 0.9
        scatter_left.append((x, y, random.uniform(0.12, 0.26), random.randint(90, 170)))
    scattered_dots(img, scatter_left, AMBER, orb_r)

    # Smaller, tidy dots around the green (right) side — collected/focused
    scatter_right = []
    for i, angle in enumerate([-1.2, -0.4, 0.4, 1.2, 2.0]):
        dist = orb_r * 1.8
        x = right[0] + math.cos(angle) * dist
        y = right[1] + math.sin(angle) * dist * 0.9
        scatter_right.append((x, y, 0.16, 160))
    scattered_dots(img, scatter_right, GREEN, orb_r)

    # Bridge arc (lavender) connecting the two orbs
    arc_thickness = int(size * 0.022)
    pts = draw_bridge_arc(img, left, right, peak_y, LAV, arc_thickness)

    # Traveler dot on the arc — placed at mid-crossing (t ≈ 0.55, past the peak,
    # suggesting motion from amber toward green — intentional transition)
    t = 0.55
    idx = int(t * (len(pts) - 1))
    tx, ty = pts[idx]
    glow_circle(img, tx, ty, orb_r * 0.38, LAV, glow_layers=5)

    # The two orbs (drawn last so they sit on top of scatter)
    glow_circle(img, left[0], left[1], orb_r, AMBER, glow_layers=7)
    glow_circle(img, right[0], right[1], orb_r, GREEN, glow_layers=7)

    # Mask to rounded corners for non-iOS contexts
    mask = rounded_rect_mask(size, int(size * 0.22))
    final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    final.paste(img, (0, 0), mask)
    return final


def main():
    master = build_icon(SIZE)
    # Full-bleed variant for iOS (iOS applies its own rounded mask, so export
    # the full square background without our rounding so there's no double mask).
    square = Image.new("RGBA", (SIZE, SIZE), (*BG, 255))
    inner = build_icon(SIZE)
    # paste inner image; it already has rounded corners — but for apple-touch
    # we prefer full-bleed. Re-render without rounding:
    # simplest: render again and skip mask
    # (build_icon always masks — so just paste onto BG square)
    square.alpha_composite(inner)  # transparent rounded corners become BG

    sizes = {
        "icon-1024.png": square,
        "icon-512.png": square.resize((512, 512), Image.LANCZOS),
        "icon-192.png": square.resize((192, 192), Image.LANCZOS),
        "apple-touch-icon.png": square.resize((180, 180), Image.LANCZOS),
        "favicon-32.png": master.resize((32, 32), Image.LANCZOS),
    }
    for name, im in sizes.items():
        path = os.path.join(OUT_DIR, name)
        im.save(path, "PNG")
        print(f"wrote {path} ({im.size[0]}x{im.size[1]})")


if __name__ == "__main__":
    main()
