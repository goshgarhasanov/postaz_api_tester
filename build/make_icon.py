"""Export the painted app icon to a multi-resolution .ico file.

Run once during a build — `build/postaz.ico` is what PyInstaller and the
Inno Setup script consume as the Windows-native icon."""
from __future__ import annotations

import sys
from pathlib import Path

# Make the project root importable so we can pull in the painter.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from app.ui.icons import app_icon


def main() -> int:
    # QPainter needs a QGuiApplication, even for off-screen rendering.
    app = QApplication.instance() or QApplication(sys.argv)
    out = Path(__file__).parent / "postaz.ico"

    icon = app_icon(256)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        pm = icon.pixmap(QSize(s, s))
        images.append(pm.toImage().convertToFormat(QImage.Format_ARGB32))

    # Pillow knows how to write multi-frame .ico — fall back to a single
    # 256x256 PNG-in-ICO if Pillow isn't present.
    try:
        from PIL import Image
    except ImportError:
        # Save the biggest size as PNG and rename so the file at least exists.
        images[-1].save(str(out.with_suffix(".png")), "PNG")
        print(f"Pillow not installed; wrote PNG to {out.with_suffix('.png')}")
        return 0

    pil_images = []
    for img in images:
        buf = bytes(img.constBits())
        pil = Image.frombuffer("RGBA", (img.width(), img.height()), buf, "raw", "BGRA", 0, 1)
        pil_images.append(pil.copy())

    biggest = pil_images[-1]
    biggest.save(
        out,
        format="ICO",
        sizes=[(im.width, im.height) for im in pil_images],
        append_images=pil_images[:-1],
    )
    print(f"wrote {out} ({len(pil_images)} sizes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
