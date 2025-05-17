document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('generateMiningPlanBtn');
    if (btn) {
        btn.addEventListener('click', miningPlan);
    }
});

function miningPlan() {
    fetch('/mining_plan')
        .then(response => response.json())
        .then(data => {
            let html = '<h3>Mining Plan</h3>';
            html += '<table><tr><th>Mineral</th><th>Needed</th><th>Have</th><th>Deficit</th><th>Suggested Ores</th></tr>';
            data.summary.forEach(row => {
                html += `<tr><td>${row.mineral}</td><td>${row.needed}</td><td>${row.have}</td><td>${row.deficit}</td><td>${row.suggested_ores.join(', ')}</td></tr>`;
            });
            html += '</table>';

            html += '<h4>Weekly Mining Schedule:</h4>';
            html += '<table><tr><th>Day</th><th>Ore Focus</th><th>Minerals</th><th>Notes</th></tr>';
            data.schedule.forEach(day => {
                html += `<tr${day.today ? ' style="background:#e0f7fa;"' : ''}><td>${day.day}</td><td>${day.ore}</td><td>${day.minerals}</td><td>${day.notes}</td></tr>`;
            });
            html += '</table>';

            html += '<h4>Ore Priorities:</h4><ul>';
            data.priorities.forEach(p => {
                html += `<li><b>${p.ore}</b>: ${p.reason}</li>`;
            });
            html += '</ul>';

            document.getElementById('miningPlanResults').innerHTML = html;
        })
        .catch(err => {
            document.getElementById('miningPlanResults').innerHTML = "Error loading mining plan.";
        });
}
