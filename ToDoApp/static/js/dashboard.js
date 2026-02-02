// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
    initializeAnalyticsChart();
    initializeCategoryChart();
    setupPeriodButtons();
    setupTaskToggles();
});

// ============================================
// CALENDAR
// ============================================

function initializeCalendar() {
    const calendarGrid = document.getElementById('calendarGrid');
    if (!calendarGrid) return;
    
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // Month selector handler
    const monthSelector = document.getElementById('monthSelector');
    if (monthSelector) {
        monthSelector.addEventListener('change', function() {
            const selectedMonth = parseInt(this.value);
            renderCalendar(selectedMonth, currentYear);
        });
    }
    
    renderCalendar(currentMonth, currentYear);
}

function renderCalendar(month, year) {
    const calendarGrid = document.getElementById('calendarGrid');
    if (!calendarGrid) return;
    
    calendarGrid.innerHTML = '';
    
    // Day headers
    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(day => {
        const header = document.createElement('div');
        header.className = 'calendar-day-header';
        header.textContent = day;
        calendarGrid.appendChild(header);
    });
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    
    // Previous month days
    const prevMonthDays = new Date(year, month, 0).getDate();
    for (let i = firstDay - 1; i >= 0; i--) {
        const day = document.createElement('div');
        day.className = 'calendar-day other-month';
        day.textContent = prevMonthDays - i;
        calendarGrid.appendChild(day);
    }
    
    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
        const day = document.createElement('div');
        day.className = 'calendar-day';
        
        const date = new Date(year, month, i);
        if (date.getDate() === today.getDate() && 
            date.getMonth() === today.getMonth() && 
            date.getFullYear() === today.getFullYear()) {
            day.classList.add('today');
        }
        
        day.textContent = i;
        calendarGrid.appendChild(day);
    }
    
    // Next month days to fill grid
    const totalCells = calendarGrid.children.length;
    const remainingCells = 42 - totalCells; // 6 rows * 7 days
    for (let i = 1; i <= remainingCells; i++) {
        const day = document.createElement('div');
        day.className = 'calendar-day other-month';
        day.textContent = i;
        calendarGrid.appendChild(day);
    }
}

// ============================================
// ANALYTICS CHART
// ============================================

let analyticsChart = null;

function initializeAnalyticsChart() {
    const ctx = document.getElementById('analyticsChart');
    if (!ctx) return;
    
    // Default data (week view)
    const defaultData = {
        labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        datasets: [
            {
                label: 'Tasks',
                data: [12, 19, 15, 19, 14, 16, 18],
                borderColor: '#F97316',
                backgroundColor: 'rgba(249, 115, 22, 0.1)',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Completed',
                data: [8, 12, 10, 15, 11, 13, 14],
                borderColor: '#7C3AED',
                backgroundColor: 'rgba(124, 58, 237, 0.1)',
                tension: 0.4,
                fill: true
            }
        ]
    };
    
    analyticsChart = new Chart(ctx, {
        type: 'line',
        data: defaultData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 14 },
                    bodyFont: { size: 12 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
    
    // Load analytics data
    loadAnalyticsData('week');
}

function loadAnalyticsData(period) {
    fetch(`/dashboard/api/analytics?period=${period}`)
        .then(response => response.json())
        .then(data => {
            if (data.data && analyticsChart) {
                const labels = data.data.map(d => d.day);
                const counts = data.data.map(d => d.count);
                
                analyticsChart.data.labels = labels;
                analyticsChart.data.datasets[0].data = counts;
                analyticsChart.update();
            }
        })
        .catch(error => {
            console.error('Error loading analytics:', error);
        });
}

function setupPeriodButtons() {
    const buttons = document.querySelectorAll('.period-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            buttons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const period = this.dataset.period;
            loadAnalyticsData(period);
        });
    });
}

// ============================================
// CATEGORY CHART
// ============================================

let categoryChart = null;

function initializeCategoryChart() {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    // Load category data
    fetch('/dashboard/api/project-categories')
        .then(response => response.json())
        .then(data => {
            if (data.categories && data.categories.length > 0) {
                renderCategoryChart(data.categories);
                renderCategoryLegend(data.categories);
            } else {
                // Default data
                renderCategoryChart([
                    { name: 'UX/UI Design', count: 40, percentage: 40 },
                    { name: 'Video Editing', count: 35, percentage: 35 },
                    { name: 'Photographer', count: 25, percentage: 25 }
                ]);
            }
        })
        .catch(error => {
            console.error('Error loading categories:', error);
            // Default data on error
            renderCategoryChart([
                { name: 'UX/UI Design', count: 40, percentage: 40 },
                { name: 'Video Editing', count: 35, percentage: 35 },
                { name: 'Photographer', count: 25, percentage: 25 }
            ]);
        });
}

function renderCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    const colors = ['#7C3AED', '#F97316', '#A78BFA', '#FB923C', '#C4B5FD'];
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.name),
            datasets: [{
                data: categories.map(c => c.percentage),
                backgroundColor: colors.slice(0, categories.length),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return `${label}: ${value}%`;
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });
    
    // Update center percentage
    const total = categories.reduce((sum, c) => sum + c.percentage, 0);
    const centerText = document.querySelector('.donut-percentage');
    if (centerText) {
        centerText.textContent = `${Math.round(total)}%`;
    }
}

function renderCategoryLegend(categories) {
    const legend = document.getElementById('categoryLegend');
    if (!legend) return;
    
    legend.innerHTML = '';
    const colors = ['#7C3AED', '#F97316', '#A78BFA', '#FB923C', '#C4B5FD'];
    
    categories.forEach((cat, index) => {
        const item = document.createElement('div');
        item.className = 'legend-item';
        
        const dot = document.createElement('div');
        dot.className = 'legend-dot';
        dot.style.backgroundColor = colors[index % colors.length];
        
        const label = document.createElement('span');
        label.textContent = cat.name;
        
        item.appendChild(dot);
        item.appendChild(label);
        legend.appendChild(item);
    });
}

// ============================================
// TASK MANAGEMENT
// ============================================

function setupTaskToggles() {
    const checkboxes = document.querySelectorAll('.task-item input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const taskItem = this.closest('.task-item');
            const taskId = taskItem.dataset.taskId;
            if (taskId) {
                toggleTask(taskId);
            }
        });
    });
}

function toggleTask(taskId) {
    fetch(`/dashboard/api/task/${taskId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Reload today's tasks
            loadTodayTasks();
        }
    })
    .catch(error => {
        console.error('Error toggling task:', error);
    });
}

function loadTodayTasks() {
    fetch('/dashboard/api/today-tasks')
        .then(response => response.json())
        .then(data => {
            if (data.tasks) {
                updateTasksList(data.tasks);
            }
        })
        .catch(error => {
            console.error('Error loading tasks:', error);
        });
}

function updateTasksList(tasks) {
    const tasksList = document.getElementById('todayTasksList');
    if (!tasksList) return;
    
    tasksList.innerHTML = '';
    
    tasks.forEach(task => {
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        taskItem.dataset.taskId = task.id;
        
        const timeAgo = calculateTimeAgo(task.created_at || new Date().toISOString());
        
        taskItem.innerHTML = `
            <div class="task-checkbox">
                <input type="checkbox" ${task.completed ? 'checked' : ''} 
                       onchange="toggleTask(${task.id})">
            </div>
            <div class="task-content">
                <div class="task-title">${escapeHtml(task.title)}</div>
                <div class="task-time">${timeAgo}</div>
            </div>
        `;
        
        tasksList.appendChild(taskItem);
    });
}

function calculateTimeAgo(createdAt) {
    if (!createdAt) return 'just now';
    
    const now = new Date();
    const created = new Date(createdAt);
    const diffMs = now - created;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    
    if (diffSec < 60) {
        return 'just now';
    } else if (diffMin < 60) {
        return `${diffMin} min ago`;
    } else if (diffHour < 24) {
        return `${diffHour} hour ago`;
    } else {
        const diffDay = Math.floor(diffHour / 24);
        return `${diffDay} day ago`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update time displays on page load
document.addEventListener('DOMContentLoaded', function() {
    const timeElements = document.querySelectorAll('.task-time[data-created]');
    timeElements.forEach(el => {
        const createdAt = el.getAttribute('data-created');
        if (createdAt) {
            el.textContent = calculateTimeAgo(createdAt);
        }
    });
});

// Make toggleTask available globally
window.toggleTask = toggleTask;

// ============================================
// SUMMARY STATS
// ============================================

function loadSummaryStats() {
    fetch('/dashboard/api/summary')
        .then(response => response.json())
        .then(data => {
            updateSummaryCards(data);
        })
        .catch(error => {
            console.error('Error loading summary:', error);
        });
}

function updateSummaryCards(stats) {
    // Update summary values if needed
    const summaryItems = document.querySelectorAll('.summary-value');
    // This would need to be customized based on your HTML structure
}

// Load summary on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSummaryStats();
});
