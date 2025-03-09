import json
import chess
import chess.pgn

def calculate_ply_from_fen(fen):
    # Split the FEN into its 6 fields
    fields = fen.split()
    if len(fields) != 6:
        raise ValueError(f"Invalid FEN: {fen}")

    # Extract active color (field 1) and fullmove number (field 5)
    active_color = fields[1]  # 'w' or 'b'
    fullmove_number = int(fields[5])  # e.g., 10

    # Calculate ply
    if active_color == 'w':
        ply = (fullmove_number - 1) * 2
    else:  # active_color == 'b'
        ply = (fullmove_number - 1) * 2 + 1

    return ply

def generate_pgn(puzzle_file, output_pgn="output/puzzles.pgn"):
    # Read the puzzles from JSON
    with open(puzzle_file, "r") as f:
        puzzles = json.load(f)

    # Open the output PGN file
    with open(output_pgn, "w") as f:
        for i, puzzle in enumerate(puzzles):
            # Create a new game for each FEN
            game = chess.pgn.Game()
            
            # Calculate ply from FEN
            try:
                ply = calculate_ply_from_fen(puzzle["fen"])
            except (ValueError, KeyError) as e:
                print(f"Error calculating ply for puzzle {i+1}: {e}")
                ply = 0  # Fallback

            # Set minimal headers
            game.headers.clear()  # Remove default headers
            game.headers["Event"] = f"Puzzle {i+1} (Ply {ply})"
            game.headers["FEN"] = puzzle["fen"]
            game.headers["Result"] = "*"  # Set result without adding moves

            # Write the game to the PGN file with a blank line separator
            # Use the raw string representation to avoid move generation
            print(str(game).strip(), file=f, end="\n\n")

    print(f"Generated {output_pgn}. Import it into your Lichess study!")

if __name__ == "__main__":
    generate_pgn("output/puzzles.json")