import { useNavigate } from 'react-router-dom';
import { ShoppingCart, ChevronRight } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const ProductCard = ({ product }) => {
  const navigate = useNavigate();

  const handleSelectClick = () => {
    navigate(`/product/${product.id}`);
  };

  return (
    <div className="glass-card overflow-hidden hover:shadow-xl transition-all hover:border-cyan-400/40">
      <div className="relative h-48 bg-gradient-to-br from-cyan-500/10 to-purple-500/10">
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-contain relative z-10"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-cyan-400/50">
            <ShoppingCart size={48} />
          </div>
        )}
      </div>
      <div className="p-4 relative z-10">
        <div className="mb-2">
          {product.category && (
            <span className="inline-block px-2 py-1 text-xs font-medium text-cyan-400 bg-cyan-500/20 rounded-full border border-cyan-500/30">
              {product.category.name}
            </span>
          )}
        </div>
        <h3 className="text-xl font-bold text-white mb-1">{product.name}</h3>
        <p className="text-sm text-gray-400 mb-3 line-clamp-2">
          {product.description}
        </p>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
            {formatPrice(product.price)}
          </span>
          <button
            onClick={handleSelectClick}
            className="w-full sm:w-auto px-4 py-2.5 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 backdrop-blur-sm text-white rounded-lg font-medium transition-all flex items-center justify-center gap-2 group shadow-lg shadow-cyan-500/20"
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
