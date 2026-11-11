"""Draw a README animation from actual H-01 integer reference samples.

This is an exported reference trace, not a capture of a physical board or browser.
"""
from pathlib import Path
import sys
import math

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from emporio.audio import dds_trace, program, validation
from PIL import Image, ImageDraw, ImageFont


def font(size, serif=False):
    roots = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]
    names = ["georgia.ttf", "DejaVuSerif.ttf"] if serif else ["arial.ttf", "DejaVuSans.ttf"]
    for root in roots:
        for name in names:
            if (root / name).is_file():
                return ImageFont.truetype(str(root / name), size)
    return ImageFont.load_default(size=size)


def main():
    settings = program()
    samples = [r["sample"] for r in dds_trace([(False, True, False, 7, settings["phase_steps"])] * 24000)]
    ink, muted, line, lime = "#173f35", "#5e7260", "#ced9c5", "#d5f69a"
    frames = []
    for frame in range(32):
        image = Image.new("RGB", (1200, 680), "#edf1e7")
        d = ImageDraw.Draw(image)
        d.text((40, 30), "KONAET / SOUND LAB / H-01", fill=ink, font=font(16))
        d.text((40, 75), "Follow the signal.", fill=ink, font=font(61, True))
        d.text((42, 155), "Three voices. Exact samples. Open digital logic.", fill=muted, font=font(19))
        d.rounded_rectangle((40, 220, 755, 575), radius=22, fill=ink)
        d.text((65, 242), "C MAJOR / TRIANGLE DDS / PCM16", fill=lime, font=font(15))
        for y in (315, 390, 465):
            d.line((64, y, 730, y), fill="#355c47", width=1)
        offset = frame * 640
        window = samples[offset:offset + 1536]
        points = [(65 + i * 665 / 511, 390 - window[i * 3] / 32768 * 250) for i in range(512)]
        d.line(points, fill=lime, width=3)
        block = window[:64]
        rms = math.sqrt(sum(x*x for x in block)/64)/32768
        d.text((65, 520), f"t = {offset / 48000:.3f} s     fs = 48,000 Hz", fill="#d6e4c9", font=font(15))
        d.rounded_rectangle((790, 220, 1160, 575), radius=22, fill="#fbfcf4", outline=line)
        d.text((815, 245), "ONE ACCEPTED PCM BLOCK", fill=muted, font=font(13))
        for i, (label, value) in enumerate((("PEAK", str(max(map(abs, block)))), ("ENERGY / 64 SAMPLES", str(sum(x*x for x in block))), ("RMS / FULL SCALE", f"{rms:.5f}"))):
            y = 290 + i * 82
            d.text((815, y), label, fill=muted, font=font(11))
            d.text((815, y+20), value, fill=ink, font=font(29, True))
        d.text((42, 610), "EXPORTED REFERENCE SIMULATION / NO PHYSICAL FPGA CONNECTED", fill=muted, font=font(13))
        status = validation()["status"]
        d.text((42, 639), "RTL evidence: " + status.replace("_", " "), fill=muted, font=font(12))
        frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE, colors=64))
    folder = ROOT / "docs/graphics"; folder.mkdir(exist_ok=True)
    path = folder / "audio-core-trace.gif"
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
    frames[0].convert("RGB").save(folder / "audio-core-trace.png")
    print(f"Generated {len(frames)} reference frames: {path.name}, {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
