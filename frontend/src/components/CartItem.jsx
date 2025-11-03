import { Minus, Plus, Trash2 } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const CartItem = ({ item, onUpdateQuantity, onRemove }) => {
  return (
    <div className="glass-panel p-4">
      <div className="flex gap-3">
        <div className="w-20 h-20 rounded-lg bg-white/10 flex-shrink-0 overflow-hidden">
          {item.image ? (
            <img
              src={item.image}
              alt={item.name}
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-white/40">
              <Trash2 size={24} />
            </div>
          )}
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-white">{item.name}</h4>
          {item.selected_taste && (
            <p className="text-sm text-white/80">Вкус: {item.selected_taste}</p>
          )}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}
                className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
                disabled={item.quantity <= 1}
              >
                <Minus size={16} className="text-white" />
              </button>
              <span className="w-8 text-center font-semibold text-white">{item.quantity}</span>
              <button
                onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
              >
                <Plus size={16} className="text-white" />
              </button>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-bold text-white">
                {formatPrice(item.price * item.quantity)}
              </span>
              <button
                onClick={() => onRemove(item.id)}
                className="text-white/80 hover:text-white transition-colors"
              >
                <Trash2 size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartItem;
