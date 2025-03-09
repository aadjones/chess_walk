import json

import chess


def calculate_ply_from_fen(fen):
    fields = fen.split()
    if len(fields) != 6:
        raise ValueError(f"Invalid FEN: {fen}")
    active_color = fields[1]
    fullmove_number = int(fields[5])
    return (fullmove_number - 1) * 2 if active_color == "w" else (fullmove_number - 1) * 2 + 1


def get_active_color_from_fen(fen):
    fields = fen.split()
    if len(fields) != 6:
        raise ValueError(f"Invalid FEN: {fen}")
    return fields[1]


def convert_coordinate_to_algebraic(fen, coord_move):
    try:
        board = chess.Board(fen)
        from_square = chess.parse_square(coord_move[:2])
        to_square = chess.parse_square(coord_move[2:])
        move = chess.Move(from_square, to_square)
        if move in board.legal_moves:
            return board.san(move)
        return coord_move
    except (ValueError, KeyError):
        return coord_move


def generate_fen_viewer(puzzle_file, output_html="output/puzzles.html"):
    with open(puzzle_file, "r") as f:
        puzzles = json.load(f)

    fens = [puzzle["fen"] for puzzle in puzzles]
    chapter_names = [f"Puzzle {i+1} (Ply {calculate_ply_from_fen(puzzle['fen'])})" for i, puzzle in enumerate(puzzles)]

    # Get all moves and frequencies
    base_all_moves = [
        [convert_coordinate_to_algebraic(puzzle["fen"], move) for move in puzzle["base_top_moves"]]
        for puzzle in puzzles
    ]
    base_all_frequencies = [[round(freq, 2) for freq in puzzle["base_freqs"]] for puzzle in puzzles]
    target_all_moves = [
        [convert_coordinate_to_algebraic(puzzle["fen"], move) for move in puzzle["target_top_moves"]]
        for puzzle in puzzles
    ]
    target_all_frequencies = [[round(freq, 2) for freq in puzzle["target_freqs"]] for puzzle in puzzles]

    # Extract rating information from each puzzle
    base_ratings = [puzzle.get("base_rating", "1400") for puzzle in puzzles]
    target_ratings = [puzzle.get("target_rating", "1800") for puzzle in puzzles]

    with open(output_html, "w") as f:
        f.write(
            f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>FEN Viewer</title>
          <link rel="icon" type="image/x-icon" href="data:image/x-icon;base64,AAABAAEAEBAQAAAAAAAoAQAAFgAAACgAAAAQAAAAIAAAAAEABAAAAAAAgAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAA/4QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA">
          <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.min.js"></script>
          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.css" />
          <style>
            .board {{
              width: 400px;
              margin: 20px;
            }}
            button {{
              margin: 5px;
            }}
            #info {{
              margin-left: 20px;
              font-family: Arial, sans-serif;
            }}
            .tables-container {{
              display: flex;
              justify-content: space-between;
              align-items: stretch;
              width: 400px;
            }}
            .move-table {{
              flex: 1;
              border-collapse: collapse;
              margin: 5px;
              height: 100%;
            }}
            .move-table th, .move-table td {{
              border: 1px solid #ddd;
              padding: 4px;
              text-align: center;
            }}
            .move-table th {{
              background-color: #f2f2f2;
            }}
            /* Optional styling for the dropdown */
            #puzzleSelect {{
              margin: 5px;
              font-size: 14px;
            }}
          </style>
        </head>
        <body>
          <div id="board" class="board"></div>

          <!-- Buttons for previous/next -->
          <button onclick="prev()">Previous</button>
          <button onclick="next()">Next</button>

          <!-- NEW: Dropdown for direct puzzle selection -->
          <select id="puzzleSelect" onchange="selectPuzzle(this.value)">
          </select>

          <div id="info"></div>

          <script>
            let fens = {json.dumps(fens)};
            let names = {json.dumps(chapter_names)};
            let baseAllMoves = {json.dumps(base_all_moves)};
            let baseAllFrequencies = {json.dumps(base_all_frequencies)};
            let targetAllMoves = {json.dumps(target_all_moves)};
            let targetAllFrequencies = {json.dumps(target_all_frequencies)};
            let baseRatings = {json.dumps(base_ratings)};
            let targetRatings = {json.dumps(target_ratings)};
            let currentIndex = 0;

            const board = Chessboard('board', {{
              position: 'start',
              draggable: true,
              pieceTheme: '../img/chesspieces/wiki/{{piece}}.svg',
              width: 400
            }});

            // Populate the dropdown with puzzle options
            const puzzleSelect = document.getElementById("puzzleSelect");
            for (let i = 0; i < names.length; i++) {{
              let option = document.createElement("option");
              option.value = i;
              option.text = names[i];
              puzzleSelect.appendChild(option);
            }}

            function loadFEN(index) {{
              if (index >= 0 && index < fens.length) {{
                currentIndex = index;
                puzzleSelect.value = index; // keep dropdown in sync

                const activeColor = fens[index].split(' ')[1];
                board.orientation(activeColor === 'w' ? 'white' : 'black');
                board.position(fens[index]);

                // Generate HTML for base moves
                let baseMovesHtml = '';
                for (let i = 0; i < baseAllMoves[index].length; i++) {{
                  baseMovesHtml += `<tr><td>${{baseAllMoves[index][i]}}</td><td>${{(baseAllFrequencies[index][i] * 100).toFixed(0)}}%</td></tr>`;
                }}

                // Generate HTML for target moves
                let targetMovesHtml = '';
                for (let i = 0; i < targetAllMoves[index].length; i++) {{
                  targetMovesHtml += `<tr><td>${{targetAllMoves[index][i]}}</td><td>${{(targetAllFrequencies[index][i] * 100).toFixed(0)}}%</td></tr>`;
                }}

                document.getElementById('info').innerHTML = `
                  <strong>${{names[index]}}</strong>
                  <div class="tables-container">
                    <table class="move-table">
                      <thead>
                        <tr><th colspan="2">${{baseRatings[index]}}</th></tr>
                        <tr><th>Move</th><th>Freq</th></tr>
                      </thead>
                      <tbody>
                        ${{baseMovesHtml}}
                      </tbody>
                    </table>
                    <table class="move-table">
                      <thead>
                        <tr><th colspan="2">${{targetRatings[index]}}</th></tr>
                        <tr><th>Move</th><th>Freq</th></tr>
                      </thead>
                      <tbody>
                        ${{targetMovesHtml}}
                      </tbody>
                    </table>
                  </div>
                `;
              }}
            }}

            // Called when user picks a puzzle from the dropdown
            function selectPuzzle(value) {{
              const idx = parseInt(value, 10);
              loadFEN(idx);
            }}

            function prev() {{
              loadFEN(currentIndex - 1);
            }}

            function next() {{
              loadFEN(currentIndex + 1);
            }}

            // Initialize with the first puzzle
            loadFEN(0);
          </script>
        </body>
        </html>
        """
        )
    print(f"Generated {output_html}. Serve it with a local server to view your FEN positions!")


if __name__ == "__main__":
    generate_fen_viewer("output/puzzles.json")
