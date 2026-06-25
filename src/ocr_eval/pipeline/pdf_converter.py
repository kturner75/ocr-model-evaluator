import base64
import io
from pathlib import Path

import pymupdf


def pdf_to_base64_images(pdf_path: Path, dpi: int = 200) -> list[str]:
    doc = pymupdf.open(str(pdf_path))
    images = []
    zoom = dpi / 72
    matrix = pymupdf.Matrix(zoom, zoom)

    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        images.append(f"data:image/png;base64,{b64}")

    doc.close()
    return images
