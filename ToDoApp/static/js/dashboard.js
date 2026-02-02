// ================= DASHBOARD JS =================

document.addEventListener('DOMContentLoaded', () => {
    initializeCalendar();
    initializeAnalyticsChart();
    initializeCategoryChart();
    setupPeriodButtons();
    setupTaskToggles();
    loadSummaryStats();
    updateInitialTaskTimes();
});

// ============================================
// CALENDAR
// ============================================

let currentYear = new Date().getFullYear();

function initializeCalendar() {
    const calendarGrid = document.getElementById('calendarGrid');
    if (!calendarGrid) return;

    const today = new Date();
    const currentMonth = today.getMonth();

    const monthSelector = document.getElementById('monthSelector');
    if (monthSelector) {
        monthSelector.addEventListener('change', function () {
            renderCalendar(parseInt(this.value), currentYear);
        });
    }

    renderCalendar(currentMonth, currentYear);
}

function renderCalendar(month, year) {
    const calendarGrid = document.getElementById('calendarGrid');
    if (!calendarGrid) return;

    calendarGrid.innerHTML = '';

    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(d => {
        const h = document.createElement('div');
        h.className = 'calendar-day-header';
        h.textContent = d;
        calendarGrid.appendChild(h);
    });

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();

    const prevMonthDays = new Date(year, month, 0).getDate();
    for (let i = firstDay - 1; i >= 0; i--) {
        const d = document.createElement('div');
        d.className = 'calendar-day other-month';
        d.textContent = prevMonthDays - i;
        calendarGrid.appendChild(d);
    }

    for (let i = 1; i <= daysInMonth; i++) {
        const d = document.createElement('div');
        d.className = 'calendar-day';

        if (
            i === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear()
        ) {
            d.classList.add('today');
        }

        d.textContent = i;
        calendarGrid.appendChild(d);
    }

    while (calendarGrid.children.length < 49) {
        const d = document.createElement('div');
        d.className = 'calendar-day other-month';
        calendarGrid.appendChild(d);
    }
}

// ============================================
// ANALYTICS CHART
// ============================================

let analyticsChart = null;

function initializeAnalyticsChart() {
    const ctx = document.getElementById('analyticsChart');
    if (!ctx) return;

    analyticsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Tasks',
                data: [],
                borderColor: '#F97316',
                backgroundColor: 'rgba(249,115,22,0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true },
                x: { grid: { display: false } }
            }
        }
    });

    loadAnalyticsData('week');
}

function loadAnalyticsData(period) {
    fetch(`/dashboard/api/analytics?period=${period}`)
        .then(r => r.json())
        .then(data => {
            if (!data.data || !analyticsChart) return;

            analyticsChart.data.labels = data.data.map(d => d.day);
            analyticsChart.data.datasets[0].data = data.data.map(d => d.count);
            analyticsChart.update();
        })
        .catch(err => console.error(err));
}

function setupPeriodButtons() {
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.period-btn')
                .forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            loadAnalyticsData(this.dataset.period);
        });
    });
}

// ============================================
// CATEGORY CHART
// ============================================

function initializeCategoryChart() {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;

    fetch('/dashboard/api/project-categories')
        .then(r => r.json())
        .then(data => {
            const cats = data.categories || [
                { name: 'UX/UI', percentage: 40 },
                { name: 'Video', percentage: 35 },
                { name: 'Photo', percentage: 25 }
            ];
            renderCategoryChart(cats);
            renderCategoryLegend(cats);
        })
        .catch(console.error);
}

function renderCategoryChart(categories) {
    new Chart(document.getElementById('categoryChart'), {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.name),
            datasets: [{
                data: categories.map(c => c.percentage),
                backgroundColor: ['#7C3AED', '#F97316', '#A78BFA']
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            cutout: '70%'
        }
    });

    const total = categories.reduce((s, c) => s + c.percentage, 0);
    const center = document.querySelector('.donut-percentage');
    if (center) center.textContent = `${total}%`;
}

function renderCategoryLegend(categories) {
    const legend = document.getElementById('categoryLegend');
    if (!legend) return;

    legend.innerHTML = '';
    categories.forEach((c, i) => {
        legend.innerHTML += `
            <div class="legend-item">
                <div class="legend-dot" style="background:#7C3AED"></div>
                <span>${escapeHtml(c.name)}</span>
            </div>
        `;
    });
}

// ============================================
// TASKS
// ============================================

function setupTaskToggles() {
    document.addEventListener('change', e => {
        if (e.target.matches('.task-item input[type="checkbox"]')) {
            const task = e.target.closest('.task-item');
            if (task?.dataset.taskId) toggleTask(task.dataset.taskId);
        }
    });
}

function toggleTask(taskId) {
    fetch(`/dashboard/api/task/${taskId}/toggle`, { method: 'POST' })
        .then(r => r.json())
        .then(() => loadTodayTasks())
        .catch(console.error);
}

function loadTodayTasks() {
    fetch('/dashboard/api/today-tasks')
        .then(r => r.json())
        .then(d => d.tasks && updateTasksList(d.tasks))
        .catch(console.error);
}

function updateTasksList(tasks) {
    const list = document.getElementById('todayTasksList');
    if (!list) return;

    list.innerHTML = '';
    tasks.forEach(t => {
        list.innerHTML += `
            <div class="task-item" data-task-id="${t.id}">
                <div class="task-checkbox">
                    <input type="checkbox" ${t.status === 'completed' ? 'checked' : ''}>
                </div>
                <div class="task-content">
                    <div class="task-title">${escapeHtml(t.title)}</div>
                    <div class="task-time">${calculateTimeAgo(t.created_at)}</div>
                </div>
            </div>
        `;
    });
}

// ============================================
// HELPERS
// ============================================

function calculateTimeAgo(date) {
    if (!date) return 'just now';
    const diff = Math.floor((Date.now() - new Date(date)) / 60000);
    if (diff < 1) return 'just now';
    if (diff < 60) return `${diff} min ago`;
    if (diff < 1440) return `${Math.floor(diff / 60)} hr ago`;
    return `${Math.floor(diff / 1440)} day ago`;
}

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

function updateInitialTaskTimes() {
    document.querySelectorAll('.task-time[data-created]')
        .forEach(el => el.textContent = calculateTimeAgo(el.dataset.created));
}

// ============================================
// SUMMARY
// ============================================

function loadSummaryStats() {
    fetch('/dashboard/api/summary')
        .then(r => r.json())
        .catch(console.error);
}

// expose
window.toggleTask = toggleTask;
