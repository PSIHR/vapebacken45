import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { categoriesAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import { Loader2, Search, ExternalLink } from 'lucide-react';

const Home = () => {
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const { showAlert, openLink } = useTelegram();
  const navigate = useNavigate();

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const response = await categoriesAPI.getAll();
      const cats = response.data.categories || [];
      console.log('Loaded categories:', cats);
      cats.forEach(cat => {
        console.log(`Category ${cat.name}: image = ${cat.image}`);
      });
      setCategories(cats);
    } catch (error) {
      console.error('Error loading categories:', error);
      showAlert('Ошибка загрузки категорий');
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryClick = (categoryId) => {
    navigate(`/catalog/${categoryId}`);
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/catalog?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleLinkClick = (url) => {
    if (openLink) {
      openLink(url);
    } else {
      window.open(url, '_blank');
    }
  };

  const filteredCategories = categories.filter(cat =>
    searchQuery
      ? cat.name.toLowerCase().includes(searchQuery.toLowerCase())
      : true
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-pink-500" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <button
            onClick={() => handleLinkClick('https://t.me/+yTWUCNVQIsJjZDUy')}
            className="w-full glass-panel p-3 rounded-lg flex items-center justify-center gap-2 hover:bg-pink-100 transition-all"
          >
            <ExternalLink size={16} className="text-gray-800" />
            <span className="text-gray-800 font-medium text-sm">Канал</span>
          </button>
        </div>

        <div className="mb-6 relative backdrop-blur-sm rounded-lg">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500 z-10" size={20} />
          <input
            type="text"
            placeholder="Поиск категорий и товаров..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-12 pr-4 py-3 rounded-lg bg-white border border-pink-200 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-pink-300 transition-all relative z-10"
          />
        </div>

        {filteredCategories.length === 0 ? (
          <div className="text-center py-16 glass-panel">
            <p className="text-gray-600 text-lg">Категории не найдены</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {filteredCategories.map((category) => (
              <div
                key={category.id}
                onClick={() => handleCategoryClick(category.id)}
                className="glass-panel rounded-2xl overflow-hidden cursor-pointer transform transition-all hover:scale-105 hover:shadow-2xl active:scale-95"
              >
                <div className="aspect-square relative overflow-hidden bg-gradient-to-br from-pink-50 to-pink-100">
                  {category.image ? (
                    <img
                      src={category.image}
                      alt={category.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-6xl text-pink-300">📦</span>
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-pink-200/60 via-transparent to-transparent" />
                </div>
                <div className="p-4">
                  <h3 className="text-gray-800 font-bold text-lg text-center">
                    {category.name}
                  </h3>
                  {category.description && (
                    <p className="text-gray-600 text-sm text-center mt-1 line-clamp-2">
                      {category.description}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;