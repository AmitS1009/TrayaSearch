import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/auth-context';

const AuthPage = ({ mode }) => {
    const isRegister = mode === 'register';
    const { login, register } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [form, setForm] = useState({ email: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const submit = async (event) => {
        event.preventDefault();
        setError('');
        setLoading(true);
        try {
            await (isRegister ? register(form) : login(form));
            navigate(location.state?.from || '/chat', { replace: true });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-64px)] grid place-items-center px-4 py-12">
            <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                <p className="text-sm font-bold uppercase tracking-[0.2em] text-indigo-600">Neusearch AI</p>
                <h1 className="text-3xl font-black text-gray-900 mt-2">
                    {isRegister ? 'Create your account' : 'Welcome back'}
                </h1>
                <p className="text-gray-500 mt-2">
                    {isRegister ? 'Save recommendations and revisit your searches.' : 'Continue your product discovery.'}
                </p>
                <form onSubmit={submit} className="mt-8 space-y-4">
                    <label className="block">
                        <span className="text-sm font-medium text-gray-700">Email</span>
                        <input
                            type="email"
                            required
                            value={form.email}
                            onChange={(event) => setForm({ ...form, email: event.target.value })}
                            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </label>
                    <label className="block">
                        <span className="text-sm font-medium text-gray-700">Password</span>
                        <input
                            type="password"
                            minLength={8}
                            required
                            value={form.password}
                            onChange={(event) => setForm({ ...form, password: event.target.value })}
                            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </label>
                    {error && <p className="text-sm text-red-600">{error}</p>}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full rounded-lg bg-indigo-600 px-4 py-3 font-bold text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                        {loading ? 'Please wait...' : isRegister ? 'Register' : 'Log in'}
                    </button>
                </form>
                <p className="text-sm text-gray-500 mt-6">
                    {isRegister ? 'Already registered?' : 'New to Neusearch?'}{' '}
                    <Link className="font-bold text-indigo-600" to={isRegister ? '/login' : '/register'}>
                        {isRegister ? 'Log in' : 'Create an account'}
                    </Link>
                </p>
            </div>
        </div>
    );
};

export default AuthPage;
