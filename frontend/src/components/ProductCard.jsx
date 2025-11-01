import { ShoppingCart, Plus } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const ProductCard = ({ product, onAddToCart }) => {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      <div className="relative h-48 bg-gray-200">
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <ShoppingCart size={48} />
          </div>
        )}
      </div>
      <div className="p-4">
        <div className="mb-2">
          {product.category && (
            <span className="text-xs text-blue-600 font-semibold">
              {product.category.name}
            </span>
          )}
        </div>
        <h3 className="text-lg font-bold text-gray-800 mb-1">{product.name}</h3>
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {product.description}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold text-green-600">
            {formatPrice(product.price)}
          </span>
          <button
            onClick={() => onAddToCart(product)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus size={18} />
            В корзину
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
