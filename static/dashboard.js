function changePassword(event) {
    event.preventDefault();
    var formData = $('#change-password').serialize();
    var pass1 = document.getElementById('password').value
    var pass2 = document.getElementById('confirm-password').value
    if (pass1 != pass2) {
        document.getElementById('response-message').innerHTML = "Passwords don't match."
        return;
    }
    $.ajax({
        url: '/changepassword',
        type: 'POST',
        data: formData,
        success: function(response) {
            document.getElementById('response-message').innerHTML = response.message;
        },
        error: function(xhr, status, error) {
            var response = JSON.parse(xhr.responseText);
            document.getElementById('response-message').innerHTML = response.message;
        }
    });
}

function updateProfile() {
    window.location.href='/profile';
}

function changePassword() {
    window.location.href='/updatepassword';
}

function playGame() {
    window.location.href='/chessboard';
}