import React, { useEffect, useState } from 'react';
import { gamesApi } from '../api/games';
import { useTelegram } from '../hooks/useTelegram';
import type { CurrentSessionResponse } from '../types/api';

interface MainMenuProps {
  onSelectGame: () => void;
  onContinueGame: (session: CurrentSessionResponse) => void;
  onOpenSettings: () => void;
  onOpenStreak: () => void;
  lang: string;
}

const MainMenu: React.FC<MainMenuProps> = ({ onSelectGame, onContinueGame, onOpenSettings, onOpenStreak, lang }) => {
  const { user } = useTelegram();
  const [activeSession, setActiveSession] = useState<CurrentSessionResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const labels: Record<string, any> = {
    en: { select: '🎮 Select a game', settings: '⚙️ Settings', continue: '▶️ Continue the game', cancel: '❌ Cancel the game', streak: '🔥 My Streak' },
    es: { select: '🎮 Seleccionar un juego', settings: '⚙️ Ajustes', continue: '▶️ Continuar el juego', cancel: '❌ Cancelar el juego', streak: '🔥 Mi racha' },
    fr: { select: '🎮 Sélectionner un jeu', settings: '⚙️ Paramètres', continue: '▶️ Continuer le jeu', cancel: '❌ Annuler le jeu', streak: '🔥 Ma série' },
    ru: { select: '🎮 Выбрать игру', settings: '⚙️ Настройки', continue: '▶️ Продолжить игру', cancel: '❌ Отменить игру', streak: '🔥 Моя активность' },
    ar: { select: '🎮 اختر لعبة', settings: '⚙️ الإعدادات', continue: '▶️ متابعة اللعبة', cancel: '❌ إلغاء اللعبة', streak: '🔥 نشاطي' },
    zh: { select: '🎮 选择游戏', settings: '⚙️ 设置', continue: '▶️ 继续游戏', cancel: '❌ 取消游戏', streak: '🔥 我的连续天数' },
    fa: { select: '🎮 انتخاب بازی', settings: '⚙️ تنظیمات', continue: '▶️ ادامه بازی', cancel: '❌ لغو بازی', streak: '🔥 فعالیت من' },
    vi: { select: '🎮 Chọn trò chơi', settings: '⚙️ Cài đặt', continue: '▶️ Tiếp tục trò chơi', cancel: '❌ Hủy trò chơi', streak: '🔥 Chuỗi của tôi' },
    ja: { select: '🎮 ゲームを選択', settings: '⚙️ 設定', continue: '▶️ ゲームを続行', cancel: '❌ ゲームをキャンセル', streak: '🔥 連続アクティビティ' },
  };

  const t = labels[lang] || labels.en;

  useEffect(() => {
    gamesApi.getCurrentSession(user.id)
      .then(setActiveSession)
      .catch(err => {
        console.error('[MainMenu] Failed to check active session:', err);
      })
      .finally(() => setLoading(false));
  }, [user.id]);

  const handleCancelGame = async () => {
    if (window.confirm('Are you sure?')) {
      await gamesApi.cancelSession(user.id);
      setActiveSession(null);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="card">
      <h2>Welcome, {user.first_name}!</h2>
      
      {activeSession ? (
        <>
          <button onClick={() => onContinueGame(activeSession)}>{t.continue}</button>
          <button onClick={handleCancelGame}>{t.cancel}</button>
        </>
      ) : (
        <button onClick={onSelectGame}>{t.select}</button>
      )}
      
      <button onClick={onOpenStreak}>{t.streak}</button>
      
      <button onClick={onOpenSettings}>{t.settings}</button>
    </div>
  );
};

export default MainMenu;
