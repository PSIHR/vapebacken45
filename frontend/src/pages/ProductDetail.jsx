import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { itemsAPI, basketAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import { formatPrice } from '../utils/helpers';
import { ArrowLeft, ShoppingCart, Check, ChevronDown, ChevronUp } from 'lucide-react';

const ProductDetail = ({ onCartUpdate }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, showAlert } = useTelegram();
  const [product, setProduct] = useState(null);
  const [selectedTastes, setSelectedTastes] = useState([]);
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
        setSelectedTastes([]);
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

  const toggleTaste = (taste) => {
    setSelectedTastes(prev => {
      const isSelected = prev.some(t => t.id === taste.id);
      if (isSelected) {
        return prev.filter(t => t.id !== taste.id);
      } else {
        return [...prev, taste];
      }
    });
  };

  const handleAddToCart = async () => {
    if (!user?.id) {
      showAlert('Пожалуйста, авторизуйтесь');
      return;
    }

    if (product.tastes && product.tastes.length > 0 && selectedTastes.length === 0) {
      showAlert('Пожалуйста, выберите хотя бы один вкус');
      return;
    }

    try {
      setAdding(true);
      
      if (product.tastes && product.tastes.length > 0) {
        await Promise.all(
          selectedTastes.map(taste =>
            basketAPI.addItem(user.id, {
              item_id: product.id,
              selected_taste: taste.name,
            })
          )
        );
        const count = selectedTastes.length;
        showAlert(`${count} ${count === 1 ? 'товар добавлен' : 'товара добавлено'} в корзину`);
      } else {
        await basketAPI.addItem(user.id, {
          item_id: product.id,
          selected_taste: null,
        });
        showAlert('Товар добавлен в корзину');
      }
      
      if (onCartUpdate) {
        await onCartUpdate();
      }
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
        <div className="text-white">Загрузка...</div>
      </div>
    );
  }

  if (!product) {
    return null;
  }

  return (
    <div className="min-h-screen pb-48">
      <div className="container mx-auto px-4 py-6">
        <button
          onClick={() => {
            const categoryId = location.state?.categoryId || product?.category?.id;
            if (categoryId) {
              navigate(`/catalog/${categoryId}`);
            } else {
              navigate('/');
            }
          }}
          className="flex items-center gap-2 text-white mb-4 hover:text-white/80"
        >
          <ArrowLeft size={20} />
          <span className="font-medium">Назад</span>
        </button>

        <div className="glass-panel overflow-hidden">
          <div className="relative h-80">
            {product.image ? (
              <img
                src={product.image}
                alt={product.name}
                loading="lazy"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white/40">
                <ShoppingCart size={80} />
              </div>
            )}
          </div>

          <div className="p-6">
            {product.category && (
              <span className="inline-block px-3 py-1 text-sm font-medium text-black bg-pink-100 rounded-full mb-3">
                {product.category.name}
              </span>
            )}

            <h1 className="text-3xl font-bold text-white mb-4">
              {product.name}
            </h1>

            {product.tastes && product.tastes.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-3">
                  Выберите вкусы ({selectedTastes.length} выбрано):
                </h3>
                <div className="grid grid-cols-2 gap-3 max-h-96 overflow-y-auto">
                  {product.tastes.map((taste) => {
                    const isSelected = selectedTastes.some(t => t.id === taste.id);
                    return (
                      <button
                        key={taste.id}
                        onClick={() => toggleTaste(taste)}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          isSelected
                            ? 'border-pink-400 bg-pink-100'
                            : 'border-white/30 hover:border-white/50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`font-medium ${
                            isSelected 
                              ? 'text-black' 
                              : 'text-white'
                          }`}>
                            {taste.name}
                          </span>
                          {isSelected && (
                            <Check size={20} className="text-black" />
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {product.description && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-2">
                  Описание:
                </h3>
                <div className="relative">
                  <p className={`text-white/80 ${!isDescriptionExpanded ? 'line-clamp-3' : ''}`}>
                    {product.description}
                  </p>
                  {product.description.length > 150 && (
                    <button
                      onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
                      className="mt-2 text-white/60 hover:text-white flex items-center gap-1 transition-colors"
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
                <h3 className="text-lg font-semibold text-white mb-3">
                  Характеристики:
                </h3>
                <div className="space-y-2">
                  {product.strength && (
                    <div className="flex justify-between items-center py-2 border-b border-white/10">
                      <span className="text-white/60">Крепкость:</span>
                      <span className="text-white font-medium">{product.strength}</span>
                    </div>
                  )}
                  {product.puffs && (
                    <div className="flex justify-between items-center py-2 border-b border-white/10">
                      <span className="text-white/60">Количество тяг:</span>
                      <span className="text-white font-medium">{product.puffs}</span>
                    </div>
                  )}
                  {product.vg_pg && (
                    <div className="flex justify-between items-center py-2 border-b border-white/10">
                      <span className="text-white/60">VG/PG:</span>
                      <span className="text-white font-medium">{product.vg_pg}</span>
                    </div>
                  )}
                  {product.tank_volume && (
                    <div className="flex justify-between items-center py-2">
                      <span className="text-white/60">Объем бака:</span>
                      <span className="text-white font-medium">{product.tank_volume}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="border-t border-white/20 pt-6 pb-4">
              <div className="flex items-center justify-between">
                <span className="text-lg text-white/80">Цена:</span>
                <span className="text-4xl font-bold text-white">
                  {formatPrice(product.price)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed bottom button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-black/80 backdrop-blur-xl border-t border-white/10 z-50">
        <div className="container mx-auto max-w-md">
          <button
            onClick={handleAddToCart}
            disabled={adding}
            className="w-full bg-pink-500 hover:bg-pink-600 text-white py-4 rounded-lg font-medium text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
  );
};

export default ProductDetail;
