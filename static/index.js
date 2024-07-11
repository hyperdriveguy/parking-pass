// Handle table row highlighting
const tableRows = document.querySelectorAll('tbody tr');
tableRows.forEach(row => {
    row.addEventListener('click', () => {
        tableRows.forEach(r => r.classList.remove('highlighted'));
        row.classList.add('highlighted');
    });
});

// Setup SSE
const evtSource = new EventSource("/parking-watch/stream");
evtSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateLatestData(data);
};

function updateLatestData(data) {
    const table = document.querySelector('#latest-data table tbody');
    // Clear existing rows
    table.innerHTML = '';
    // Add new rows
    for (let row of data.slice(-2)) {
        let tr = document.createElement('tr');
        for (let value of Object.values(row)) {
            let td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
        }
        table.appendChild(tr);
    }
}
