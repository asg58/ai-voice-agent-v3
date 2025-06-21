import React from 'react';
import { 
  Drawer, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Toolbar,
  Divider
} from '@mui/material';
import { 
  Dashboard as DashboardIcon,
  Memory as ServicesIcon,
  Timeline as MetricsIcon,
  Notifications as AlertsIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

// Drawer width
const drawerWidth = 240;

/**
 * Sidebar component with navigation links
 * @param {Object} props - Component props
 * @param {boolean} props.open - Whether the drawer is open
 * @returns {JSX.Element} Sidebar component
 */
const Sidebar = ({ open }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Navigation items
  const navItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Services', icon: <ServicesIcon />, path: '/services' },
    { text: 'Metrics', icon: <MetricsIcon />, path: '/metrics' },
    { text: 'Alerts', icon: <AlertsIcon />, path: '/alerts' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' }
  ];

  return (
    <Drawer
      variant="persistent"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <Divider />
      <List>
        {navItems.map((item) => (
          <ListItem 
            button 
            key={item.text}
            onClick={() => navigate(item.path)}
            selected={location.pathname === item.path}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;