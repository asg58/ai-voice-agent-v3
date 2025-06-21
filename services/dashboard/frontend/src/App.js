import React, { useState, useContext } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, Toolbar, CssBaseline } from '@mui/material';
import { AuthContext } from './context/AuthContext';

// Components
import Header from './components/Header';
import Sidebar from './components/Sidebar';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Services from './pages/Services';
import Alerts from './pages/Alerts';

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useContext(AuthContext);
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

function App() {
  const [drawerOpen, setDrawerOpen] = useState(true);
  const { isAuthenticated } = useContext(AuthContext);
  
  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };
  
  // Drawer width for content margin
  const drawerWidth = 240;
  
  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {isAuthenticated && (
        <>
          <Header toggleDrawer={toggleDrawer} />
          <Sidebar open={drawerOpen} />
        </>
      )}
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerOpen ? drawerWidth : 0}px)` },
          ml: { sm: drawerOpen ? `${drawerWidth}px` : 0 },
          transition: theme => theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        {isAuthenticated && <Toolbar />}
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/services" element={
            <ProtectedRoute>
              <Services />
            </ProtectedRoute>
          } />
          <Route path="/alerts" element={
            <ProtectedRoute>
              <Alerts />
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default App;