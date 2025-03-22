from pathlib import Path

import yaml

CONFIG = yaml.safe_load(Path("configs/summarizer.yaml").read_text())
GPT_MODEL = "gpt-4o-2024-08-06"
