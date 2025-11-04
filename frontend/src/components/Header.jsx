import { Link } from 'react-router-dom';
import { HelpCircle } from 'lucide-react';

const Header = () => {
  return (
    <header className="glass-header sticky top-0 z-50 pt-safe">
      <div className="container mx-auto px-4 py-3">
        <div className="flex flex-col items-center gap-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-semibold text-gray-800">
              BASTER SHOP
            </span>
          </Link>
          
          <Link 
            to="/faq"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-pink-100 hover:bg-pink-200 transition-colors"
          >
            <HelpCircle className="w-5 h-5 text-pink-600" />
            <span className="text-sm font-medium text-pink-600">FAQ</span>
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;
