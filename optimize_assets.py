import os
import re
from PIL import Image

def minify_css(css):
    # Remove comments
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    # Remove whitespace around operators and brackets
    css = re.sub(r'\s*([\{\};:\,])\s*', r'\1', css)
    # Remove unnecessary spaces
    css = re.sub(r'\s+', ' ', css)
    # Remove last semicolon in block
    css = re.sub(r';\}', '}', css)
    return css.strip()

def minify_js(js):
    # Remove single line comments
    js = re.sub(r'//.*?\n', '\n', js)
    # Remove multi-line comments
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
    # Replace multiple spaces/newlines with single space
    js = re.sub(r'\s+', ' ', js)
    return js.strip()

def optimize_images():
    img_dir = 'static/images'
    images_to_convert = ['hero_bg.png', 'logo.png', 'logo_icon.png']
    
    for img_name in images_to_convert:
        src_path = os.path.join(img_dir, img_name)
        if os.path.exists(src_path):
            dest_name = os.path.splitext(img_name)[0] + '.webp'
            dest_path = os.path.join(img_dir, dest_name)
            print(f"Converting {src_path} to {dest_path}...")
            try:
                with Image.open(src_path) as img:
                    # Convert to RGB if it's RGBA and saving as WebP (WebP supports RGBA too, so we can keep it or convert depending on alpha channel)
                    img.save(dest_path, 'WEBP', quality=85)
                print(f"Successfully converted to WebP: {dest_path}")
            except Exception as e:
                print(f"Error converting {img_name}: {e}")
        else:
            print(f"Source image not found: {src_path}")

def main():
    print("=== Optimizing Static Assets ===")
    
    # 1. Minify CSS
    css_path = 'static/css/style.css'
    min_css_path = 'static/css/style.min.css'
    if os.path.exists(css_path):
        print(f"Minifying {css_path}...")
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        minified_css = minify_css(css_content)
        with open(min_css_path, 'w', encoding='utf-8') as f:
            f.write(minified_css)
        print(f"CSS Minified successfully. Size reduced from {os.path.getsize(css_path)} to {os.path.getsize(min_css_path)} bytes.")
        
    # 2. Minify JS
    js_path = 'static/js/app.js'
    min_js_path = 'static/js/app.min.js'
    if os.path.exists(js_path):
        print(f"Minifying {js_path}...")
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        minified_js = minify_js(js_content)
        with open(min_js_path, 'w', encoding='utf-8') as f:
            f.write(minified_js)
        print(f"JS Minified successfully. Size reduced from {os.path.getsize(js_path)} to {os.path.getsize(min_js_path)} bytes.")
        
    # 3. Optimize Images
    optimize_images()
    
    print("=== Optimization Complete ===")

if __name__ == '__main__':
    main()
