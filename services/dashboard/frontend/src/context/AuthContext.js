import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

// Create the auth context
export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is already logged in on component mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUserData(token);
    } else {
      setLoading(false);
    }
  }, []);

  // Fetch user data using the token
  const fetchUserData = async (token) => {
    try {
      const response = await axios.get('/api/v1/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setUser(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching user data:', err);
      localStorage.removeItem('token');
      setLoading(false);
    }
  };

  // Login function
  const login = async (username, password) => {
    try {
      setError(null);
      const response = await axios.post('/api/v1/auth/login', {
        username,
        password
      });
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      await fetchUserData(access_token);
      return true;
    } catch (err) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
      return false;
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  // Context value
  const value = {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};