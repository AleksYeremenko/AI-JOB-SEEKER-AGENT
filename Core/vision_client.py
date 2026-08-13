import base64
import requests
import json

class OmniParserClient:
    def __init__(self, host="http://localhost:8000"):
        self.host = host
        self.parse_endpoint = f"{self.host}/parse"

    def parse_screenshot(self, image_path: str):
        """
        Sends a screenshot to the local OmniParser server and returns:
        - parsed_content (string map of icons and their text/labels)
        - image_base64 (the annotated image with red boxes)
        """
        try:
            with open(image_path, "rb") as f:
                files = {"file": f}
                response = requests.post(self.parse_endpoint, files=files)
            
            response.raise_for_status()
            data = response.json()
            return data["parsed_content"], data["image_base64"]
        except Exception as e:
            print(f"Failed to connect to OmniParser: {e}")
            return None, None

# Example usage for your InteractiveApplier:
if __name__ == "__main__":
    client = OmniParserClient()
    image_path = "AIjobseekerTest.png"
    parsed_content, image_with_boxes = client.parse_screenshot(image_path)
    print("OmniParser found these elements:")
    print(parsed_content)
    # 
    # Now send `parsed_content` to Ollama and ask: 
    # "Which icon ID should I click to enter the salary expectation?"
