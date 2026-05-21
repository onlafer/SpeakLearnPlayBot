import React, { useEffect, useState } from 'react';
import { gamesApi } from '../api/games';
import type { GameInfoSchema } from '../types/api';

interface GameListProps {
  onStartGame: (gameId: string) => void;
  onBack: () => void;
  lang: string;
}

const GameList: React.FC<GameListProps> = ({ onStartGame, onBack, lang }) => {
  const [games, setGames] = useState<GameInfoSchema[]>([]);
  const [loading, setLoading] = useState(true);

  // temp filter
  const allowedGames = ['verb_tense_quiz', 'verb_aspect_quiz', 'russian_cases_quiz'];

  useEffect(() => {
    gamesApi.listGames(lang)
      .then((data) => {
        setGames(data.filter(g => allowedGames.includes(g.game_id)));
      })
      .finally(() => setLoading(false));
  }, [lang]);

  if (loading) return <div>Loading games...</div>;

  return (
    <div className="card">
      <h2>Select a Game</h2>
      <div className="button-grid">
        {games.map((game) => (
          <button key={game.game_id} onClick={() => onStartGame(game.game_id)}>
            {game.name}
          </button>
        ))}
      </div>
      <button onClick={onBack} style={{ marginTop: '2rem', backgroundColor: '#666' }}>
        Back to Menu
      </button>
    </div>
  );
};

export default GameList;
