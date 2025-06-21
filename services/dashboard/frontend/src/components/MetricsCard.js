import React from 'react';
import { Card, CardContent, Typography, Box, LinearProgress } from '@mui/material';
import { formatPercentage, getStatusColor } from '../utils/formatters';

/**
 * Metrics card component for displaying a metric with a progress bar
 * @param {Object} props - Component props
 * @param {string} props.title - Card title
 * @param {number} props.value - Metric value
 * @param {string} props.unit - Metric unit
 * @param {number} props.max - Maximum value for the progress bar
 * @param {number} props.warningThreshold - Warning threshold
 * @param {number} props.errorThreshold - Error threshold
 * @returns {JSX.Element} MetricsCard component
 */
const MetricsCard = ({ 
  title, 
  value, 
  unit = '%', 
  max = 100,
  warningThreshold = 70,
  errorThreshold = 90
}) => {
  // Calculate progress value
  const progress = (value / max) * 100;
  
  // Get status color based on value
  const statusColor = getStatusColor(value, warningThreshold, errorThreshold);

  return (
    <Card className="card">
      <CardContent className="card-content">
        <Typography variant="h6" component="div" gutterBottom>
          {title}
        </Typography>
        <Typography variant="h4" component="div" sx={{ color: statusColor }}>
          {unit === '%' ? formatPercentage(value) : `${value} ${unit}`}
        </Typography>
        <Box sx={{ mt: 2 }}>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ 
              height: 10, 
              borderRadius: 5,
              backgroundColor: '#e0e0e0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: statusColor
              }
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default MetricsCard;