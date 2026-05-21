import React, { useState, useEffect } from 'react';
import MainMenu from './components/MainMenu';
import GameList from './components/GameList';
import GameScreen from './components/GameScreen';
import Settings from './components/Settings';
import StreakScreen from './components/StreakScreen';
import { useTelegram } from './hooks/useTelegram';
import { gamesApi } from './api/games';
import type { GameStateSchema, CurrentSessionResponse } from './types/api';

type Screen = 'MENU' | 'GAME_LIST' | 'GAME' | 'SETTINGS' | 'STREAK';

const App: React.FC = () => {
  const { user, expand } = useTelegram();
  const [screen, setScreen] = useState<Screen>('MENU');
  const [lang, setLang] = useState<string>(localStorage.getItem('lang') || 'en');
  const [currentGameId, setCurrentGameId] = useState<string | null>(null);
  const [initialGameState, setInitialGameState] = useState<GameStateSchema | null>(null);

  useEffect(() => {
    expand();
  }, [expand]);

  const handleStartGame = async (gameId: string) => {
    try {
      const response = await gamesApi.startGame(gameId, user.id, lang);
      setCurrentGameId(gameId);
      setInitialGameState(response.state);
      setScreen('GAME');
    } catch (error) {
      console.error('Failed to start game', error);
      alert('Failed to start game');
    }
  };

  const handleContinueGame = (session: CurrentSessionResponse) => {
    if (session.state) {
      setCurrentGameId(session.game_id);
      setInitialGameState(session.state);
      setScreen('GAME');
    }
  };

  const handleSetLang = (newLang: string) => {
    setLang(newLang);
    localStorage.setItem('lang', newLang);
  };

  return (
    <div className="App">
      {screen === 'MENU' && (
        <MainMenu 
          lang={lang}
          onSelectGame={() => setScreen('GAME_LIST')} 
          onContinueGame={handleContinueGame}
          onOpenSettings={() => setScreen('SETTINGS')}
          onOpenStreak={() => setScreen('STREAK')}
        />
      )}
      
      {screen === 'GAME_LIST' && (
        <GameList 
          lang={lang}
          onStartGame={handleStartGame} 
          onBack={() => setScreen('MENU')} 
        />
      )}
      
      {screen === 'GAME' && currentGameId && initialGameState && (
        <GameScreen 
          lang={lang}
          gameId={currentGameId} 
          initialState={initialGameState} 
          onFinished={() => setScreen('MENU')}
        />
      )}
      
      {screen === 'SETTINGS' && (
        <Settings 
          lang={lang} 
          onSetLang={handleSetLang} 
          onBack={() => setScreen('MENU')} 
        />
      )}

      {screen === 'STREAK' && (
        <StreakScreen 
          lang={lang} 
          onBack={() => setScreen('MENU')} 
        />
      )}
    </div>
  );
};

export default App;
