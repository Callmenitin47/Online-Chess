function loadBoard() {
    var board = document.getElementById('chess-board-window');
    for (let i = 0; i < 8; i++) {

        for (let j = 0; j < 8; j++) {
            var box = document.createElement('div');
            box.setAttribute('row', i + 1);
            box.setAttribute('col', j + 1);

            if (i % 2 == 0) {
                if (j % 2 == 0) {
                    box.className = 'bright';
                } else {
                    box.className = 'dark';

                }

            } else {
                if (j % 2 == 0) {
                    box.className = 'dark';
                } else {
                    box.className = 'bright';

                }

            }

            board.appendChild(box);
        }
    }

    for (let i = 1; i <= 8; i++) {
        const selector = `[row="2"][col="${i}"]`;
        const element = document.querySelector(selector);
        element.style.backgroundImage = 'url(../static/files/pieces/black_pawn.png)';
    }

    for (let i = 1; i <= 8; i++) {
        const selector = `[row="7"][col="${i}"]`;
        const element = document.querySelector(selector);
        element.style.backgroundImage = 'url(../static/files/pieces/white_pawn.png)';
    }

    // For Black pieces

    document.querySelector('[row="1"][col="1"]').style.backgroundImage = 'url(../static/files/pieces/black_rook.png)';
    document.querySelector('[row="1"][col="2"]').style.backgroundImage = 'url(../static/files/pieces/black_knight.png)';
    document.querySelector('[row="1"][col="3"]').style.backgroundImage = 'url(../static/files/pieces/black_bishop.png)';
    document.querySelector('[row="1"][col="4"]').style.backgroundImage = 'url(../static/files/pieces/black_queen.png)';
    document.querySelector('[row="1"][col="5"]').style.backgroundImage = 'url(../static/files/pieces/black_king.png)';
    document.querySelector('[row="1"][col="6"]').style.backgroundImage = 'url(../static/files/pieces/black_bishop.png)';
    document.querySelector('[row="1"][col="7"]').style.backgroundImage = 'url(../static/files/pieces/black_knight.png)';
    document.querySelector('[row="1"][col="8"]').style.backgroundImage = 'url(../static/files/pieces/black_rook.png)';

    // For White pieces

    document.querySelector('[row="8"][col="1"]').style.backgroundImage = 'url(../static/files/pieces/white_rook.png)';
    document.querySelector('[row="8"][col="2"]').style.backgroundImage = 'url(../static/files/pieces/white_knight.png)';
    document.querySelector('[row="8"][col="3"]').style.backgroundImage = 'url(../static/files/pieces/white_bishop.png)';
    document.querySelector('[row="8"][col="4"]').style.backgroundImage = 'url(../static/files/pieces/white_queen.png)';
    document.querySelector('[row="8"][col="5"]').style.backgroundImage = 'url(../static/files/pieces/white_king.png)';
    document.querySelector('[row="8"][col="6"]').style.backgroundImage = 'url(../static/files/pieces/white_bishop.png)';
    document.querySelector('[row="8"][col="7"]').style.backgroundImage = 'url(../static/files/pieces/white_knight.png)';
    document.querySelector('[row="8"][col="8"]').style.backgroundImage = 'url(../static/files/pieces/white_rook.png)';

}

loadBoard();