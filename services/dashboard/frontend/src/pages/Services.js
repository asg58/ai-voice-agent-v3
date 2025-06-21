import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Grid, 
  Box, 
  CircularProgress, 
  Alert,
  TextField,
  InputAdornment
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import ServiceCard from '../components/ServiceCard';
import { getServices } from '../services/api';

/**
 * Services page component
 * @returns {JSX.Element} Services page component
 */
const Services = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [services, setServices] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch services data
  const fetchServices = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getServices();
      setServices(response.data);
    } catch (err) {
      console.error('Error fetching services:', err);
      setError('Failed to load services. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Filter services based on search term
  const filteredServices = services.filter(service => 
    service.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    service.host.toLowerCase().includes(searchTerm.toLowerCase()) ||
    service.status.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Fetch data on component mount
  useEffect(() => {
    fetchServices();
    
    // Set up polling for services data
    const interval = setInterval(fetchServices, 30000); // Poll every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      <Typography variant="h4" component="h1" gutterBottom>
        Services
      </Typography>
      
      {/* Search bar */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search services..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>
      
      {/* Loading state */}
      {loading && services.length === 0 && (
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
      
      {/* Services grid */}
      {!loading && filteredServices.length > 0 && (
        <Grid container spacing={3}>
          {filteredServices.map(service => (
            <Grid item xs={12} sm={6} md={4} key={service.id}>
              <ServiceCard service={service} />
            </Grid>
          ))}
        </Grid>
      )}
      
      {/* No services found */}
      {!loading && filteredServices.length === 0 && (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="body1" color="text.secondary">
            No services found matching your search.
          </Typography>
        </Box>
      )}
    </div>
  );
};

export default Services;