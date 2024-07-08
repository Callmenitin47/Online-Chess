function showSignupForm() {
    document.getElementById('login-form').style.display='none';
    document.getElementById('signup-form').style.display='block';
}

function showLoginForm() {
    document.getElementById('signup-form').style.display='none';
    document.getElementById('login-form').style.display='block';
}

function submitSignupForm(event) {
    event.preventDefault();
    var formData = $('#newuser-form').serialize();
    $.ajax({
        url: '/signup',
        type: 'POST',
        data: formData,
        success: function(response)
        {
            alert(response.message);
            document.getElementById('signup').reset();
        },
        error: function(xhr, status, error)
        {
            var response=JSON.parse(xhr.responseText);
            alert(response.error);
        }  
    });
}

function submitLoginForm(event) {
    event.preventDefault();
    var formData = $('#signin-form').serialize();
    $.ajax({
        url: '/login',
        type: 'POST',
        data: formData,
        success: function(response)
        {
            window.location.href='/profile';
        },
        error: function(xhr, status, error)
        {
            alert("Login Username/Password is incorrect");
        }  
    });
}