function loadBoard() {
    var board = document.getElementById('chess-board-window');
    for (let i = 0; i < 8; i++) {

        for (let j = 0; j < 8; j++) {
            var box = document.createElement('div');
            box.setAttribute('row', i + 1);
            box.setAttribute('col', j + 1);
            box.addEventListener('click',boxClicked);

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

const socket = io('http://localhost:5000', {
        withCredentials: true // Ensure cookies are sent with the connection request
    });

// On connect, send a request to join a game
socket.on('connect', () => {
        // Get the span element
        var userTokenSpan = document.getElementById('user_token');
        // Get the custom attribute values
        var sid = userTokenSpan.getAttribute('user-sid');
        var id = userTokenSpan.getAttribute('user-id');
    sessions_details={'sid':sid,'id':id};
    socket.emit('join_room',sessions_details);
});

// If opponent found then update frontend and start the game
socket.on('match_found', (data) => {
    document.getElementById("opponent-name").innerHTML=data['fullname'];
    document.getElementById("opponent-country").innerHTML='Country: '+data['country'];
    document.getElementById("opponent-played").innerHTML='Games Played: '+data['total'];
    document.getElementById("opponent-won").innerHTML='Games Won: '+data['won'];
    document.getElementById("opponent-drawn").innerHTML='Games Drawn: '+data['drawn'];
    document.getElementById("opponent-dp").src='/static/files/'+data['dp'];
    socket.emit('join_match',{'room_id':data['room_id']})
});

socket.on('move_update', (data) => {
    if(data['status']=='valid')
    {
        document.querySelector('[row="'+data['dest_row']+'"][col="'+data['dest_col']+'"]').style.backgroundImage =data['piece'];
        document.querySelector('[row="'+data['source_row']+'"][col="'+data['source_col']+'"]').style.backgroundImage ="";
    }
});

socket.on('match_ended', (data) => {
    document.getElementById('winner-message').innerHTML=data['status'];
    document.getElementById('winner-popup').style.display="flex";
});

socket.on('turn', (data) => {
    document.getElementById('turn-message').innerHTML=data['turn'];
});

socket.on('pawn_promotion', (data) => {
    document.getElementById('promotion-menu').style.display='flex';
});

socket.on('draw_offered', (data) => {
    document.getElementById('draw-accept-popup').style.display='flex';
});

var source_selected=false;
var selected_row=-1;
var selected_col=-1;
var selected_box;

function boxClicked(event)
{
    var clickedElement=event.target;

    if(source_selected==false)
    {
        source_selected=true;
        selected_row=clickedElement.getAttribute('row');
        selected_col=clickedElement.getAttribute('col');
        selected_box=clickedElement;
        clickedElement.classList.add('box-clicked');
    }
    else{
        source_selected=false;
        selected_box.classList.remove('box-clicked');
        selected_dest_row=clickedElement.getAttribute('row');
        selected_dest_col=clickedElement.getAttribute('col');
        var move={'r1':selected_row,'c1':selected_col,'r2':selected_dest_row,'c2':selected_dest_col}
        socket.emit('move',move);
    }

}

function newGame() {
    window.location.href='/chessboard';
}

function resignGame() {
    document.getElementById('winner-message').innerHTML="You have resigned from the game!";
    document.getElementById('winner-popup').style.display="flex";
    socket.emit('resign');
}

function offerDraw() {
    socket.emit('offer_draw');
}

function promotePawn(newPiece) 
{
    socket.emit('pawn_promotion', { 'piece': newPiece });
    document.getElementById('promotion-menu').style.display='None';
}

function handleYes()
{
    socket.emit('draw_move', { 'offer': 'accepted' });
    document.getElementById('draw-accept-popup').style.display='none';
}

function handleNo()
{
    socket.emit('draw_move', { 'offer': 'rejected' });
    document.getElementById('draw-accept-popup').style.display='none';
}

// Add click handlers for the promotion pieces
document.querySelectorAll('.promotion-piece').forEach(piece => {
    piece.addEventListener('click', (event) => {
        promotePawn(event.target.getAttribute('piece'));
    });
});

document.getElementById('resign-button').addEventListener('click',resignGame);
document.getElementById('draw-button').addEventListener('click',offerDraw);





