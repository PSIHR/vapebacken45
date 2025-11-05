import { Link } from 'react-router-dom';
import { HelpCircle } from 'lucide-react';

const Header = () => {
  return (
    <header className="glass-header sticky top-0 z-50 pt-safe">
      <div className="container mx-auto px-4 py-3">
        <div className="flex flex-col items-center gap-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-semibold text-white">
              VAPE PLUG
            </span>
          </Link>
          
          <Link 
            to="/faq"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500/20 to-purple-500/20 hover:from-cyan-500/30 hover:to-purple-500/30 transition-all border border-cyan-500/30"
          >
            <HelpCircle className="w-5 h-5 text-cyan-400" />
            <span className="text-sm font-medium text-cyan-400">FAQ</span>
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;
