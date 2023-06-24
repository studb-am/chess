import chess 
import chess.pgn
import json
import chess.engine as ce
import requests as r

wb_path = "https://en.wikibooks.org/w/api.php?titles=Chess_Opening_Theory"
engine = ce.SimpleEngine.popen_uci("stockfish")
limit = ce.Limit(depth=10, time=0.5)

def make_analysis_on_pgn(pgn_path: str, wb_path: str = wb_path) -> None:
    orig_wb_path = wb_path
    pgn = open(pgn_path)
    game = chess.pgn.read_game(pgn)
    analysis = dict() #initialization of the analysis dictionary
    board = game.board() #initialization of the chess board

    analysis['meta'] = { **game.headers }
    analysis['steps'] = list()

    for move in game.mainline_moves():
        print('next move', str(move))
        moveRecord = dict()
        moveRecord['turn'] = 'w' if board.turn else 'b'
        moveRecord['movePlayed'] = str(move)
        #Get the top3 suggestions
        suggestions = engine.analyse(board=board, limit=limit, multipv=3)
        top3suggestions = list()
        for suggestion in suggestions:
            localRow = dict()
            wins , draws, losses = suggestion['score'].wdl()
            localRow['score'] = { 'w': wins, 'd': draws, 'l': losses}
            localRow['suggestedMoves'] = [str(pv) for pv in suggestion['pv']]
            localRow['nextMove'] = str(suggestion['pv'][0])
            top3suggestions.append(localRow)
        moveRecord['engineSuggestions'] = top3suggestions
        
        #Apply Move
        turnNum = board.fullmove_number
        san_move = board.san(move)
        board.push(move)
        #Get suggestions from wikibook           
        wb_path += f"/{turnNum}.{'_' if not board.turn else '..'}{san_move}"
        try:
            wb_result = r.get(f"{wb_path}&redirects&origin=*&action=query&prop=extracts&formatversion=2&format=json&exchars=1200")
            explaination = json.loads(wb_result.text)
            if 'query' in explaination and 'pages' in explaination['query'] and 'extract' in explaination['query']['pages'][0]:
                moveRecord['wbSummary'] = f"{explaination['query']['pages'][0]['extract']}<br />Further details available on <a href='{wb_path.replace(orig_wb_path,'https://en.wikibooks.org/wiki/Chess_Opening_Theory')}'>Wikibooks</a>"
        except Exception as err:
            print(f"No match found for {wb_path}. Error: {err}")
        
        analysis['steps'].append(moveRecord)
    
    file_name = pgn_path.replace("pgns/","matchAnalysis/").replace(".pgn",".json")
    with open(file_name, 'w') as f:
        f.write(json.dumps(analysis, indent=4))
        print("Export successfully done")

#test execution of the function    
if __name__ == "__main__":
    make_analysis_on_pgn("pgns/20230617__1.pgn")