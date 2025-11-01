import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { basketAPI, ordersAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import { formatPrice } from '../utils/helpers';
import { metroLines } from '../data/metroData';
import { Loader2 } from 'lucide-react';

const Checkout = () => {
  const [cartItems, setCartItems] = useState([]);
  const [totalPrice, setTotalPrice] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    address: '',
    payment: 'Наличные',
    delivery: 'Курьером',
    promocode: '',
    metro_line: '',
    metro_station: '',
  });
  
  const [availableStations, setAvailableStations] = useState([]);

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

    if (formData.delivery === 'По метро') {
      if (!formData.metro_line || !formData.metro_station) {
        showAlert('Заполните все обязательные поля');
        return;
      }
    } else if (!formData.address) {
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
    const { name, value } = e.target;
    
    if (name === 'delivery') {
      setFormData({
        ...formData,
        [name]: value,
        metro_line: '',
        metro_station: '',
        address: value === 'По метро' ? '' : formData.address,
      });
      setAvailableStations([]);
    } else if (name === 'metro_line') {
      setFormData({
        ...formData,
        [name]: value,
        metro_station: '',
      });
      setAvailableStations(metroLines[value] || []);
    } else {
      setFormData({
        ...formData,
        [name]: value,
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-white" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-6 pb-24">
        <h1 className="text-2xl font-bold mb-6 text-white">
          Оформление заказа
        </h1>
        <div className="glass-panel p-4 mb-4">
          <p className="text-white/80 text-sm">
            📍 Доставка по Минску, Беларусь
          </p>
          <p className="text-white/80 text-sm mt-2">
            💬 Вопросы: <a href="https://t.me/vapepluggmanager" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">@vapepluggmanager</a>
          </p>
        </div>

        <div className="glass-panel p-4 mb-4">
          <h3 className="font-semibold text-lg mb-3 text-white">
            Ваш заказ:
          </h3>
          {cartItems.map((item) => (
            <div key={item.id} className="flex justify-between mb-2 text-sm">
              <span className="text-white/80">
                {item.name} <span className="text-white font-medium">x{item.quantity}</span>
              </span>
              <span className="font-semibold text-white">
                {formatPrice(item.price * item.quantity)}
              </span>
            </div>
          ))}
          <div className="border-t border-white/20 mt-3 pt-3 flex justify-between font-bold text-lg">
            <span className="text-white">Итого:</span>
            <span className="text-white">
              {formatPrice(totalPrice)}
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="glass-panel p-4">
          <div className="mb-4">
            <label className="block text-white font-medium mb-2">
              Способ доставки
            </label>
            <select
              name="delivery"
              value={formData.delivery}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
            >
              <option value="Курьером" className="bg-purple-600">Курьером</option>
              <option value="Самовывоз" className="bg-purple-600">Самовывоз</option>
              <option value="По метро" className="bg-purple-600">По метро</option>
            </select>
          </div>

          {formData.delivery === 'По метро' ? (
            <>
              <div className="mb-4">
                <label className="block text-white font-medium mb-2">
                  Линия метро <span className="text-red-300">*</span>
                </label>
                <select
                  name="metro_line"
                  value={formData.metro_line}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
                  required
                >
                  <option value="" className="bg-purple-600">Выберите линию метро</option>
                  {Object.keys(metroLines).map((line) => (
                    <option key={line} value={line} className="bg-purple-600">
                      {line}
                    </option>
                  ))}
                </select>
              </div>

              {formData.metro_line && (
                <div className="mb-4">
                  <label className="block text-white font-medium mb-2">
                    Станция метро <span className="text-red-300">*</span>
                  </label>
                  <select
                    name="metro_station"
                    value={formData.metro_station}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
                    required
                  >
                    <option value="" className="bg-purple-600">Выберите станцию</option>
                    {availableStations.map((station) => (
                      <option key={station} value={station} className="bg-purple-600">
                        {station}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </>
          ) : (
            <div className="mb-4">
              <label className="block text-white font-medium mb-2">
                Адрес доставки <span className="text-red-300">*</span>
              </label>
              <textarea
                name="address"
                value={formData.address}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white placeholder-white/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
                rows="3"
                placeholder="Улица, дом, квартира"
                required={formData.delivery !== 'По метро'}
              />
            </div>
          )}

          <div className="mb-4">
            <label className="block text-white font-medium mb-2">
              Способ оплаты
            </label>
            <select
              name="payment"
              value={formData.payment}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
            >
              <option value="Наличные" className="bg-purple-600">Наличные</option>
              <option value="Карта" className="bg-purple-600">Карта</option>
            </select>
          </div>


          <div className="mb-6">
            <label className="block text-white font-medium mb-2">
              Промокод
            </label>
            <input
              type="text"
              name="promocode"
              value={formData.promocode}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white placeholder-white/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
              placeholder="Введите промокод"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-white/30 hover:bg-white/40 text-white py-3 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 backdrop-blur-sm"
          >
            {submitting ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Оформление...
              </>
            ) : (
              'Подтвердить заказ'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Checkout;
