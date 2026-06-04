import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/auth-context';

const Navbar = () => {
    const { token, user, logout } = useAuth();
    return (
        <nav className="bg-white shadow-sm sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <Link to="/" className="flex-shrink-0 flex items-center">
                            <span className="text-2xl font-bold text-indigo-600">Neusearch AI</span>
                        </Link>
                    </div>
                    <div className="flex items-center space-x-4">
                        <Link to="/" className="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">
                            Home
                        </Link>
                        {token ? (
                            <>
                                <Link to="/metrics" className="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">
                                    Metrics
                                </Link>
                                <span className="hidden md:inline text-sm text-gray-500">{user?.email}</span>
                                <Link to="/chat" className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors">
                                    AI Assistant
                                </Link>
                                <button type="button" onClick={logout} className="text-sm font-medium text-gray-600 hover:text-red-600">
                                    Log out
                                </button>
                            </>
                        ) : (
                            <>
                                <Link to="/login" className="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">
                                    Log in
                                </Link>
                                <Link to="/register" className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors">
                                    Get started
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
