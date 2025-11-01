import { ShoppingCart, Package } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Header = ({ cartCount }) => {
  const location = useLocation();

  return (
    <header className="bg-blue-600 text-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-xl font-bold">
            🛍️ Магазин
          </Link>
          <div className="flex gap-4">
            <Link
              to="/cart"
              className={`relative p-2 rounded-lg transition-colors ${
                location.pathname === '/cart' ? 'bg-blue-700' : 'hover:bg-blue-700'
              }`}
            >
              <ShoppingCart size={24} />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </Link>
            <Link
              to="/orders"
              className={`p-2 rounded-lg transition-colors ${
                location.pathname === '/orders' ? 'bg-blue-700' : 'hover:bg-blue-700'
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
