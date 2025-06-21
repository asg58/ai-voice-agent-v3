import React, { useState, useEffect } from 'react';
import { 
  Grid, 
  Typography, 
  Paper, 
  Box, 
  CircularProgress,
  Alert
} from '@mui/material';
import MetricsCard from '../components/MetricsCard';
import ServiceCard from '../components/ServiceCard';
import AlertItem from '../components/AlertItem';
import { getDashboardSummary, acknowledgeAlert } from '../services/api';

/**
 * Dashboard page component
 * @returns {JSX.Element} Dashboard page component
 */
const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getDashboardSummary();
      setDashboardData(response.data);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle alert acknowledgement
  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      // Update the dashboard data
      setDashboardData(prevData => ({
        ...prevData,
        alerts: prevData.alerts.map(alert => 
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      }));
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchDashboardData();
    
    // Set up polling for dashboard data
    const interval = setInterval(fetchDashboardData, 30000); // Poll every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  // Show loading state
  if (loading && !dashboardData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Show error state
  if (error && !dashboardData) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <div className="dashboard-container">
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      {dashboardData && (
        <>
          {/* System Metrics */}
          <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 4 }}>
            System Metrics
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <MetricsCard 
                title="CPU Usage" 
                value={dashboardData.system_metrics.cpu_usage} 
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricsCard 
                title="Memory Usage" 
                value={dashboardData.system_metrics.memory_usage} 
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricsCard 
                title="Disk Usage" 
                value={dashboardData.system_metrics.disk_usage} 
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricsCard 
                title="Network Traffic" 
                value={Math.round(dashboardData.system_metrics.network_rx / 1024 / 1024)} 
                unit="MB" 
                max={100}
                warningThreshold={50}
                errorThreshold={80}
              />
            </Grid>
          </Grid>
          
          {/* Services */}
          <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 4 }}>
            Services
          </Typography>
          <Grid container spacing={3}>
            {dashboardData.services.map(service => (
              <Grid item xs={12} sm={6} md={4} key={service.id}>
                <ServiceCard service={service} />
              </Grid>
            ))}
          </Grid>
          
          {/* Alerts */}
          <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 4 }}>
            Recent Alerts
          </Typography>
          {dashboardData.alerts.length > 0 ? (
            dashboardData.alerts.map(alert => (
              <AlertItem 
                key={alert.id} 
                alert={alert} 
                onAcknowledge={handleAcknowledgeAlert} 
              />
            ))
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                No alerts at this time.
              </Typography>
            </Paper>
          )}
        </>
      )}
    </div>
  );
};

export default Dashboard;