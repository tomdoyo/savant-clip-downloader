"""Download pitch videos from Baseball Savant, one pitch, a whole game, or a player's season.

Use:  python download_clips.py 2f22ed14-a540-37f3-9bbc-3f44ed2f945f   (one pitch, by play id)
      python download_clips.py 776188                                 (a whole game, by game_pk)
      python download_clips.py --player 592450 --season 2024          (every pitch a batter saw)
      python download_clips.py --player 592789 --season 2024 --pitching  (every pitch a pitcher threw)
Out:  clips/<play_id>.mp4
"""
import argparse
import csv
import html
import io
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

USER_AGENT = "savant-clip-downloader"
OUT = Path("clips")


def get(url):
    """Bytes at url."""
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as r:
        return r.read()


def play_ids(game_pk, player=None, role="batter"):
    """Every pitch's play id in one game, from the MLB Stats API game feed. One player's, if given."""
    feed = json.loads(get(f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"))
    return [ev["playId"] for play in feed["liveData"]["plays"]["allPlays"]
            if player is None or play["matchup"][role]["id"] == player
            for ev in play["playEvents"] if ev.get("isPitch") and ev.get("playId")]


def player_play_ids(player, start, end, pitching=False):
    """Every pitch's play id for one player between two dates, Savant's search for the games."""
    role = "pitcher" if pitching else "batter"
    rows = get("https://baseballsavant.mlb.com/statcast_search/csv?all=true&type=details"
               f"&player_type={role}&{role}s_lookup%5B%5D={player}"
               f"&game_date_gt={start}&game_date_lt={end}").decode()
    games = sorted({row["game_pk"] for row in csv.DictReader(io.StringIO(rows))})
    return [play_id for game_pk in games for play_id in play_ids(game_pk, player, role)]


def download(play_id, tries=3):
    """One pitch video to clips/. Returns ok | on disk | no video | failed."""
    dest = OUT / f"{play_id}.mp4"
    if dest.exists():
        return "on disk"
    for attempt in range(1, tries + 1):
        try:
            page = get(f"https://baseballsavant.mlb.com/sporty-videos?playId={play_id}").decode()
            source = re.search(r'<source\s+src="([^"]+\.mp4[^"]*)"', page)
            if not source:
                return "no video"  # Savant never published one (spring training, very recent games, etc.)
            clip = get(html.unescape(source.group(1)))
            if clip[4:8] == b"ftyp":  # every MP4 file has "ftyp" at byte 4
                dest.write_bytes(clip)
                return "ok"
        except OSError:
            pass
        time.sleep(5 * attempt)
    return "failed"


def download_all(ids):
    """Every clip in ids, one at a time, printing each result as it lands."""
    results = []
    for n, play_id in enumerate(ids, 1):
        results.append(download(play_id))
        print(f"[{n}/{len(ids)}] {play_id}: {results[-1]}")
    return results


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    parser = argparse.ArgumentParser(description="Download pitch videos from Baseball Savant.")
    parser.add_argument("targets", nargs="*", help="play ids (with dashes) or game_pks (digits)")
    parser.add_argument("--player", type=int, help="MLB player id, every pitch this player saw")
    parser.add_argument("--season", type=int, help="season year, required with --player")
    parser.add_argument("--pitching", action="store_true", help="pitches thrown, not pitches seen")
    parser.add_argument("--start-date", help="YYYY-MM-DD, defaults to the start of the season")
    parser.add_argument("--end-date", help="YYYY-MM-DD, defaults to the end of the season")
    args = parser.parse_args()

    if args.player:
        if not args.season:
            parser.error("--player needs --season")
        ids = player_play_ids(args.player, args.start_date or f"{args.season}-01-01",
                              args.end_date or f"{args.season}-12-31", args.pitching)
        results = download_all(ids)
        print(args.player, {r: results.count(r) for r in set(results)})

    for arg in args.targets:
        ids = [arg] if "-" in arg else play_ids(arg)  # play ids have dashes, game_pks are digits
        results = download_all(ids)
        print(arg, {r: results.count(r) for r in set(results)})
