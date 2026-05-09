"""Seed the database with artists, albums, songs, users, reviews, lists, and activity."""
import json
from datetime import datetime, timedelta

from .database import SessionLocal
from . import models
from .auth import hash_password


def seed_database():
    db = SessionLocal()
    try:
        if db.query(models.Artist).count() > 0:
            return  # Already seeded

        # ── Genres ──────────────────────────────────────────────────────────
        genre_names = [
            "Pop", "Rock", "Hip-Hop", "Alternative", "R&B",
            "Indie", "Electronic", "Folk", "Jazz", "Classical",
        ]
        genres: dict[str, models.Genre] = {}
        for name in genre_names:
            g = models.Genre(name=name)
            db.add(g)
            genres[name] = g
        db.flush()

        # ── Artists ─────────────────────────────────────────────────────────
        artists_seed = [
            {
                "name": "Taylor Swift",
                "bio": (
                    "Taylor Alison Swift is an American singer-songwriter. "
                    "Her discography spans multiple genres and her narrative "
                    "songwriting has received widespread critical praise."
                ),
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/b/b1/Taylor_Swift_at_the_2023_MTV_Video_Music_Awards_3.png",
                "formed_year": 2004,
                "country": "USA",
                "genres": ["Pop", "Folk", "Indie"],
            },
            {
                "name": "The Beatles",
                "bio": (
                    "The Beatles were an English rock band formed in Liverpool "
                    "in 1960. Widely regarded as the most influential band in "
                    "the history of popular music."
                ),
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/The_Fabs.JPG/1200px-The_Fabs.JPG",
                "formed_year": 1960,
                "country": "UK",
                "genres": ["Rock", "Pop"],
            },
            {
                "name": "Kendrick Lamar",
                "bio": (
                    "Kendrick Lamar Duckworth is an American rapper and songwriter "
                    "widely regarded as one of the most skilled rappers of his generation."
                ),
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Kendrick_Lamar_at_The_Comedy_Store.jpg/440px-Kendrick_Lamar_at_The_Comedy_Store.jpg",
                "formed_year": 2003,
                "country": "USA",
                "genres": ["Hip-Hop"],
            },
            {
                "name": "Radiohead",
                "bio": (
                    "Radiohead are an English rock band from Abingdon, Oxfordshire, "
                    "formed in 1985. Known for pushing the boundaries of alternative rock."
                ),
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Radiohead_band_photo.jpg/440px-Radiohead_band_photo.jpg",
                "formed_year": 1985,
                "country": "UK",
                "genres": ["Alternative", "Rock", "Electronic"],
            },
            {
                "name": "Frank Ocean",
                "bio": (
                    "Frank Ocean is an American singer, songwriter, and record producer "
                    "known for his unconventional music and themes of love, heartbreak, "
                    "beauty, and nostalgia."
                ),
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Frank_Ocean_2012.jpg/440px-Frank_Ocean_2012.jpg",
                "formed_year": 2009,
                "country": "USA",
                "genres": ["R&B", "Indie", "Hip-Hop"],
            },
        ]

        artists: dict[str, models.Artist] = {}
        for data in artists_seed:
            artist_genres = data.pop("genres")
            artist = models.Artist(**data)
            for gname in artist_genres:
                artist.genres.append(genres[gname])
            db.add(artist)
            artists[artist.name] = artist
        db.flush()

        # ── Albums & Songs ───────────────────────────────────────────────────
        catalog = [
            {
                "artist": "Taylor Swift",
                "albums": [
                    {
                        "title": "Folklore",
                        "release_date": "2020-07-24",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/f/f8/Taylor_Swift_-_Folklore.png",
                        "description": "Folklore is Taylor Swift's eighth studio album — a surprise indie-folk record recorded entirely during lockdown.",
                        "genres": ["Folk", "Indie", "Pop"],
                        "songs": [
                            {"title": "the 1",                           "duration_seconds": 210, "track_number": 1},
                            {"title": "cardigan",                        "duration_seconds": 239, "track_number": 2},
                            {"title": "the last great american dynasty", "duration_seconds": 231, "track_number": 3},
                            {"title": "exile (feat. Bon Iver)",          "duration_seconds": 285, "track_number": 4},
                            {"title": "my tears ricochet",               "duration_seconds": 255, "track_number": 5},
                            {"title": "seven",                           "duration_seconds": 212, "track_number": 6},
                            {"title": "august",                          "duration_seconds": 261, "track_number": 7},
                            {"title": "this is me trying",               "duration_seconds": 215, "track_number": 8},
                        ],
                    },
                    {
                        "title": "1989",
                        "release_date": "2014-10-27",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/f/f6/Taylor_Swift_-_1989.png",
                        "description": "Taylor Swift's fifth studio album marked a definitive shift to synth-pop.",
                        "genres": ["Pop"],
                        "songs": [
                            {"title": "Welcome to New York", "duration_seconds": 212, "track_number": 1},
                            {"title": "Blank Space",         "duration_seconds": 231, "track_number": 2},
                            {"title": "Style",               "duration_seconds": 231, "track_number": 3},
                            {"title": "Bad Blood",           "duration_seconds": 211, "track_number": 4},
                            {"title": "Shake It Off",        "duration_seconds": 219, "track_number": 5},
                            {"title": "Out of the Woods",    "duration_seconds": 235, "track_number": 6},
                        ],
                    },
                    {
                        "title": "Midnights",
                        "release_date": "2022-10-21",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/9/9f/Midnights_-_Taylor_Swift.png",
                        "description": "Taylor Swift's tenth studio album explores the stories of 13 sleepless nights.",
                        "genres": ["Pop", "Electronic"],
                        "songs": [
                            {"title": "Lavender Haze",    "duration_seconds": 202, "track_number": 1},
                            {"title": "Maroon",           "duration_seconds": 218, "track_number": 2},
                            {"title": "Anti-Hero",        "duration_seconds": 200, "track_number": 3},
                            {"title": "Snow on the Beach","duration_seconds": 255, "track_number": 4},
                            {"title": "Midnight Rain",    "duration_seconds": 174, "track_number": 5},
                            {"title": "Karma",            "duration_seconds": 208, "track_number": 6},
                        ],
                    },
                ],
            },
            {
                "artist": "The Beatles",
                "albums": [
                    {
                        "title": "Abbey Road",
                        "release_date": "1969-09-26",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/4/42/Beatles_-_Abbey_Road.jpg",
                        "description": "The Beatles' eleventh studio album, featuring the iconic medley on side two.",
                        "genres": ["Rock", "Pop"],
                        "songs": [
                            {"title": "Come Together",             "duration_seconds": 259, "track_number": 1},
                            {"title": "Something",                 "duration_seconds": 183, "track_number": 2},
                            {"title": "Octopus's Garden",          "duration_seconds": 171, "track_number": 3},
                            {"title": "Here Comes the Sun",        "duration_seconds": 185, "track_number": 4},
                            {"title": "Because",                   "duration_seconds": 165, "track_number": 5},
                            {"title": "You Never Give Me Your Money", "duration_seconds": 242, "track_number": 6},
                        ],
                    },
                    {
                        "title": "Sgt. Pepper's Lonely Hearts Club Band",
                        "release_date": "1967-06-01",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/5/50/Sgt._Pepper%27s_Lonely_Hearts_Club_Band.jpg",
                        "description": "Widely considered one of the greatest albums ever recorded.",
                        "genres": ["Rock", "Pop"],
                        "songs": [
                            {"title": "Sgt. Pepper's Lonely Hearts Club Band", "duration_seconds": 122, "track_number": 1},
                            {"title": "With a Little Help from My Friends",    "duration_seconds": 163, "track_number": 2},
                            {"title": "Lucy in the Sky with Diamonds",         "duration_seconds": 209, "track_number": 3},
                            {"title": "Getting Better",                        "duration_seconds": 168, "track_number": 4},
                            {"title": "A Day in the Life",                     "duration_seconds": 337, "track_number": 5},
                        ],
                    },
                ],
            },
            {
                "artist": "Kendrick Lamar",
                "albums": [
                    {
                        "title": "To Pimp a Butterfly",
                        "release_date": "2015-03-15",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/f/f6/To_Pimp_a_Butterfly.png",
                        "description": "A genre-defying album addressing institutional racism, fame, and self-worth through jazz, funk, and spoken word.",
                        "genres": ["Hip-Hop"],
                        "songs": [
                            {"title": "Wesley's Theory",      "duration_seconds": 271, "track_number": 1},
                            {"title": "King Kunta",           "duration_seconds": 234, "track_number": 2},
                            {"title": "Institutionalized",    "duration_seconds": 268, "track_number": 3},
                            {"title": "Alright",              "duration_seconds": 219, "track_number": 4},
                            {"title": "u",                    "duration_seconds": 270, "track_number": 5},
                            {"title": "The Blacker the Berry","duration_seconds": 310, "track_number": 6},
                        ],
                    },
                    {
                        "title": "DAMN.",
                        "release_date": "2017-04-14",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/5/51/Kendrick_Lamar_-_Damn.png",
                        "description": "Kendrick Lamar's fourth studio album, winner of the Pulitzer Prize for Music.",
                        "genres": ["Hip-Hop"],
                        "songs": [
                            {"title": "BLOOD.",   "duration_seconds": 117, "track_number": 1},
                            {"title": "DNA.",     "duration_seconds": 185, "track_number": 2},
                            {"title": "YAH.",    "duration_seconds": 140, "track_number": 3},
                            {"title": "ELEMENT.","duration_seconds": 216, "track_number": 4},
                            {"title": "HUMBLE.", "duration_seconds": 177, "track_number": 5},
                            {"title": "LOVE.",   "duration_seconds": 213, "track_number": 6},
                        ],
                    },
                ],
            },
            {
                "artist": "Radiohead",
                "albums": [
                    {
                        "title": "OK Computer",
                        "release_date": "1997-05-21",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/b/ba/Radioheadokcomputer.png",
                        "description": "A landmark alternative rock album tackling themes of alienation, consumerism, and political apathy.",
                        "genres": ["Alternative", "Rock"],
                        "songs": [
                            {"title": "Airbag",                      "duration_seconds": 277, "track_number": 1},
                            {"title": "Paranoid Android",            "duration_seconds": 383, "track_number": 2},
                            {"title": "Subterranean Homesick Alien", "duration_seconds": 271, "track_number": 3},
                            {"title": "Exit Music (For a Film)",     "duration_seconds": 244, "track_number": 4},
                            {"title": "Karma Police",                "duration_seconds": 263, "track_number": 5},
                            {"title": "No Surprises",                "duration_seconds": 228, "track_number": 6},
                        ],
                    },
                    {
                        "title": "Kid A",
                        "release_date": "2000-10-02",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/b/b5/Radiohead.kida.albumart.jpg",
                        "description": "Radiohead's radical departure into electronic and experimental music.",
                        "genres": ["Alternative", "Electronic"],
                        "songs": [
                            {"title": "Everything in Its Right Place", "duration_seconds": 247, "track_number": 1},
                            {"title": "Kid A",                         "duration_seconds": 274, "track_number": 2},
                            {"title": "The National Anthem",           "duration_seconds": 350, "track_number": 3},
                            {"title": "How to Disappear Completely",   "duration_seconds": 354, "track_number": 4},
                            {"title": "Optimistic",                    "duration_seconds": 322, "track_number": 5},
                        ],
                    },
                ],
            },
            {
                "artist": "Frank Ocean",
                "albums": [
                    {
                        "title": "Blonde",
                        "release_date": "2016-08-20",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/a/a0/Frank_Ocean_-_Blonde.jpeg",
                        "description": "Frank Ocean's critically acclaimed second album exploring identity, love, and loss.",
                        "genres": ["R&B", "Indie"],
                        "songs": [
                            {"title": "Nikes",        "duration_seconds": 311, "track_number": 1},
                            {"title": "Ivy",          "duration_seconds": 245, "track_number": 2},
                            {"title": "Pink + White", "duration_seconds": 183, "track_number": 3},
                            {"title": "Self Control", "duration_seconds": 229, "track_number": 4},
                            {"title": "Nights",       "duration_seconds": 309, "track_number": 5},
                            {"title": "Solo",         "duration_seconds": 191, "track_number": 6},
                        ],
                    },
                    {
                        "title": "channel ORANGE",
                        "release_date": "2012-07-10",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/2/2d/Channel_ORANGE.jpg",
                        "description": "Frank Ocean's debut studio album — a sprawling R&B masterpiece.",
                        "genres": ["R&B", "Hip-Hop"],
                        "songs": [
                            {"title": "Thinkin Bout You", "duration_seconds": 200, "track_number": 1},
                            {"title": "Sierra Leone",     "duration_seconds": 176, "track_number": 2},
                            {"title": "Sweet Life",       "duration_seconds": 249, "track_number": 3},
                            {"title": "Lost",             "duration_seconds": 236, "track_number": 4},
                            {"title": "Pyramids",         "duration_seconds": 578, "track_number": 5},
                            {"title": "Bad Religion",     "duration_seconds": 172, "track_number": 6},
                        ],
                    },
                ],
            },
        ]

        for entry in catalog:
            artist = artists[entry["artist"]]
            for album_data in entry["albums"]:
                songs_data = album_data.pop("songs")
                album_genres = album_data.pop("genres")
                album = models.Album(**album_data, artist_id=artist.id)
                for gname in album_genres:
                    if gname in genres:
                        album.genres.append(genres[gname])
                db.add(album)
                db.flush()
                for s in songs_data:
                    db.add(models.Song(**s, artist_id=artist.id, album_id=album.id))

        # Flush so we can look up IDs by name below
        db.flush()

        def alb(title: str) -> models.Album:
            return db.query(models.Album).filter(models.Album.title == title).first()

        def trk(title: str) -> models.Song:
            return db.query(models.Song).filter(models.Song.title == title).first()

        # ── Users ────────────────────────────────────────────────────────────
        users_seed = [
            dict(username="musiclover",      email="demo@tunelog.com",      pw="password123",
                 bio="I love music more than anything. Always searching for the next great album."),
            dict(username="indie_vibes",     email="indie@tunelog.com",     pw="password123",
                 bio="Chasing the perfect lo-fi moment. Vinyl collector, chronic over-listener."),
            dict(username="hiphop_head",     email="hiphop@tunelog.com",    pw="password123",
                 bio="Hip-hop is poetry. Kendrick, Cole, Frank — the holy trinity."),
            dict(username="classicrock_fan", email="classic@tunelog.com",   pw="password123",
                 bio="Nothing beats the classics. Abbey Road is the greatest album ever recorded."),
            dict(username="rbsoul",          email="rbsoul@tunelog.com",    pw="password123",
                 bio="R&B is the soul of music. Frank Ocean changed my life."),
            dict(username="audiophile99",    email="audio@tunelog.com",     pw="password123",
                 bio="Listening on $3000 headphones since 2008. Production quality matters."),
        ]
        users: dict[str, models.User] = {}
        for u in users_seed:
            user = models.User(
                username=u["username"],
                email=u["email"],
                hashed_password=hash_password(u["pw"]),
                bio=u["bio"],
            )
            db.add(user)
            users[u["username"]] = user
        db.flush()

        # ── Reviews ──────────────────────────────────────────────────────────
        def review(user_key, *, album_title=None, song_title=None, rating, text=None, days_ago=0):
            return models.Review(
                user_id=users[user_key].id,
                album_id=alb(album_title).id if album_title else None,
                song_id=trk(song_title).id  if song_title  else None,
                rating=rating,
                text=text,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
                updated_at=datetime.utcnow() - timedelta(days=days_ago),
            )

        reviews = [
            # ── Folklore ──────────────────────────────────────────────────
            review("musiclover", album_title="Folklore", rating=5.0, days_ago=90,
                   text="A perfect album. Every track is a masterpiece of quiet storytelling. Taylor completely reinvented herself here."),
            review("indie_vibes", album_title="Folklore", rating=4.5, days_ago=85,
                   text="The indie-folk pivot suits Taylor perfectly. 'cardigan' and 'august' are some of her finest work to date."),
            review("classicrock_fan", album_title="Folklore", rating=4.0, days_ago=80,
                   text="Not usually my genre, but this album genuinely pulled me in. Surprisingly moving and restrained."),

            # ── 1989 ──────────────────────────────────────────────────────
            review("musiclover", album_title="1989", rating=4.0, days_ago=100,
                   text="The album that proved Taylor could dominate any genre. Pure pop craftsmanship throughout."),
            review("indie_vibes", album_title="1989", rating=3.5, days_ago=95,
                   text="Fun and polished, but I prefer the more personal direction she took on Folklore. Shake It Off is undeniably infectious."),

            # ── Midnights ─────────────────────────────────────────────────
            review("musiclover", album_title="Midnights", rating=4.5, days_ago=40,
                   text="Anti-Hero is an earworm and Lavender Haze sets the perfect mood. A grower for sure."),
            review("indie_vibes", album_title="Midnights", rating=4.0, days_ago=35,
                   text="The 3am edition bonus tracks push it from good to genuinely great. Took a few listens to click."),

            # ── Abbey Road ────────────────────────────────────────────────
            review("classicrock_fan", album_title="Abbey Road", rating=5.0, days_ago=120,
                   text="The greatest album ever recorded. The medley on side two is humanity at its creative peak. Flawless."),
            review("musiclover", album_title="Abbey Road", rating=5.0, days_ago=110,
                   text="Here Comes the Sun never gets old. Neither does anything else on this record."),
            review("audiophile99", album_title="Abbey Road", rating=5.0, days_ago=115,
                   text="Geoff Emerick's engineering still sounds incredible decades later. A sonic and compositional masterpiece."),

            # ── Sgt. Pepper's ─────────────────────────────────────────────
            review("classicrock_fan", album_title="Sgt. Pepper's Lonely Hearts Club Band", rating=5.0, days_ago=130,
                   text="A Day in the Life might be the greatest song ever written. The whole album sits at that level."),
            review("audiophile99", album_title="Sgt. Pepper's Lonely Hearts Club Band", rating=4.5, days_ago=125,
                   text="Groundbreaking for its time and still sounds fresh. The production innovations are staggering."),

            # ── To Pimp a Butterfly ───────────────────────────────────────
            review("hiphop_head", album_title="To Pimp a Butterfly", rating=5.0, days_ago=60,
                   text="Kendrick's magnum opus. The jazz and funk influences make this feel ageless. Alright became an anthem."),
            review("rbsoul", album_title="To Pimp a Butterfly", rating=5.0, days_ago=55,
                   text="This album will be studied for decades. The spoken-word sections alone are worth the price of admission."),
            review("musiclover", album_title="To Pimp a Butterfly", rating=4.5, days_ago=65,
                   text="Challenging and rewarding in equal measure. One of the most important albums of this century."),

            # ── DAMN. ─────────────────────────────────────────────────────
            review("hiphop_head", album_title="DAMN.", rating=5.0, days_ago=70,
                   text="Kendrick's most accessible album. HUMBLE. and DNA. are instant classics. Pulitzer-winning for a reason."),
            review("musiclover", album_title="DAMN.", rating=4.5, days_ago=75,
                   text="The duality of the tracklist is brilliant — it plays completely differently in reverse order. Genius."),
            review("rbsoul", album_title="DAMN.", rating=4.5, days_ago=68,
                   text="LOVE. is criminally underrated on this record. Hits differently every single listen."),

            # ── OK Computer ───────────────────────────────────────────────
            review("audiophile99", album_title="OK Computer", rating=5.0, days_ago=150,
                   text="The defining album of its era. Paranoid Android alone justifies a perfect score. Still timeless."),
            review("indie_vibes", album_title="OK Computer", rating=5.0, days_ago=145,
                   text="Thom Yorke predicted the digital alienation we all feel now. Visionary doesn't even cover it."),
            review("musiclover", album_title="OK Computer", rating=4.5, days_ago=140,
                   text="Essential listening. The production is still mind-blowing 25+ years later."),
            review("classicrock_fan", album_title="OK Computer", rating=5.0, days_ago=148,
                   text="Karma Police is one of the greatest songs of the 90s. The whole album operates at that level."),

            # ── Kid A ─────────────────────────────────────────────────────
            review("audiophile99", album_title="Kid A", rating=5.0, days_ago=155,
                   text="Radiohead at their most daring. An acquired taste that never leaves you once it finally clicks."),
            review("indie_vibes", album_title="Kid A", rating=4.5, days_ago=150,
                   text="Everything in Its Right Place is one of the greatest opening tracks in history. Haunting and beautiful."),

            # ── Blonde ────────────────────────────────────────────────────
            review("rbsoul", album_title="Blonde", rating=5.0, days_ago=50,
                   text="Frank Ocean at his most vulnerable and artistic. Nights alone is worth a perfect score."),
            review("indie_vibes", album_title="Blonde", rating=5.0, days_ago=45,
                   text="Changed what R&B could be. Still emotionally processing this record years after its release."),
            review("audiophile99", album_title="Blonde", rating=4.5, days_ago=48,
                   text="The unconventional production choices are jarring at first, then revelatory. A true masterwork."),

            # ── channel ORANGE ────────────────────────────────────────────
            review("rbsoul", album_title="channel ORANGE", rating=5.0, days_ago=80,
                   text="Thinkin Bout You still hits like it did on first listen. Pyramids is a 10-minute journey unto itself."),
            review("hiphop_head", album_title="channel ORANGE", rating=4.5, days_ago=75,
                   text="Frank crosses genre lines with effortless grace here. Bad Religion is stunning."),

            # ── Song reviews ──────────────────────────────────────────────
            review("audiophile99", song_title="Paranoid Android", rating=5.0, days_ago=140,
                   text="Six minutes of genius across three distinct movements. The greatest rock song of the 90s, full stop."),
            review("musiclover", song_title="cardigan", rating=5.0, days_ago=88,
                   text="The production is so delicate and the lyrics so vivid. Peak Taylor."),
            review("rbsoul", song_title="Nights", rating=5.0, days_ago=50,
                   text="The beat switch halfway through is one of the most arresting moments in modern music. Nothing else like it."),
            review("hiphop_head", song_title="HUMBLE.", rating=5.0, days_ago=70,
                   text="Sit down. Be humble. The beat drop is still unmatched years later. Iconic."),
            review("classicrock_fan", song_title="Come Together", rating=5.0, days_ago=118,
                   text="The bass riff that launched a thousand rock songs. Lennon at his most mysteriously cool."),
            review("indie_vibes", song_title="Everything in Its Right Place", rating=5.0, days_ago=149,
                   text="Six minutes of hypnotic beauty. The album could have ended here and still been a masterpiece."),
            review("musiclover", song_title="Here Comes the Sun", rating=5.0, days_ago=110,
                   text="Timeless warmth in a three-minute song. George Harrison's finest moment."),
            review("rbsoul", song_title="Pink + White", rating=4.5, days_ago=47,
                   text="So delicate and beautiful. Frank's falsetto here is otherworldly."),
            review("indie_vibes", song_title="exile (feat. Bon Iver)", rating=5.0, days_ago=84,
                   text="Two incredible artists making something greater than the sum of their parts. Perfect duet."),
            review("hiphop_head", song_title="Alright", rating=5.0, days_ago=58,
                   text="An anthem for a generation. The jazz production is perfection. We gon' be alright."),
            review("audiophile99", song_title="Karma Police", rating=4.5, days_ago=148,
                   text="Arrest this man. The build and release in this song is textbook genius."),
            review("classicrock_fan", song_title="A Day in the Life", rating=5.0, days_ago=128,
                   text="The orchestral swells, the alarm clock, the final chord — this is what music can do at its absolute best."),
            review("musiclover", song_title="Anti-Hero", rating=4.5, days_ago=38,
                   text="It's me, hi, I'm the problem. Devastatingly catchy and more vulnerable than it first appears."),
        ]
        for r in reviews:
            db.add(r)
        db.flush()

        # ── Follows ──────────────────────────────────────────────────────────
        follow_pairs = [
            ("musiclover",      "indie_vibes"),
            ("musiclover",      "hiphop_head"),
            ("musiclover",      "audiophile99"),
            ("indie_vibes",     "musiclover"),
            ("indie_vibes",     "rbsoul"),
            ("indie_vibes",     "audiophile99"),
            ("hiphop_head",     "musiclover"),
            ("hiphop_head",     "rbsoul"),
            ("rbsoul",          "indie_vibes"),
            ("rbsoul",          "hiphop_head"),
            ("audiophile99",    "musiclover"),
            ("audiophile99",    "indie_vibes"),
            ("audiophile99",    "classicrock_fan"),
            ("classicrock_fan", "musiclover"),
            ("classicrock_fan", "audiophile99"),
        ]
        for follower_key, followed_key in follow_pairs:
            db.add(models.UserFollow(
                follower_id=users[follower_key].id,
                followed_id=users[followed_key].id,
                created_at=datetime.utcnow() - timedelta(days=30),
            ))

        # ── Album statuses ────────────────────────────────────────────────────
        def status(user_key, album_title, stat, days_ago=20):
            return models.UserAlbumStatus(
                user_id=users[user_key].id,
                album_id=alb(album_title).id,
                status=stat,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            )

        statuses = [
            status("musiclover", "Folklore",                           "favorites",      days_ago=88),
            status("musiclover", "1989",                               "listened",       days_ago=98),
            status("musiclover", "Midnights",                          "listened",       days_ago=38),
            status("musiclover", "OK Computer",                        "listened",       days_ago=138),
            status("musiclover", "DAMN.",                              "listened",       days_ago=73),
            status("musiclover", "Abbey Road",                         "favorites",      days_ago=108),
            status("musiclover", "To Pimp a Butterfly",                "listened",       days_ago=63),

            status("hiphop_head", "DAMN.",                             "favorites",      days_ago=68),
            status("hiphop_head", "To Pimp a Butterfly",               "favorites",      days_ago=58),
            status("hiphop_head", "channel ORANGE",                    "listened",       days_ago=73),
            status("hiphop_head", "Folklore",                          "want_to_listen", days_ago=40),

            status("indie_vibes", "Folklore",                          "favorites",      days_ago=83),
            status("indie_vibes", "OK Computer",                       "favorites",      days_ago=143),
            status("indie_vibes", "Blonde",                            "favorites",      days_ago=43),
            status("indie_vibes", "Kid A",                             "listened",       days_ago=148),
            status("indie_vibes", "Midnights",                         "listened",       days_ago=33),
            status("indie_vibes", "DAMN.",                             "want_to_listen", days_ago=30),

            status("rbsoul", "Blonde",                                 "favorites",      days_ago=48),
            status("rbsoul", "channel ORANGE",                         "favorites",      days_ago=78),
            status("rbsoul", "DAMN.",                                  "listened",       days_ago=66),
            status("rbsoul", "To Pimp a Butterfly",                    "listened",       days_ago=53),
            status("rbsoul", "Midnights",                              "want_to_listen", days_ago=20),

            status("audiophile99", "OK Computer",                      "favorites",      days_ago=148),
            status("audiophile99", "Kid A",                            "favorites",      days_ago=153),
            status("audiophile99", "Abbey Road",                       "favorites",      days_ago=113),
            status("audiophile99", "Blonde",                           "listened",       days_ago=46),
            status("audiophile99", "Sgt. Pepper's Lonely Hearts Club Band", "listened",  days_ago=123),

            status("classicrock_fan", "Abbey Road",                    "favorites",      days_ago=118),
            status("classicrock_fan", "Sgt. Pepper's Lonely Hearts Club Band", "favorites", days_ago=128),
            status("classicrock_fan", "OK Computer",                   "listened",       days_ago=146),
            status("classicrock_fan", "Folklore",                      "listened",       days_ago=78),
        ]
        for s in statuses:
            db.add(s)

        # ── Lists ─────────────────────────────────────────────────────────────
        lists_seed = [
            {
                "user": "musiclover",
                "name": "All-Time Favorites",
                "description": "The albums that mean the most to me, no matter the genre or decade.",
                "list_type": "favorites",
                "albums": ["Folklore", "Abbey Road", "OK Computer", "DAMN.", "Blonde"],
            },
            {
                "user": "musiclover",
                "name": "Still Need to Explore",
                "description": "On my radar — just need more time with these.",
                "list_type": "want_to_listen",
                "albums": ["Kid A", "channel ORANGE"],
            },
            {
                "user": "indie_vibes",
                "name": "Chill Evening Listens",
                "description": "The albums I put on when the day is finally over.",
                "list_type": "custom",
                "albums": ["Folklore", "Blonde", "Kid A"],
            },
            {
                "user": "hiphop_head",
                "name": "Essential Hip-Hop",
                "description": "The rap records everyone needs to hear at least once before they die.",
                "list_type": "custom",
                "albums": ["To Pimp a Butterfly", "DAMN.", "channel ORANGE"],
            },
            {
                "user": "audiophile99",
                "name": "Audiophile Reference Picks",
                "description": "Exceptional production — great for testing audio equipment or just deep listening.",
                "list_type": "custom",
                "albums": ["Abbey Road", "OK Computer", "Kid A", "Blonde"],
            },
            {
                "user": "classicrock_fan",
                "name": "The Classic Rock Canon",
                "description": "If it's not on this list, does it really belong in the conversation?",
                "list_type": "custom",
                "albums": ["Abbey Road", "Sgt. Pepper's Lonely Hearts Club Band"],
            },
            {
                "user": "rbsoul",
                "name": "Listened",
                "description": "Everything I've made it all the way through.",
                "list_type": "listened",
                "albums": ["Blonde", "channel ORANGE", "DAMN.", "To Pimp a Butterfly"],
            },
        ]
        for l in lists_seed:
            lst = models.List(
                user_id=users[l["user"]].id,
                name=l["name"],
                description=l["description"],
                list_type=l["list_type"],
                is_public=True,
            )
            db.add(lst)
            db.flush()
            for album_title in l["albums"]:
                a = alb(album_title)
                if a:
                    db.add(models.ListItem(list_id=lst.id, album_id=a.id))

        # ── Activities ────────────────────────────────────────────────────────
        def activity(user_key, action_type, target_type=None, target_id=None, days_ago=0):
            return models.Activity(
                user_id=users[user_key].id,
                action_type=action_type,
                target_type=target_type,
                target_id=target_id,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            )

        activities = [
            # Album reviews
            activity("musiclover",      "reviewed_album", "album", alb("Folklore").id,                            days_ago=90),
            activity("musiclover",      "reviewed_album", "album", alb("Abbey Road").id,                          days_ago=110),
            activity("musiclover",      "reviewed_album", "album", alb("DAMN.").id,                               days_ago=75),
            activity("musiclover",      "reviewed_album", "album", alb("To Pimp a Butterfly").id,                 days_ago=65),
            activity("indie_vibes",     "reviewed_album", "album", alb("OK Computer").id,                         days_ago=145),
            activity("indie_vibes",     "reviewed_album", "album", alb("Blonde").id,                              days_ago=45),
            activity("indie_vibes",     "reviewed_album", "album", alb("Folklore").id,                            days_ago=85),
            activity("indie_vibes",     "reviewed_album", "album", alb("Kid A").id,                               days_ago=150),
            activity("hiphop_head",     "reviewed_album", "album", alb("To Pimp a Butterfly").id,                 days_ago=60),
            activity("hiphop_head",     "reviewed_album", "album", alb("DAMN.").id,                               days_ago=70),
            activity("hiphop_head",     "reviewed_album", "album", alb("channel ORANGE").id,                      days_ago=75),
            activity("rbsoul",          "reviewed_album", "album", alb("Blonde").id,                              days_ago=50),
            activity("rbsoul",          "reviewed_album", "album", alb("channel ORANGE").id,                      days_ago=80),
            activity("rbsoul",          "reviewed_album", "album", alb("DAMN.").id,                               days_ago=68),
            activity("audiophile99",    "reviewed_album", "album", alb("OK Computer").id,                         days_ago=150),
            activity("audiophile99",    "reviewed_album", "album", alb("Kid A").id,                               days_ago=155),
            activity("audiophile99",    "reviewed_album", "album", alb("Abbey Road").id,                          days_ago=115),
            activity("audiophile99",    "reviewed_album", "album", alb("Blonde").id,                              days_ago=48),
            activity("classicrock_fan", "reviewed_album", "album", alb("Abbey Road").id,                          days_ago=120),
            activity("classicrock_fan", "reviewed_album", "album", alb("Sgt. Pepper's Lonely Hearts Club Band").id, days_ago=130),
            activity("classicrock_fan", "reviewed_album", "album", alb("OK Computer").id,                         days_ago=148),
            # Song reviews
            activity("musiclover",      "reviewed_song",  "song",  trk("cardigan").id,                            days_ago=88),
            activity("musiclover",      "reviewed_song",  "song",  trk("Here Comes the Sun").id,                  days_ago=110),
            activity("musiclover",      "reviewed_song",  "song",  trk("Anti-Hero").id,                           days_ago=38),
            activity("indie_vibes",     "reviewed_song",  "song",  trk("exile (feat. Bon Iver)").id,              days_ago=84),
            activity("indie_vibes",     "reviewed_song",  "song",  trk("Everything in Its Right Place").id,       days_ago=149),
            activity("hiphop_head",     "reviewed_song",  "song",  trk("HUMBLE.").id,                             days_ago=70),
            activity("hiphop_head",     "reviewed_song",  "song",  trk("Alright").id,                             days_ago=58),
            activity("rbsoul",          "reviewed_song",  "song",  trk("Nights").id,                              days_ago=50),
            activity("rbsoul",          "reviewed_song",  "song",  trk("Pink + White").id,                        days_ago=47),
            activity("audiophile99",    "reviewed_song",  "song",  trk("Paranoid Android").id,                    days_ago=140),
            activity("audiophile99",    "reviewed_song",  "song",  trk("Karma Police").id,                        days_ago=148),
            activity("classicrock_fan", "reviewed_song",  "song",  trk("Come Together").id,                       days_ago=118),
            activity("classicrock_fan", "reviewed_song",  "song",  trk("A Day in the Life").id,                   days_ago=128),
            # Favorites / status
            activity("musiclover",      "marked_album_favorites",      "album", alb("Folklore").id,               days_ago=88),
            activity("musiclover",      "marked_album_favorites",      "album", alb("Abbey Road").id,             days_ago=108),
            activity("musiclover",      "marked_album_listened",       "album", alb("DAMN.").id,                  days_ago=73),
            activity("indie_vibes",     "marked_album_favorites",      "album", alb("Blonde").id,                 days_ago=43),
            activity("indie_vibes",     "marked_album_favorites",      "album", alb("OK Computer").id,            days_ago=143),
            activity("hiphop_head",     "marked_album_favorites",      "album", alb("To Pimp a Butterfly").id,    days_ago=58),
            activity("rbsoul",          "marked_album_favorites",      "album", alb("Blonde").id,                 days_ago=48),
            activity("audiophile99",    "marked_album_favorites",      "album", alb("OK Computer").id,            days_ago=148),
            activity("classicrock_fan", "marked_album_favorites",      "album", alb("Abbey Road").id,             days_ago=118),
            # Follows
            activity("musiclover",      "followed", "user", users["indie_vibes"].id,                              days_ago=30),
            activity("musiclover",      "followed", "user", users["hiphop_head"].id,                              days_ago=30),
            activity("musiclover",      "followed", "user", users["audiophile99"].id,                             days_ago=28),
            activity("indie_vibes",     "followed", "user", users["musiclover"].id,                               days_ago=28),
            activity("indie_vibes",     "followed", "user", users["rbsoul"].id,                                   days_ago=25),
            activity("hiphop_head",     "followed", "user", users["musiclover"].id,                               days_ago=27),
            activity("rbsoul",          "followed", "user", users["indie_vibes"].id,                              days_ago=26),
            activity("audiophile99",    "followed", "user", users["classicrock_fan"].id,                          days_ago=20),
        ]
        for a in activities:
            db.add(a)

        db.commit()
        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()


