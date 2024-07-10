// Get all table rows
const tableRows = document.querySelectorAll('tbody tr');

// Add click event listener to each row
tableRows.forEach(row => {
    row.addEventListener('click', () => {
        // Remove the highlighted class from all rows
        tableRows.forEach(r => r.classList.remove('highlighted'));

        // Add the highlighted class to the clicked row
        row.classList.add('highlighted');
    });
});

// Add this script to your index.html file, just before the closing </body> tag
function refreshPage() {
    location.reload();
}

// Set the auto-refresh interval to 15 minutes (900000 milliseconds)
setInterval(refreshPage, 900000);

// Display a countdown timer
function updateCountdown() {
    const countdownElement = document.getElementById('countdown');
    let seconds = 900;
    
    function tick() {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        countdownElement.textContent = `Next refresh in ${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        if (seconds > 0) {
            seconds--;
            setTimeout(tick, 1000);
        }
    }
    
    tick();
}

updateCountdown();