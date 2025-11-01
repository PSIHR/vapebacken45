import { ShoppingCart, Package, Sparkles } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Header = ({ cartCount }) => {
  const location = useLocation();

  return (
    <header className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white shadow-2xl sticky top-0 z-50 backdrop-blur-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="text-2xl group-hover:scale-110 transition-transform duration-300">🛍️</span>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-blue-100">
              Магазин
            </span>
            <Sparkles size={18} className="text-yellow-300 animate-pulse" />
          </Link>
          <div className="flex gap-3">
            <Link
              to="/cart"
              className={`relative p-3 rounded-xl transition-all duration-300 transform hover:scale-110 ${
                location.pathname === '/cart' 
                  ? 'bg-white/30 shadow-lg' 
                  : 'bg-white/10 hover:bg-white/20'
              }`}
            >
              <ShoppingCart size={24} className="animate-bounce-subtle" />
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-gradient-to-r from-red-500 to-pink-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center shadow-lg animate-pulse ring-2 ring-white">
                  {cartCount}
                </span>
              )}
            </Link>
            <Link
              to="/orders"
              className={`p-3 rounded-xl transition-all duration-300 transform hover:scale-110 ${
                location.pathname === '/orders' 
                  ? 'bg-white/30 shadow-lg' 
                  : 'bg-white/10 hover:bg-white/20'
              }`}
            >
              <Package size={24} />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
