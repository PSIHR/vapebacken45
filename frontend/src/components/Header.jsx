import { Link } from 'react-router-dom';
import { HelpCircle } from 'lucide-react';

const Header = () => {
  return (
    <header className="glass-header sticky top-0 z-50 pt-safe">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-semibold text-white">
              VAPE PLUG
            </span>
          </Link>
          
          <Link 
            to="/faq"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
          >
            <HelpCircle className="w-5 h-5 text-white" />
            <span className="text-sm font-medium text-white">FAQ</span>
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;
