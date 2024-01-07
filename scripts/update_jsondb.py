import json
import shutil
from os.path import dirname, isfile

from youtube_archivist import YoutubeMonitor

archive = YoutubeMonitor(db_name="StarMedia",
                         min_duration=30 * 60,
                         blacklisted_kwords=["trailer", "teaser", "movie scene",
                                             "movie clip", "behind the scenes",
                                             "Movie Preview",
                                             "soundtrack", " OST", "opening theme"])
archive_ru = YoutubeMonitor(db_name="StarMedia_ru",
                            min_duration=30 * 60,
                            blacklisted_kwords=["trailer", "teaser", "movie scene",
                                                "movie clip", "behind the scenes",
                                                "Movie Preview",
                                                "soundtrack", " OST", "opening theme"])

# load previous cache
cache_file = f"{dirname(dirname(__file__))}/bootstrap.json"
cache_file_ru = f"{dirname(dirname(__file__))}/bootstrap_ru.json"
if isfile(cache_file):
    try:
        with open(cache_file) as f:
            data = json.load(f)
            archive.db.update(data)
            archive.db.store()
    except:
        pass  # corrupted for some reason

    shutil.rmtree(cache_file, ignore_errors=True)

for url in [
    "https://www.youtube.com/channel/UCuSx-lf2ft7hPceGVNHybOw"
]:
    # parse new vids
    archive.parse_videos(url)
for url in [
    "https://www.youtube.com/user/starmedia"
]:
    # parse new vids
    archive_ru.parse_videos(url)

# save bootstrap cache
shutil.copy(archive.db.path, cache_file)
shutil.copy(archive_ru.db.path, cache_file_ru)
