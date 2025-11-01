import { useEffect, useState } from 'react';

export const useTelegram = () => {
  const [tg, setTg] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const telegram = window.Telegram?.WebApp;
    if (telegram) {
      telegram.ready();
      telegram.expand();
      
      // Запрос полноэкранного режима (убирает шапку и панели Telegram)
      if (telegram.requestFullscreen) {
        try {
          telegram.requestFullscreen();
        } catch (error) {
          console.log('Fullscreen not available:', error);
        }
      }
      
      setTg(telegram);
      setUser(telegram.initDataUnsafe?.user);
    }
  }, []);

  const showAlert = (message) => {
    tg?.showAlert(message);
  };

  const showConfirm = (message) => {
    return new Promise((resolve) => {
      tg?.showConfirm(message, resolve);
    });
  };

  const close = () => {
    tg?.close();
  };

  const MainButton = {
    show: () => tg?.MainButton?.show(),
    hide: () => tg?.MainButton?.hide(),
    setText: (text) => tg?.MainButton?.setText(text),
    onClick: (callback) => tg?.MainButton?.onClick(callback),
    offClick: (callback) => tg?.MainButton?.offClick(callback),
    showProgress: () => tg?.MainButton?.showProgress(),
    hideProgress: () => tg?.MainButton?.hideProgress(),
  };

  return {
    tg,
    user,
    showAlert,
    showConfirm,
    close,
    MainButton,
  };
};
