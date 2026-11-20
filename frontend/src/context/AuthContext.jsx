import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('cicada_user');
    const token = localStorage.getItem('cicada_token');
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('cicada_user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('cicada_token', access_token);
    localStorage.setItem('cicada_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const register = async (email, password, fullName, role = 'Operator') => {
    const res = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      role
    });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('cicada_token', access_token);
    localStorage.setItem('cicada_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('cicada_token');
    localStorage.removeItem('cicada_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

