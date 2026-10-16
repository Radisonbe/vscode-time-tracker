import json
with open("process_settings.json", "r", encoding="utf-8") as file:
    settings = json.load(file)
print(settings["tracked_exe"])
print(type(settings["tracked_exe"]))