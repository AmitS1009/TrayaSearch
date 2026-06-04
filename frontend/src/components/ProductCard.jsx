import React from 'react';

const ProductCard = ({ product, onClick }) => {
    return (
        <div
            className="group bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-1"
            onClick={() => onClick(product.id)}
        >
            <div className="h-64 overflow-hidden bg-gray-50 flex items-center justify-center p-4">
                <img
                    src={product.image_url || 'https://via.placeholder.com/300'}
                    alt={product.title}
                    className="h-full w-full object-contain group-hover:scale-105 transition-transform duration-300"
                />
            </div>
            <div className="p-5">
                <div className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-1">{product.category}</div>
                <h3 className="text-lg font-bold text-gray-900 line-clamp-2 h-14" title={product.title}>
                    {product.title}
                </h3>
                <div className="mt-4 flex justify-between items-center">
                    <span className="text-xl font-bold text-gray-900">{product.price}</span>
                    <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm">
                        View Details
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ProductCard;
