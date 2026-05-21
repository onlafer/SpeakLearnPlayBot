declare global {
  interface Window {
    Telegram?: any;
  }
}

export const useTelegram = () => {
  const tg = typeof window !== 'undefined' && window.Telegram?.WebApp ? window.Telegram.WebApp : undefined;

  return {
    tg,
    user: tg?.initDataUnsafe?.user || { id: 12345, first_name: 'Local', last_name: 'Test' }, // Mock for local dev
    expand: () => {
      try {
        tg?.expand();
      } catch (e) {
        console.warn('Failed to expand Telegram WebApp', e);
      }
    },
    close: () => {
      try {
        tg?.close();
      } catch (e) {
        console.warn('Failed to close Telegram WebApp', e);
      }
    },
  };
};

