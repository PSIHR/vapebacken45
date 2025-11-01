import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="glass-header sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-center">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-semibold text-white">
              VAPE PLUG
            </span>
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;
