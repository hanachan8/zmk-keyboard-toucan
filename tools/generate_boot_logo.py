from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


FRAME_W = 96
FRAME_H = 96
OUTPUT_FRAMES = 5


def crop_logo(source: Image.Image) -> Image.Image:
    rgb = source.convert("RGB")
    mask = Image.new("1", rgb.size)
    pixels = mask.load()
    source_pixels = rgb.load()

    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = source_pixels[x, y]
            pixels[x, y] = 1 if max(r, g, b) >= 160 else 0

    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("No bright logo pixels found in the source image")

    return mask.crop(bbox)


def fit_logo(mask: Image.Image) -> Image.Image:
    target = Image.new("1", (FRAME_W, FRAME_H), 0)
    scale = min(92 / mask.width, 92 / mask.height)
    resized = mask.resize(
        (max(1, round(mask.width * scale)), max(1, round(mask.height * scale))),
        Image.Resampling.NEAREST,
    )
    target.paste(
        resized,
        ((FRAME_W - resized.width) // 2, (FRAME_H - resized.height) // 2),
    )
    return target


def horizontal_fragments(frame_index: int) -> list[tuple[int, int, int]]:
    """Return (y, height, horizontal offset) bands for each reveal frame."""
    return [
        [(18, 2, -3), (39, 2, 2), (59, 2, -2), (81, 2, 3)],
        [(10, 4, 2), (21, 5, -3), (34, 5, 1), (47, 4, -2),
         (58, 6, 3), (71, 5, -1), (85, 4, 2)],
        [(5, 7, 0), (17, 7, -2), (29, 8, 1), (42, 7, 0),
         (54, 8, 2), (67, 8, -1), (82, 8, 0)],
        [(0, FRAME_H, 0)],
        [(0, FRAME_H, 0)],
    ][frame_index]


def make_frame(logo: Image.Image, frame_index: int) -> Image.Image:
    frame = Image.new("1", logo.size, 0)
    for y, height, offset in horizontal_fragments(frame_index):
        band = logo.crop((0, y, logo.width, min(y + height, logo.height)))
        frame.paste(band, (offset, y))

    if frame_index == 3:
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 25, FRAME_W - 1, 26), fill=0)
        draw.rectangle((0, 66, FRAME_W - 1, 67), fill=0)
        shifted = logo.crop((0, 44, FRAME_W, 48))
        draw.rectangle((0, 44, FRAME_W - 1, 47), fill=0)
        frame.paste(shifted, (2, 44))

    return frame


def lvgl_indexed_1bit_data(image: Image.Image) -> bytes:
    # LVGL indexed images start with two BGRA palette entries.
    data = bytearray(
        [
            0x00, 0x00, 0x00, 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF,
        ]
    )
    width_bytes = (image.width + 7) // 8
    pixels = image.load()

    for y in range(image.height):
        row = bytearray(width_bytes)
        for x in range(image.width):
            if pixels[x, y]:
                row[x // 8] |= 0x80 >> (x % 8)
        data.extend(row)

    return bytes(data)


def format_bytes(data: bytes) -> str:
    lines = []
    for start in range(0, len(data), 12):
        chunk = data[start:start + 12]
        lines.append("    " + ", ".join(f"0x{value:02x}" for value in chunk) + ",")
    return "\n".join(lines)


def write_c_file(frames: list[Image.Image], destination: Path) -> None:
    parts = [
        "#include <lvgl.h>",
        "",
        "#ifndef LV_ATTRIBUTE_IMG_BOOT_LOGO",
        "#define LV_ATTRIBUTE_IMG_BOOT_LOGO",
        "#endif",
        "",
    ]

    for index, frame in enumerate(frames):
        data = lvgl_indexed_1bit_data(frame)
        parts.extend(
            [
                (
                    "const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST "
                    f"LV_ATTRIBUTE_IMG_BOOT_LOGO uint8_t boot_logo_{index}_map[] = {{"
                ),
                format_bytes(data),
                "};",
                "",
                f"const lv_img_dsc_t boot_logo_{index} = {{",
                "    .header.cf = LV_IMG_CF_INDEXED_1BIT,",
                "    .header.always_zero = 0,",
                "    .header.reserved = 0,",
                f"    .header.w = {frame.width},",
                f"    .header.h = {frame.height},",
                f"    .data_size = {len(data)},",
                f"    .data = boot_logo_{index}_map,",
                "};",
                "",
            ]
        )

    destination.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--assets-dir", type=Path, required=True)
    args = parser.parse_args()

    args.assets_dir.mkdir(parents=True, exist_ok=True)
    logo = fit_logo(crop_logo(Image.open(args.source)))
    frames = [make_frame(logo, index) for index in range(OUTPUT_FRAMES)]

    logo.save(args.assets_dir / "boot_logo_master.png")
    for index, frame in enumerate(frames):
        frame.save(args.assets_dir / f"boot_logo_{index}.png")

    write_c_file(frames, args.assets_dir / "boot_logo.c")


if __name__ == "__main__":
    main()
