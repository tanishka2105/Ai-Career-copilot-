from PIL import Image, ImageDraw

for size in (192, 512):
    img = Image.new("RGB", (size, size), "#6d4aff")
    d = ImageDraw.Draw(img)
    d.ellipse((size * 0.22, size * 0.22, size * 0.78, size * 0.78), outline="white", width=size // 14)
    img.save(f"frontend/icon-{size}.png")
print("icons ban gaye")