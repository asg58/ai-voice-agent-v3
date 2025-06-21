import React, { useContext } from 'react';
import { AppBar, Toolbar, Typography, Button, IconButton, Box } from '@mui/material';
import { Menu as MenuIcon, ExitToApp as LogoutIcon } from '@mui/icons-material';
import { AuthContext } from '../context/AuthContext';

/**
 * Header component with app bar and navigation
 * @param {Object} props - Component props
 * @param {Function} props.toggleDrawer - Function to toggle the drawer
 * @returns {JSX.Element} Header component
 */
const Header = ({ toggleDrawer }) => {
  const { user, logout } = useContext(AuthContext);

  return (
    <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={toggleDrawer}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI Voice Agent Dashboard
        </Typography>
        {user && (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="body1" sx={{ mr: 2 }}>
              {user.full_name || user.username}
            </Typography>
            <Button 
              color="inherit" 
              onClick={logout}
              startIcon={<LogoutIcon />}
            >
              Logout
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;