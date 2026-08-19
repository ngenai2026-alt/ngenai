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
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                    images.append(file)
            
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
