import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { itemsAPI, categoriesAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import ProductCard from '../components/ProductCard';
import { Loader2, Search, ChevronLeft } from 'lucide-react';

const CategoryProducts = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const { showAlert } = useTelegram();

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [productsResponse, categoriesResponse] = await Promise.all([
        itemsAPI.getAll(),
        categoriesAPI.getAll()
      ]);
      
      const items = productsResponse.data.items || [];
      const cats = categoriesResponse.data.categories || [];
      
      const currentCategory = cats.find(cat => cat.id === parseInt(id));
      setCategory(currentCategory);
      
      // Фильтруем товары только этой категории
      const categoryProducts = items.filter(
        product => product.category?.id === parseInt(id)
      );
      setProducts(categoryProducts);
    } catch (error) {
      console.error('Error loading data:', error);
      showAlert('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(product =>
    searchQuery
      ? product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        product.description?.toLowerCase().includes(searchQuery.toLowerCase())
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
        {/* Кнопка назад и название категории */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-white/80 hover:text-white mb-4 transition-colors"
          >
            <ChevronLeft size={20} />
            <span className="ml-1">Назад к категориям</span>
          </button>
          
          {category && (
            <h1 className="text-2xl font-bold text-white">
              {category.name}
            </h1>
          )}
        </div>

        <div className="mb-6 relative backdrop-blur-sm rounded-lg">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white z-10" size={20} />
          <input
            type="text"
            placeholder="Поиск товаров..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all relative z-10"
          />
        </div>

        {filteredProducts.length === 0 ? (
          <div className="text-center py-16 glass-panel">
            <p className="text-white/80 text-lg">
              {searchQuery ? 'Товары не найдены' : 'В этой категории пока нет товаров'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {filteredProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CategoryProducts;
