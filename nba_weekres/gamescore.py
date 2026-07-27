def game_score(stat_row):
    """Hollinger Game Score from a single player box-score row.

    GmSc = PTS + 0.4*FG - 0.7*FGA - 0.4*(FTA-FT) + 0.7*OREB + 0.3*DREB
           + STL + 0.7*AST + 0.7*BLK - 0.4*PF - TOV
    """
    pts = stat_row.get("points", 0) or 0
    fgm = stat_row.get("fgm", 0) or 0
    fga = stat_row.get("fga", 0) or 0
    ftm = stat_row.get("ftm", 0) or 0
    fta = stat_row.get("fta", 0) or 0
    oreb = stat_row.get("offReb", 0) or 0
    dreb = stat_row.get("defReb", 0) or 0
    stl = stat_row.get("steals", 0) or 0
    ast = stat_row.get("assists", 0) or 0
    blk = stat_row.get("blocks", 0) or 0
    pf = stat_row.get("pFouls", 0) or 0
    tov = stat_row.get("turnovers", 0) or 0

    return (
        pts
        + 0.4 * fgm
        - 0.7 * fga
        - 0.4 * (fta - ftm)
        + 0.7 * oreb
        + 0.3 * dreb
        + stl
        + 0.7 * ast
        + 0.7 * blk
        - 0.4 * pf
        - tov
    )
