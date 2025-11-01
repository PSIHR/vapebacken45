import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { basketAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import CartItem from '../components/CartItem';
import { formatPrice } from '../utils/helpers';
import { ShoppingBag, Loader2 } from 'lucide-react';

const Cart = ({ onCartUpdate }) => {
  const [cartItems, setCartItems] = useState([]);
  const [totalPrice, setTotalPrice] = useState(0);
  const [loading, setLoading] = useState(true);
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
      onCartUpdate();
    } catch (error) {
      console.error('Error loading cart:', error);
      showAlert('Ошибка загрузки корзины');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    if (newQuantity < 1) return;
    
    const updatedItems = cartItems.map(item =>
      item.id === itemId ? { ...item, quantity: newQuantity } : item
    );
    setCartItems(updatedItems);
    setTotalPrice(updatedItems.reduce((sum, item) => sum + item.price * item.quantity, 0));
  };

  const handleRemoveItem = async (itemId) => {
    try {
      await basketAPI.removeItem(user.id, itemId);
      await loadCart();
      showAlert('Товар удален из корзины');
    } catch (error) {
      console.error('Error removing item:', error);
      showAlert('Ошибка удаления товара');
    }
  };

  const handleCheckout = () => {
    if (cartItems.length === 0) {
      showAlert('Корзина пуста');
      return;
    }
    navigate('/checkout');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-blue-600" size={48} />
      </div>
    );
  }

  if (cartItems.length === 0) {
    return (
      <div className="min-h-screen bg-[#f4f4f5] flex items-center justify-center">
        <div className="text-center p-8">
          <div className="bg-white p-12 rounded-lg border border-gray-200">
            <ShoppingBag className="mx-auto text-gray-400 mb-6" size={64} />
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Корзина пуста
            </h2>
            <p className="text-gray-600 mb-6">Добавьте товары из каталога</p>
            <button
              onClick={() => navigate('/')}
              className="bg-[#3390ec] hover:bg-[#2b7cd3] text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Перейти в каталог
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f4f5]">
      <div className="container mx-auto px-4 py-6 pb-32">
        <h1 className="text-2xl font-bold mb-6 text-gray-900">
          Корзина
        </h1>
        
        <div className="mb-6 space-y-3">
          {cartItems.map((item) => (
            <CartItem
              key={item.id}
              item={item}
              onUpdateQuantity={handleUpdateQuantity}
              onRemove={handleRemoveItem}
            />
          ))}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4 sticky bottom-20">
          <div className="flex justify-between items-center mb-3 text-gray-700">
            <span className="text-base font-medium">Товаров:</span>
            <span className="text-base font-semibold text-gray-900">
              {cartItems.length}
            </span>
          </div>
          <div className="flex justify-between items-center mb-4 text-xl font-bold border-t border-gray-200 pt-3">
            <span className="text-gray-900">Итого:</span>
            <span className="text-gray-900">
              {formatPrice(totalPrice)}
            </span>
          </div>
          <button
            onClick={handleCheckout}
            className="w-full bg-[#3390ec] hover:bg-[#2b7cd3] text-white py-3 rounded-lg font-medium transition-colors"
          >
            Оформить заказ
          </button>
        </div>
      </div>
    </div>
  );
};

export default Cart;