def seed_extra_data():
    """Add more artists, users, reviews, likes, and lists to an existing database."""
    db = SessionLocal()
    try:
        if db.query(models.Artist).filter(models.Artist.name == "Beyoncé").first():
            return  # Already ran

        # ── Extra genres ────────────────────────────────────────────────────
        genres: dict[str, models.Genre] = {g.name: g for g in db.query(models.Genre).all()}
        for name in ["Dance", "Soul", "Funk"]:
            if name not in genres:
                g = models.Genre(name=name)
                db.add(g)
                genres[name] = g
        db.flush()

        # ── New artists ─────────────────────────────────────────────────────
        new_artists_seed = [
            {
                "name": "Beyoncé",
                "bio": "Beyoncé Giselle Knowles-Carter is an American singer, songwriter, and actress. Regarded as one of the greatest entertainers of her generation, she has won more Grammy Awards than any other artist.",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Beyonc%C3%A9_at_The_Super_Bowl_50_Half-Time_Show.jpg/440px-Beyonc%C3%A9_at_The_Super_Bowl_50_Half-Time_Show.jpg",
                "formed_year": 1997, "country": "USA",
                "genres": ["Pop", "R&B", "Soul"],
            },
            {
                "name": "The Weeknd",
                "bio": "Abel Makkonen Tesfaye, known professionally as The Weeknd, is a Canadian singer and songwriter. Known for his sonic versatility spanning R&B, pop, and synth-wave.",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/The_Weeknd_-_The_After_Hours_Tour_%28cropped%29.jpg/440px-The_Weeknd_-_The_After_Hours_Tour_%28cropped%29.jpg",
                "formed_year": 2009, "country": "Canada",
                "genres": ["R&B", "Pop", "Electronic"],
            },
            {
                "name": "Tyler, the Creator",
                "bio": "Tyler Gregory Okonma, known as Tyler, the Creator, is an American rapper, singer, and producer known for his eccentric style and boundary-pushing concept albums.",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Tyler_The_Creator_2019.png/440px-Tyler_The_Creator_2019.png",
                "formed_year": 2007, "country": "USA",
                "genres": ["Hip-Hop", "Alternative", "Electronic"],
            },
            {
                "name": "Billie Eilish",
                "bio": "Billie Eilish Pirate Baird O'Connell is an American singer and songwriter who rose to fame as a teenager. Her dark, whispered pop style has made her one of the most distinctive voices of her generation.",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Billie_Eilish_at_the_2019_Vanity_Fair_Party_%28cropped%29.jpg/440px-Billie_Eilish_at_the_2019_Vanity_Fair_Party_%28cropped%29.jpg",
                "formed_year": 2015, "country": "USA",
                "genres": ["Pop", "Alternative", "Electronic"],
            },
            {
                "name": "Daft Punk",
                "bio": "Daft Punk were a French electronic music duo composed of Thomas Bangalter and Guy-Manuel de Homem-Christo. One of the most influential acts in dance and electronic music history.",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Daft_Punk_at_Coachella_2006.jpg/440px-Daft_Punk_at_Coachella_2006.jpg",
                "formed_year": 1993, "country": "France",
                "genres": ["Electronic", "Dance", "Funk"],
            },
        ]

        new_artists: dict[str, models.Artist] = {}
        for data in new_artists_seed:
            artist_genres = data.pop("genres")
            artist = models.Artist(**data)
            for gname in artist_genres:
                if gname in genres:
                    artist.genres.append(genres[gname])
            db.add(artist)
            new_artists[artist.name] = artist
        db.flush()

        # ── New albums & songs ───────────────────────────────────────────────
        new_catalog = [
            {
                "artist": "Beyoncé",
                "albums": [
                    {
                        "title": "Lemonade",
                        "release_date": "2016-04-23",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/5/53/Beyonce_Lemonade_album_cover.png",
                        "description": "Beyoncé's sixth studio album — a visual and sonic odyssey through infidelity, forgiveness, and Black womanhood.",
                        "genres": ["R&B", "Soul", "Pop"],
                        "songs": [
                            {"title": "Hold Up",      "duration_seconds": 214, "track_number": 2},
                            {"title": "Don't Hurt Yourself", "duration_seconds": 218, "track_number": 3},
                            {"title": "Sorry",        "duration_seconds": 222, "track_number": 4},
                            {"title": "Freedom",      "duration_seconds": 255, "track_number": 9},
                            {"title": "Formation",    "duration_seconds": 213, "track_number": 12},
                            {"title": "Love Drought", "duration_seconds": 242, "track_number": 10},
                        ],
                    },
                    {
                        "title": "Renaissance",
                        "release_date": "2022-07-29",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/a/a0/Beyonc%C3%A9_-_Renaissance.png",
                        "description": "A disco and dance-music love letter celebrating Black queer culture and the joy of movement.",
                        "genres": ["Dance", "R&B", "Electronic"],
                        "songs": [
                            {"title": "BREAK MY SOUL",    "duration_seconds": 256, "track_number": 4},
                            {"title": "CUFF IT",          "duration_seconds": 218, "track_number": 9},
                            {"title": "ALIEN SUPERSTAR",  "duration_seconds": 232, "track_number": 6},
                            {"title": "VIRGO'S GROOVE",   "duration_seconds": 316, "track_number": 11},
                            {"title": "CHURCH GIRL",      "duration_seconds": 247, "track_number": 12},
                        ],
                    },
                ],
            },
            {
                "artist": "The Weeknd",
                "albums": [
                    {
                        "title": "After Hours",
                        "release_date": "2020-03-20",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/c/c4/The_Weeknd_-_After_Hours.png",
                        "description": "The Weeknd's fourth studio album — a cinematic synth-pop concept record about heartbreak and excess.",
                        "genres": ["R&B", "Pop", "Electronic"],
                        "songs": [
                            {"title": "Alone Again",       "duration_seconds": 261, "track_number": 1},
                            {"title": "Too Late",          "duration_seconds": 239, "track_number": 4},
                            {"title": "Hardest to Love",   "duration_seconds": 241, "track_number": 5},
                            {"title": "Blinding Lights",   "duration_seconds": 200, "track_number": 9},
                            {"title": "In Your Eyes",      "duration_seconds": 237, "track_number": 10},
                            {"title": "Until I Bleed Out", "duration_seconds": 209, "track_number": 14},
                        ],
                    },
                    {
                        "title": "Starboy",
                        "release_date": "2016-11-25",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/3/39/The_Weeknd_-_Starboy.png",
                        "description": "The Weeknd's third studio album blending dark R&B with mainstream pop sensibilities.",
                        "genres": ["R&B", "Pop", "Electronic"],
                        "songs": [
                            {"title": "Starboy",          "duration_seconds": 230, "track_number": 1},
                            {"title": "False Alarm",      "duration_seconds": 220, "track_number": 2},
                            {"title": "I Feel It Coming", "duration_seconds": 269, "track_number": 13},
                            {"title": "Die for You",      "duration_seconds": 260, "track_number": 9},
                            {"title": "Secrets",          "duration_seconds": 309, "track_number": 7},
                        ],
                    },
                ],
            },
            {
                "artist": "Tyler, the Creator",
                "albums": [
                    {
                        "title": "IGOR",
                        "release_date": "2019-05-17",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/8/84/Tyler_the_Creator_-_Igor.png",
                        "description": "Tyler's fifth album — a maximalist neo-soul concept record about unrequited love told through an alter ego.",
                        "genres": ["Hip-Hop", "Alternative", "Electronic"],
                        "songs": [
                            {"title": "IGOR'S THEME",           "duration_seconds": 174, "track_number": 1},
                            {"title": "EARFQUAKE",              "duration_seconds": 189, "track_number": 2},
                            {"title": "I THINK",                "duration_seconds": 193, "track_number": 3},
                            {"title": "GONE, GONE / THANK YOU", "duration_seconds": 263, "track_number": 9},
                            {"title": "ARE WE STILL FRIENDS?",  "duration_seconds": 210, "track_number": 12},
                        ],
                    },
                    {
                        "title": "Flower Boy",
                        "release_date": "2017-07-21",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/8/88/Tyler_the_Creator_-_Flower_Boy.png",
                        "description": "Tyler's most introspective album — lush, confessional, and bursting with color.",
                        "genres": ["Hip-Hop", "Alternative", "Indie"],
                        "songs": [
                            {"title": "Foreword",           "duration_seconds": 122, "track_number": 1},
                            {"title": "See You Again",      "duration_seconds": 237, "track_number": 2},
                            {"title": "Garden Shed",        "duration_seconds": 225, "track_number": 5},
                            {"title": "Boredom",            "duration_seconds": 262, "track_number": 6},
                            {"title": "911 / Mr. Lonely",   "duration_seconds": 297, "track_number": 9},
                            {"title": "November",           "duration_seconds": 263, "track_number": 13},
                        ],
                    },
                ],
            },
            {
                "artist": "Billie Eilish",
                "albums": [
                    {
                        "title": "When We All Fall Asleep, Where Do We Go?",
                        "release_date": "2019-03-29",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/3/38/When_We_All_Fall_Asleep%2C_Where_Do_We_Go%3F.png",
                        "description": "Billie Eilish's debut album — a genre-blurring collection of dark pop and bedroom whispers that captured an entire generation.",
                        "genres": ["Pop", "Alternative", "Electronic"],
                        "songs": [
                            {"title": "bad guy",              "duration_seconds": 194, "track_number": 2},
                            {"title": "wish you were gay",    "duration_seconds": 189, "track_number": 4},
                            {"title": "when the party's over","duration_seconds": 203, "track_number": 8},
                            {"title": "bury a friend",        "duration_seconds": 193, "track_number": 10},
                            {"title": "all the good girls go to hell", "duration_seconds": 158, "track_number": 11},
                            {"title": "8",                    "duration_seconds": 172, "track_number": 13},
                        ],
                    },
                    {
                        "title": "HIT ME HARD AND SOFT",
                        "release_date": "2024-05-17",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/3/3e/Billie_Eilish_-_Hit_Me_Hard_and_Soft.png",
                        "description": "Billie Eilish's third album — a deeply personal record navigating identity, intimacy, and fame.",
                        "genres": ["Pop", "Alternative", "Indie"],
                        "songs": [
                            {"title": "LUNCH",         "duration_seconds": 173, "track_number": 1},
                            {"title": "CHIHIRO",       "duration_seconds": 310, "track_number": 2},
                            {"title": "THE GREATEST",  "duration_seconds": 231, "track_number": 3},
                            {"title": "BIRDS OF A FEATHER", "duration_seconds": 211, "track_number": 4},
                            {"title": "WILDFLOWER",    "duration_seconds": 287, "track_number": 5},
                        ],
                    },
                ],
            },
            {
                "artist": "Daft Punk",
                "albums": [
                    {
                        "title": "Random Access Memories",
                        "release_date": "2013-05-17",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/a/a1/Random_Access_Memories.jpg",
                        "description": "Daft Punk's fourth and final album — a love letter to the golden age of studio recording, with live musicians and legendary collaborators.",
                        "genres": ["Electronic", "Funk", "Dance"],
                        "songs": [
                            {"title": "Give Life Back to Music", "duration_seconds": 274, "track_number": 1},
                            {"title": "Giorgio by Moroder",      "duration_seconds": 544, "track_number": 3},
                            {"title": "Within",                  "duration_seconds": 230, "track_number": 4},
                            {"title": "Instant Crush",           "duration_seconds": 337, "track_number": 5},
                            {"title": "Lose Yourself to Dance",  "duration_seconds": 353, "track_number": 6},
                            {"title": "Get Lucky",               "duration_seconds": 369, "track_number": 8},
                        ],
                    },
                    {
                        "title": "Discovery",
                        "release_date": "2001-02-26",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/a/ae/Daft_Punk_Discovery_cover.png",
                        "description": "Daft Punk's second album — an anime-soundtracked, euphoria-inducing masterpiece of filtered house and nu-disco.",
                        "genres": ["Electronic", "Dance", "Funk"],
                        "songs": [
                            {"title": "One More Time",                       "duration_seconds": 320, "track_number": 1},
                            {"title": "Aerodynamic",                          "duration_seconds": 212, "track_number": 2},
                            {"title": "Digital Love",                         "duration_seconds": 301, "track_number": 3},
                            {"title": "Harder, Better, Faster, Stronger",     "duration_seconds": 224, "track_number": 4},
                            {"title": "Something About Us",                   "duration_seconds": 257, "track_number": 9},
                            {"title": "Voyager",                              "duration_seconds": 227, "track_number": 11},
                        ],
                    },
                ],
            },
        ]

        all_new_albums: dict[str, models.Album] = {}
        all_new_songs:  dict[str, models.Song]  = {}

        for entry in new_catalog:
            artist = new_artists[entry["artist"]]
            for album_data in entry["albums"]:
                songs_data   = album_data.pop("songs")
                album_genres = album_data.pop("genres")
                album = models.Album(**album_data, artist_id=artist.id)
                for gname in album_genres:
                    if gname in genres:
                        album.genres.append(genres[gname])
                db.add(album)
                db.flush()
                all_new_albums[album.title] = album
                for s in songs_data:
                    song = models.Song(**s, artist_id=artist.id, album_id=album.id)
                    db.add(song)
                    db.flush()
                    all_new_songs[song.title] = song

        db.flush()

        # ── Helpers ──────────────────────────────────────────────────────────
        def alb(title: str) -> models.Album:
            a = all_new_albums.get(title)
            if not a:
                a = db.query(models.Album).filter(models.Album.title == title).first()
            return a

        def trk(title: str) -> models.Song:
            s = all_new_songs.get(title)
            if not s:
                s = db.query(models.Song).filter(models.Song.title == title).first()
            return s

        def existing_user(username: str) -> models.User:
            return db.query(models.User).filter(models.User.username == username).first()

        # ── New users ────────────────────────────────────────────────────────
        new_users_seed = [
            dict(username="bey_hive",        email="beyhive@tunelog.com",    pw="password123",
                 bio="Certified member of the Beyhive. Lemonade changed my life and I will die on that hill.",
                 prefs={"genres": ["R&B", "Pop", "Soul"], "moods": ["empowering", "emotional"], "free_text": "Beyoncé, SZA, Lizzo — power and vulnerability in music"}),
            dict(username="synth_wave_kid",  email="synth@tunelog.com",      pw="password123",
                 bio="Chasing 80s nostalgia through modern production. The Weeknd and Daft Punk are my north stars.",
                 prefs={"genres": ["Electronic", "R&B", "Dance"], "moods": ["chill", "energetic"], "free_text": "Synthwave, nu-disco, everything with a pulsing bassline"}),
            dict(username="tyler_fan_2019",  email="tylerfan@tunelog.com",   pw="password123",
                 bio="IGOR was a spiritual experience. Tyler literally cannot miss.",
                 prefs={"genres": ["Hip-Hop", "Alternative", "Indie"], "moods": ["introspective", "chill"], "free_text": "Conceptual albums, weird production, music that tells a story"}),
            dict(username="gen_z_ears",      email="genz@tunelog.com",       pw="password123",
                 bio="Billie Eilish got me into music at 13. Now I can't stop listening to everything.",
                 prefs={"genres": ["Pop", "Alternative", "Indie"], "moods": ["emotional", "chill"], "free_text": "Billie Eilish, Olivia Rodrigo, Lorde — confessional pop done right"}),
            dict(username="dance_floor_dan", email="dancedan@tunelog.com",   pw="password123",
                 bio="If I can't move to it, is it even music? Daft Punk forever. One More Time is perfection.",
                 prefs={"genres": ["Electronic", "Dance", "Funk"], "moods": ["energetic", "happy"], "free_text": "House, disco, funk — music made to move"}),
        ]

        new_users: dict[str, models.User] = {}
        for u in new_users_seed:
            prefs = u.pop("prefs", None)
            user = models.User(
                username=u["username"],
                email=u["email"],
                hashed_password=hash_password(u["pw"]),
                bio=u["bio"],
                music_preferences=json.dumps(prefs) if prefs else None,
            )
            db.add(user)
            new_users[u["username"]] = user
        db.flush()

        all_users = {**new_users}
        for uname in ["musiclover", "indie_vibes", "hiphop_head", "classicrock_fan", "rbsoul", "audiophile99"]:
            u = existing_user(uname)
            if u:
                all_users[uname] = u

        # ── New follows ──────────────────────────────────────────────────────
        new_follow_pairs = [
            ("bey_hive",        "rbsoul"),
            ("bey_hive",        "musiclover"),
            ("synth_wave_kid",  "audiophile99"),
            ("synth_wave_kid",  "dance_floor_dan"),
            ("tyler_fan_2019",  "hiphop_head"),
            ("tyler_fan_2019",  "indie_vibes"),
            ("gen_z_ears",      "indie_vibes"),
            ("gen_z_ears",      "bey_hive"),
            ("dance_floor_dan", "synth_wave_kid"),
            ("dance_floor_dan", "audiophile99"),
            ("musiclover",      "bey_hive"),
            ("indie_vibes",     "gen_z_ears"),
            ("hiphop_head",     "tyler_fan_2019"),
            ("rbsoul",          "bey_hive"),
        ]
        existing_follows = {
            (f.follower_id, f.followed_id)
            for f in db.query(models.UserFollow).all()
        }
        for follower_key, followed_key in new_follow_pairs:
            fu = all_users.get(follower_key)
            fod = all_users.get(followed_key)
            if fu and fod and (fu.id, fod.id) not in existing_follows:
                db.add(models.UserFollow(
                    follower_id=fu.id,
                    followed_id=fod.id,
                    created_at=datetime.utcnow() - timedelta(days=10),
                ))

        # ── New reviews ──────────────────────────────────────────────────────
        def rev(user_key, *, album_title=None, song_title=None, rating, text=None, days_ago=0):
            uid = all_users[user_key].id
            return models.Review(
                user_id=uid,
                album_id=alb(album_title).id if album_title else None,
                song_id=trk(song_title).id   if song_title  else None,
                rating=rating, text=text,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
                updated_at=datetime.utcnow() - timedelta(days=days_ago),
            )

        new_reviews = [
            # ── Lemonade ──────────────────────────────────────────────────
            rev("bey_hive",        album_title="Lemonade", rating=5.0, days_ago=6,
                text="A visual and sonic masterpiece. Beyoncé lays herself bare across every genre imaginable. Formation alone is worth a perfect score."),
            rev("musiclover",      album_title="Lemonade", rating=4.5, days_ago=8,
                text="The range on this album is staggering — country, blues, hip-hop, R&B. Arguably her best creative statement."),
            rev("rbsoul",          album_title="Lemonade", rating=5.0, days_ago=5,
                text="Hold Up and Freedom are some of the greatest songs she has ever recorded. The visual album companion makes every listen richer."),
            rev("gen_z_ears",      album_title="Lemonade", rating=4.5, days_ago=3,
                text="I came for the bops and stayed for the genuine emotional devastation. Sorry goes off."),

            # ── Renaissance ───────────────────────────────────────────────
            rev("bey_hive",        album_title="Renaissance", rating=5.0, days_ago=4,
                text="She said 'this one is for the clubs' and delivered a 16-track monument to dance music. CUFF IT and VIRGO'S GROOVE are life-changing."),
            rev("dance_floor_dan", album_title="Renaissance", rating=5.0, days_ago=7,
                text="As someone who lives for the dance floor, this album is basically a religious experience. BREAK MY SOUL had me in tears at a festival."),
            rev("synth_wave_kid",  album_title="Renaissance", rating=4.5, days_ago=9,
                text="The production on this thing is immaculate. Every single track is a club weapon. ALIEN SUPERSTAR is her best solo track in years."),
            rev("indie_vibes",     album_title="Renaissance", rating=4.0, days_ago=11,
                text="Not usually my scene but the production excellence is undeniable. CUFF IT is the rare mainstream banger that holds up on headphones."),

            # ── Formation (song) ──────────────────────────────────────────
            rev("bey_hive",        song_title="Formation", rating=5.0, days_ago=6,
                text="The most important music video of the 2010s. Musically it's a Mardi Gras parade run through a trap filter and it slaps impossibly hard."),
            rev("rbsoul",          song_title="Freedom", rating=5.0, days_ago=5,
                text="Beyoncé and Kendrick on the same track. The gospel choir outro. The urgency. An anthem that will last forever."),

            # ── After Hours ───────────────────────────────────────────────
            rev("synth_wave_kid",  album_title="After Hours", rating=5.0, days_ago=12,
                text="The definitive Weeknd album. Every track bleeds into the next in this slow-motion nightmare of heartbreak and neon lights."),
            rev("musiclover",      album_title="After Hours", rating=4.5, days_ago=14,
                text="Blinding Lights alone would justify this album's existence, but the deeper cuts like Alone Again hit even harder. Stunning production."),
            rev("indie_vibes",     album_title="After Hours", rating=4.0, days_ago=13,
                text="The 80s synth-pop influences are perfectly deployed here. Hardest to Love is criminally underrated. Dark, cinematic, immaculate."),
            rev("gen_z_ears",      album_title="After Hours", rating=4.5, days_ago=2,
                text="Until I Bleed Out as a closer is genuinely unsettling in the best way. This album lives in its own universe."),

            # ── Blinding Lights (song) ────────────────────────────────────
            rev("synth_wave_kid",  song_title="Blinding Lights", rating=5.0, days_ago=12,
                text="The 80s synth hook. The percussion. The melody you can't get out of your head for weeks. A stone cold pop classic."),
            rev("dance_floor_dan", song_title="Blinding Lights", rating=5.0, days_ago=8,
                text="The most addictive three minutes in modern pop. Every DJ drops this and every crowd loses their mind. Instant classic."),

            # ── Starboy ───────────────────────────────────────────────────
            rev("synth_wave_kid",  album_title="Starboy", rating=4.0, days_ago=20,
                text="Die for You is the purest love song in his catalogue. The Daft Punk collabs I Feel It Coming and Starboy are genuine high points."),
            rev("rbsoul",          album_title="Starboy", rating=4.0, days_ago=22,
                text="The transition from dark mixtapes to polished pop is jarring but undeniably works. Secrets is a hidden gem."),

            # ── IGOR ──────────────────────────────────────────────────────
            rev("tyler_fan_2019",  album_title="IGOR", rating=5.0, days_ago=7,
                text="Tyler invented a new genre here. EARFQUAKE is devastating. ARE WE STILL FRIENDS? destroyed me. I cried on public transit."),
            rev("hiphop_head",     album_title="IGOR", rating=5.0, days_ago=9,
                text="The most cohesive rap album of the last decade. Tyler doesn't rap so much as he conducts — every element serves the heartbreak narrative."),
            rev("musiclover",      album_title="IGOR", rating=4.5, days_ago=11,
                text="GONE, GONE / THANK YOU pulls the rug out in the most perfect way. Tyler's best album and it isn't close."),
            rev("indie_vibes",     album_title="IGOR", rating=4.5, days_ago=10,
                text="Somehow both maximalist and intimate. The neo-soul palette Tyler uses here is genuinely unlike anything else in hip-hop."),

            # ── Flower Boy ────────────────────────────────────────────────
            rev("tyler_fan_2019",  album_title="Flower Boy", rating=5.0, days_ago=30,
                text="See You Again makes me feel things I can't describe. This album is Tyler at his most vulnerable and it's beautiful."),
            rev("indie_vibes",     album_title="Flower Boy", rating=4.5, days_ago=32,
                text="Boredom is everything I want in a summer song. The whole album feels like watching the world through a window on a perfect day."),
            rev("hiphop_head",     album_title="Flower Boy", rating=4.5, days_ago=28,
                text="Garden Shed is a moment of breathtaking honesty. Tyler grew up before our ears on this one."),

            # ── EARFQUAKE (song) ──────────────────────────────────────────
            rev("tyler_fan_2019",  song_title="EARFQUAKE", rating=5.0, days_ago=7,
                text="The falsetto. The strings. The way it collapses in the chorus. One of the most uniquely beautiful songs in modern music."),

            # ── When We All Fall Asleep ───────────────────────────────────
            rev("gen_z_ears",      album_title="When We All Fall Asleep, Where Do We Go?", rating=5.0, days_ago=5,
                text="This album rewired my brain at 14 and I've never fully recovered. bad guy is the sound of a generation defining itself."),
            rev("indie_vibes",     album_title="When We All Fall Asleep, Where Do We Go?", rating=4.5, days_ago=14,
                text="when the party's over is one of the most affecting pieces of music released this decade. Billie's vocal control is extraordinary."),
            rev("musiclover",      album_title="When We All Fall Asleep, Where Do We Go?", rating=4.5, days_ago=13,
                text="The ASMR interludes and whispered vocals should not work this well but they absolutely do. Genuinely inventive pop."),
            rev("synth_wave_kid",  album_title="When We All Fall Asleep, Where Do We Go?", rating=4.0, days_ago=18,
                text="The production is weirder and bolder than any major-label debut has a right to be. bury a friend is a banger."),

            # ── HIT ME HARD AND SOFT ─────────────────────────────────────
            rev("gen_z_ears",      album_title="HIT ME HARD AND SOFT", rating=5.0, days_ago=2,
                text="BIRDS OF A FEATHER is her best song. Full stop. This whole album is her most fully realized work — every track lands perfectly."),
            rev("musiclover",      album_title="HIT ME HARD AND SOFT", rating=4.5, days_ago=4,
                text="CHIHIRO is a 5-minute journey that justifies the whole album. Billie has grown into one of the most interesting artists of her generation."),
            rev("indie_vibes",     album_title="HIT ME HARD AND SOFT", rating=4.5, days_ago=6,
                text="WILDFLOWER is heartbreakingly beautiful. The production restraint compared to her debut makes every moment land harder."),

            # ── bad guy (song) ────────────────────────────────────────────
            rev("gen_z_ears",      song_title="bad guy", rating=5.0, days_ago=5,
                text="The bassline. The smirk. The duh. An entire cultural moment compressed into three and a half minutes."),
            rev("musiclover",      song_title="bad guy", rating=4.5, days_ago=13,
                text="The production is so deceptively simple — one kick pattern, one bassline, total confidence. Hits every single time."),

            # ── Random Access Memories ────────────────────────────────────
            rev("dance_floor_dan", album_title="Random Access Memories", rating=5.0, days_ago=15,
                text="Get Lucky is the greatest pure joy recorded in the 21st century. The whole album sounds like the 70s dreaming about the future."),
            rev("audiophile99",    album_title="Random Access Memories", rating=5.0, days_ago=60,
                text="Giorgio by Moroder might be the most perfectly produced track of the 2010s. The live musicians give this a warmth their earlier work couldn't achieve."),
            rev("synth_wave_kid",  album_title="Random Access Memories", rating=5.0, days_ago=25,
                text="Their farewell to the world and they went out making something that will last forever. Instant Crush with Julian Casablancas is devastating."),
            rev("musiclover",      album_title="Random Access Memories", rating=4.5, days_ago=40,
                text="Fragments of Time and Within are overlooked treasures. This album rewards patient listening more than almost anything else."),

            # ── Discovery ─────────────────────────────────────────────────
            rev("dance_floor_dan", album_title="Discovery", rating=5.0, days_ago=20,
                text="One More Time is the greatest opening statement in electronic music history. This album still sounds better than almost anything released today."),
            rev("audiophile99",    album_title="Discovery", rating=5.0, days_ago=80,
                text="Harder Better Faster Stronger is three minutes of pure mechanical ecstasy. The production innovations on this record are still being copied."),
            rev("synth_wave_kid",  album_title="Discovery", rating=5.0, days_ago=35,
                text="Digital Love is the most romantic song in a robot's heart. Something About Us might make me cry every single time. Flawless."),
            rev("indie_vibes",     album_title="Discovery", rating=4.5, days_ago=28,
                text="I came in skeptical of electronic music and left a convert. The melody on Digital Love is just unfair. A masterclass in dance music."),

            # ── Get Lucky / One More Time (songs) ─────────────────────────
            rev("dance_floor_dan", song_title="Get Lucky", rating=5.0, days_ago=15,
                text="Pharrell, Daft Punk, Nile Rodgers. The funk they summoned together is genuinely supernatural. The most feel-good song ever recorded."),
            rev("dance_floor_dan", song_title="One More Time", rating=5.0, days_ago=20,
                text="Celebrate and dance so free. Music is the key. This song has never failed to fill a dance floor and it never will. Transcendent."),
            rev("synth_wave_kid",  song_title="Harder, Better, Faster, Stronger", rating=5.0, days_ago=35,
                text="Four words, infinite replayability. The vocoder work is still unlike anything else. This is the DNA of a thousand songs."),
        ]

        db.flush()
        existing_review_ids = {(r.user_id, r.album_id, r.song_id)
                               for r in db.query(models.Review).all()}
        for r in new_reviews:
            key = (r.user_id, r.album_id, r.song_id)
            if key not in existing_review_ids:
                db.add(r)
                existing_review_ids.add(key)
        db.flush()

        # ── Review likes ─────────────────────────────────────────────────────
        like_pairs = []
        for album_title, liker_keys in [
            ("Lemonade",          ["musiclover", "rbsoul", "indie_vibes", "gen_z_ears", "synth_wave_kid"]),
            ("Renaissance",       ["dance_floor_dan", "synth_wave_kid", "rbsoul", "musiclover"]),
            ("After Hours",       ["synth_wave_kid", "musiclover", "gen_z_ears", "indie_vibes"]),
            ("IGOR",              ["hiphop_head", "indie_vibes", "musiclover", "tyler_fan_2019"]),
            ("Flower Boy",        ["tyler_fan_2019", "indie_vibes", "hiphop_head"]),
            ("When We All Fall Asleep, Where Do We Go?", ["gen_z_ears", "musiclover", "indie_vibes"]),
            ("HIT ME HARD AND SOFT", ["gen_z_ears", "musiclover", "indie_vibes"]),
            ("Random Access Memories", ["dance_floor_dan", "audiophile99", "synth_wave_kid", "musiclover"]),
            ("Discovery",         ["dance_floor_dan", "audiophile99", "synth_wave_kid", "indie_vibes"]),
            ("Folklore",          ["bey_hive", "gen_z_ears", "tyler_fan_2019"]),
            ("OK Computer",       ["tyler_fan_2019", "synth_wave_kid", "dance_floor_dan"]),
            ("Blonde",            ["bey_hive", "tyler_fan_2019", "gen_z_ears"]),
        ]:
            target_alb = alb(album_title)
            if not target_alb:
                continue
            target_reviews = db.query(models.Review).filter(
                models.Review.album_id == target_alb.id,
                models.Review.text.isnot(None),
            ).all()
            for rev_obj in target_reviews[:2]:
                for liker_key in liker_keys:
                    liker = all_users.get(liker_key)
                    if liker and liker.id != rev_obj.user_id:
                        like_pairs.append((liker.id, rev_obj.id))

        existing_likes = {(l.user_id, l.review_id) for l in db.query(models.ReviewLike).all()}
        for uid, rid in like_pairs:
            if (uid, rid) not in existing_likes:
                db.add(models.ReviewLike(user_id=uid, review_id=rid))
                existing_likes.add((uid, rid))

        # ── New album statuses ────────────────────────────────────────────────
        new_statuses = [
            ("bey_hive",        "Lemonade",            "favorites",      6),
            ("bey_hive",        "Renaissance",          "favorites",      4),
            ("bey_hive",        "Blonde",               "listened",      10),
            ("synth_wave_kid",  "After Hours",          "favorites",     12),
            ("synth_wave_kid",  "Random Access Memories","favorites",    25),
            ("synth_wave_kid",  "Discovery",            "favorites",     35),
            ("synth_wave_kid",  "Starboy",              "listened",      20),
            ("synth_wave_kid",  "Kid A",                "listened",      15),
            ("tyler_fan_2019",  "IGOR",                 "favorites",      7),
            ("tyler_fan_2019",  "Flower Boy",           "favorites",     30),
            ("tyler_fan_2019",  "To Pimp a Butterfly",  "listened",      20),
            ("tyler_fan_2019",  "DAMN.",                "want_to_listen", 5),
            ("gen_z_ears",      "When We All Fall Asleep, Where Do We Go?", "favorites", 5),
            ("gen_z_ears",      "HIT ME HARD AND SOFT", "favorites",      2),
            ("gen_z_ears",      "Lemonade",             "listened",       3),
            ("gen_z_ears",      "Folklore",             "listened",       8),
            ("gen_z_ears",      "Midnights",            "want_to_listen", 6),
            ("dance_floor_dan", "Random Access Memories","favorites",    15),
            ("dance_floor_dan", "Discovery",            "favorites",     20),
            ("dance_floor_dan", "Renaissance",          "listened",       7),
            ("dance_floor_dan", "After Hours",          "listened",      12),
            ("musiclover",      "Lemonade",             "listened",       8),
            ("musiclover",      "After Hours",          "listened",      14),
            ("musiclover",      "IGOR",                 "listened",      11),
            ("musiclover",      "When We All Fall Asleep, Where Do We Go?", "listened", 13),
            ("musiclover",      "HIT ME HARD AND SOFT", "want_to_listen", 4),
            ("indie_vibes",     "Flower Boy",           "listened",       32),
            ("indie_vibes",     "IGOR",                 "listened",       10),
            ("indie_vibes",     "Lemonade",             "listened",        8),
            ("indie_vibes",     "Discovery",            "listened",       28),
            ("hiphop_head",     "IGOR",                 "favorites",       9),
            ("hiphop_head",     "Flower Boy",           "listened",       28),
            ("hiphop_head",     "Lemonade",             "want_to_listen", 12),
            ("rbsoul",          "Lemonade",             "favorites",       5),
            ("rbsoul",          "Renaissance",          "listened",        6),
            ("rbsoul",          "After Hours",          "listened",       15),
            ("audiophile99",    "Random Access Memories","favorites",     60),
            ("audiophile99",    "Discovery",            "favorites",      80),
            ("audiophile99",    "After Hours",          "listened",       14),
        ]

        existing_statuses = {
            (s.user_id, s.album_id)
            for s in db.query(models.UserAlbumStatus).all()
        }
        for user_key, album_title, stat, days_ago in new_statuses:
            u = all_users.get(user_key)
            a = alb(album_title)
            if u and a and (u.id, a.id) not in existing_statuses:
                db.add(models.UserAlbumStatus(
                    user_id=u.id, album_id=a.id, status=stat,
                    created_at=datetime.utcnow() - timedelta(days=days_ago),
                ))
                existing_statuses.add((u.id, a.id))

        # ── New lists ─────────────────────────────────────────────────────────
        new_lists_seed = [
            {
                "user": "bey_hive",
                "name": "The Bey Canon",
                "description": "Every Beyoncé album ranked in my heart. Non-negotiable top tier.",
                "list_type": "custom",
                "albums": ["Lemonade", "Renaissance"],
            },
            {
                "user": "synth_wave_kid",
                "name": "Drives at Night",
                "description": "Window down, volume up, city lights. The perfect late-night driving playlist.",
                "list_type": "custom",
                "albums": ["After Hours", "Random Access Memories", "OK Computer", "Starboy"],
            },
            {
                "user": "tyler_fan_2019",
                "name": "Concept Album Hall of Fame",
                "description": "Albums that tell a complete story from track 1 to the end. No skips allowed.",
                "list_type": "custom",
                "albums": ["IGOR", "Flower Boy", "To Pimp a Butterfly", "Lemonade"],
            },
            {
                "user": "gen_z_ears",
                "name": "Albums That Defined My Teens",
                "description": "The records that were playing while I figured out who I am. Precious to me.",
                "list_type": "custom",
                "albums": ["When We All Fall Asleep, Where Do We Go?", "HIT ME HARD AND SOFT", "Folklore", "Midnights"],
            },
            {
                "user": "dance_floor_dan",
                "name": "Eternal Dance Floor Bangers",
                "description": "Put any of these on at a party and watch the floor fill up. Guaranteed.",
                "list_type": "custom",
                "albums": ["Discovery", "Random Access Memories", "Renaissance"],
            },
            {
                "user": "musiclover",
                "name": "2020s Must-Listens",
                "description": "The albums from this decade I think everyone should experience at least once.",
                "list_type": "custom",
                "albums": ["Folklore", "After Hours", "IGOR", "Renaissance", "HIT ME HARD AND SOFT"],
            },
            {
                "user": "indie_vibes",
                "name": "Late Night Headphone Albums",
                "description": "Best experienced alone, in the dark, with good headphones and nowhere to be.",
                "list_type": "custom",
                "albums": ["Kid A", "Blonde", "Flower Boy", "When We All Fall Asleep, Where Do We Go?"],
            },
            {
                "user": "audiophile99",
                "name": "Studio Engineering Masterclasses",
                "description": "Albums where the production craft is itself a performance. Test your setup with these.",
                "list_type": "custom",
                "albums": ["Random Access Memories", "Abbey Road", "OK Computer", "Blonde", "IGOR"],
            },
        ]

        for l in new_lists_seed:
            u = all_users.get(l["user"])
            if not u:
                continue
            lst = models.List(
                user_id=u.id,
                name=l["name"],
                description=l["description"],
                list_type=l["list_type"],
                is_public=True,
                created_at=datetime.utcnow() - timedelta(days=5),
            )
            db.add(lst)
            db.flush()
            for album_title in l["albums"]:
                a = alb(album_title)
                if a:
                    db.add(models.ListItem(list_id=lst.id, album_id=a.id))

        # ── New activities ────────────────────────────────────────────────────
        def act(user_key, action_type, target_type=None, target_id=None, days_ago=0):
            u = all_users.get(user_key)
            if not u:
                return None
            return models.Activity(
                user_id=u.id,
                action_type=action_type,
                target_type=target_type,
                target_id=target_id,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            )

        new_activities = [
            # Recent reviews (within 21 days)
            act("bey_hive",        "reviewed_album", "album", alb("Lemonade").id,            days_ago=6),
            act("bey_hive",        "reviewed_album", "album", alb("Renaissance").id,         days_ago=4),
            act("bey_hive",        "reviewed_song",  "song",  trk("Formation").id,           days_ago=6),
            act("gen_z_ears",      "reviewed_album", "album", alb("HIT ME HARD AND SOFT").id, days_ago=2),
            act("gen_z_ears",      "reviewed_album", "album", alb("Lemonade").id,            days_ago=3),
            act("gen_z_ears",      "reviewed_album", "album", alb("When We All Fall Asleep, Where Do We Go?").id, days_ago=5),
            act("gen_z_ears",      "reviewed_song",  "song",  trk("bad guy").id,             days_ago=5),
            act("synth_wave_kid",  "reviewed_album", "album", alb("After Hours").id,         days_ago=12),
            act("synth_wave_kid",  "reviewed_album", "album", alb("Renaissance").id,         days_ago=9),
            act("synth_wave_kid",  "reviewed_song",  "song",  trk("Blinding Lights").id,     days_ago=12),
            act("tyler_fan_2019",  "reviewed_album", "album", alb("IGOR").id,                days_ago=7),
            act("tyler_fan_2019",  "reviewed_song",  "song",  trk("EARFQUAKE").id,           days_ago=7),
            act("dance_floor_dan", "reviewed_album", "album", alb("Random Access Memories").id, days_ago=15),
            act("dance_floor_dan", "reviewed_song",  "song",  trk("Get Lucky").id,           days_ago=15),
            act("dance_floor_dan", "reviewed_song",  "song",  trk("One More Time").id,       days_ago=20),
            act("musiclover",      "reviewed_album", "album", alb("Lemonade").id,            days_ago=8),
            act("musiclover",      "reviewed_album", "album", alb("After Hours").id,         days_ago=14),
            act("musiclover",      "reviewed_album", "album", alb("HIT ME HARD AND SOFT").id, days_ago=4),
            act("indie_vibes",     "reviewed_album", "album", alb("IGOR").id,                days_ago=10),
            act("indie_vibes",     "reviewed_album", "album", alb("HIT ME HARD AND SOFT").id, days_ago=6),
            act("indie_vibes",     "reviewed_album", "album", alb("Renaissance").id,         days_ago=11),
            act("rbsoul",          "reviewed_album", "album", alb("Lemonade").id,            days_ago=5),
            act("rbsoul",          "reviewed_song",  "song",  trk("Freedom").id,             days_ago=5),
            act("hiphop_head",     "reviewed_album", "album", alb("IGOR").id,                days_ago=9),
            act("hiphop_head",     "reviewed_album", "album", alb("Flower Boy").id,          days_ago=28),
            act("audiophile99",    "reviewed_album", "album", alb("Random Access Memories").id, days_ago=60),
            # Favorites / status
            act("bey_hive",        "marked_album_favorites", "album", alb("Lemonade").id,    days_ago=6),
            act("bey_hive",        "marked_album_favorites", "album", alb("Renaissance").id, days_ago=4),
            act("gen_z_ears",      "marked_album_favorites", "album", alb("HIT ME HARD AND SOFT").id, days_ago=2),
            act("tyler_fan_2019",  "marked_album_favorites", "album", alb("IGOR").id,        days_ago=7),
            act("dance_floor_dan", "marked_album_favorites", "album", alb("Random Access Memories").id, days_ago=15),
            act("dance_floor_dan", "marked_album_favorites", "album", alb("Discovery").id,   days_ago=20),
            act("synth_wave_kid",  "marked_album_favorites", "album", alb("After Hours").id, days_ago=12),
            act("musiclover",      "marked_album_listened",  "album", alb("Lemonade").id,    days_ago=8),
            act("indie_vibes",     "marked_album_listened",  "album", alb("IGOR").id,        days_ago=10),
            act("rbsoul",          "marked_album_favorites", "album", alb("Lemonade").id,    days_ago=5),
            # Follows
            act("bey_hive",        "followed", "user", all_users.get("rbsoul", models.User()).id,      days_ago=10),
            act("gen_z_ears",      "followed", "user", all_users.get("bey_hive", models.User()).id,    days_ago=8),
            act("tyler_fan_2019",  "followed", "user", all_users.get("hiphop_head", models.User()).id, days_ago=9),
            act("synth_wave_kid",  "followed", "user", all_users.get("dance_floor_dan", models.User()).id, days_ago=10),
        ]

        for a in new_activities:
            if a is not None:
                db.add(a)

        db.commit()
        print("Extra seed data added successfully!")
    except Exception as e:
        db.rollback()
        print(f"Extra seed error: {e}")
        raise
    finally:
        db.close()


