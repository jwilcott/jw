import os
from PIL import Image
import math

folder = r"H:\Shared drives\Roblox Creative Studio\Projects\Social3D\NFL\Logos"

images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
images.sort()  # sort alphabetically

num_images = len(images)
print(f"Found {num_images} images")

cols = 4
rows = math.ceil(num_images / cols)

# Assume all images are 500x500
img_width, img_height = 500, 500
padding = 20
cell_width = img_width + 2 * padding
cell_height = img_height + 2 * padding
total_width = cols * cell_width
total_height = rows * cell_height

combined = Image.new('RGB', (total_width, total_height), (0, 0, 0))  # black background

for i, img_name in enumerate(images):
    img_path = os.path.join(folder, img_name)
    img = Image.open(img_path)
    col = i % cols
    row = i // cols
    x = col * cell_width + padding
    y = row * cell_height + padding
    combined.paste(img, (x, y))

output_path = os.path.join(folder, "NFL_Logos_Grid.jpg")
combined.save(output_path, 'JPEG', quality=95)

print(f"Saved combined image to {output_path}")