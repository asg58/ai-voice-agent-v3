/**
 * Format a date to a readable string
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
export const formatDate = (date) => {
  if (!date) return 'N/A';
  const d = new Date(date);
  return d.toLocaleString();
};

/**
 * Format bytes to a human-readable string
 * @param {number} bytes - Bytes to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted bytes string
 */
export const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Format a percentage value
 * @param {number} value - Percentage value
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value) => {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)}%`;
};

/**
 * Get status color based on value
 * @param {number} value - Value to check
 * @param {number} warningThreshold - Warning threshold
 * @param {number} errorThreshold - Error threshold
 * @returns {string} Status color
 */
export const getStatusColor = (value, warningThreshold = 70, errorThreshold = 90) => {
  if (value >= errorThreshold) return '#f44336'; // Red
  if (value >= warningThreshold) return '#ff9800'; // Orange
  return '#4caf50'; // Green
};

/**
 * Get alert level color
 * @param {string} level - Alert level
 * @returns {string} Alert level color
 */
export const getAlertLevelColor = (level) => {
  switch (level.toLowerCase()) {
    case 'critical':
      return '#f44336'; // Red
    case 'error':
      return '#ff5722'; // Deep Orange
    case 'warning':
      return '#ff9800'; // Orange
    case 'info':
      return '#2196f3'; // Blue
    default:
      return '#757575'; // Grey
  }
};

/**
 * Get service status color
 * @param {string} status - Service status
 * @returns {string} Status color
 */
export const getServiceStatusColor = (status) => {
  switch (status.toLowerCase()) {
    case 'healthy':
      return '#4caf50'; // Green
    case 'warning':
      return '#ff9800'; // Orange
    case 'error':
      return '#f44336'; // Red
    default:
      return '#757575'; // Grey
  }
};