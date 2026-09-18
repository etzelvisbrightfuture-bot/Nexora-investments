document.addEventListener('DOMContentLoaded', function() {
    console.log("Nexora main.js loaded successfully!");

    // Example: If your buttons have a class like .invest-btn
    const investButtons = document.querySelectorAll('.invest-btn');
    investButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            console.log("Invest button clicked!");
            // If you are using a modal, trigger it here.
            // If it's a form, let the form submit naturally.
        });
    });
});