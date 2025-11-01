import { ShoppingCart, Plus, Sparkles } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const ProductCard = ({ product, onAddToCart }) => {
  return (
    <div className="group bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 border border-gray-100">
      <div className="relative h-56 bg-gradient-to-br from-gray-100 to-gray-200 overflow-hidden">
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 group-hover:text-gray-500 transition-colors">
            <ShoppingCart size={64} className="animate-bounce-subtle" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      </div>
      <div className="p-5">
        <div className="mb-2 flex items-center gap-2">
          {product.category && (
            <span className="px-3 py-1 text-xs font-bold bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-full shadow-md">
              {product.category.name}
            </span>
          )}
          <Sparkles size={14} className="text-yellow-500" />
        </div>
        <h3 className="text-xl font-bold text-gray-800 mb-2 group-hover:text-blue-600 transition-colors">{product.name}</h3>
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {product.description}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-3xl font-extrabold bg-gradient-to-r from-green-500 to-emerald-600 bg-clip-text text-transparent">
            {formatPrice(product.price)}
          </span>
          <button
            onClick={() => onAddToCart(product)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-5 py-3 rounded-xl flex items-center gap-2 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
          >
            <Plus size={20} />
            <span className="font-semibold">В корзину</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
