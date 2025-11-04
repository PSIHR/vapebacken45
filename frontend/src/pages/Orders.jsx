import { useState, useEffect } from 'react';
import { userAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import OrderCard from '../components/OrderCard';
import { Package, Loader2 } from 'lucide-react';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, showAlert } = useTelegram();

  useEffect(() => {
    loadOrders();
  }, [user]);

  const loadOrders = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const response = await userAPI.getOrders(user.id);
      setOrders(response.data || []);
    } catch (error) {
      console.error('Error loading orders:', error);
      showAlert('Ошибка загрузки заказов');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-pink-500" size={48} />
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="min-h-screen">
        <div className="container mx-auto px-4 py-12">
          <div className="text-center glass-panel p-12 rounded-lg shadow-xl">
            <Package className="mx-auto text-pink-300 mb-4" size={64} />
            <h2 className="text-3xl font-bold text-gray-800 mb-2">Ваши заказы</h2>
            <p className="text-gray-700 text-lg">У вас пока нет оформленных заказов. Свяжитесь с нами для консультации.</p>
            <p className="text-gray-600 mt-4">По вопросам: @baster_mks</p>
            <p className="text-gray-600">Находимся в Беларуси, Минск.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">Мои заказы</h1>
        <div>
          {orders.map((order) => (
            <OrderCard key={order.id} order={order} />
          ))}
        </div>
        <div className="mt-8 text-center">
          <p className="text-gray-700">По вопросам: @baster_mks</p>
          <p className="text-gray-600">Находимся в Беларуси, Минск.</p>
        </div>
      </div>
    </div>
  );
};

export default Orders;