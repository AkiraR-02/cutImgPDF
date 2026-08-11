import os
from PIL import Image, ImageDraw, ImageFont

def generate_tall_code_screenshot(filename, width=800, height=2500):
    """
    Programmatically creates a tall image simulating a VS Code screenshot with code,
    syntax coloring, and line numbers to test the dynamic splitting logic.
    """
    # Create image with VS Code dark theme background
    bg_color = (30, 30, 30) # #1E1E1E
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to load default font
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
        
    # Draw a line numbers column bar
    draw.rectangle([(0, 0), (60, height)], fill=(40, 40, 40))
    # Border line for the column bar
    draw.line([(60, 0), (60, height)], fill=(60, 60, 60), width=1)
    
    # Generate some code-like lines
    colors = {
        'keyword': (86, 156, 214),   # Blue
        'comment': (106, 153, 85),   # Green
        'string': (206, 145, 120),   # Peach/Orange
        'func': (220, 220, 170),     # Light Yellow
        'text': (212, 212, 212),     # Light Grey
        'indent': (60, 60, 60)       # Guide line
    }
    
    code_templates = [
        ("import os", "keyword"),
        ("import sys", "keyword"),
        ("from PIL import Image", "keyword"),
        ("", "text"),
        ("# This is a very long code screenshot used to test pdf splitting", "comment"),
        ("def process_image_splitting(img_path, page_height):", "func"),
        ("    \"\"\"", "string"),
        ("    La lógica matemática calcula la escala y corta horizontalmente.", "string"),
        ("    \"\"\"", "string"),
        ("    scale = width / img.width", "text"),
        ("    h_scaled = img.height * scale", "text"),
        ("    if h_scaled <= page_height:", "keyword"),
        ("        print('Image fits completely')", "string"),
        ("        return [img]", "keyword"),
        ("    ", "text"),
        ("    slices = []", "text"),
        ("    d = 0.0", "text"),
        ("    while d < h_scaled:", "keyword"),
        ("        h_slice = min(page_height, h_scaled - d)", "text"),
        ("        y_start = d / scale", "text"),
        ("        y_end = (d + h_slice) / scale", "text"),
        ("        slice_img = img.crop((0, int(y_start), img.width, int(y_end)))", "text"),
        ("        slices.append(slice_img)", "text"),
        ("        d += h_slice", "text"),
        ("    return slices", "keyword"),
        ("", "text"),
        ("def main_execution_loop():", "func"),
        ("    print('Starting automated document assembly')", "string"),
        ("    config = load_json('config.json')", "text"),
        ("    for item in config:", "keyword"),
        ("        if item['type'] == 'image':", "keyword"),
        ("            add_image(item['path'])", "text"),
        ("        elif item['type'] == 'title':", "keyword"),
        ("            add_title(item['text'])", "text"),
        ("    print('Done generating document')", "string"),
        ("", "text"),
    ]
    
    y = 20
    line_number = 1
    
    # Loop to fill the entire height
    while y < height - 30:
        # Draw line number
        draw.text((15, y), str(line_number), fill=(128, 128, 128), font=font)
        
        # Select a template line
        template_idx = (line_number - 1) % len(code_templates)
        code_text, token_type = code_templates[template_idx]
        
        # Draw text indent guidelines if any
        indent_level = len(code_text) - len(code_text.lstrip(' '))
        for lvl in range(4, indent_level + 1, 4):
            guide_x = 75 + (lvl * 6)
            draw.line([(guide_x, y), (guide_x, y + 14)], fill=colors['indent'], width=1)
            
        # Draw code line
        draw.text((80, y), code_text, fill=colors[token_type], font=font)
        
        y += 18
        line_number += 1
        
    # Save the generated image
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)
    print(f"Generated tall screenshot: {filename} ({width}x{height} px)")

def generate_standard_image(filename, width=400, height=300, bg_color=(20, 80, 120), text="Demo"):
    """Creates a standard dimension image to test regular insertion."""
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
        
    draw.text((width // 4, height // 2), text, fill=(255, 255, 255), font=font)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)
    print(f"Generated standard image: {filename} ({width}x{height} px)")

if __name__ == "__main__":
    # Generate assets in the test_assets folder
    generate_tall_code_screenshot("test_assets/tall_code.png", width=800, height=2500)
    generate_standard_image("test_assets/standard1.png", width=400, height=300, bg_color=(76, 175, 80), text="Imagen Izquierda")
    generate_standard_image("test_assets/standard2.png", width=400, height=300, bg_color=(156, 39, 176), text="Imagen Derecha")
    generate_standard_image("test_assets/regular_screenshot.png", width=1200, height=800, bg_color=(33, 33, 33), text="Captura de Pantalla Normal")
