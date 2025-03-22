import glob
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from summarizer.config import CONFIG, GPT_MODEL

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,  # Change to logging.DEBUG to see more detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Load environment variables (e.g., OPENAI_API_KEY) from .env
load_dotenv()

logger = logging.getLogger(__name__)
client = OpenAI()

SYSTEM_PRELIMINARY = """
You are a summarizer. Return only a markdown summary of the folder's purpose.
"""

SYSTEM_MERMAID = """
You are an expert at creating high-level Mermaid flowcharts.
Group related functions into subgraphs.
Use only function names (no file paths), and draw arrows for import/function dependencies.
Return only the Mermaid code.
"""

SYSTEM_COMBINED = """
Using the folder's preliminary summary and its Mermaid diagram code, 
produce one combined high-level Markdown summary that explains the folder's purpose 
and how all components fit together.
"""


def load_summaries():
    logger.info("Loading summaries from JSON files")
    texts = []
    for path in glob.glob(f"{CONFIG['paths']['summaries_dir']}/*.json"):
        logger.debug(f"Reading summary file: {path}")
        data = json.load(open(path, "r"))
        texts.append(data.get("summary", json.dumps(data)))
    logger.info(f"Loaded {len(texts)} summary files")
    return "\n\n".join(texts)


def call_llm(system: str, user: str) -> str:
    logger.info("Making LLM API call")
    logger.debug(f"System prompt: {system[:100]}...")
    logger.debug(f"User prompt length: {len(user)} characters")
    resp = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.0,
    )
    logger.debug("Received response from LLM")
    return resp.choices[0].message.content.strip()


def main():
    logger.info("Starting aggregation process")
    combined = load_summaries()

    reports = Path(CONFIG["paths"]["reports_dir"])
    reports.mkdir(exist_ok=True)
    logger.info(f"Created/verified reports directory: {reports}")

    dir_name = Path(CONFIG["paths"]["src_dir"]).name

    logger.info("Generating preliminary summary")
    preliminary = call_llm(SYSTEM_PRELIMINARY, combined)

    logger.info("Generating Mermaid diagram")
    mermaid = call_llm(SYSTEM_MERMAID, combined)
    (reports / f"{dir_name}_flow.mmd").write_text(mermaid + "\n")
    logger.debug("Wrote Mermaid diagram to file")

    logger.info("Generating combined summary")
    combined = call_llm(SYSTEM_COMBINED, f"{preliminary}\n\n{mermaid}")
    (reports / f"{dir_name}_summary.md").write_text(combined + "\n")
    logger.debug("Wrote combined summary to file")

    logger.info("Aggregation process completed successfully")


if __name__ == "__main__":
    main()
