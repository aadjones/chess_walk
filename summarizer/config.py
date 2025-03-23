from pathlib import Path

import yaml

CONFIG = yaml.safe_load(Path("configs/summarizer.yaml").read_text())
PRELIMINARY_MODEL = "gpt-4o-mini"
MAIN_MODEL = "gpt-4o"
