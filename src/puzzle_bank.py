import json
import os
from pathlib import Path
from src.logger import logger


def add_puzzle(puzzle, filename="output/puzzles.json"):
    """
    Adds a single puzzle to the puzzle bank file. Creates the file if it doesn't exist.
    
    Args:
        puzzle (dict): The puzzle data to add
        filename (str): Path to the puzzle bank JSON file
    """
    try:
        puzzles = []
        file_path = Path(filename)
        os.makedirs(file_path.parent, exist_ok=True)  # Ensure directory exists
        
        if file_path.exists():
            logger.debug(f"Reading existing puzzles from {filename}")
            with open(file_path, "r") as f:
                puzzles = json.load(f)
                
        puzzles.append(puzzle)
        logger.debug(f"Writing {len(puzzles)} puzzles to {filename}")
        
        with open(file_path, "w") as f:
            json.dump(puzzles, f, indent=2)
            
        logger.info(f"Added puzzle to {filename} (total: {len(puzzles)})")
    except Exception as e:
        logger.error(f"Error adding puzzle to {filename}: {e}")

def save_bank(puzzles, filename="output/puzzles.json"):
    """
    Saves a collection of puzzles to the puzzle bank file, overwriting any existing file.
    
    Args:
        puzzles (list): List of puzzle data dictionaries
        filename (str): Path to the puzzle bank JSON file
    """
    try:
        file_path = Path(filename)
        os.makedirs(file_path.parent, exist_ok=True)  # Ensure directory exists
        
        logger.debug(f"Writing {len(puzzles)} puzzles to {filename}")
        with open(file_path, "w") as f:
            json.dump(puzzles, f, indent=2)
            
        logger.info(f"Saved {len(puzzles)} puzzles to {filename}")
    except Exception as e:
        logger.error(f"Error saving puzzles to {filename}: {e}")