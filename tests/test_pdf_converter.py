import base64
from pathlib import Path

from ocr_eval.pipeline.pdf_converter import pdf_to_base64_images
from ocr_eval.sample.generate_invoice import generate_sample_invoice


def test_pdf_to_base64(tmp_path):
    pdf_path, _ = generate_sample_invoice(tmp_path)
    images = pdf_to_base64_images(pdf_path)
    assert len(images) == 1

    prefix = "data:image/png;base64,"
    assert images[0].startswith(prefix)

    img_bytes = base64.b64decode(images[0][len(prefix):])
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"
