import { Sparkles, Crown, Gem } from 'lucide-react';

const LoyaltyCard = ({ loyaltyData }) => {
  const { loyalty_level, stamps, discount_percentage, stamps_until_discount } = loyaltyData;

  const cardConfig = {
    White: {
      gradient: 'from-gray-200 via-gray-300 to-gray-400',
      icon: Sparkles,
      iconColor: 'text-gray-700',
      title: 'White Card',
      textColor: 'text-gray-900',
      stampColor: 'bg-gray-700',
      stampEmptyColor: 'bg-gray-300',
      shadow: 'shadow-gray-400/50'
    },
    Platinum: {
      gradient: 'from-gray-400 via-gray-500 to-gray-600',
      icon: Crown,
      iconColor: 'text-white',
      title: 'Platinum Card',
      textColor: 'text-white',
      stampColor: 'bg-white',
      stampEmptyColor: 'bg-gray-300',
      shadow: 'shadow-gray-600/50'
    },
    Black: {
      gradient: 'from-gray-800 via-gray-900 to-black',
      icon: Gem,
      iconColor: 'text-white',
      title: 'Black Card',
      textColor: 'text-white',
      stampColor: 'bg-white',
      stampEmptyColor: 'bg-gray-600',
      shadow: 'shadow-black/50'
    }
  };

  const config = cardConfig[loyalty_level] || cardConfig.White;
  const Icon = config.icon;

  const renderStamps = () => {
    const stampElements = [];
    const isDiscountActive = stamps === 5; // Скидка активна когда 5 штампов
    
    for (let i = 0; i < 6; i++) {
      const isDiscountStamp = i === 5 && isDiscountActive; // 6-й круг подсвечивается
      
      stampElements.push(
        <div
          key={i}
          className={`w-10 h-10 rounded-full ${
            i < stamps ? config.stampColor : config.stampEmptyColor
          } ${isDiscountStamp ? 'ring-4 ring-white scale-110 animate-pulse' : ''} flex items-center justify-center ${i < stamps && loyalty_level === 'White' ? 'text-white' : i < stamps ? 'text-black' : 'text-gray-600'} font-bold text-sm transition-all duration-300`}
        >
          {i < stamps ? '✓' : i + 1}
        </div>
      );
    }
    return stampElements;
  };

  return (
    <div className="w-full max-w-md mx-auto mb-6">
      <div 
        className={`relative bg-gradient-to-br ${config.gradient} rounded-2xl p-6 ${config.shadow} shadow-2xl transform hover:scale-105 transition-all duration-300`}
        style={{
          transform: 'perspective(1000px) rotateX(2deg)',
          transition: 'all 0.3s ease'
        }}
      >
        {/* Card shine effect */}
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/20 to-transparent rounded-2xl"></div>
        
        {/* Header */}
        <div className="flex items-center justify-between mb-4 relative z-10">
          <div className="flex items-center gap-2">
            <Icon className={`${config.iconColor} animate-pulse`} size={32} />
            <div>
              <h3 className={`font-bold text-xl ${config.textColor}`}>{config.title}</h3>
              <p className={`text-sm ${config.textColor} opacity-80`}>Программа лояльности</p>
            </div>
          </div>
          <div className={`text-3xl font-black ${config.textColor}`}>
            {discount_percentage}%
          </div>
        </div>

        {/* Stamps */}
        <div className="mb-4 relative z-10">
          <p className={`text-sm font-medium mb-2 ${config.textColor} ${stamps === 5 ? 'animate-bounce-subtle' : ''}`}>
            {stamps === 5
              ? '🎉 На эту покупку у вас скидка!' 
              : stamps_until_discount > 0 
                ? `Еще ${stamps_until_discount} ${stamps_until_discount === 1 ? 'покупка' : 'покупки'} для скидки на 6-й заказ` 
                : 'Скидка доступна!'}
          </p>
          <div className="grid grid-cols-6 gap-2">
            {renderStamps()}
          </div>
        </div>

        {/* Info */}
        <div className={`text-xs ${config.textColor} opacity-75 relative z-10`}>
          {loyalty_level === 'Black' 
            ? '🎉 Максимальный уровень! Скидка навсегда на каждый 6-й товар'
            : 'Покупайте больше, получайте больше скидок!'}
        </div>

        {/* Decorative corner elements */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-bl-full"></div>
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-black/10 rounded-tr-full"></div>
      </div>
    </div>
  );
};

export default LoyaltyCard;
