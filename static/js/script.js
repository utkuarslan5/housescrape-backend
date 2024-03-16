// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // Code to run after the document is fully loaded

    // Example of handling a click event on an element with the id 'submit-button'
    const submitButton = document.getElementById('submit-button');
    if (submitButton) {
        submitButton.addEventListener('click', function() {
            // Logic to execute when the submit button is clicked
            console.log('Submit button clicked');
        });
    }
});