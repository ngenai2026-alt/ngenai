import os
import json

def generate_gallery_data():
    gallery_dir = "workshops_gallery"
    output_file = "gallery_data.js"
    
    if not os.path.exists(gallery_dir):
        print(f"Directory {gallery_dir} does not exist.")
        return
        
    gallery_items = []
    
    # List subfolders
    for item in sorted(os.listdir(gallery_dir)):
        item_path = os.path.join(gallery_dir, item)
        if os.path.isdir(item_path) and not item.startswith("."):
            # Scan images inside subfolder
            images = []
            for file in sorted(os.listdir(item_path)):
                lower_file = file.lower()
                if lower_file.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                    images.append(file)
                elif lower_file.endswith('.heic'):
                    heic_path = os.path.join(item_path, file)
                    jpg_filename = file[:-5] + ".jpg"
                    jpg_path = os.path.join(item_path, jpg_filename)
                    if not os.path.exists(jpg_path):
                        print(f"Converting {file} to JPEG for browser compatibility...")
                        try:
                            try:
                                import pillow_heif
                                from PIL import Image
                            except ImportError:
                                import subprocess
                                import sys
                                print("Installing pillow-heif and pillow for HEIC support...")
                                subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow-heif", "pillow"])
                                import pillow_heif
                                from PIL import Image
                            
                            heif_file = pillow_heif.read_heif(heic_path)
                            image = Image.frombytes(
                                heif_file.mode,
                                heif_file.size,
                                heif_file.data,
                                "raw",
                            )
                            image.save(jpg_path, "JPEG", quality=90)
                            print(f"Successfully converted {file} -> {jpg_filename}")
                        except Exception as e:
                            print(f"Failed to convert {file}: {e}")
                            continue
                    
                    if os.path.exists(jpg_path):
                        images.append(jpg_filename)
            
            if images:
                for img in images:
                    gallery_items.append({
                        "src": f"workshops_gallery/{item}/{img}",
                        "category": item.lower().replace(" ", "-").replace("/", "-"),
                        "categoryTitle": item,
                        "caption": f"{item} Workshop Session"
                    })
                    
    # Write to gallery_data.js
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("// Pre-compiled gallery data for production environment\n")
        f.write(f"const GALLERY_DATA = {json.dumps(gallery_items, indent=2)};\n")
        
    print(f"Successfully compiled {len(gallery_items)} images into {output_file}")

if __name__ == "__main__":
    generate_gallery_data()
