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
      
      // Блокировка закрытия приложения свайпом вниз по контенту
      // Пользователь всё ещё может закрыть приложение через шапку или кнопку закрытия
      if (telegram.disableVerticalSwipes) {
        telegram.disableVerticalSwipes();
      }
      
      setTg(telegram);
      setUser(telegram.initDataUnsafe?.user);
    } else {
      // Mock user для preview/тестирования
      setUser({ id: 123456789, username: 'preview_user' });
    }
  }, []);

  const showAlert = (message) => {
    if (tg?.showAlert) {
      tg.showAlert(message);
    } else {
      console.log('Alert:', message);
    }
  };

  const showConfirm = (message) => {
    return new Promise((resolve) => {
      if (tg?.showConfirm) {
        tg.showConfirm(message, resolve);
      } else {
        resolve(window.confirm(message));
      }
    });
  };

  const close = () => {
    if (tg?.close) {
      tg.close();
    } else {
      console.log('Close app');
    }
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
