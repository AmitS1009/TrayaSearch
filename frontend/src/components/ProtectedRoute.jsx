import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/auth-context';

const ProtectedRoute = ({ children }) => {
    const { token } = useAuth();
    const location = useLocation();
    return token ? children : <Navigate to="/login" replace state={{ from: location.pathname }} />;
};

export default ProtectedRoute;
