// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', () => {
  // DOM elements
  const activeSessionsEl = document.getElementById('active-sessions');
  const totalConversationsEl = document.getElementById('total-conversations');
  const systemStatusLight = document.getElementById('system-status-light');
  const systemStatusText = document.getElementById('system-status-text');
  const recentConversationsEl = document.getElementById('recent-conversations');

  // Update system status UI
  function updateSystemStatus(status) {
    systemStatusLight.className = 'status-light';

    switch (status) {
      case 'healthy':
        systemStatusLight.classList.add('active');
        systemStatusText.textContent = 'Healthy';
        break;
      case 'degraded':
        systemStatusLight.classList.add('processing');
        systemStatusText.textContent = 'Degraded';
        break;
      case 'unhealthy':
        systemStatusLight.classList.add('error');
        systemStatusText.textContent = 'Unhealthy';
        break;
      default:
        systemStatusLight.classList.remove('active', 'processing', 'error');
        systemStatusText.textContent = 'Unknown';
    }
  }

  // Fetch dashboard data
  async function fetchDashboardData() {
    try {
      // Fetch active sessions
      const sessionsResponse = await fetch('/sessions');
      if (sessionsResponse.ok) {
        const sessionsData = await sessionsResponse.json();
        activeSessionsEl.textContent = sessionsData.active_sessions || 0;
        totalConversationsEl.textContent = sessionsData.total_sessions || 0;

        // Update recent conversations
        if (sessionsData.recent_sessions && sessionsData.recent_sessions.length > 0) {
          recentConversationsEl.innerHTML = '';

          sessionsData.recent_sessions.forEach((session) => {
            const sessionEl = document.createElement('div');
            sessionEl.className = 'session-item';
            sessionEl.innerHTML = `
              <div class="session-header">
                <span class="session-id">${session.id.substring(0, 8)}...</span>
                <span class="session-time">${new Date(session.created_at).toLocaleString()}</span>
              </div>
              <div class="session-duration">Duration: ${session.duration || 'N/A'}</div>
            `;
            recentConversationsEl.appendChild(sessionEl);
          });
        } else {
          recentConversationsEl.innerHTML = '<p>No recent conversations</p>';
        }
      }

      // Fetch system health
      const healthResponse = await fetch('/health/health');
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        updateSystemStatus(healthData.status);
      } else {
        updateSystemStatus('unhealthy');
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      updateSystemStatus('unhealthy');
    }
  }

  // Initialize
  fetchDashboardData();

  // Refresh data every 30 seconds
  setInterval(fetchDashboardData, 30000);
});
