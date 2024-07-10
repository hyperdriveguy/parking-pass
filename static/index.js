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