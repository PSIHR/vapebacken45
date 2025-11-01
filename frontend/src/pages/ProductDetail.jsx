import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { itemsAPI, basketAPI } from '../services/api';
import { useTelegram } from '../hooks/useTelegram';
import { formatPrice } from '../utils/helpers';
import { ArrowLeft, ShoppingCart, Check } from 'lucide-react';

const ProductDetail = ({ onCartUpdate }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, showAlert } = useTelegram();
  const [product, setProduct] = useState(null);
  const [selectedTaste, setSelectedTaste] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

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
      <div className="min-h-screen bg-[#f4f4f5] flex items-center justify-center">
        <div className="text-gray-500">Загрузка...</div>
      </div>
    );
  }

  if (!product) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#f4f4f5]">
      <div className="container mx-auto px-4 py-6 pb-32">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-700 mb-4 hover:text-gray-900"
        >
          <ArrowLeft size={20} />
          <span className="font-medium">Назад</span>
        </button>

        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="relative h-80 bg-gray-100">
            {product.image ? (
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <ShoppingCart size={80} />
              </div>
            )}
          </div>

          <div className="p-6">
            {product.category && (
              <span className="inline-block px-3 py-1 text-sm font-medium text-[#3390ec] bg-blue-50 rounded mb-3">
                {product.category.name}
              </span>
            )}

            <h1 className="text-3xl font-bold text-gray-900 mb-3">
              {product.name}
            </h1>

            <p className="text-lg text-gray-600 mb-6">
              {product.description}
            </p>

            {product.tastes && product.tastes.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Выберите вкус:
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {product.tastes.map((taste) => (
                    <button
                      key={taste.id}
                      onClick={() => setSelectedTaste(taste)}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        selectedTaste?.id === taste.id
                          ? 'border-[#3390ec] bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-900">
                          {taste.name}
                        </span>
                        {selectedTaste?.id === taste.id && (
                          <Check size={20} className="text-[#3390ec]" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="border-t border-gray-200 pt-6">
              <div className="flex items-center justify-between mb-6">
                <span className="text-lg text-gray-600">Цена:</span>
                <span className="text-4xl font-bold text-gray-900">
                  {formatPrice(product.price)}
                </span>
              </div>

              <button
                onClick={handleAddToCart}
                disabled={adding}
                className="w-full bg-[#3390ec] hover:bg-[#2b7cd3] text-white py-4 rounded-lg font-medium text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
