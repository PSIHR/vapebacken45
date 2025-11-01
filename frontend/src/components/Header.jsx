import { ShoppingCart, Package } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Header = ({ cartCount }) => {
  const location = useLocation();

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-semibold text-gray-900">
              Магазин
            </span>
          </Link>
          <div className="flex gap-3">
            <Link
              to="/cart"
              className={`relative p-2 rounded-lg transition-colors ${
                location.pathname === '/cart' 
                  ? 'bg-gray-100' 
                  : 'hover:bg-gray-100'
              }`}
            >
              <ShoppingCart size={24} className="text-gray-700" />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-[#3390ec] text-white text-xs font-semibold rounded-full w-5 h-5 flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </Link>
            <Link
              to="/orders"
              className={`p-2 rounded-lg transition-colors ${
                location.pathname === '/orders' 
                  ? 'bg-gray-100' 
                  : 'hover:bg-gray-100'
              }`}
            >
              <Package size={24} className="text-gray-700" />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
