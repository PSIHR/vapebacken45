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

  return (
    <Router>
      <div className="min-h-screen pt-safe pb-safe">
        <Header />
        <main className="pb-24 pt-4">
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
