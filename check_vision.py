import os
import glob
import json
import ast
from Core.vision_client import OmniParserClient

import sys

def main():
    if len(sys.argv) > 1:
        latest_screenshot = sys.argv[1]
        print(f"Analyzing specified screenshot: {latest_screenshot}")
    else:
        # Находим самый свежий скриншот
        screenshots = glob.glob('Data/screenshots/*.png')
        if not screenshots:
            print("❌ Скриншоты не найдены в Data/screenshots/")
            return
        latest_screenshot = max(screenshots, key=os.path.getctime)
        print(f"Analyzing latest screenshot: {latest_screenshot}")
    
    print("Waiting for OmniParser...")
    client = OmniParserClient()
    parsed_str, image_b64 = client.parse_screenshot(latest_screenshot)
    
    # Парсим ответ
    parsed_content = {}
    for line in parsed_str.strip().split('\n'):
        if ': ' in line:
            key, val_str = line.split(': ', 1)
            try:
                parsed_content[key.strip()] = ast.literal_eval(val_str.strip())
            except:
                pass
                
    # Сохраняем в красивый JSON
    output_file = "vision_debug.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # Сохраним отфильтрованный вариант для удобства чтения
        clean = {k: v for k, v in parsed_content.items() if v.get('type') == 'text' or v.get('interactivity')}
        json.dump(clean, f, ensure_ascii=False, indent=2)
        
    print(f"Done! Results saved to: {output_file}")
    print("Open it in VSCode and press Ctrl+F to search for 'Apply'.")

if __name__ == "__main__":
    main()
