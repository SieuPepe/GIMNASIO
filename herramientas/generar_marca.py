"""Regenera las variantes del logotipo a partir del original.

    python herramientas/generar_marca.py

Lee assets/marca/kevin-logo.png (en color y con fondo transparente) y produce
la versión en blanco, el símbolo suelto y el icono de Windows. Hay que
ejecutarlo cada vez que cambie el logotipo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MARCA = Path(__file__).resolve().parents[1] / "assets" / "marca"
ORIGEN = MARCA / "kevin-logo.png"
TAMANOS_ICONO = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def en_blanco(imagen):
    """Mismo dibujo, todo blanco: conserva la silueta y cambia el color."""
    from PIL import Image
    blanco = Image.new("RGBA", imagen.size, (255, 255, 255, 0))
    blanco.putalpha(imagen.getchannel("A"))
    return blanco


def separar_simbolo(imagen):
    """Recorta el símbolo buscando el hueco vertical que lo separa del texto."""
    alfa = imagen.getchannel("A")
    con_dibujo = [y for y in range(imagen.height)
                  if any(alfa.getpixel((x, y)) > 40 for x in range(0, imagen.width, 3))]
    if not con_dibujo:
        return imagen
    corte, anterior = imagen.height, con_dibujo[0]
    for y in con_dibujo[1:]:
        if y - anterior > 12:
            corte = y
            break
        anterior = y
    arriba = imagen.crop((0, 0, imagen.width, corte))
    caja = arriba.getchannel("A").getbbox()
    return arriba.crop(caja) if caja else arriba


def main() -> int:
    try:
        from PIL import Image
    except ImportError:
        print("Hace falta Pillow:  pip install pillow")
        return 1
    if not ORIGEN.exists():
        print(f"No encuentro {ORIGEN}")
        return 1

    logo = Image.open(ORIGEN).convert("RGBA")
    if logo.getchannel("A").getextrema()[0] == 255:
        print("Aviso: el original no tiene transparencia. En las cabeceras de los "
              "PDF recortará un rectángulo de fondo.")

    en_blanco(logo).save(MARCA / "kevin-logo-blanco.png")
    simbolo = separar_simbolo(logo)
    simbolo.save(MARCA / "kevin-iso.png")
    en_blanco(simbolo).save(MARCA / "kevin-iso-blanco.png")

    lado = max(simbolo.size)
    cuadrado = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    cuadrado.paste(simbolo, ((lado - simbolo.width) // 2, (lado - simbolo.height) // 2))
    margen = int(lado * 0.06)
    lienzo = Image.new("RGBA", (lado + margen * 2, lado + margen * 2), (0, 0, 0, 0))
    lienzo.paste(cuadrado, (margen, margen))
    lienzo.save(MARCA / "kevin.ico", sizes=TAMANOS_ICONO)

    for fichero in ("kevin-logo-blanco.png", "kevin-iso.png",
                    "kevin-iso-blanco.png", "kevin.ico"):
        print(f"   {fichero}")
    print("\nVariantes regeneradas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
