import React, { useState } from 'react';
import { apiFetch } from '../api';
import { AuthContext } from './auth-context';


export function AuthProvider({ children }) {
    const [token, setToken] = useState(null);
    const [user, setUser] = useState(null);

    const authenticate = async (path, credentials) => {
        const result = await apiFetch(path, {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
        setToken(result.access_token);
        const profile = await apiFetch('/auth/me', {}, result.access_token);
        setUser(profile);
    };

    const value = {
        token,
        user,
        login: (credentials) => authenticate('/auth/login', credentials),
        register: (credentials) => authenticate('/auth/register', credentials),
        logout: () => {
            setToken(null);
            setUser(null);
        },
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
