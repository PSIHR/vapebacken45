import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useTelegram } from './hooks/useTelegram';
import { userAPI, basketAPI } from './services/api';
import Header from './components/Header';
import Catalog from './pages/Catalog';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import Orders from './pages/Orders';

function App() {
  const [cartCount, setCartCount] = useState(0);
  const { user, tg } = useTelegram();

  useEffect(() => {
    if (user?.id) {
      registerUser();
      updateCartCount();
    }
  }, [user]);

  const registerUser = async () => {
    try {
      await userAPI.register({
        telegramId: user.id,
        username: user.username || `user${user.id}`,
      });
    } catch (error) {
      console.error('Error registering user:', error);
    }
  };

  const updateCartCount = async () => {
    if (!user?.id) return;
    
    try {
      const response = await basketAPI.get(user.id);
      const items = response.data.items || [];
      setCartCount(items.length);
    } catch (error) {
      console.error('Error updating cart count:', error);
    }
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header cartCount={cartCount} />
        <main>
          <Routes>
            <Route path="/" element={<Catalog onCartUpdate={updateCartCount} />} />
            <Route path="/cart" element={<Cart onCartUpdate={updateCartCount} />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/orders" element={<Orders />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
