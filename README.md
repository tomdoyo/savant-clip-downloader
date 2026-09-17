# Savant clip downloader

Download pitch videos from Baseball Savant, one pitch at a time or a whole game.

## Use

```
python download_clips.py 2f22ed14-a540-37f3-9bbc-3f44ed2f945f
```

An argument with dashes is a `playId`, the ID at the end of a Savant video link (`sporty-videos?playId=...`). The clip saves to `clips/<playId>.mp4`, and the script prints a count of results:

```
2f22ed14-a540-37f3-9bbc-3f44ed2f945f {'ok': 1}
```

An argument of only digits is a `game_pk`, the number in the game's MLB.com or Baseball Savant link. The script then downloads every pitch of that game:

```
python download_clips.py 776188
```

Clips are about 4 MB each, which puts a full game around 1 GB. The script downloads them one at a time and skips any clip already on disk, so you can rerun a game safely.

`--player` with `--season` downloads every pitch one player saw that year, and `--pitching` switches that to every pitch they threw. `--start-date` and `--end-date` narrow it to part of the season:

```
python download_clips.py --player 592450 --season 2024
python download_clips.py --player 592789 --season 2024 --pitching
python download_clips.py --player 592450 --season 2024 --start-date 2024-09-15 --end-date 2024-09-17
```

A season is thousands of clips, so start with a date range. Each clip prints its result as it lands:

```
[1/23] cc03faf2-5f4c-439a-8746-3054e6ba0c24: ok
[2/23] 47597bb1-56c2-4970-9e0a-9716864d1699: on disk
```

## How it works

1. For a game, the MLB Stats API game feed lists the `playId` of each pitch.
2. For a player, Savant's search CSV lists the games they played, and the game feed gives their pitches in each one.
3. The Savant page `sporty-videos?playId=...` has the clip link in a `<source>` tag.
4. The script downloads the clip from that link.

## Notes

- If a page has no `<source>` tag, Savant has no video for that pitch. Spring training games and games from the last day or so often have none.
- Timeouts and server errors often clear up on their own. The script tries each clip 3 times, and if one still fails you can run the game again later.
