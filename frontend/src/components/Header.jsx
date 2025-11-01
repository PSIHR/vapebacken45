import { ShoppingCart, Package } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Header = ({ cartCount }) => {
  const location = useLocation();

  return (
    <header className="glass-header sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-semibold text-white">
              Магазин
            </span>
          </Link>
          <div className="flex gap-3">
            <Link
              to="/cart"
              className={`relative p-2 rounded-lg transition-colors ${
                location.pathname === '/cart' 
                  ? 'bg-white/20' 
                  : 'hover:bg-white/10'
              }`}
            >
              <ShoppingCart size={24} className="text-white" />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-white text-purple-600 text-xs font-semibold rounded-full w-5 h-5 flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </Link>
            <Link
              to="/orders"
              className={`p-2 rounded-lg transition-colors ${
                location.pathname === '/orders' 
                  ? 'bg-white/20' 
                  : 'hover:bg-white/10'
              }`}
            >
              <Package size={24} className="text-white" />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
