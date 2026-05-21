export interface ButtonSchema {
  text: string;
  callback_data: string;
}

export interface GameStateSchema {
  text: string;
  buttons: ButtonSchema[];
}

export interface GameInfoSchema {
  game_id: string;
  name: string;
}

export interface StartGameResponse {
  session_id?: number;
  game_id: string;
  score: number;
  current_question: number;
  status: string;
  state: GameStateSchema;
}

export interface ActionResponse {
  game_id: string;
  score: number;
  current_question: number;
  status: string;
  state?: GameStateSchema;
  finished: boolean;
}

export interface CurrentSessionResponse {
  game_id: string;
  score: number;
  current_question: number;
  status: string;
  state?: GameStateSchema;
}

export interface StreakResponse {
  user_id: number;
  streak_count: number;
  last_activity_date: string | null;
  activity_history: string[];
}
