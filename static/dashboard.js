function updatePassword(event) {
    event.preventDefault();
    var formData = $('#change-password').serialize();
    var pass1 = document.getElementById('password').value
    var pass2 = document.getElementById('confirm-password').value
    if (pass1 != pass2) {
        document.getElementById('response-message').innerHTML="Passwords don't match."
        return;
    }

    $.ajax({
        url: '/changepassword',
        type: 'POST',
        data: formData,
        success: function(response) {
            document.getElementById('response-message').innerHTML=response.message;
        },
        error: function(xhr, status, error) {
            var response = JSON.parse(xhr.responseText);
            document.getElementById('response-message').innerHTML=response.message;
        }
    });
    document.getElementById('change-password').reset();
}

function updateProfile() {
    window.location.href='/updatedata';
}

function changePassword() {
    window.location.href='/updatepassword';
}

function playGame() {
    window.location.href='/chessboard';
}


function updateProfileData(event) {
    event.preventDefault();
    var formData = new FormData(document.getElementById('profile-data'));
   $.ajax({
                url: '/updateprofile',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    alert(response.message)
                },
                error: function(xhr, status, error) {
                    var response = JSON.parse(xhr.responseText);
                    alert(response.error);
                }
            });

}

 function selectCountry() {
     var element = document.querySelector('#country');
     const customAttributeValue = element.getAttribute('selected-country');
     for (let i = 0; i < element.options.length; i++) {
         if (element.options[i].value === customAttributeValue) {
             element.selectedIndex = i;
             break;
         }
     }
 }

selectCountry();

document.getElementById('upload-photo').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('profile-image').src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});