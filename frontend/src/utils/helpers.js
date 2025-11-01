export const formatPrice = (price) => {
  return `${price}₽`;
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
    waiting_for_courier: 'text-yellow-600',
    in_delivery: 'text-blue-600',
    delivered: 'text-green-600',
    completed: 'text-gray-600',
    canceled: 'text-red-600',
  };
  return colorMap[status] || 'text-gray-600';
};
