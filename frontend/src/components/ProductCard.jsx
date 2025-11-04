import { useNavigate } from 'react-router-dom';
import { ShoppingCart, ChevronRight } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const ProductCard = ({ product }) => {
  const navigate = useNavigate();

  const handleSelectClick = () => {
    navigate(`/product/${product.id}`);
  };

  return (
    <div className="glass-card overflow-hidden hover:shadow-xl transition-all">
      <div className="relative h-48 bg-pink-50">
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-contain relative z-10"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-pink-300">
            <ShoppingCart size={48} />
          </div>
        )}
      </div>
      <div className="p-4 relative z-10">
        <div className="mb-2">
          {product.category && (
            <span className="inline-block px-2 py-1 text-xs font-medium text-pink-600 bg-pink-100 rounded-full">
              {product.category.name}
            </span>
          )}
        </div>
        <h3 className="text-xl font-bold text-gray-800 mb-1">{product.name}</h3>
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {product.description}
        </p>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <span className="text-2xl font-bold text-pink-600">
            {formatPrice(product.price)}
          </span>
          <button
            onClick={handleSelectClick}
            className="w-full sm:w-auto px-4 py-2.5 bg-pink-500 hover:bg-pink-600 backdrop-blur-sm text-white rounded-lg font-medium transition-all flex items-center justify-center gap-2 group"
          >
            Выбрать
            <ChevronRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
