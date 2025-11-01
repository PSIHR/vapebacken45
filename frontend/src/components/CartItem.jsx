import { Minus, Plus, Trash2 } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const CartItem = ({ item, onUpdateQuantity, onRemove }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4 mb-3">
      <div className="flex gap-3">
        <div className="w-20 h-20 rounded-lg bg-gray-200 flex-shrink-0 overflow-hidden">
          {item.image ? (
            <img
              src={item.image}
              alt={item.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <Trash2 size={24} />
            </div>
          )}
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-800">{item.name}</h4>
          {item.selected_taste && (
            <p className="text-sm text-gray-600">Вкус: {item.selected_taste}</p>
          )}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}
                className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300"
                disabled={item.quantity <= 1}
              >
                <Minus size={16} />
              </button>
              <span className="w-8 text-center font-semibold">{item.quantity}</span>
              <button
                onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300"
              >
                <Plus size={16} />
              </button>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-bold text-green-600">
                {formatPrice(item.price * item.quantity)}
              </span>
              <button
                onClick={() => onRemove(item.id)}
                className="text-red-500 hover:text-red-700"
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
