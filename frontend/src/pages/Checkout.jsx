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
    postal_full_name: '',
    postal_phone: '',
    postal_address: '',
    postal_index: '',
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
    } else if (formData.delivery === 'Европочта') {
      setDeliveryCost(5);
    } else if (formData.delivery === 'Белпочта') {
      setDeliveryCost(3);
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
    } else if (formData.delivery === 'Европочта') {
      if (!formData.postal_full_name || !formData.postal_phone || !formData.postal_address) {
        showAlert('Заполните все обязательные поля');
        return;
      }
    } else if (formData.delivery === 'Белпочта') {
      if (!formData.postal_full_name || !formData.postal_phone || !formData.postal_address || !formData.postal_index) {
        showAlert('Заполните все обязательные поля');
        return;
      }
    }

    // Set address for pickup and metro if not provided
    let orderAddress = formData.address;
    if (formData.delivery === 'Самовывоз') {
      orderAddress = 'ст. м. Якуба Коласа (Самовывоз)';
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
        postal_full_name: '',
        postal_phone: '',
        postal_address: '',
        postal_index: '',
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
        <Loader2 className="animate-spin text-pink-500" size={48} />
      </div>
    );
  }

  const finalTotal = totalPrice + deliveryCost;

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-6 pb-24">
        <h1 className="text-2xl font-bold mb-6 text-gray-800">
          Оформление заказа
        </h1>
        
        <div className="glass-panel p-4 mb-4">
          <p className="text-gray-700 text-sm">
            📍 Доставка по Минску, Беларусь
          </p>
          <p className="text-gray-700 text-sm mt-2">
            💬 Вопросы: <a href="https://t.me/baster_mks" target="_blank" rel="noopener noreferrer" className="text-pink-600 hover:text-pink-700 underline">@baster_mks</a>
          </p>
        </div>

        <div className="glass-panel p-4 mb-4">
          <h3 className="font-semibold text-lg mb-3 text-gray-800">
            Ваш заказ:
          </h3>
          {cartItems.map((item) => (
            <div key={item.id} className="flex justify-between mb-2 text-sm">
              <span className="text-gray-700">
                {item.name} <span className="text-gray-800 font-medium">x{item.quantity}</span>
              </span>
              <span className="font-semibold text-gray-800">
                {formatPrice(item.price * item.quantity)}
              </span>
            </div>
          ))}
          <div className="border-t border-pink-200 mt-3 pt-3">
            <div className="flex justify-between text-base mb-1">
              <span className="text-gray-700">Товары:</span>
              <span className="text-gray-800">{formatPrice(totalPrice)}</span>
            </div>
            {deliveryCost > 0 && (
              <div className="flex justify-between text-base mb-1">
                <span className="text-gray-700">Доставка:</span>
                <span className="text-gray-800">{formatPrice(deliveryCost)}</span>
              </div>
            )}
            <div className="flex justify-between font-bold text-lg mt-2 pt-2 border-t border-pink-200">
              <span className="text-gray-800">Итого:</span>
              <span className="text-pink-600">{formatPrice(finalTotal)}</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="glass-panel p-4">
          <div className="mb-4">
            <label className="block text-gray-800 font-medium mb-2">
              Способ доставки
            </label>
            <div className="relative">
              <select
                name="delivery"
                value={formData.delivery}
                onChange={handleChange}
                className="w-full px-3 py-2 pr-10 border border-pink-200 bg-white text-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
              >
                <option value="Курьером" className="bg-gray-800">Курьером до адреса</option>
                <option value="Самовывоз" className="bg-gray-800">Самовывоз</option>
                <option value="По метро" className="bg-gray-800">До станции метро</option>
                <option value="Яндекс доставка" className="bg-gray-800">Яндекс доставка</option>
                <option value="Европочта" className="bg-gray-800">Европочта (5 BYN)</option>
                <option value="Белпочта" className="bg-gray-800">Белпочта (3-5 BYN)</option>
              </select>
              <button
                type="button"
                onClick={() => showDeliveryInfo(formData.delivery)}
                className="absolute right-10 top-1/2 -translate-y-1/2 p-1 hover:bg-white/10 rounded-full transition-colors"
              >
                <Info className="w-5 h-5 text-white/70 hover:text-white" />
              </button>
            </div>
          </div>

          {formData.delivery === 'По метро' && (
            <>
              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Линия метро <span className="text-white">*</span>
                </label>
                <select
                  name="metro_line"
                  value={formData.metro_line}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white text-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  required
                >
                  <option value="" className="bg-gray-800">Выберите линию метро</option>
                  {Object.keys(metroLines).map((line) => (
                    <option key={line} value={line} className="bg-gray-800">
                      {line}
                    </option>
                  ))}
                </select>
              </div>

              {formData.metro_line && (
                <div className="mb-4">
                  <label className="block text-gray-800 font-medium mb-2">
                    Станция метро <span className="text-white">*</span>
                  </label>
                  <select
                    name="metro_station"
                    value={formData.metro_station}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-pink-200 bg-white text-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                    required
                  >
                    <option value="" className="bg-gray-800">Выберите станцию</option>
                    {availableStations.map((station) => (
                      <option key={station} value={station} className="bg-gray-800">
                        {station}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Предпочтительное время <span className="text-white">*</span>
                </label>
                <input
                  type="text"
                  name="preferred_time"
                  value={formData.preferred_time}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  placeholder="Например: 15:00-16:00"
                  required
                />
                <p className="text-gray-600 text-xs mt-1">
                  Укажите удобное для вас время доставки
                </p>
              </div>
            </>
          )}

          {formData.delivery === 'Самовывоз' && (
            <>
              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Адрес самовывоза
                </label>
                <div className="glass-card p-3">
                  <p className="text-white text-sm">
                    ст. м. Якуба Коласа
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Предпочтительное время <span className="text-white">*</span>
                </label>
                <input
                  type="text"
                  name="preferred_time"
                  value={formData.preferred_time}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  placeholder="Например: 14:00"
                  required
                />
                <p className="text-gray-600 text-xs mt-1">
                  Работаем: 13:00-20:00. Уведомляйте менеджера за 15 минут
                </p>
              </div>
            </>
          )}

          {(formData.delivery === 'Курьером' || formData.delivery === 'Яндекс доставка') && (
            <>
              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Адрес доставки <span className="text-white">*</span>
                </label>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  rows="3"
                  placeholder="Улица, дом, квартира"
                  required
                />
              </div>

              {formData.delivery === 'Курьером' && (
                <div className="mb-4">
                  <label className="block text-gray-800 font-medium mb-2">
                    Временной промежуток <span className="text-white">*</span>
                  </label>
                  <select
                    name="time_slot"
                    value={formData.time_slot}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-pink-200 bg-white text-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                    required
                  >
                    <option value="" className="bg-gray-800">Выберите время</option>
                    <option value="14:00-16:00" className="bg-gray-800">14:00-16:00 (дневной)</option>
                    <option value="18:00-21:30" className="bg-gray-800">18:00-21:30 (вечерний)</option>
                  </select>
                  <p className="text-gray-600 text-xs mt-1">
                    Точное время зависит от маршрута курьера
                  </p>
                </div>
              )}
            </>
          )}

          {formData.delivery === 'Европочта' && (
            <>
              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  ФИО получателя <span className="text-white">*</span>
                </label>
                <input
                  type="text"
                  name="postal_full_name"
                  value={formData.postal_full_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  placeholder="Иванов Иван Иванович"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Номер телефона <span className="text-white">*</span>
                </label>
                <input
                  type="tel"
                  name="postal_phone"
                  value={formData.postal_phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  placeholder="+375 (29) 123-45-67"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Адрес пункта выдачи или номер ОПС <span className="text-white">*</span>
                </label>
                <textarea
                  name="postal_address"
                  value={formData.postal_address}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  rows="3"
                  placeholder="Адрес пункта выдачи Европочты или номер ОПС"
                  required
                />
                <p className="text-gray-600 text-xs mt-1">
                  Стоимость пересылки: 5 BYN. Наложенный платеж (оплата при получении)
                </p>
              </div>
            </>
          )}

          {formData.delivery === 'Белпочта' && (
            <>
              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  ФИО получателя <span className="text-white">*</span>
                </label>
                <input
                  type="text"
                  name="postal_full_name"
                  value={formData.postal_full_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  placeholder="Иванов Иван Иванович"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Номер телефона <span className="text-white">*</span>
                </label>
                <input
                  type="tel"
                  name="postal_phone"
                  value={formData.postal_phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  placeholder="+375 (29) 123-45-67"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Полный адрес <span className="text-white">*</span>
                </label>
                <textarea
                  name="postal_address"
                  value={formData.postal_address}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  rows="3"
                  placeholder="Город/поселок, улица, дом, квартира"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-gray-800 font-medium mb-2">
                  Почтовый индекс <span className="text-white">*</span>
                </label>
                <input
                  type="text"
                  name="postal_index"
                  value={formData.postal_index}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
                  placeholder="220000"
                  required
                />
                <p className="text-gray-600 text-xs mt-1">
                  Стоимость пересылки: 3-5 BYN (определяет почта). Наложенный платеж (оплата при получении)
                </p>
              </div>
            </>
          )}

          <div className="mb-4">
            <label className="block text-gray-800 font-medium mb-2">
              Способ оплаты
            </label>
            <select
              name="payment"
              value={formData.payment}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-pink-200 bg-white text-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
            >
              <option value="Наличные" className="bg-gray-800">Наличные</option>
              <option value="Карта" className="bg-gray-800">Карта</option>
              <option value="USDT" className="bg-gray-800">USDT</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-gray-800 font-medium mb-2">
              Промокод
            </label>
            <input
              type="text"
              name="promocode"
              value={formData.promocode}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-pink-200 bg-white/10 text-gray-800 placeholder-gray/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-transparent"
              placeholder="Введите промокод"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-pink-500 hover:bg-pink-600 text-white py-3 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-panel max-w-lg w-full max-h-[80vh] overflow-y-auto relative">
            <button
              onClick={() => setShowInfoModal(false)}
              className="absolute top-4 right-4 p-2 hover:bg-pink-100 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-gray-800" />
            </button>
            
            <h3 className="text-xl font-bold text-gray-800 mb-4 pr-10">
              {currentDeliveryInfo.title}
            </h3>
            
            <div className="text-gray-700 whitespace-pre-line text-sm leading-relaxed">
              {currentDeliveryInfo.content}
            </div>

            <button
              onClick={() => setShowInfoModal(false)}
              className="w-full mt-6 bg-pink-500 hover:bg-pink-600 text-white py-2 rounded-lg font-medium transition-all"
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
