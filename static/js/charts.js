// Chart.js implementations for study analytics

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  initializeProgressCharts();
  initializeStudyCharts();
  initializeTestCharts();
  initializePomodoroCharts();
});

// Progress Charts (Dashboard)
function initializeProgressCharts() {
  const subjectProgressCtx = document.getElementById('subject-progress-chart');
  
  if (subjectProgressCtx) {
    const physicsProgress = parseFloat(subjectProgressCtx.dataset.physics) || 0;
    const chemistryProgress = parseFloat(subjectProgressCtx.dataset.chemistry) || 0;
    const biologyProgress = parseFloat(subjectProgressCtx.dataset.biology) || 0;
    
    new Chart(subjectProgressCtx, {
      type: 'doughnut',
      data: {
        labels: ['Physics', 'Chemistry', 'Biology'],
        datasets: [{
          data: [physicsProgress, chemistryProgress, biologyProgress],
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(16, 185, 129, 0.8)',
            'rgba(245, 158, 11, 0.8)'
          ],
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return context.label + ': ' + context.parsed + '%';
              }
            }
          }
        }
      }
    });
  }
}

// Study Time Charts
function initializeStudyCharts() {
  const studyChartCtx = document.getElementById('study-time-chart');
  
  if (studyChartCtx) {
    const days = parseInt(studyChartCtx.dataset.days) || 30;
    
    fetch(`/study_stats?days=${days}`)
      .then(response => response.json())
      .then(data => {
        new Chart(studyChartCtx, {
          type: 'line',
          data: {
            labels: data.dates,
            datasets: [{
              label: 'Study Time (minutes)',
              data: data.durations,
              fill: true,
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderColor: 'rgba(59, 130, 246, 1)',
              borderWidth: 2,
              tension: 0.4,
              pointBackgroundColor: 'rgba(59, 130, 246, 1)',
              pointBorderColor: '#fff',
              pointBorderWidth: 2,
              pointRadius: 4,
              pointHoverRadius: 6
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
                mode: 'index',
                intersect: false,
                callbacks: {
                  label: function(context) {
                    const hours = Math.floor(context.parsed.y / 60);
                    const minutes = context.parsed.y % 60;
                    return `${hours}h ${minutes}m`;
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  callback: function(value) {
                    return Math.floor(value / 60) + 'h';
                  }
                }
              }
            }
          }
        });
      })
      .catch(err => console.error('Error loading study stats:', err));
  }
}

// Test Performance Charts
function initializeTestCharts() {
  const testChartCtx = document.getElementById('test-performance-chart');
  
  if (testChartCtx) {
    fetch('/test_stats')
      .then(response => response.json())
      .then(data => {
        const datasets = [
          {
            label: 'Overall %',
            data: data.percentages,
            borderColor: 'rgba(99, 102, 241, 1)',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            fill: true
          }
        ];
        
        // Add subject-wise data if available
        if (data.physics_scores && data.physics_scores.length > 0) {
          datasets.push({
            label: 'Physics %',
            data: data.physics_scores,
            borderColor: 'rgba(59, 130, 246, 1)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            borderDash: [5, 5]
          });
        }
        
        if (data.chemistry_scores && data.chemistry_scores.length > 0) {
          datasets.push({
            label: 'Chemistry %',
            data: data.chemistry_scores,
            borderColor: 'rgba(16, 185, 129, 1)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            borderDash: [5, 5]
          });
        }
        
        if (data.biology_scores && data.biology_scores.length > 0) {
          datasets.push({
            label: 'Biology %',
            data: data.biology_scores,
            borderColor: 'rgba(245, 158, 11, 1)',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            borderDash: [5, 5]
          });
        }
        
        new Chart(testChartCtx, {
          type: 'line',
          data: {
            labels: data.dates,
            datasets: datasets
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top'
              },
              tooltip: {
                mode: 'index',
                intersect: false
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                  callback: function(value) {
                    return value + '%';
                  }
                }
              }
            }
          }
        });
      })
      .catch(err => console.error('Error loading test stats:', err));
  }
}

// Pomodoro Session Charts
function initializePomodoroCharts() {
  const pomodoroChartCtx = document.getElementById('pomodoro-chart');
  
  if (pomodoroChartCtx) {
    const days = parseInt(pomodoroChartCtx.dataset.days) || 7;
    
    fetch(`/pomodoro/stats?days=${days}`)
      .then(response => response.json())
      .then(data => {
        new Chart(pomodoroChartCtx, {
          type: 'bar',
          data: {
            labels: data.dates,
            datasets: [{
              label: 'Pomodoro Sessions',
              data: data.sessions,
              backgroundColor: 'rgba(239, 68, 68, 0.8)',
              borderColor: 'rgba(239, 68, 68, 1)',
              borderWidth: 1
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
                callbacks: {
                  label: function(context) {
                    return context.parsed.y + ' sessions (' + (context.parsed.y * 25) + ' min)';
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  stepSize: 1
                }
              }
            }
          }
        });
      })
      .catch(err => console.error('Error loading Pomodoro stats:', err));
  }
}

// Update chart time range (for interactive controls)
function updateChartRange(chartType, days) {
  switch(chartType) {
    case 'study':
      initializeStudyCharts();
      break;
    case 'pomodoro':
      initializePomodoroCharts();
      break;
  }
}
