from app import create_app
from app.models import Game, Match, MatchPlayer, GameStatus

app = create_app()
with app.app_context():
    games = Game.query.filter_by(status=GameStatus.COMPLETED).all()
    print(f'Found {len(games)} completed games')
    
    for g in games:
        match = g.matches.first()
        if match and match.status == 'approved':
            print(f'Game {g.id} has approved match {match.id}')
            winner = MatchPlayer.query.filter_by(match_id=match.id, placement=1).first()
            if winner:
                print(f'  Winner: User {winner.user_id}')
            else:
                print('  No winner found')
