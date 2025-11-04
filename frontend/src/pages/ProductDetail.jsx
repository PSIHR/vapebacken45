import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { itemsAPI, basketAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import { formatPrice } from '../utils/helpers';
import { ArrowLeft, ShoppingCart, Check, ChevronDown, ChevronUp } from 'lucide-react';

const ProductDetail = ({ onCartUpdate }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, showAlert } = useTelegram();
  const [product, setProduct] = useState(null);
  const [selectedTaste, setSelectedTaste] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);

  useEffect(() => {
    loadProduct();
  }, [id]);

  const loadProduct = async () => {
    try {
      setLoading(true);
      const response = await itemsAPI.getAll();
      const foundProduct = response.data.items.find(item => item.id === parseInt(id));
      
      if (foundProduct) {
        setProduct(foundProduct);
        if (foundProduct.tastes && foundProduct.tastes.length > 0) {
          setSelectedTaste(foundProduct.tastes[0]);
        }
      } else {
        showAlert('Товар не найден');
        navigate('/');
      }
    } catch (error) {
      console.error('Error loading product:', error);
      showAlert('Ошибка загрузки товара');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!user?.id) {
      showAlert('Пожалуйста, авторизуйтесь');
      return;
    }

    try {
      setAdding(true);
      await basketAPI.addItem(user.id, {
        item_id: product.id,
        selected_taste: selectedTaste?.name || null,
      });
      
      showAlert('Товар добавлен в корзину');
      if (onCartUpdate) {
        await onCartUpdate();
      }
      navigate('/cart');
    } catch (error) {
      console.error('Error adding to cart:', error);
      showAlert('Ошибка добавления в корзину');
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-800">Загрузка...</div>
      </div>
    );
  }

  if (!product) {
    return null;
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-6 pb-32">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-800 mb-4 hover:text-gray-800/80"
        >
          <ArrowLeft size={20} />
          <span className="font-medium">Назад</span>
        </button>

        <div className="glass-panel overflow-hidden">
          <div className="relative h-80 bg-pink-50">
            {product.image ? (
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-800/40">
                <ShoppingCart size={80} />
              </div>
            )}
          </div>

          <div className="p-6">
            {product.category && (
              <span className="inline-block px-3 py-1 text-sm font-medium text-gray-800 bg-pink-100 rounded-full mb-3">
                {product.category.name}
              </span>
            )}

            <h1 className="text-3xl font-bold text-gray-800 mb-4">
              {product.name}
            </h1>

            {product.tastes && product.tastes.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Выберите вкус:
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {product.tastes.map((taste) => (
                    <button
                      key={taste.id}
                      onClick={() => setSelectedTaste(taste)}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        selectedTaste?.id === taste.id
                          ? 'border-white bg-pink-100'
                          : 'border-white/30 hover:border-white/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-800">
                          {taste.name}
                        </span>
                        {selectedTaste?.id === taste.id && (
                          <Check size={20} className="text-gray-800" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {product.description && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  Описание:
                </h3>
                <div className="relative">
                  <p className={`text-gray-800/80 ${!isDescriptionExpanded ? 'line-clamp-3' : ''}`}>
                    {product.description}
                  </p>
                  {product.description.length > 150 && (
                    <button
                      onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
                      className="mt-2 text-gray-800/60 hover:text-gray-800 flex items-center gap-1 transition-colors"
                    >
                      {isDescriptionExpanded ? (
                        <>
                          Свернуть <ChevronUp size={18} />
                        </>
                      ) : (
                        <>
                          Подробнее <ChevronDown size={18} />
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            )}

            {(product.strength || product.puffs || product.vg_pg || product.tank_volume) && (
              <div className="mb-6 bg-white/5 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Характеристики:
                </h3>
                <div className="space-y-2">
                  {product.strength && (
                    <div className="flex justify-between items-center py-2 border-b border-white/10">
                      <span className="text-gray-800/60">Крепкость:</span>
                      <span className="text-gray-800 font-medium">{product.strength}</span>
                    </div>
                  )}
                  {product.puffs && (
                    <div className="flex justify-between items-center py-2 border-b border-white/10">
                      <span className="text-gray-800/60">Количество тяг:</span>
                      <span className="text-gray-800 font-medium">{product.puffs}</span>
                    </div>
                  )}
                  {product.vg_pg && (
                    <div className="flex justify-between items-center py-2 border-b border-white/10">
                      <span className="text-gray-800/60">VG/PG:</span>
                      <span className="text-gray-800 font-medium">{product.vg_pg}</span>
                    </div>
                  )}
                  {product.tank_volume && (
                    <div className="flex justify-between items-center py-2">
                      <span className="text-gray-800/60">Объем бака:</span>
                      <span className="text-gray-800 font-medium">{product.tank_volume}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="border-t border-white/20 pt-6">
              <div className="flex items-center justify-between mb-6">
                <span className="text-lg text-gray-800/80">Цена:</span>
                <span className="text-4xl font-bold text-gray-800">
                  {formatPrice(product.price)}
                </span>
              </div>

              <button
                onClick={handleAddToCart}
                disabled={adding}
                className="w-full bg-pink-500 hover:bg-pink-600 text-gray-800 py-4 rounded-lg font-medium text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 backdrop-blur-sm"
              >
                {adding ? (
                  'Добавление...'
                ) : (
                  <>
                    <ShoppingCart size={24} />
                    Добавить в корзину
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;
