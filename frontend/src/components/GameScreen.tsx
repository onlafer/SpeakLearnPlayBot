import React, { useState } from 'react';
import { gamesApi } from '../api/games';
import { useTelegram } from '../hooks/useTelegram';
import type { GameStateSchema } from '../types/api';
import FormattedText from './FormattedText';

interface GameScreenProps {
  initialState: GameStateSchema;
  gameId: string;
  onFinished: () => void;
  lang: string;
}

const GameScreen: React.FC<GameScreenProps> = ({ initialState, onFinished }) => {
  const { user } = useTelegram();
  const [state, setState] = useState<GameStateSchema>(initialState);
  const [loading, setLoading] = useState(false);
  const [finished, setFinished] = useState(false);

  const handleAction = async (callbackData: string) => {
    if (callbackData === 'show_menu') {
      try {
        await gamesApi.cancelSession(user.id);
      } catch (e) {
        console.error('Failed to cancel session on menu request', e);
      }
      onFinished();
      return;
    }

    setLoading(true);
    try {
      const response = await gamesApi.action(user.id, callbackData);
      if (response.state) {
        setState(response.state);
      }
      if (response.finished) {
        setFinished(true);
      }
    } catch (error) {
      console.error('Action failed', error);
      alert('Action failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="game-text">
        <FormattedText text={state.text} />
      </div>
      
      {!finished ? (
        <div className="button-grid">
          {state.buttons.map((btn, idx) => (
            <button 
              key={`${btn.callback_data}-${idx}`} 
              onClick={() => handleAction(btn.callback_data)}
              disabled={loading}
            >
              {btn.text}
            </button>
          ))}
        </div>
      ) : (
        <button onClick={onFinished} style={{ marginTop: '2rem' }}>
          Back to Menu
        </button>
      )}
    </div>
  );
};

export default GameScreen;
