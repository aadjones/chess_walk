#!/usr/bin/env python3

import os
import glob
import json
import logging

from dotenv import load_dotenv
from openai import OpenAI, APIError

from parameters import GPT_MODEL

# Load .env into environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Ensure API key is available
if not os.getenv("OPENAI_API_KEY"):
    logging.error("OPENAI_API_KEY not set — please add it to your .env file")
    exit(1)

client = OpenAI()  # reads OPENAI_API_KEY from env

def load_summaries(directory="summaries") -> str:
    summaries = []
    for path in glob.glob(os.path.join(directory, "*.json")):
        logging.info(f"Loading {path}")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Failed to read {path}: {e}")
            continue
        summaries.append(data.get("summary", json.dumps(data)))
    return "\n\n".join(summaries)

def generate_concise_summary(text: str) -> str:
    system = "You are a summarizer. Return only a markdown summary of the folder's purpose."
    resp = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role":"system","content":system}, {"role":"user","content":text}],
        temperature=0.0,
    )
    return resp.choices[0].message.content.strip()

def generate_mermaid_diagram(text: str) -> str:
    system = """
You are an expert at creating high‑level Mermaid flowcharts.
Group related functions into subgraphs named API Layer, Divergence Analysis, Walker Pipeline, Utilities.
Use only function names (no file paths), and draw arrows for import/function dependencies.
Return only the Mermaid code.
"""
    resp = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role":"system","content":system}, {"role":"user","content":text}],
        temperature=0.0,
    )
    return resp.choices[0].message.content.strip()


def generate_folder_summary(summary_md: str, diagram_mmd: str) -> str:
    system = (
        "Using the folder's summary and its Mermaid diagram code, "
        "produce one combined high-level Markdown summary that explains the folder's purpose "
        "and how all components fit together."
    )
    prompt = f"Concise summary:\n{summary_md}\n\nMermaid diagram code:\n{diagram_mmd}"
    resp = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role":"system","content":system}, {"role":"user","content":prompt}],
        temperature=0.0,
    )
    return resp.choices[0].message.content.strip()

if __name__ == "__main__":
    combined = load_summaries()

    logging.info("Generating concise.md…")
    summary = generate_concise_summary(combined)
    with open("concise.md", "w") as f:
        f.write(summary + "\n")

    logging.info("Generating summary.mmd…")
    diagram = generate_mermaid_diagram(combined)
    with open("summary.mmd", "w") as f:
        f.write(diagram + "\n")

    logging.info("Generating src_summary.md…")
    combined_summary = generate_folder_summary(summary, diagram)
    with open("src_summary.md", "w", encoding="utf-8") as f:
        f.write(combined_summary + "\n")

    logging.info("✅ concise.md, summary.mmd, and src_summary.md created.")

