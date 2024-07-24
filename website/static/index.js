function deleteNote(noteId) {
  fetch("/delete-note", {
    method: "POST",
    body: JSON.stringify({ noteId: noteId }),
  }).then((_res) => {
    window.location.href = "/";
  });
}

function userListFunc() {
    var userList = document.getElementById('userList')
    var button = document.getElementById('userListBtn')

    if (userList.style.display === 'none') {
        userList.style.display = 'block';
        button.textContent = 'Hide Users'
    }
    else {
        userList.style.display = 'none';
        button.textContent = 'Show Users'
    }

}



function delteUser(userId) {
    fetch('/delete-user', {  // Ensure the URL matches the route in Flask
        method: "POST",
        headers: {
            'Content-Type': 'application/json'  // Set the correct content type
        },
        body: JSON.stringify({ userId: userId })  // Correct key to match Flask
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();  // Reload the page to reflect changes
        } else {
            console.error('Error deleting user');
        }
    });
}



        
