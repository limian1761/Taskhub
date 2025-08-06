document.addEventListener("DOMContentLoaded", function () {
    // --- ECharts Graph Initialization ---
    initTaskGraph();

    // --- KPI Cards Data Loading ---
    loadKpiData();

    // --- Tasks Table Data Loading ---
    loadTasksData();
});

/**
 * Initializes the ECharts graph.
 */
function initTaskGraph() {
    var myChart = echarts.init(document.getElementById('task-graph-container'));
    myChart.showLoading();

    fetch('/api/system/task-graph')
        .then(response => response.json())
        .then(data => {
            myChart.hideLoading();
            var option = {
                title: { text: 'Hunter-Task Interaction Network' },
                tooltip: {
                    formatter: function (params) {
                        if (params.dataType === 'node') {
                            return `${params.data.name}<br/>Value: ${params.data.value}`;
                        }
                        return params.data.name;
                    }
                },
                legend: [{ data: data.categories.map(a => a.name) }],
                series: [{
                    name: 'Taskhub Graph',
                    type: 'graph',
                    layout: 'force',
                    data: data.nodes,
                    links: data.links,
                    categories: data.categories,
                    roam: true,
                    label: { show: true, position: 'right', formatter: '{b}' },
                    force: { repulsion: 100 },
                    edgeSymbol: ['circle', 'arrow'],
                    edgeSymbolSize: [4, 10],
                    edgeLabel: { show: true, formatter: p => p.data.name }
                }]
            };
            myChart.setOption(option);
        })
        .catch(error => {
            myChart.hideLoading();
            console.error('Error fetching graph data:', error);
            document.getElementById('task-graph-container').innerText = 'Failed to load graph data.';
        });

    window.onresize = () => myChart.resize();
}

/**
 * Loads KPI data from the API and populates the cards.
 */
function loadKpiData() {
    const kpiContainer = document.getElementById('kpi-cards');
    fetch('/api/system/stats')
        .then(response => response.json())
        .then(data => {
            const kpiData = [
                { title: 'Total Tasks', value: data.total_tasks, color: 'primary' },
                { title: 'In Progress', value: data.in_progress, color: 'warning' },
                { title: 'Pending Tasks', value: data.pending, color: 'info' },
                { title: 'Active Hunters', value: data.active_hunters, color: 'success' }
            ];
            kpiContainer.innerHTML = kpiData.map(kpi => `
                <div class="col-md-3">
                    <div class="card kpi-card border-${kpi.color}">
                        <div class="card-body">
                            <h5 class="card-title text-uppercase">${kpi.title}</h5>
                            <p class="card-text">${kpi.value}</p>
                        </div>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error fetching KPI data:', error);
            kpiContainer.innerHTML = '<p class="text-danger">Could not load system stats.</p>';
        });
}

/**
 * Loads tasks data from the API and populates the table.
 */
function loadTasksData() {
    const tableBody = document.getElementById('tasks-table-body');
    fetch('/api/system/tasks')
        .then(response => response.json())
        .then(tasks => {
            if (tasks.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No tasks found.</td></tr>';
                return;
            }
            tableBody.innerHTML = tasks.map(task => `
                <tr>
                    <td>${task.id.substring(0, 8)}...</td>
                    <td>${task.name}</td>
                    <td><span class="badge bg-${getStatusColor(task.status)}">${task.status}</span></td>
                    <td>${task.assignee}</td>
                </tr>
            `).join('');
        })
        .catch(error => {
            console.error('Error fetching tasks data:', error);
            tableBody.innerHTML = '<tr><td colspan="4" class="text-danger">Could not load tasks.</td></tr>';
        });
}

/**
 * Returns a Bootstrap color class based on task status.
 * @param {string} status - The status of the task.
 * @returns {string} A Bootstrap background color class.
 */
function getStatusColor(status) {
    switch (status) {
        case 'COMPLETED': return 'success';
        case 'IN_PROGRESS': return 'warning';
        case 'PENDING': return 'secondary';
        default: return 'light';
    }
}
