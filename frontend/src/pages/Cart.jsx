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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-center p-8">
          <div className="bg-white/80 backdrop-blur-sm p-12 rounded-3xl shadow-2xl">
            <ShoppingBag className="mx-auto text-purple-400 mb-6 animate-bounce-subtle" size={80} />
            <h2 className="text-3xl font-extrabold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
              Корзина пуста
            </h2>
            <p className="text-gray-600 mb-8 text-lg">Добавьте товары из каталога</p>
            <button
              onClick={() => navigate('/')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-4 rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
            >
              🛍️ Перейти в каталог
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <div className="container mx-auto px-4 py-8 pb-32">
        <h1 className="text-4xl font-extrabold mb-8 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
          🛒 Корзина
        </h1>
        
        <div className="mb-6 space-y-4">
          {cartItems.map((item) => (
            <CartItem
              key={item.id}
              item={item}
              onUpdateQuantity={handleUpdateQuantity}
              onRemove={handleRemoveItem}
            />
          ))}
        </div>

        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl p-6 mb-4 sticky bottom-20 border border-purple-100">
          <div className="flex justify-between items-center mb-4 text-gray-700">
            <span className="text-lg font-semibold">Товаров:</span>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {cartItems.length}
            </span>
          </div>
          <div className="flex justify-between items-center mb-6 text-2xl font-extrabold border-t border-purple-100 pt-4">
            <span>Итого:</span>
            <span className="bg-gradient-to-r from-green-500 to-emerald-600 bg-clip-text text-transparent">
              {formatPrice(totalPrice)}
            </span>
          </div>
          <button
            onClick={handleCheckout}
            className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white py-4 rounded-xl font-bold text-lg transition-all duration-300 transform hover:scale-105 shadow-xl hover:shadow-2xl"
          >
            ✨ Оформить заказ
          </button>
        </div>
      </div>
    </div>
  );
};

export default Cart;
