import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { apiFetch } from '../api';
import { useAuth } from '../context/auth-context';

const ProductDetail = () => {
    const { id } = useParams();
    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const { token } = useAuth();

    useEffect(() => {
        apiFetch(`/products/${id}`, {}, token)
            .then(data => {
                setProduct(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching product:", err);
                setLoading(false);
            });
    }, [id, token]);

    if (loading) return <div className="text-center py-10">Loading...</div>;
    if (!product) return <div className="text-center py-10">Product not found</div>;

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
                <div className="md:flex">
                    <div className="md:flex-shrink-0 md:w-1/2 bg-gray-50 p-8 flex items-center justify-center">
                        <img
                            className="h-96 w-full object-contain mix-blend-multiply"
                            src={product.image_url || 'https://via.placeholder.com/600'}
                            alt={product.title}
                        />
                    </div>
                    <div className="p-8 md:w-1/2 flex flex-col justify-center">
                        <div className="uppercase tracking-wide text-sm text-indigo-600 font-bold mb-2">{product.category}</div>
                        <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 leading-tight mb-4">
                            {product.title}
                        </h1>
                        <p className="text-3xl text-gray-900 font-bold mb-6">{product.price}</p>

                        <div className="prose prose-indigo text-gray-600 mb-8">
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                            <p className="leading-relaxed">
                                {product.description || "No description available."}
                            </p>
                        </div>

                        {product.features && product.features.length > 0 && (
                            <div className="mb-8">
                                <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Benefits</h3>
                                <ul className="space-y-2">
                                    {product.features.map((feature, idx) => (
                                        <li key={idx} className="flex items-start text-gray-600">
                                            <svg className="h-5 w-5 text-green-500 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                            </svg>
                                            {feature}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <div className="mt-auto pt-6 border-t border-gray-100">
                            <a
                                href={product.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="w-full md:w-auto inline-flex items-center justify-center px-8 py-4 border border-transparent text-lg font-medium rounded-xl text-white bg-indigo-600 hover:bg-indigo-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                            >
                                Buy Now on Traya
                                <svg className="ml-2 -mr-1 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProductDetail;
