"""Seed the database with artists, albums, songs, users, reviews, lists, and activity."""
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
