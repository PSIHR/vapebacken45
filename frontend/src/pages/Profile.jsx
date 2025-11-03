import { useState, useEffect } from 'react';
import { useTelegram } from '../hooks/useTelegram';
import { userAPI } from '../services/api';
import LoyaltyCard from '../components/LoyaltyCard';
import { Loader2, Package, Calendar, MapPin } from 'lucide-react';
import { formatPrice } from '../utils/helpers';

const Profile = () => {
  const [loyaltyData, setLoyaltyData] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, showAlert } = useTelegram();

  useEffect(() => {
    if (user?.id) {
      loadData();
    }
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [loyaltyResponse, ordersResponse] = await Promise.all([
        userAPI.getLoyalty(user.id),
        userAPI.getOrders(user.id)
      ]);

      setLoyaltyData(loyaltyResponse.data);
      setOrders(ordersResponse.data || []);
    } catch (error) {
      console.error('Error loading profile data:', error);
      showAlert('Ошибка загрузки данных профиля');
    } finally {
      setLoading(false);
    }
  };

  const getStatusText = (status) => {
    const statusMap = {
      waiting_for_courier: 'Ожидает курьера',
      in_delivery: 'В доставке',
      delivered: 'Доставлен',
      cancelled: 'Отменен'
    };
    return statusMap[status] || status;
  };

  const getStatusColor = (status) => {
    const colorMap = {
      waiting_for_courier: 'bg-white/20 text-white/90',
      in_delivery: 'bg-white/30 text-white',
      delivered: 'bg-white/40 text-white',
      cancelled: 'bg-gray-600/30 text-gray-300'
    };
    return colorMap[status] || 'bg-gray-500/20 text-gray-300';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-white" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-24">
      <div className="container mx-auto px-4 py-6">
        {/* User Info */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Профиль</h1>
          <p className="text-white/60">@{user?.username || 'Пользователь'}</p>
        </div>

        {/* Loyalty Card */}
        {loyaltyData && <LoyaltyCard loyaltyData={loyaltyData} />}

        {/* Orders Section */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-white mb-4">Мои заказы</h2>
          
          {orders.length === 0 ? (
            <div className="glass-panel text-center py-16">
              <Package className="mx-auto mb-4 text-white/40" size={64} />
              <p className="text-white/60 text-lg">У вас пока нет заказов</p>
            </div>
          ) : (
            <div className="space-y-4">
              {orders.map((order) => (
                <div key={order.id} className="glass-panel p-4 hover:bg-white/10 transition-all">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-white font-bold text-lg">Заказ №{order.id}</h3>
                      <div className="flex items-center gap-2 text-white/60 text-sm mt-1">
                        <Calendar size={14} />
                        <span>{new Date(order.created_at).toLocaleDateString('ru-RU')}</span>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                      {getStatusText(order.status)}
                    </span>
                  </div>

                  {/* Order Items */}
                  <div className="mb-3 space-y-2">
                    {order.items?.map((item, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-white/80">
                          {item.name} 
                          {item.selected_taste && ` (${item.selected_taste})`}
                          {' '}x{item.quantity}
                        </span>
                        <span className="text-white font-medium">
                          {formatPrice(item.total_price)} BYN
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Delivery Info */}
                  <div className="flex items-start gap-2 text-white/60 text-sm mb-3">
                    <MapPin size={14} className="mt-0.5 flex-shrink-0" />
                    <span>{order.address}</span>
                  </div>

                  {/* Total */}
                  <div className="pt-3 border-t border-white/10 flex justify-between items-center">
                    <span className="text-white/80">Итого:</span>
                    <span className="text-white font-bold text-xl">
                      {formatPrice(order.total_price)} BYN
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
