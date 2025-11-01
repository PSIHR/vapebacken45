import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { basketAPI, ordersAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import { formatPrice } from '../utils/helpers';
import { metroLines } from '../data/metroData';
import { deliveryInfo } from '../data/deliveryInfo';
import { Loader2, Info, X } from 'lucide-react';

const Checkout = () => {
  const [cartItems, setCartItems] = useState([]);
  const [totalPrice, setTotalPrice] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [currentDeliveryInfo, setCurrentDeliveryInfo] = useState(null);
  const [deliveryCost, setDeliveryCost] = useState(0);
  
  const [formData, setFormData] = useState({
    address: '',
    payment: 'Наличные',
    delivery: 'Курьером',
    promocode: '',
    metro_line: '',
    metro_station: '',
    preferred_time: '',
    time_slot: '',
  });
  
  const [availableStations, setAvailableStations] = useState([]);

  const { user, showAlert } = useTelegram();
  const navigate = useNavigate();

  useEffect(() => {
    loadCart();
  }, [user]);

  useEffect(() => {
    calculateDeliveryCost();
  }, [formData.delivery, totalPrice]);

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

  const calculateDeliveryCost = () => {
    if (formData.delivery === 'Курьером') {
      if (totalPrice < 80) {
        setDeliveryCost(8);
      } else {
        setDeliveryCost(0);
      }
    } else {
      setDeliveryCost(0);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.delivery === 'По метро') {
      if (!formData.metro_line || !formData.metro_station || !formData.preferred_time) {
        showAlert('Заполните все обязательные поля');
        return;
      }
    } else if (formData.delivery === 'Самовывоз') {
      if (!formData.preferred_time) {
        showAlert('Укажите предпочтительное время');
        return;
      }
    } else if (formData.delivery === 'Курьером') {
      if (!formData.address || !formData.time_slot) {
        showAlert('Заполните все обязательные поля');
        return;
      }
    } else if (formData.delivery === 'Яндекс доставка') {
      if (!formData.address) {
        showAlert('Укажите адрес доставки');
        return;
      }
    }

    // Set address for pickup and metro if not provided
    let orderAddress = formData.address;
    if (formData.delivery === 'Самовывоз') {
      orderAddress = 'пр. Дзержинского 26, подъезд 4 (Самовывоз)';
    } else if (formData.delivery === 'По метро') {
      orderAddress = `${formData.metro_line} - ${formData.metro_station} (Метро)`;
    }

    try {
      setSubmitting(true);
      await ordersAPI.createFromBasket(user.id, {
        ...formData,
        address: orderAddress,
        delivery_cost: deliveryCost,
      });
      showAlert('Заказ успешно оформлен!');
      navigate('/profile');
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
        address: '',
        preferred_time: '',
        time_slot: '',
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

  const showDeliveryInfo = (deliveryType) => {
    setCurrentDeliveryInfo(deliveryInfo[deliveryType]);
    setShowInfoModal(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-white" size={48} />
      </div>
    );
  }

  const finalTotal = totalPrice + deliveryCost;

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
          <div className="border-t border-white/20 mt-3 pt-3">
            <div className="flex justify-between text-base mb-1">
              <span className="text-white/80">Товары:</span>
              <span className="text-white">{formatPrice(totalPrice)}</span>
            </div>
            {deliveryCost > 0 && (
              <div className="flex justify-between text-base mb-1">
                <span className="text-white/80">Доставка:</span>
                <span className="text-white">{formatPrice(deliveryCost)}</span>
              </div>
            )}
            <div className="flex justify-between font-bold text-lg mt-2 pt-2 border-t border-white/20">
              <span className="text-white">Итого:</span>
              <span className="text-white">{formatPrice(finalTotal)}</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="glass-panel p-4">
          <div className="mb-4">
            <label className="block text-white font-medium mb-2">
              Способ доставки
            </label>
            <div className="relative">
              <select
                name="delivery"
                value={formData.delivery}
                onChange={handleChange}
                className="w-full px-3 py-2 pr-10 border border-white/30 bg-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
              >
                <option value="Курьером" className="bg-purple-600">Курьером до адреса</option>
                <option value="Самовывоз" className="bg-purple-600">Самовывоз</option>
                <option value="По метро" className="bg-purple-600">До станции метро</option>
                <option value="Яндекс доставка" className="bg-purple-600">Яндекс доставка</option>
              </select>
              <button
                type="button"
                onClick={() => showDeliveryInfo(formData.delivery)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-white/10 rounded-full transition-colors"
              >
                <Info className="w-5 h-5 text-white/70 hover:text-white" />
              </button>
            </div>
          </div>

          {formData.delivery === 'По метро' && (
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

              <div className="mb-4">
                <label className="block text-white font-medium mb-2">
                  Предпочтительное время <span className="text-red-300">*</span>
                </label>
                <input
                  type="text"
                  name="preferred_time"
                  value={formData.preferred_time}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white placeholder-white/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
                  placeholder="Например: 15:00-16:00"
                  required
                />
                <p className="text-white/60 text-xs mt-1">
                  Укажите удобное для вас время доставки
                </p>
              </div>
            </>
          )}

          {formData.delivery === 'Самовывоз' && (
            <>
              <div className="mb-4">
                <label className="block text-white font-medium mb-2">
                  Адрес самовывоза
                </label>
                <div className="glass-card p-3">
                  <p className="text-white text-sm">
                    пр. Дзержинского 26, подъезд 4
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-white font-medium mb-2">
                  Предпочтительное время <span className="text-red-300">*</span>
                </label>
                <input
                  type="text"
                  name="preferred_time"
                  value={formData.preferred_time}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white placeholder-white/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
                  placeholder="Например: 14:00"
                  required
                />
                <p className="text-white/60 text-xs mt-1">
                  Работаем: 13:00-20:00. Уведомляйте менеджера за 15 минут
                </p>
              </div>
            </>
          )}

          {(formData.delivery === 'Курьером' || formData.delivery === 'Яндекс доставка') && (
            <>
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
                  required
                />
              </div>

              {formData.delivery === 'Курьером' && (
                <div className="mb-4">
                  <label className="block text-white font-medium mb-2">
                    Временной промежуток <span className="text-red-300">*</span>
                  </label>
                  <select
                    name="time_slot"
                    value={formData.time_slot}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-white/30 bg-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
                    required
                  >
                    <option value="" className="bg-purple-600">Выберите время</option>
                    <option value="14:00-16:00" className="bg-purple-600">14:00-16:00 (дневной)</option>
                    <option value="18:00-21:30" className="bg-purple-600">18:00-21:30 (вечерний)</option>
                  </select>
                  <p className="text-white/60 text-xs mt-1">
                    Точное время зависит от маршрута курьера
                  </p>
                </div>
              )}
            </>
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
              <option value="USDT" className="bg-purple-600">USDT</option>
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

      {showInfoModal && currentDeliveryInfo && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-panel max-w-lg w-full max-h-[80vh] overflow-y-auto relative">
            <button
              onClick={() => setShowInfoModal(false)}
              className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-white" />
            </button>
            
            <h3 className="text-xl font-bold text-white mb-4 pr-10">
              {currentDeliveryInfo.title}
            </h3>
            
            <div className="text-white/80 whitespace-pre-line text-sm leading-relaxed">
              {currentDeliveryInfo.content}
            </div>

            <button
              onClick={() => setShowInfoModal(false)}
              className="w-full mt-6 bg-white/30 hover:bg-white/40 text-white py-2 rounded-lg font-medium transition-all"
            >
              Закрыть
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Checkout;
