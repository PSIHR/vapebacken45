import { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useTelegram } from "./hooks/useTelegram";
import { userAPI, basketAPI } from "./services/api";
import Header from "./components/Header";
import BottomNavigation from "./components/BottomNavigation";
import Catalog from "./pages/Catalog";
import ProductDetail from "./pages/ProductDetail";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import Orders from "./pages/Orders";
import Profile from "./pages/Profile";
import FAQ from "./pages/FAQ";

function App() {
  const [cartCount, setCartCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const { user, tg } = useTelegram();

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);

    if (user?.id) {
      registerUser();
      updateCartCount();
    }

    return () => clearTimeout(timer);
  }, [user]);

  const registerUser = async () => {
    try {
      await userAPI.register({
        telegramId: user.id,
        username: user.username || `user${user.id}`,
      });
    } catch (error) {
      console.error("Error registering user:", error);
    }
  };

  const updateCartCount = async () => {
    if (!user?.id) return;

    try {
      const response = await basketAPI.get(user.id);
      const items = response.data.items || [];
      setCartCount(items.length);
    } catch (error) {
      console.error("Error updating cart count:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-purple-800">
        <div className="text-center">
          <div className="animate-pulse mb-6">
            <div className="text-6xl mb-4">💨</div>
            <h1 className="text-4xl font-bold text-white" style={{ fontFamily: 'Unbounded, sans-serif' }}>
              VAPE PLUG
            </h1>
          </div>
        </div>
      </div>
    );
  }

  if (!tg) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-purple-900 via-blue-900 to-purple-800">
        <div className="max-w-md w-full backdrop-blur-xl bg-white/10 rounded-3xl p-8 border border-white/20 shadow-2xl text-center">
          <div className="text-6xl mb-6">📱</div>
          <h1 className="text-3xl font-bold text-white mb-4" style={{ fontFamily: 'Unbounded, sans-serif' }}>
            Telegram Mini App
          </h1>
          <p className="text-white/80 text-lg mb-6">
            Это приложение работает только внутри Telegram
          </p>
          <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
            <p className="text-white/90 text-sm mb-4">
              Чтобы открыть приложение:
            </p>
            <ol className="text-left text-white/70 text-sm space-y-2">
              <li>1. Откройте Telegram</li>
              <li>2. Найдите нашего бота</li>
              <li>3. Нажмите кнопку "Открыть приложение"</li>
            </ol>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen pt-safe pb-safe pt-40">
        <Header />
        <main className="pb-48">
          <Routes>
            <Route path="/" element={<Catalog />} />
            <Route
              path="/product/:id"
              element={<ProductDetail onCartUpdate={updateCartCount} />}
            />
            <Route
              path="/cart"
              element={<Cart onCartUpdate={updateCartCount} />}
            />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/faq" element={<FAQ />} />
          </Routes>
        </main>
        <BottomNavigation cartCount={cartCount} />
      </div>
    </Router>
  );
}

export default App;