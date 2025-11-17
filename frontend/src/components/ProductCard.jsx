import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart, ChevronRight, Search, X } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const ProductCard = ({ product }) => {
  const navigate = useNavigate();
  const [showTastesModal, setShowTastesModal] = useState(false);

  const handleSelectClick = () => {
    navigate(`/product/${product.id}`, { 
      state: { categoryId: product.category?.id } 
    });
  };

  const handleTastesClick = (e) => {
    e.stopPropagation();
    setShowTastesModal(true);
  };

  const handleCloseModal = (e) => {
    e.stopPropagation();
    setShowTastesModal(false);
  };

  const handleGoToProduct = () => {
    setShowTastesModal(false);
    navigate(`/product/${product.id}`, { 
      state: { categoryId: product.category?.id } 
    });
  };

  const getStrengthBadge = () => {
    if (!product.strength) {
      if (product.category?.name === 'РАСХОДНИКИ') {
        return (
          <span className="inline-block px-2 py-1 text-xs font-medium text-cyan-400 bg-cyan-500/20 rounded-full border border-cyan-500/30">
            {product.category.name}
          </span>
        );
      }
      return null;
    }

    const strengthMatch = product.strength.match(/(\d+)\s*(?:mg|мг)?/i);
    if (!strengthMatch) return null;

    const strengthValue = parseInt(strengthMatch[1]);
    let bgColor, textColor, borderColor;

    if (strengthValue >= 70) {
      bgColor = 'bg-red-900/40';
      textColor = 'text-red-300';
      borderColor = 'border-red-700/50';
    } else if (strengthValue >= 40) {
      bgColor = 'bg-red-500/30';
      textColor = 'text-red-200';
      borderColor = 'border-red-500/40';
    } else {
      bgColor = 'bg-green-500/30';
      textColor = 'text-green-200';
      borderColor = 'border-green-500/40';
    }

    return (
      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full border ${bgColor} ${textColor} ${borderColor}`}>
        {product.strength}
      </span>
    );
  };

  return (
    <>
      <div className="glass-card overflow-hidden hover:shadow-xl transition-all hover:border-cyan-400/40 flex flex-col">
        <div className="relative h-36">
          {product.image ? (
            <img
              src={product.image}
              alt={product.name}
              loading="lazy"
              className="w-full h-full object-contain relative z-10"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-cyan-400/50">
              <ShoppingCart size={40} />
            </div>
          )}
        </div>
        <div className="p-2.5 relative z-10 flex flex-col flex-1">
          <div className="mb-1">
            {getStrengthBadge()}
          </div>
          <h3 className="text-base font-bold text-white mb-1 line-clamp-2">{product.name}</h3>
          <div className="mt-auto">
            <span className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent block mb-1.5">
              {formatPrice(product.price)}
            </span>
            <div className="flex gap-1.5">
              {product.tastes && product.tastes.length > 0 && (
                <button
                  onClick={handleTastesClick}
                  className="flex-shrink-0 p-1.5 bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-500 hover:to-pink-400 backdrop-blur-sm text-white rounded-md transition-all shadow-lg shadow-purple-500/20"
                  title="Просмотр вкусов"
                >
                  <Search size={16} />
                </button>
              )}
              <button
                onClick={handleSelectClick}
                className="flex-1 px-2.5 py-1.5 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 backdrop-blur-sm text-white rounded-md font-medium transition-all flex items-center justify-center gap-1 group shadow-lg shadow-cyan-500/20 text-xs"
              >
                Выбрать
                <ChevronRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tastes Modal */}
      {showTastesModal && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={handleCloseModal}
        >
          <div
            className="glass-panel max-w-md w-full max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-black/40 backdrop-blur-md p-4 flex justify-between items-center border-b border-white/10">
              <h3 className="text-xl font-bold text-white">Доступные вкусы</h3>
              <button
                onClick={handleCloseModal}
                className="text-white/60 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            
            <div className="p-4 space-y-2">
              {product.tastes && product.tastes.map((taste) => (
                <div
                  key={taste.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10 hover:border-cyan-400/40 transition-all"
                >
                  <span className="text-white font-medium">{taste.name}</span>
                  {taste.image && (
                    <div className="w-10 h-10 rounded-lg overflow-hidden">
                      <img 
                        src={taste.image} 
                        alt={taste.name}
                        loading="lazy"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="sticky bottom-0 bg-black/40 backdrop-blur-md p-4 border-t border-white/10">
              <button
                onClick={handleGoToProduct}
                className="w-full px-4 py-3 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-white rounded-lg font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
              >
                Перейти к товару
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ProductCard;
