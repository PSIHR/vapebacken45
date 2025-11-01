import { useNavigate } from 'react-router-dom';
import { ShoppingCart, Plus } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const ProductCard = ({ product, onAddToCart }) => {
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate(`/product/${product.id}`);
  };

  const handleAddToCart = (e) => {
    e.stopPropagation();
    onAddToCart(product);
  };

  return (
    <div 
      onClick={handleCardClick}
      className="glass-card overflow-hidden hover:shadow-xl transition-all cursor-pointer"
    >
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
        <div className="flex items-center justify-between">
          <span className="text-lg font-semibold text-white">
            {formatPrice(product.price)}
          </span>
          <button
            onClick={handleAddToCart}
            className="bg-white/30 hover:bg-white/40 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-all backdrop-blur-sm"
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
