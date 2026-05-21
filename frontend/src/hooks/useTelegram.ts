declare global {
  interface Window {
    Telegram: any;
  }
}

export const useTelegram = () => {
  const tg = window.Telegram.WebApp;

  return {
    tg,
    user: tg?.initDataUnsafe?.user || { id: 12345, first_name: 'Local', last_name: 'Test' }, // Mock for local dev
    expand: () => tg?.expand(),
    close: () => tg?.close(),
  };
};
