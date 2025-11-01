import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { basketAPI, ordersAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import { formatPrice } from '../utils/helpers';
import { Loader2 } from 'lucide-react';

const Checkout = () => {
  const [cartItems, setCartItems] = useState([]);
  const [totalPrice, setTotalPrice] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    address: '',
    telephone: '',
    payment: 'Наличные',
    delivery: 'Курьером',
    promocode: '',
  });

  const { user, showAlert } = useTelegram();
  const navigate = useNavigate();

  useEffect(() => {
    loadCart();
  }, [user]);

  const loadCart = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const response = await basketAPI.get(user.id);
      setCartItems(response.data.items || []);
      setTotalPrice(response.data.total_price || 0);
    } catch (error) {
      console.error('Error loading cart:', error);
      showAlert('Ошибка загрузки корзины');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.address || !formData.telephone) {
      showAlert('Заполните все обязательные поля');
      return;
    }

    try {
      setSubmitting(true);
      await ordersAPI.createFromBasket(user.id, formData);
      showAlert('Заказ успешно оформлен!');
      navigate('/orders');
    } catch (error) {
      console.error('Error creating order:', error);
      showAlert(error.response?.data?.detail || 'Ошибка создания заказа');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-blue-600" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <div className="container mx-auto px-4 py-8 pb-24">
        <h1 className="text-4xl font-extrabold mb-8 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
          📝 Оформление заказа
        </h1>

        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 mb-6 border border-purple-100">
          <h3 className="font-bold text-xl mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Ваш заказ:
          </h3>
          {cartItems.map((item) => (
            <div key={item.id} className="flex justify-between mb-3 text-base p-2 hover:bg-purple-50 rounded-lg transition-colors">
              <span className="text-gray-800 font-medium">
                {item.name} <span className="text-purple-600 font-bold">x{item.quantity}</span>
              </span>
              <span className="font-bold bg-gradient-to-r from-green-500 to-emerald-600 bg-clip-text text-transparent">
                {formatPrice(item.price * item.quantity)}
              </span>
            </div>
          ))}
          <div className="border-t border-purple-100 mt-4 pt-4 flex justify-between font-extrabold text-2xl">
            <span>Итого:</span>
            <span className="bg-gradient-to-r from-green-500 to-emerald-600 bg-clip-text text-transparent">
              {formatPrice(totalPrice)}
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-purple-100">
          <div className="mb-5">
            <label className="block text-gray-800 font-bold mb-2 text-lg">
              📍 Адрес доставки <span className="text-red-500">*</span>
            </label>
            <textarea
              name="address"
              value={formData.address}
              onChange={handleChange}
              className="w-full px-4 py-3 border-2 border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              rows="3"
              placeholder="Улица, дом, квартира"
              required
            />
          </div>

          <div className="mb-5">
            <label className="block text-gray-800 font-bold mb-2 text-lg">
              📱 Телефон <span className="text-red-500">*</span>
            </label>
            <input
              type="tel"
              name="telephone"
              value={formData.telephone}
              onChange={handleChange}
              className="w-full px-4 py-3 border-2 border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              placeholder="+7 (999) 123-45-67"
              required
            />
          </div>

          <div className="mb-5">
            <label className="block text-gray-800 font-bold mb-2 text-lg">
              💳 Способ оплаты
            </label>
            <select
              name="payment"
              value={formData.payment}
              onChange={handleChange}
              className="w-full px-4 py-3 border-2 border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all bg-white"
            >
              <option value="Наличные">💵 Наличные</option>
              <option value="Карта">💳 Карта</option>
            </select>
          </div>

          <div className="mb-5">
            <label className="block text-gray-800 font-bold mb-2 text-lg">
              🚚 Способ доставки
            </label>
            <select
              name="delivery"
              value={formData.delivery}
              onChange={handleChange}
              className="w-full px-4 py-3 border-2 border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all bg-white"
            >
              <option value="Курьером">🚚 Курьером</option>
              <option value="Самовывоз">🏪 Самовывоз</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-gray-800 font-bold mb-2 text-lg">
              🎁 Промокод
            </label>
            <input
              type="text"
              name="promocode"
              value={formData.promocode}
              onChange={handleChange}
              className="w-full px-4 py-3 border-2 border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              placeholder="Введите промокод"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white py-4 rounded-xl font-bold text-lg transition-all duration-300 transform hover:scale-105 shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="animate-spin" size={24} />
                Оформление...
              </>
            ) : (
              <>
                ✨ Подтвердить заказ
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Checkout;