def seed_activity_boost():
    """Add a dense wave of very recent activity so feeds, trending, and stats feel lively."""
    db = SessionLocal()
    try:
        if db.query(models.Activity).count() >= 200:
            return  # Already boosted

        all_users = {u.username: u for u in db.query(models.User).all()}
        all_albums = {a.title: a for a in db.query(models.Album).all()}
        all_songs  = {s.title: s for s in db.query(models.Song).all()}

        existing_review_keys = {
            (r.user_id, r.album_id, r.song_id) for r in db.query(models.Review).all()
        }
        existing_status_keys = {
            (s.user_id, s.album_id) for s in db.query(models.UserAlbumStatus).all()
        }

        def alb(t): return all_albums.get(t)
        def trk(t): return all_songs.get(t)
        def usr(u): return all_users.get(u)

        def add_review(username, *, album_title=None, song_title=None, rating, text, days_ago):
            u = usr(username)
            a = alb(album_title) if album_title else None
            s = trk(song_title)  if song_title  else None
            if not u: return
            if album_title and not a: return
            if song_title  and not s: return
            key = (u.id, a.id if a else None, s.id if s else None)
            if key in existing_review_keys: return
            existing_review_keys.add(key)
            r = models.Review(
                user_id=u.id,
                album_id=a.id if a else None,
                song_id=s.id  if s else None,
                rating=rating, text=text,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
                updated_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db.add(r)
            db.add(models.Activity(
                user_id=u.id,
                action_type="reviewed_album" if album_title else "reviewed_song",
                target_type="album" if album_title else "song",
                target_id=a.id if a else (s.id if s else None),
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            ))

        def add_status(username, album_title, status, days_ago):
            u = usr(username)
            a = alb(album_title)
            if not u or not a: return
            if (u.id, a.id) in existing_status_keys: return
            existing_status_keys.add((u.id, a.id))
            db.add(models.UserAlbumStatus(
                user_id=u.id, album_id=a.id, status=status,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            ))
            action = {"listened": "marked_album_listened", "favorites": "marked_album_favorites",
                      "want_to_listen": "marked_album_want_to_listen"}.get(status)
            if action:
                db.add(models.Activity(
                    user_id=u.id, action_type=action, target_type="album", target_id=a.id,
                    created_at=datetime.utcnow() - timedelta(days=days_ago),
                ))

        # ── Recent reviews (within 14 days) ──────────────────────────────────
        recent_reviews = [
            # Abbey Road wave
            ("bey_hive",       "Abbey Road",       4.5, "Even as a pop fan, the craftsmanship here is undeniable. Something might be the most beautiful guitar solo ever recorded.", 3),
            ("gen_z_ears",     "Abbey Road",       5.0, "OK so I finally listened to this and I completely understand why everyone says this is the greatest album ever. Here Comes the Sun lives in my heart now.", 5),
            ("tyler_fan_2019", "Abbey Road",       4.5, "I went in expecting to find it overrated. I was wrong. The medley is genuinely mind-blowing.", 8),
            # OK Computer wave
            ("bey_hive",       "OK Computer",      4.5, "Coming from pop, this was eye-opening. No Surprises alone is worth the whole album.", 4),
            ("gen_z_ears",     "OK Computer",      5.0, "This album literally predicted TikTok anxiety in 1997. How???", 6),
            ("dance_floor_dan","OK Computer",      4.0, "Not what I usually listen to but Karma Police is genuinely one of the most affecting songs I've ever heard.", 9),
            # DAMN. wave
            ("bey_hive",       "DAMN.",            4.5, "HUMBLE. goes insane. The production throughout is immaculate.", 2),
            ("gen_z_ears",     "DAMN.",            4.5, "LOVE. with Zacari is the most underrated song on here. I cried.", 4),
            ("synth_wave_kid", "DAMN.",            4.5, "The production is so inventive. Kendrick makes hip-hop sound like film scores here.", 7),
            # Folklore wave
            ("dance_floor_dan","Folklore",         4.0, "Okay I thought this was going to be boring but august absolutely wrecked me.", 3),
            ("tyler_fan_2019", "Folklore",         4.5, "exile is a perfect song. I wasn't expecting to care this much.", 6),
            # To Pimp a Butterfly wave
            ("bey_hive",       "To Pimp a Butterfly", 5.0, "Freedom on this album hits completely differently after hearing Beyoncé's version. Kendrick is a genius.", 7),
            ("synth_wave_kid", "To Pimp a Butterfly", 4.5, "The jazz-rap fusion is unlike anything I'd heard before. Alright is an anthem for the ages.", 10),
            # Blonde wave
            ("tyler_fan_2019", "Blonde",           5.0, "This album is the reason I make music. The most emotionally sophisticated R&B record I've ever heard.", 5),
            ("gen_z_ears",     "Blonde",           5.0, "Self Control is the most beautiful thing Frank Ocean has ever recorded and I will not hear otherwise.", 3),
            ("dance_floor_dan","Blonde",           4.0, "Not my usual scene but Nights' beat switch is the most arresting moment in any album I've listened to.", 8),
            # Sgt. Pepper's
            ("bey_hive",       "Sgt. Pepper's Lonely Hearts Club Band", 4.5, "A Day in the Life makes me feel things I can't describe. This album is sacred.", 11),
            ("gen_z_ears",     "Sgt. Pepper's Lonely Hearts Club Band", 4.5, "I had to stop what I was doing when A Day in the Life ended. Nothing compares.", 9),
            # channel ORANGE
            ("bey_hive",       "channel ORANGE",   5.0, "Pyramids is a 9-minute odyssey and I would give it 10 stars if I could. Frank was already fully formed here.", 6),
            ("gen_z_ears",     "channel ORANGE",   4.5, "Thinkin Bout You is the song you put on when you want to feel everything at once.", 5),
            ("synth_wave_kid", "channel ORANGE",   4.5, "The production is so lush and warm. This album feels like summer through a lens of longing.", 13),
            # Kid A
            ("bey_hive",       "Kid A",            4.0, "I had to listen three times before it clicked and then I couldn't stop. Haunting and beautiful.", 10),
            ("dance_floor_dan","Kid A",            4.0, "How to Disappear Completely should not be this affecting but it completely is. Radiohead is in a league of their own.", 12),
            # 1989
            ("dance_floor_dan","1989",             4.0, "Style and Out of the Woods are underrated bangers. Taylor was genuinely operating at a different level here.", 4),
            ("synth_wave_kid", "1989",             4.0, "The 80s pop production is impeccable. Blank Space is satirically perfect. Shake It Off is unstoppable.", 7),
            # Midnights
            ("bey_hive",       "Midnights",        4.5, "Lavender Haze is such a mood. The whole album is like being wrapped in velvet at 3am.", 5),
            ("dance_floor_dan","Midnights",        4.0, "Karma absolutely goes off. Anti-Hero is painfully relatable.", 8),
        ]

        for username, album_title, rating, text, days_ago in recent_reviews:
            add_review(username, album_title=album_title, rating=rating, text=text, days_ago=days_ago)

        # ── Recent song reviews ───────────────────────────────────────────────
        recent_song_reviews = [
            ("gen_z_ears",     "Here Comes the Sun",            5.0, "This song is a hug. The most comforting three minutes in all of music.", 5),
            ("bey_hive",       "Nights",                        5.0, "That beat switch. Nothing else exists like it.", 6),
            ("dance_floor_dan","BREAK MY SOUL",                 5.0, "Every time this comes on at a party the whole room shifts. Beyoncé gave us an anthem.", 7),
            ("gen_z_ears",     "BIRDS OF A FEATHER",            5.0, "I want this played at every important moment of my life from now on. Billie's best song.", 2),
            ("tyler_fan_2019", "See You Again",                 5.0, "I am not okay after this song. The kiwi verse. The chorus. All of it.", 5),
            ("synth_wave_kid", "Die for You",                   5.0, "This song makes me believe in love. The Weeknd at his most purely romantic.", 8),
            ("bey_hive",       "cardigan",                      5.0, "The production is so delicate it feels like it could break. Taylor's finest hour.", 3),
            ("dance_floor_dan","Digital Love",                  5.0, "The guitar solo on this song is the most romantic thing any robot has ever done.", 9),
            ("synth_wave_kid", "Something About Us",            5.0, "Six words: 'It might not be the right time.' Perfect.", 11),
            ("gen_z_ears",     "Anti-Hero",                     4.5, "It's me, hi. This song is devastatingly accurate about a specific kind of anxiety.", 4),
            ("tyler_fan_2019", "King Kunta",                    5.0, "The groove on this is absolutely ridiculous. Kendrick rapping over live funk is unmatched.", 10),
            ("bey_hive",       "HUMBLE.",                       5.0, "The video, the beat drop, sit down. Iconic is not a strong enough word.", 2),
        ]

        for username, song_title, rating, text, days_ago in recent_song_reviews:
            add_review(username, song_title=song_title, rating=rating, text=text, days_ago=days_ago)

        # ── Recent status updates ─────────────────────────────────────────────
        recent_statuses = [
            ("bey_hive",       "Abbey Road",            "listened",       3),
            ("bey_hive",       "OK Computer",           "listened",       4),
            ("bey_hive",       "DAMN.",                 "listened",       2),
            ("bey_hive",       "Sgt. Pepper's Lonely Hearts Club Band", "listened", 11),
            ("bey_hive",       "channel ORANGE",        "listened",       6),
            ("bey_hive",       "Kid A",                 "want_to_listen", 10),
            ("gen_z_ears",     "OK Computer",           "listened",       6),
            ("gen_z_ears",     "DAMN.",                 "listened",       4),
            ("gen_z_ears",     "Blonde",                "favorites",      3),
            ("gen_z_ears",     "channel ORANGE",        "listened",       5),
            ("gen_z_ears",     "Abbey Road",            "listened",       5),
            ("gen_z_ears",     "Sgt. Pepper's Lonely Hearts Club Band", "want_to_listen", 9),
            ("gen_z_ears",     "1989",                  "want_to_listen", 6),
            ("dance_floor_dan","Folklore",              "listened",       3),
            ("dance_floor_dan","1989",                  "listened",       4),
            ("dance_floor_dan","Blonde",                "listened",       8),
            ("dance_floor_dan","Kid A",                 "listened",       12),
            ("dance_floor_dan","DAMN.",                 "want_to_listen", 6),
            ("synth_wave_kid", "DAMN.",                 "listened",       7),
            ("synth_wave_kid", "channel ORANGE",        "listened",       13),
            ("synth_wave_kid", "Flower Boy",            "listened",       9),
            ("synth_wave_kid", "Folklore",              "want_to_listen", 5),
            ("tyler_fan_2019", "Blonde",                "favorites",      5),
            ("tyler_fan_2019", "channel ORANGE",        "listened",       8),
            ("tyler_fan_2019", "Sgt. Pepper's Lonely Hearts Club Band", "want_to_listen", 12),
        ]

        for username, album_title, status, days_ago in recent_statuses:
            add_status(username, album_title, status, days_ago)

        db.commit()
        print("Activity boost seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Activity boost error: {e}")
        raise
    finally:
        db.close()
