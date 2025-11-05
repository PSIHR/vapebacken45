import { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { itemsAPI, categoriesAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import ProductCard from '../components/ProductCard';
import { Loader2, Search, ArrowLeft } from 'lucide-react';

const Catalog = () => {
  const { categoryId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [loading, setLoading] = useState(true);
  const { showAlert } = useTelegram();

  useEffect(() => {
    loadData();
  }, [categoryId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const productsResponse = await itemsAPI.getAll();
      const items = productsResponse.data.items || [];
      setProducts(items);

      if (categoryId) {
        const categoriesResponse = await categoriesAPI.getAll();
        const cats = categoriesResponse.data.categories || [];
        const foundCategory = cats.find(c => c.id === parseInt(categoryId));
        setCategory(foundCategory || null);
        
        if (!foundCategory) {
          showAlert('Категория не найдена');
        }
      } else {
        setCategory(null);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      showAlert('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(product => {
    const matchesCategory = categoryId
      ? product.category?.id === parseInt(categoryId)
      : true;

    const matchesSearch = searchQuery
      ? product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        product.description?.toLowerCase().includes(searchQuery.toLowerCase())
      : true;

    return matchesCategory && matchesSearch;
  });

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
        <button
          onClick={() => navigate('/')}
          className="mb-4 flex items-center gap-2 glass-panel px-4 py-2 rounded-lg hover:bg-pink-100 transition-all"
        >
          <ArrowLeft size={20} className="text-white" />
          <span className="text-white font-medium">Назад к категориям</span>
        </button>

        {category && (
          <div className="mb-6 glass-panel p-4 rounded-2xl">
            <h1 className="text-2xl font-bold text-white">{category.name}</h1>
            {category.description && (
              <p className="text-white/60 mt-2">{category.description}</p>
            )}
          </div>
        )}

        <div className="mb-6 relative backdrop-blur-sm rounded-lg">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/70 z-10" size={20} />
          <input
            type="text"
            placeholder="Поиск товаров..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 rounded-lg bg-white border border-pink-200 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-pink-300 transition-all relative z-10"
          />
        </div>

        {filteredProducts.length === 0 ? (
          <div className="text-center py-16 glass-panel">
            <p className="text-white/60 text-lg">Товары не найдены</p>
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

export default Catalog;