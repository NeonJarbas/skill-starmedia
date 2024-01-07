import random
from os.path import join, dirname

import requests
from json_database import JsonStorageXDG

from ovos_utils.ocp import MediaType, PlaybackType
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class StarMediaSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.MOVIE,
                                MediaType.DOCUMENTARY,
                                MediaType.VIDEO_EPISODES]
        self.skill_icon = self.default_bg = join(dirname(__file__), "ui", "starmedia_icon.jpg")
        self.archive = JsonStorageXDG("StarMedia", subfolder="OCP")
        self.archive_ru = JsonStorageXDG("StarMedia_ru", subfolder="OCP")
        self.media_type_exceptions = {}
        super().__init__(*args, **kwargs)

    def initialize(self):
        self._sync_db()
        self.load_ocp_keywords()

    def _sync_db(self):
        bootstrap = "https://github.com/JarbasSkills/skill-starmedia/raw/dev/bootstrap.json"
        data = requests.get(bootstrap).json()
        self.archive.merge(data)
        bootstrap = "https://github.com/JarbasSkills/skill-starmedia/raw/dev/bootstrap_ru.json"
        data = requests.get(bootstrap).json()
        self.archive_ru.merge(data)
        self.schedule_event(self._sync_db, random.randint(3600, 24 * 3600))

    def load_ocp_keywords(self):
        title = []
        series = []
        docus = []

        genre = ["russian", "war"]

        if any(l.startswith("ru-") for l in self.native_langs):
            db = list(self.archive.values()) + list(self.archive_ru.values())
        else:
            db = self.archive.values()

        for data in db:
            t = data["title"].replace("★English Version★", "")
            if any(w in t.lower() for w in ["documentar", "docudrama"]):
                t = t.split(".")[0].split("-")[0].split("(")[0].strip()
                docus.append(t)
                self.media_type_exceptions[data["url"]] = MediaType.DOCUMENTARY
            elif "series" in t.lower() or "episode" in t.lower():
                t = t.split(".")[0].split("-")[0].split("(")[0].strip()
                series.append(t)
                self.media_type_exceptions[data["url"]] = MediaType.VIDEO_EPISODES
            else:
                t = t.split(".")[0].split("-")[0].split("(")[0].strip()
                if '"' in t:
                    t = t.split('"')[1]
                if "/" in t:
                    t1, t2 = t.split("/")
                    title.append(t1.strip())
                    title.append(t2.strip())
                title.append(t.strip())

        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_name", title)
        self.register_ocp_keyword(MediaType.DOCUMENTARY,
                                  "documentary_name", docus)
        self.register_ocp_keyword(MediaType.VIDEO_EPISODES,
                                  "series_name", series)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "film_genre", genre)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_streaming_provider",
                                  ["StarMedia",
                                   "Star Media"])

    def get_playlist(self, score=50, num_entries=25):
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
        base_score = 15 if media_type == MediaType.MOVIE else 0
        entities = self.ocp_voc_match(phrase)

        # russian media, bonus if russian is a native lang
        if any(l.startswith("ru-") for l in self.native_langs):
            base_score += 15

        skill = "movie_streaming_provider" in entities  # skill matched

        base_score += 30 * len(entities)
        title = entities.get("movie_name")
        dtitle = entities.get("documentary_name")
        stitle = entities.get("series_name")

        if media_type == MediaType.DOCUMENTARY:
            candidates = [video for video in self.archive.values()
                          if self.media_type_exceptions.get(video["url"], MediaType.MOVIE) ==
                          MediaType.DOCUMENTARY]
        elif media_type == MediaType.VIDEO_EPISODES:
            candidates = [video for video in self.archive.values()
                          if self.media_type_exceptions.get(video["url"], MediaType.MOVIE) ==
                          MediaType.VIDEO_EPISODES]

        else:
            candidates = [video for video in self.archive.values()
                          if video["url"] not in self.media_type_exceptions]

        # movies
        if title:
            base_score += 30
            candidates = [video for video in candidates
                          if title.lower() in video["title"].lower()]
            for video in candidates:
                yield {
                    "title": video["title"],
                    "author": video["author"],
                    "match_confidence": min(100, base_score),
                    "media_type": MediaType.MOVIE,
                    "uri": "youtube//" + video["url"],
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": video["thumbnail"]
                }

        # series
        if stitle:
            base_score += 30
            candidates = [video for video in candidates
                          if stitle.lower() in video["title"].lower()]
            for video in candidates:
                yield {
                    "title": video["title"],
                    "author": video["author"],
                    "match_confidence": min(100, base_score),
                    "media_type": MediaType.VIDEO_EPISODES,
                    "uri": "youtube//" + video["url"],
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": video["thumbnail"]
                }

        # documentaries
        if dtitle:
            base_score += 20
            candidates = [video for video in candidates
                          if dtitle.lower() in video["title"].lower()]
            for video in candidates:
                yield {
                    "title": video["title"],
                    "author": video["author"],
                    "match_confidence": min(100, base_score),
                    "media_type": MediaType.DOCUMENTARY,
                    "uri": "youtube//" + video["url"],
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": video["thumbnail"]
                }

        if skill:
            yield self.get_playlist()

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
        } for video in self.archive.values()]


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = StarMediaSkill(bus=FakeBus(), skill_id="t.fake")
    for r in s.search_db("Armed Love", MediaType.VIDEO_EPISODES):
        print(r)
        # {'title': 'Armed Love - Episode 2. Russian TV series. Сriminal Melodrama. English Subtitles. StarMedia', 'author': 'StarMediaEN', 'match_confidence': 60, 'media_type': <MediaType.VIDEO_EPISODES: 19>, 'uri': 'youtube//https://youtube.com/watch?v=khsu0pKhENM', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/khsu0pKhENM/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/khsu0pKhENM/sddefault.jpg'}
        # {'title': 'Armed Love - Episode 1. Russian TV series. Сriminal Melodrama. English Subtitles. StarMedia', 'author': 'StarMediaEN', 'match_confidence': 60, 'media_type': <MediaType.VIDEO_EPISODES: 19>, 'uri': 'youtube//https://youtube.com/watch?v=4-wbbW2ndH8', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/4-wbbW2ndH8/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/4-wbbW2ndH8/sddefault.jpg'}
        # {'title': 'Armed Love - Episode 3. Russian TV series. Сriminal Melodrama. English Subtitles. StarMedia', 'author': 'StarMediaEN', 'match_confidence': 60, 'media_type': <MediaType.VIDEO_EPISODES: 19>, 'uri': 'youtube//https://youtube.com/watch?v=oQ-xz-_qTgw', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/oQ-xz-_qTgw/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/oQ-xz-_qTgw/sddefault.jpg'}
        # {'title': 'Armed Love - Episode 4. Russian TV series. Сriminal Melodrama. English Subtitles. StarMedia', 'author': 'StarMediaEN', 'match_confidence': 60, 'media_type': <MediaType.VIDEO_EPISODES: 19>, 'uri': 'youtube//https://youtube.com/watch?v=510FsxZBYhQ', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/510FsxZBYhQ/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/510FsxZBYhQ/sddefault.jpg'}
