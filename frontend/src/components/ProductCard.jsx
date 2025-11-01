import { ShoppingCart, Plus } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const ProductCard = ({ product, onAddToCart }) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="relative h-48 bg-gray-100">
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
            <span className="inline-block px-2 py-1 text-xs font-medium text-[#3390ec] bg-blue-50 rounded">
              {product.category.name}
            </span>
          )}
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-1">{product.name}</h3>
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {product.description}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold text-gray-900">
            {formatPrice(product.price)}
          </span>
          <button
            onClick={() => onAddToCart(product)}
            className="bg-[#3390ec] hover:bg-[#2b7cd3] text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus size={18} />
            <span className="font-medium">В корзину</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
