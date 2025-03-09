import json

def generate_fen_viewer(puzzle_file, output_html="fen_viewer.html"):
    with open(puzzle_file, "r") as f:
        puzzles = json.load(f)

    fens = [puzzle["fen"] for puzzle in puzzles]
    chapter_names = [f"Puzzle {i+1} (Ply {puzzle.get('ply', 0)})" for i, puzzle in enumerate(puzzles)]

    with open(output_html, "w") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
          <title>FEN Viewer</title>
          <link rel="icon" type="image/x-icon" href="data:image/x-icon;base64,AAABAAEAEBAQAAAAAAAoAQAAFgAAACgAAAAQAAAAIAAAAAEABAAAAAAAgAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAA/4QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA">
          <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.min.js"></script>
          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.css" />
          <style>
            .board { width: 400px; margin: 20px; }
            button { margin: 5px; }
            #info { margin-left: 20px; font-family: Arial, sans-serif; }
          </style>
        </head>
        <body>
          <div id="board" class="board"></div>
          <button onclick="prev()">Previous</button>
          <button onclick="next()">Next</button>
          <div id="info"></div>
          <script>
            let fens = """ + json.dumps(fens) + """;
            let names = """ + json.dumps(chapter_names) + """;
            let currentIndex = 0;
            const board = Chessboard('board', {
              position: 'start',
              draggable: true,
              pieceTheme: 'img/chesspieces/wiki/{piece}.png'
            });

            function loadFEN(index) {
              if (index >= 0 && index < fens.length) {
                board.position(fens[index]);
                document.getElementById('info').innerText = names[index];
                currentIndex = index;
              }
            }

            function prev() { loadFEN(currentIndex - 1); }
            function next() { loadFEN(currentIndex + 1); }

            loadFEN(0);
          </script>
        </body>
        </html>
        """)
    print(f"Generated {output_html}. Open it in a browser to view your FEN positions!")

if __name__ == "__main__":
    generate_fen_viewer("output/puzzles.json")