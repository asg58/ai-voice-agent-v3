import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Chip, 
  Box,
  Button
} from '@mui/material';
import { 
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { formatDate, getServiceStatusColor } from '../utils/formatters';
import { useNavigate } from 'react-router-dom';

/**
 * Service card component for displaying service information
 * @param {Object} props - Component props
 * @param {Object} props.service - Service data
 * @returns {JSX.Element} ServiceCard component
 */
const ServiceCard = ({ service }) => {
  const navigate = useNavigate();
  
  // Get status icon based on service status
  const getStatusIcon = (status) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return <HealthyIcon sx={{ color: '#4caf50' }} />;
      case 'warning':
        return <WarningIcon sx={{ color: '#ff9800' }} />;
      case 'error':
        return <ErrorIcon sx={{ color: '#f44336' }} />;
      default:
        return <InfoIcon sx={{ color: '#2196f3' }} />;
    }
  };

  return (
    <Card className="card">
      <CardContent className="card-content">
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="div">
            {service.name}
          </Typography>
          <Chip 
            icon={getStatusIcon(service.status)}
            label={service.status}
            sx={{ 
              backgroundColor: getServiceStatusColor(service.status) + '20',
              color: getServiceStatusColor(service.status),
              fontWeight: 'bold'
            }}
          />
        </Box>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          <strong>Host:</strong> {service.host}:{service.port}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          <strong>Last Heartbeat:</strong> {formatDate(service.last_heartbeat)}
        </Typography>
        
        {service.metadata && (
          <Box sx={{ mt: 1, mb: 2 }}>
            {Object.entries(service.metadata).map(([key, value]) => (
              <Typography key={key} variant="body2" color="text.secondary">
                <strong>{key}:</strong> {value}
              </Typography>
            ))}
          </Box>
        )}
        
        <Button 
          variant="outlined" 
          size="small"
          onClick={() => navigate(`/services/${service.id}`)}
          sx={{ mt: 1 }}
        >
          View Details
        </Button>
      </CardContent>
    </Card>
  );
};

export default ServiceCard;