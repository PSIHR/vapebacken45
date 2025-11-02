import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { categoriesAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import { Loader2, Search, ChevronRight } from 'lucide-react';

const Home = () => {
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const { showAlert } = useTelegram();
  const navigate = useNavigate();

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const response = await categoriesAPI.getAll();
      const cats = response.data.categories || [];
      setCategories(cats);
    } catch (error) {
      console.error('Error loading categories:', error);
      showAlert('Ошибка загрузки категорий');
    } finally {
      setLoading(false);
    }
  };

  const filteredCategories = categories.filter(category =>
    searchQuery
      ? category.name.toLowerCase().includes(searchQuery.toLowerCase())
      : true
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-white" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 relative backdrop-blur-sm rounded-lg">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white z-10" size={20} />
          <input
            type="text"
            placeholder="Поиск категорий..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all relative z-10"
          />
        </div>

        {filteredCategories.length === 0 ? (
          <div className="text-center py-16 glass-panel">
            <p className="text-white/80 text-lg">Категории не найдены</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredCategories.map((category) => (
              <button
                key={category.id}
                onClick={() => navigate(`/category/${category.id}`)}
                className="w-full glass-panel hover:bg-white/30 transition-all duration-200 group"
              >
                <div className="flex items-center justify-between p-4">
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="w-16 h-16 rounded-lg overflow-hidden bg-white/10 flex-shrink-0">
                      <img
                        src={category.image}
                        alt={category.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="text-left flex-1">
                      <h3 className="text-white font-bold text-lg mb-1">
                        {category.name}
                      </h3>
                      <p className="text-white/70 text-sm">
                        {category.items?.length || 0} товаров
                      </p>
                    </div>
                  </div>
                  <ChevronRight 
                    className="text-white/60 group-hover:text-white group-hover:translate-x-1 transition-all" 
                    size={24} 
                  />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
