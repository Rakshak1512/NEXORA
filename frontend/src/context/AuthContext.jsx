import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('cynera_user') || localStorage.getItem('cicada_user');
    const savedOrg = localStorage.getItem('cynera_org');
    const token = localStorage.getItem('cynera_token') || localStorage.getItem('cicada_token');

    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
        if (savedOrg) {
          setOrganization(JSON.parse(savedOrg));
        }
      } catch (e) {
        localStorage.removeItem('cynera_user');
        localStorage.removeItem('cynera_org');
      }
    }
    setLoading(false);
  }, []);

  const setSession = (accessToken, userData, orgData = null) => {
    localStorage.setItem('cynera_token', accessToken);
    localStorage.setItem('cynera_user', JSON.stringify(userData));
    setUser(userData);
    if (orgData) {
      localStorage.setItem('cynera_org', JSON.stringify(orgData));
      setOrganization(orgData);
    }
  };

  const login = async (email, password, require2fa = false) => {
    const res = await api.post('/auth/login', { email, password, require_2fa: require2fa });
    const data = res.data;
    if (data.status === 'otp_required') {
      return { requireOtp: true, email: data.email };
    }
    const { access_token, user: userData, organization: orgData } = data;
    setSession(access_token, userData, orgData);
    return { success: true, user: userData };
  };

  const demoLogin = async (email) => {
    const res = await api.post('/auth/demo-login', { email });
    const { access_token, user: userData, organization: orgData } = res.data;
    setSession(access_token, userData, orgData);
    return { success: true, user: userData };
  };

  const register = async (formData) => {
    // If formData is an object with organization fields, call /auth/register-org
    if (formData.organization_name) {
      const res = await api.post('/auth/register-org', formData);
      return res.data; // { status: "otp_sent", email, purpose, message }
    } else {
      // Legacy register
      const res = await api.post('/auth/register', formData);
      const { access_token, user: userData, organization: orgData } = res.data;
      setSession(access_token, userData, orgData);
      return { success: true, user: userData };
    }
  };

  const logout = () => {
    localStorage.removeItem('cynera_token');
    localStorage.removeItem('cynera_user');
    localStorage.removeItem('cynera_org');
    localStorage.removeItem('cicada_token');
    localStorage.removeItem('cicada_user');
    setUser(null);
    setOrganization(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      organization, 
      loading, 
      login, 
      demoLogin,
      register, 
      setSession, 
      logout, 
      isAuthenticated: !!user 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
