import client from './client';
import type { 
  GameInfoSchema, 
  StartGameResponse, 
  ActionResponse, 
  CurrentSessionResponse,
  StreakResponse
} from '../types/api';

export const gamesApi = {
  listGames: async (lang: string): Promise<GameInfoSchema[]> => {
    const response = await client.get<GameInfoSchema[]>('/api/games', {
      params: { lang },
    });
    return response.data;
  },

  startGame: async (gameId: string, userId: number, lang: string): Promise<StartGameResponse> => {
    const response = await client.post<StartGameResponse>(`/api/games/${gameId}/start`, {
      user_id: userId,
      lang,
      });
    return response.data;
  },

  action: async (userId: number, callbackData: string): Promise<ActionResponse> => {
    const response = await client.post<ActionResponse>('/api/sessions/action', {
      user_id: userId,
      callback_data: callbackData,
    });
    return response.data;
  },

  cancelSession: async (userId: number): Promise<{ ok: boolean; message: string }> => {
    const response = await client.post('/api/sessions/cancel', {
      user_id: userId,
    });
    return response.data;
  },

  getCurrentSession: async (userId: number): Promise<CurrentSessionResponse | null> => {
    try {
      const response = await client.get<CurrentSessionResponse>('/api/sessions/current', {
        params: { user_id: userId },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  getStreak: async (userId: number): Promise<StreakResponse> => {
    const response = await client.get<StreakResponse>(`/api/streak/${userId}`);
    return response.data;
  },
};
