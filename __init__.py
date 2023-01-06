from os.path import join, dirname
import random
from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.log import LOG
from ovos_utils.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media
from youtube_archivist import YoutubeMonitor


class StarMediaSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super().__init__("StarMedia")
        self.supported_media = [MediaType.MOVIE,
                                MediaType.GENERIC]
        self.skill_icon = self.default_bg = join(dirname(__file__), "ui", "starmedia_icon.jpg")
        self.archive = YoutubeMonitor(db_name="StarMedia",
                                      min_duration=30 * 60,
                                      logger=LOG,
                                      blacklisted_kwords=["trailer", "teaser", "movie scene",
                                                          "movie clip", "behind the scenes",
                                                          "Movie Preview",
                                                          "soundtrack", " OST", "opening theme"])
        self.archive_ru = YoutubeMonitor(db_name="StarMedia_ru",
                                      min_duration=30 * 60,
                                      logger=LOG,
                                      blacklisted_kwords=["trailer", "teaser", "movie scene",
                                                          "movie clip", "behind the scenes",
                                                          "Movie Preview",
                                                          "soundtrack", " OST", "opening theme"])

    def initialize(self):
        bootstrap = "https://github.com/JarbasSkills/skill-starmedia/raw/dev/bootstrap.json"
        self.archive.bootstrap_from_url(bootstrap)
        bootstrap_ru = "https://github.com/JarbasSkills/skill-starmedia/raw/dev/bootstrap_ru.json"
        self.archive.bootstrap_from_url(bootstrap_ru)
        self.schedule_event(self._sync_db, random.randint(3600, 24 * 3600))

    def _sync_db(self):
        url = "https://www.youtube.com/channel/UCuSx-lf2ft7hPceGVNHybOw"  # english subs
        ru_url = "https://www.youtube.com/user/starmedia"  # russian only
        self.archive.parse_videos(url)
        self.archive_ru.parse_videos(ru_url)
        self.schedule_event(self._sync_db, random.randint(3600, 24*3600))

    # matching
    def match_skill(self, phrase, media_type):
        score = 0
        if self.voc_match(phrase, "movie") or media_type == MediaType.MOVIE:
            score += 10
        if self.voc_match(phrase, "maverick"):
            score += 50
        return score

    def normalize_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "maverick")
        title = self.remove_voc(title, "movie")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join(
            [w for w in title.split(" ") if w])  # remove extra spaces

    def calc_score(self, phrase, match, base_score=0):
        score = base_score
        score += 100 * fuzzy_match(phrase.lower(), match["title"].lower())
        return min(100, score)

    def get_playlist(self, score=50, num_entries=250):
        pl = self.featured_media()[:num_entries]
        return {
            "match_confidence": score,
            "media_type": MediaType.MOVIE,
            "playlist": pl,
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "image": self.skill_icon,
            "bg_image": self.default_bg,
            "title": "StarMedia (Movie Playlist)",
            "author": "StarMedia"
        }

    @ocp_search()
    def search_db(self, phrase, media_type):
        base_score = self.match_skill(phrase, media_type)
        if self.voc_match(phrase, "starmedia"):
            yield self.get_playlist(base_score)
        if media_type == MediaType.MOVIE:
            # only search db if user explicitly requested movies
            phrase = self.normalize_title(phrase)
            for url, video in self.archive.db.items():
                yield {
                    "title": video["title"],
                    "author": "Full Free Films",
                    "match_confidence": self.calc_score(phrase, video, base_score),
                    "media_type": MediaType.MOVIE,
                    "uri": "youtube//" + url,
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": self.default_bg
                }

    @ocp_featured_media()
    def featured_media(self):
        return [{
            "title": video["title"],
            "image": video["thumbnail"],
            "match_confidence": 70,
            "media_type": MediaType.MOVIE,
            "uri": "youtube//" + video["url"],
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "bg_image": video["thumbnail"],
            "skill_id": self.skill_id
        } for video in self.archive.sorted_entries()]


def create_skill():
    return StarMediaSkill()
