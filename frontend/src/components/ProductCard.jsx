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
      <div className="relative h-48 bg-white/10">
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-contain relative z-10"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-white/60">
            <ShoppingCart size={48} />
          </div>
        )}
      </div>
      <div className="p-4 relative z-10">
        <div className="mb-2">
          {product.category && (
            <span className="inline-block px-2 py-1 text-xs font-medium text-white bg-white/20 rounded-full">
              {product.category.name}
            </span>
          )}
        </div>
        <h3 className="text-xl font-bold text-white mb-1">{product.name}</h3>
        <p className="text-sm text-white/80 mb-3 line-clamp-2">
          {product.description}
        </p>
        <div className="flex items-center justify-between gap-3">
          <span className="text-2xl font-bold text-white">
            {formatPrice(product.price)}
          </span>
          <button
            onClick={handleSelectClick}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white rounded-lg font-medium transition-all flex items-center gap-2 group"
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
