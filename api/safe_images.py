"""Decodificación acotada de medallas; no abre plugins ajenos a los formatos admitidos."""
import io
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 8_000_000


async def read_bounded(file):
    data = bytearray()
    try:
        while chunk := await file.read(64 * 1024):
            if len(data) + len(chunk) > MAX_BYTES:
                raise HTTPException(413, "La imagen excede el límite de 10 MB")
            data.extend(chunk)
    finally:
        await file.close()
    return bytes(data)


def resize_image_to_256(data):
    try:
        with Image.open(io.BytesIO(data), formats=["PNG", "JPEG", "WEBP", "BMP", "GIF"]) as image:
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
                raise ValueError("Dimensiones de imagen no permitidas")
            image.load()
            resized = image.convert("RGBA").resize((256, 256), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            resized.save(output, format="PNG")
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("El archivo no es una imagen válida o excede sus dimensiones") from exc
