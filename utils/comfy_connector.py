import json
import urllib.request
import urllib.error


def send_to_comfy(status_text):
    try:
        with open("Data/workflow_api.json", "r") as f:
            workflow = json.load(f)

        # Безопасный поиск и замена текста
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                inputs = node_data.get("inputs", {})

                # Ищем ноды генерации текста
                if "CLIPTextEncode" in class_type or "Lumina" in class_type:
                    if "text" in inputs and isinstance(inputs["text"], str):
                        inputs["text"] = f"STATUS: {status_text}"
                    elif "user_prompt" in inputs and isinstance(inputs["user_prompt"], str):
                        inputs["user_prompt"] = f"STATUS: {status_text}"

        p = {"prompt": workflow}
        data = json.dumps(p).encode('utf-8')

        req = urllib.request.Request("http://127.0.0.1:8000/prompt", data=data)
        req.add_header("Content-Type", "application/json")

        urllib.request.urlopen(req)
        print(f"🎨 ComfyUI обновил экран: {status_text}")

    except urllib.error.HTTPError as e:
        # Если ComfyUI вернул ошибку, читаем её содержимое!
        error_body = e.read().decode('utf-8')
        print(f"❌ Ошибка 500! ComfyUI жалуется на: {error_body}")
    except Exception as e:
        print(f"❌ Ошибка соединения с ComfyUI: {e}")