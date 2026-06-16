import React, { useEffect, useState } from 'react';
import { gamesApi } from '../api/games';
import { useTelegram } from '../hooks/useTelegram';
import type { StreakResponse } from '../types/api';

interface StreakScreenProps {
  lang: string;
  onBack: () => void;
}

const StreakScreen: React.FC<StreakScreenProps> = ({ lang, onBack }) => {
  const { user } = useTelegram();
  const [streakData, setStreakData] = useState<StreakResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [currentDate, setCurrentDate] = useState(new Date());

  const translations: Record<string, any> = {
    en: {
      title: 'My Activity',
      daysConsecutive: 'days in a row',
      back: 'Back to Menu',
      weekdays: ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'],
      loading: 'Loading streak...',
      error: 'Failed to load activity data'
    },
    ru: {
      title: 'Моя активность',
      daysConsecutive: 'дней подряд',
      back: 'Назад в меню',
      weekdays: ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'],
      loading: 'Загружаем активность...',
      error: 'Ошибка загрузки данных активности'
    }
  };

  const t = translations[lang] || translations.en;

  useEffect(() => {
    gamesApi.getStreak(user.id)
      .then(setStreakData)
      .catch(err => {
        console.error('Failed to get streak', err);
        setErrorMsg(err.message || String(err));
      })
      .finally(() => setLoading(false));
  }, [user.id]);

  const changeMonth = (delta: number) => {
    const nextDate = new Date(currentDate);
    nextDate.setMonth(nextDate.getMonth() + delta);
    setCurrentDate(nextDate);
  };

  if (loading) {
    return <div className="card">{t.loading}</div>;
  }

  if (errorMsg) {
    const hasTg = typeof window !== 'undefined' && typeof window.Telegram !== 'undefined';
    const initData = hasTg ? window.Telegram?.WebApp?.initData : '';
    const initDataUnsafe = hasTg ? JSON.stringify(window.Telegram?.WebApp?.initDataUnsafe, null, 2) : '';

    return (
      <div className="card error" style={{ textAlign: 'center', padding: '1.5rem' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>⚠️</div>
        <h3 style={{ color: '#ff4d4d', marginBottom: '1rem' }}>{t.error}</h3>
        <div style={{ margin: '1rem 0', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '8px', fontSize: '0.85rem', textAlign: 'left', wordBreak: 'break-all', maxHeight: '300px', overflowY: 'auto' }}>
          <p style={{ marginBottom: '0.5rem' }}><strong>Error Details:</strong> {errorMsg}</p>
          <p style={{ marginBottom: '0.5rem' }}><strong>Request User ID:</strong> {user.id}</p>
          <p style={{ marginBottom: '0.5rem' }}><strong>API Base URL:</strong> {localStorage.getItem('api_url') || 'Relative (same domain)'}</p>
          <p style={{ marginBottom: '0.5rem' }}><strong>Full URL:</strong> {window.location.href}</p>
          <p style={{ marginBottom: '0.5rem' }}><strong>Telegram Script:</strong> {hasTg ? 'Loaded ✅' : 'Missing ❌'}</p>
          <p style={{ marginBottom: '0.5rem' }}><strong>InitData:</strong> {initData || 'None'}</p>
          <p><strong>InitData Unsafe:</strong></p>
          <pre style={{ background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', overflowX: 'auto', whiteSpace: 'pre-wrap' }}>{initDataUnsafe || 'None'}</pre>
        </div>
        <button onClick={onBack}>{t.back}</button>
      </div>
    );
  }

  if (!streakData) {
    return <div className="card error">{t.error}</div>;
  }

  const activeDays = new Set(streakData.activity_history);
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Get localized month name
  const monthName = new Intl.DateTimeFormat(lang === 'ru' ? 'ru-RU' : 'en-US', {
    month: 'long',
    year: 'numeric'
  }).format(currentDate);
  const formattedMonthName = monthName.charAt(0).toUpperCase() + monthName.slice(1);

  // Calendar calculations
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  
  // Calculate day of week index (0 = Monday, 6 = Sunday)
  let startDayIndex = firstDay.getDay() - 1;
  if (startDayIndex === -1) startDayIndex = 6;

  const prevLastDay = new Date(year, month, 0).getDate();
  const calendarDays: Array<{ dateStr?: string; dayNum: number; isCurrentMonth: boolean; isActive: boolean; isToday: boolean }> = [];

  // Previous month padding
  for (let i = startDayIndex - 1; i >= 0; i--) {
    calendarDays.push({
      dayNum: prevLastDay - i,
      isCurrentMonth: false,
      isActive: false,
      isToday: false
    });
  }

  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  // Current month days
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
    calendarDays.push({
      dateStr,
      dayNum: i,
      isCurrentMonth: true,
      isActive: activeDays.has(dateStr),
      isToday: dateStr === todayStr
    });
  }

  // Next month padding to fill full calendar grid rows
  const remaining = 42 - calendarDays.length;
  const nextMonthPadding = remaining > 7 ? remaining - 7 : remaining;
  for (let i = 1; i <= nextMonthPadding; i++) {
    if (calendarDays.length >= 49) break;
    calendarDays.push({
      dayNum: i,
      isCurrentMonth: false,
      isActive: false,
      isToday: false
    });
  }

  return (
    <div className="card">
      <h2 style={{ marginBottom: '1.5rem' }}>{t.title}</h2>
      
      <div className="streak-badge-card">
        <div className="streak-fire-icon">🔥</div>
        <div className="streak-badge-count">{streakData.streak_count}</div>
        <div className="streak-badge-label">{t.daysConsecutive}</div>
      </div>

      <div className="calendar-badge-card">
        <div className="calendar-nav-header">
          <div className="calendar-nav-month">{formattedMonthName}</div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="nav-arrow-btn" onClick={() => changeMonth(-1)}>←</button>
            <button className="nav-arrow-btn" onClick={() => changeMonth(1)}>→</button>
          </div>
        </div>

        <div className="calendar-days-grid">
          {t.weekdays.map((wd: string) => (
            <div key={wd} className="calendar-grid-weekday">{wd}</div>
          ))}
          {calendarDays.map((day, idx) => {
            let className = 'calendar-grid-day';
            if (!day.isCurrentMonth) className += ' other-month';
            if (day.isActive) className += ' active';
            if (day.isToday) className += ' today';
            
            return (
              <div key={idx} className={className}>
                {day.dayNum}
              </div>
            );
          })}
        </div>
      </div>
      <button onClick={onBack} className="back-button">
        <svg className="back-arrow-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span>{t.back}</span>
      </button>
    </div>
  );
};

export default StreakScreen;
