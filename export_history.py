import json
import os

input_file = r"C:\Users\yerem\.gemini\antigravity-cli\brain\79f80ec1-1899-40c9-8c47-671bad9cbc34\.system_generated\logs\transcript_full.jsonl"
output_file = r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\FULL_HISTORY.md"

if not os.path.exists(input_file):
    print(f"Error: Transcript file not found at {input_file}")
    import sys
    sys.exit(1)

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(output_file, 'w', encoding='utf-8') as out:
    out.write("# Полная история сообщений и сгенерированного кода\n\n")
    out.write("Это автоматически сгенерированный транскрипт всей нашей текущей сессии.\n\n---\n\n")
    
    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except:
            continue
            
        step_type = data.get("type", "")
        
        if step_type == "USER_INPUT":
            out.write("## 👤 ЮЗЕР (USER)\n\n")
            out.write(data.get("content", "") + "\n\n")
            out.write("---\n\n")
            
        elif step_type == "PLANNER_RESPONSE":
            out.write("## 🤖 АГЕНТ (AI)\n\n")
            
            # Text response to user
            content = data.get("content", "")
            if content:
                out.write("### Ответ:\n")
                out.write(content + "\n\n")
            
            # Tool calls containing the code
            tool_calls = data.get("tool_calls", [])
            if tool_calls:
                out.write("### Выполненные действия и сгенерированный код:\n")
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            args = {}
                            
                    out.write(f"**Инструмент:** `{name}`\n")
                    
                    if "TargetFile" in args:
                        out.write(f"**Файл:** `{args['TargetFile']}`\n\n")
                        
                    if "CodeContent" in args:
                        out.write("```python\n" + str(args["CodeContent"]) + "\n```\n")
                    elif "ReplacementContent" in args:
                        out.write("```python\n" + str(args["ReplacementContent"]) + "\n```\n")
                    elif "CommandLine" in args:
                        out.write("```bash\n" + str(args["CommandLine"]) + "\n```\n")
                        
                out.write("\n")
            out.write("---\n\n")

print("✅ FULL_HISTORY.md generated successfully!")
