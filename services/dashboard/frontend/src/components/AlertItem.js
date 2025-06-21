import React from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  Chip, 
  Button,
  IconButton
} from '@mui/material';
import { 
  CheckCircle as AcknowledgeIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { formatDate, getAlertLevelColor } from '../utils/formatters';

/**
 * Alert item component for displaying an alert
 * @param {Object} props - Component props
 * @param {Object} props.alert - Alert data
 * @param {Function} props.onAcknowledge - Function to acknowledge the alert
 * @returns {JSX.Element} AlertItem component
 */
const AlertItem = ({ alert, onAcknowledge }) => {
  // Get alert level class
  const getAlertClass = (level) => {
    switch (level.toLowerCase()) {
      case 'critical':
        return 'alert-critical';
      case 'error':
        return 'alert-error';
      case 'warning':
        return 'alert-warning';
      case 'info':
        return 'alert-info';
      default:
        return '';
    }
  };

  // Get alert level icon
  const getLevelIcon = (level) => {
    switch (level.toLowerCase()) {
      case 'critical':
      case 'error':
        return <ErrorIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'info':
      default:
        return <InfoIcon />;
    }
  };

  return (
    <Paper 
      elevation={1} 
      className={getAlertClass(alert.level)}
      sx={{ 
        p: 2, 
        mb: 2, 
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        opacity: alert.acknowledged ? 0.7 : 1
      }}
    >
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Chip 
            icon={getLevelIcon(alert.level)}
            label={alert.level.toUpperCase()}
            size="small"
            sx={{ 
              mr: 2,
              backgroundColor: getAlertLevelColor(alert.level) + '20',
              color: getAlertLevelColor(alert.level),
              fontWeight: 'bold'
            }}
          />
          <Typography variant="subtitle1" component="div">
            {alert.service_name}
          </Typography>
        </Box>
        
        <Typography variant="body1" gutterBottom>
          {alert.message}
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          {formatDate(alert.timestamp)}
        </Typography>
      </Box>
      
      {!alert.acknowledged && (
        <IconButton 
          color="primary" 
          onClick={() => onAcknowledge(alert.id)}
          title="Acknowledge"
        >
          <AcknowledgeIcon />
        </IconButton>
      )}
    </Paper>
  );
};

export default AlertItem;