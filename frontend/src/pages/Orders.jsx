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
        <Loader2 className="animate-spin text-blue-600" size={48} />
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="text-center">
          <Package className="mx-auto text-gray-400 mb-4" size={64} />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Нет заказов</h2>
          <p className="text-gray-600">У вас пока нет оформленных заказов</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Мои заказы</h1>
      <div>
        {orders.map((order) => (
          <OrderCard key={order.id} order={order} />
        ))}
      </div>
    </div>
  );
};

export default Orders;
