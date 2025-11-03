export const formatPrice = (price) => {
  return `${price} BYN`;
};

export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

export const getStatusText = (status) => {
  const statusMap = {
    waiting_for_courier: '⏳ Ожидает курьера',
    in_delivery: '🚗 В доставке',
    delivered: '✅ Доставлен',
    completed: '🏁 Завершен',
    canceled: '❌ Отменен',
  };
  return statusMap[status] || status;
};

export const getStatusColor = (status) => {
  const colorMap = {
    waiting_for_courier: 'text-white/80',
    in_delivery: 'text-white/90',
    delivered: 'text-white',
    completed: 'text-gray-400',
    canceled: 'text-gray-500',
  };
  return colorMap[status] || 'text-gray-600';
};
