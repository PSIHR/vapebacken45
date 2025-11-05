import { useNavigate, useLocation } from 'react-router-dom';
import { Store, ShoppingCart, User } from 'lucide-react';

const BottomNavigation = ({ cartCount }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    {
      id: 'catalog',
      label: 'Каталог',
      icon: Store,
      path: '/',
    },
    {
      id: 'cart',
      label: 'Корзина',
      icon: ShoppingCart,
      path: '/cart',
      badge: cartCount > 0 ? cartCount : null,
    },
    {
      id: 'profile',
      label: 'Профиль',
      icon: User,
      path: '/profile',
    },
  ];

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/' || location.pathname.startsWith('/product/');
    }
    return location.pathname === path;
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 pb-safe">
      <div className="glass-bottom-nav mx-4 mb-4">
        <div className="flex items-center justify-around px-2 py-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            
            return (
              <button
                key={item.id}
                onClick={() => navigate(item.path)}
                aria-label={item.label}
                aria-current={active ? 'page' : undefined}
                className={`flex flex-col items-center justify-center gap-1 px-6 py-2 rounded-2xl transition-all relative ${
                  active
                    ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400'
                    : 'text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/10'
                }`}
              >
                <div className="relative">
                  <Icon size={24} strokeWidth={active ? 2.5 : 2} />
                  {item.badge && (
                    <span className="absolute -top-1 -right-1 bg-gradient-to-r from-pink-500 to-purple-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                      {item.badge}
                    </span>
                  )}
                </div>
                <span className={`text-xs font-medium ${active ? 'font-semibold' : ''}`}>
                  {item.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default BottomNavigation;
