import { useState, useEffect } from 'react';
import { itemsAPI, basketAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import ProductCard from '../components/ProductCard';
import { Loader2 } from 'lucide-react';

const Catalog = ({ onCartUpdate }) => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTaste, setSelectedTaste] = useState({});
  const { user, showAlert } = useTelegram();

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const response = await itemsAPI.getAll();
      const items = response.data.items || [];
      setProducts(items);

      const uniqueCategories = [...new Set(items.map(item => item.category).filter(Boolean))];
      setCategories(uniqueCategories);
    } catch (error) {
      console.error('Error loading products:', error);
      showAlert('Ошибка загрузки товаров');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (product) => {
    if (!user?.id) {
      showAlert('Необходима авторизация через Telegram');
      return;
    }

    try {
      let taste = null;
      if (product.tastes && product.tastes.length > 0) {
        taste = selectedTaste[product.id] || product.tastes[0].name;
      }

      await basketAPI.addItem(user.id, {
        item_id: product.id,
        quantity: 1,
        selected_taste: taste,
      });

      showAlert(`${product.name} добавлен в корзину`);
      onCartUpdate();
    } catch (error) {
      console.error('Error adding to cart:', error);
      showAlert('Ошибка добавления в корзину');
    }
  };

  const filteredProducts = selectedCategory
    ? products.filter(p => p.category?.id === selectedCategory.id)
    : products;

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
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">
            VAPE PLUG
          </h1>
          <p className="text-white/70 mt-2">📍 Минск, Беларусь</p>
          <p className="text-white/70 mt-1">💬 По всем вопросам: <a href="https://t.me/vapepluggmanager" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">@vapepluggmanager</a></p>
        </div>

        {categories.length > 0 && (
          <div className="mb-6 flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-all ${
                !selectedCategory
                  ? 'bg-white text-purple-600'
                  : 'bg-white/20 text-white hover:bg-white/30 backdrop-blur-sm'
              }`}
            >
              Все
            </button>
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat)}
                className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-all ${
                  selectedCategory?.id === cat.id
                    ? 'bg-white text-purple-600'
                    : 'bg-white/20 text-white hover:bg-white/30 backdrop-blur-sm'
                }`}
              >
                {cat.name}
              </button>
            ))}
          </div>
        )}

        {filteredProducts.length === 0 ? (
          <div className="text-center py-16 glass-panel">
            <p className="text-white/80 text-lg">Товары не найдены</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Catalog;