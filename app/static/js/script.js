document.addEventListener('DOMContentLoaded', function() {
    // This function will run after the document is fully loaded

    function onLoad() {
        // This function can be used to initialize the page and load any data
        console.log("HouseScraper App is loaded and ready!");
    }

    function handleSubmit(event) {
        event.preventDefault();
        // This function can be used to handle form submissions
        // For example, to scrape data when a user submits a form
        let formData = new FormData(event.target);
        fetch('/scrape', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            // You can add code here to update the DOM with the scraped house data
        })
        .catch(error => console.error('Error:', error));
    }

    // Attach event listeners
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }

    // Call the onLoad function
    onLoad();
});