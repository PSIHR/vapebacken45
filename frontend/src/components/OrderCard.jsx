import { formatPrice, formatDate, getStatusText, getStatusColor } from '../utils/helpers';

const OrderCard = ({ order }) => {
  return (
    <div className="glass-panel p-4 mb-4">
      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="text-sm text-white/80">Заказ #{order.id}</span>
          <p className="text-xs text-white/60">{formatDate(order.created_at)}</p>
        </div>
        <span className={`text-sm font-semibold ${getStatusColor(order.status)}`}>
          {getStatusText(order.status)}
        </span>
      </div>
      
      <div className="border-t border-white/20 pt-3 mb-3">
        <h4 className="text-sm font-semibold text-white mb-2">Состав заказа:</h4>
        {order.items?.map((item, index) => (
          <div key={index} className="flex justify-between text-sm mb-1">
            <span className="text-white/80">
              {item.name} x{item.quantity}
              {item.tastes?.length > 0 && ` (${item.tastes.join(', ')})`}
            </span>
            <span className="text-white">{formatPrice(item.total_price)}</span>
          </div>
        ))}
      </div>

      <div className="border-t border-white/20 pt-3">
        <div className="flex justify-between items-center mb-2">
          <span className="text-white/80">Доставка:</span>
          <span className="text-white">{order.delivery}</span>
        </div>
        <div className="flex justify-between items-center mb-2">
          <span className="text-white/80">Адрес:</span>
          <span className="text-white text-sm">{order.address}</span>
        </div>
        {order.discount > 0 && (
          <div className="flex justify-between items-center mb-2">
            <span className="text-white/80">Скидка:</span>
            <span className="text-white/90">-{formatPrice(order.discount)}</span>
          </div>
        )}
        <div className="flex justify-between items-center font-bold text-lg border-t border-white/20 pt-2">
          <span className="text-white">Итого:</span>
          <span className="text-white font-bold">{formatPrice(order.total_price)}</span>
        </div>
      </div>
    </div>
  );
};

export default OrderCard;
