import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  CircularProgress, 
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Paper
} from '@mui/material';
import AlertItem from '../components/AlertItem';
import { getAlerts, acknowledgeAlert } from '../services/api';

/**
 * Alerts page component
 * @returns {JSX.Element} Alerts page component
 */
const Alerts = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all');

  // Fetch alerts data
  const fetchAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getAlerts();
      setAlerts(response.data);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError('Failed to load alerts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle alert acknowledgement
  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      // Update the alerts data
      setAlerts(prevAlerts => 
        prevAlerts.map(alert => 
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      );
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  // Filter alerts based on filter value
  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true;
    if (filter === 'unacknowledged') return !alert.acknowledged;
    return alert.level.toLowerCase() === filter.toLowerCase();
  });

  // Fetch data on component mount
  useEffect(() => {
    fetchAlerts();
    
    // Set up polling for alerts data
    const interval = setInterval(fetchAlerts, 30000); // Poll every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      <Typography variant="h4" component="h1" gutterBottom>
        Alerts
      </Typography>
      
      {/* Filter */}
      <Box sx={{ mb: 3 }}>
        <FormControl variant="outlined" sx={{ minWidth: 200 }}>
          <InputLabel id="alert-filter-label">Filter</InputLabel>
          <Select
            labelId="alert-filter-label"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            label="Filter"
          >
            <MenuItem value="all">All Alerts</MenuItem>
            <MenuItem value="unacknowledged">Unacknowledged</MenuItem>
            <MenuItem value="critical">Critical</MenuItem>
            <MenuItem value="error">Error</MenuItem>
            <MenuItem value="warning">Warning</MenuItem>
            <MenuItem value="info">Info</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {/* Loading state */}
      {loading && alerts.length === 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      )}
      
      {/* Error state */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      
      {/* Alerts list */}
      {!loading && filteredAlerts.length > 0 && (
        <Box>
          {filteredAlerts.map(alert => (
            <AlertItem 
              key={alert.id} 
              alert={alert} 
              onAcknowledge={handleAcknowledgeAlert} 
            />
          ))}
        </Box>
      )}
      
      {/* No alerts found */}
      {!loading && filteredAlerts.length === 0 && (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No alerts found matching your filter.
          </Typography>
        </Paper>
      )}
    </div>
  );
};

export default Alerts;