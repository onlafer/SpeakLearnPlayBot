class GameRegistry:
    def __init__(self):
        self._games = {}

    def register(self, game):
        if game.game_id in self._games:
            raise ValueError(f"Game with id {game.game_id} already registered.")
        self._games[game.game_id] = game

    def get_game(self, game_id):
        return self._games.get(game_id)

    def get_all_games(self):
        return self._games

game_registry = GameRegistry()
