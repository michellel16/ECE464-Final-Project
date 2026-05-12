"""Seed the database with artists, albums, songs, users, reviews, lists, and activity."""
import json
import random
from datetime import datetime, timedelta

from .database import SessionLocal
from . import models
from .auth import hash_password


def seed_database():
    db = SessionLocal()
    try:
        if db.query(models.Artist).count() > 0:
            return  # Already seeded

        # â”€â”€ Genres â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ Artists â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ Albums & Songs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        catalog = [
            {
                "artist": "Taylor Swift",
                "albums": [
                    {
                        "title": "Folklore",
                        "release_date": "2020-07-24",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/f/f8/Taylor_Swift_-_Folklore.png",
                        "description": "Folklore is Taylor Swift's eighth studio album â€” a surprise indie-folk record recorded entirely during lockdown.",
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
                        "description": "Frank Ocean's debut studio album â€” a sprawling R&B masterpiece.",
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

        # â”€â”€ Users â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        users_seed = [
            dict(username="musiclover",      email="demo@tunelog.com",      pw="password123",
                 bio="I love music more than anything. Always searching for the next great album."),
            dict(username="indie_vibes",     email="indie@tunelog.com",     pw="password123",
                 bio="Chasing the perfect lo-fi moment. Vinyl collector, chronic over-listener."),
            dict(username="hiphop_head",     email="hiphop@tunelog.com",    pw="password123",
                 bio="Hip-hop is poetry. Kendrick, Cole, Frank â€” the holy trinity."),
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

        # â”€â”€ Reviews â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            # â”€â”€ Folklore â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("musiclover", album_title="Folklore", rating=5.0, days_ago=90,
                   text="A perfect album. Every track is a masterpiece of quiet storytelling. Taylor completely reinvented herself here."),
            review("indie_vibes", album_title="Folklore", rating=4.5, days_ago=85,
                   text="The indie-folk pivot suits Taylor perfectly. 'cardigan' and 'august' are some of her finest work to date."),
            review("classicrock_fan", album_title="Folklore", rating=4.0, days_ago=80,
                   text="Not usually my genre, but this album genuinely pulled me in. Surprisingly moving and restrained."),

            # â”€â”€ 1989 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("musiclover", album_title="1989", rating=4.0, days_ago=100,
                   text="The album that proved Taylor could dominate any genre. Pure pop craftsmanship throughout."),
            review("indie_vibes", album_title="1989", rating=3.5, days_ago=95,
                   text="Fun and polished, but I prefer the more personal direction she took on Folklore. Shake It Off is undeniably infectious."),

            # â”€â”€ Midnights â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("musiclover", album_title="Midnights", rating=4.5, days_ago=40,
                   text="Anti-Hero is an earworm and Lavender Haze sets the perfect mood. A grower for sure."),
            review("indie_vibes", album_title="Midnights", rating=4.0, days_ago=35,
                   text="The 3am edition bonus tracks push it from good to genuinely great. Took a few listens to click."),

            # â”€â”€ Abbey Road â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("classicrock_fan", album_title="Abbey Road", rating=5.0, days_ago=120,
                   text="The greatest album ever recorded. The medley on side two is humanity at its creative peak. Flawless."),
            review("musiclover", album_title="Abbey Road", rating=5.0, days_ago=110,
                   text="Here Comes the Sun never gets old. Neither does anything else on this record."),
            review("audiophile99", album_title="Abbey Road", rating=5.0, days_ago=115,
                   text="Geoff Emerick's engineering still sounds incredible decades later. A sonic and compositional masterpiece."),

            # â”€â”€ Sgt. Pepper's â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("classicrock_fan", album_title="Sgt. Pepper's Lonely Hearts Club Band", rating=5.0, days_ago=130,
                   text="A Day in the Life might be the greatest song ever written. The whole album sits at that level."),
            review("audiophile99", album_title="Sgt. Pepper's Lonely Hearts Club Band", rating=4.5, days_ago=125,
                   text="Groundbreaking for its time and still sounds fresh. The production innovations are staggering."),

            # â”€â”€ To Pimp a Butterfly â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("hiphop_head", album_title="To Pimp a Butterfly", rating=5.0, days_ago=60,
                   text="Kendrick's magnum opus. The jazz and funk influences make this feel ageless. Alright became an anthem."),
            review("rbsoul", album_title="To Pimp a Butterfly", rating=5.0, days_ago=55,
                   text="This album will be studied for decades. The spoken-word sections alone are worth the price of admission."),
            review("musiclover", album_title="To Pimp a Butterfly", rating=4.5, days_ago=65,
                   text="Challenging and rewarding in equal measure. One of the most important albums of this century."),

            # â”€â”€ DAMN. â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("hiphop_head", album_title="DAMN.", rating=5.0, days_ago=70,
                   text="Kendrick's most accessible album. HUMBLE. and DNA. are instant classics. Pulitzer-winning for a reason."),
            review("musiclover", album_title="DAMN.", rating=4.5, days_ago=75,
                   text="The duality of the tracklist is brilliant â€” it plays completely differently in reverse order. Genius."),
            review("rbsoul", album_title="DAMN.", rating=4.5, days_ago=68,
                   text="LOVE. is criminally underrated on this record. Hits differently every single listen."),

            # â”€â”€ OK Computer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("audiophile99", album_title="OK Computer", rating=5.0, days_ago=150,
                   text="The defining album of its era. Paranoid Android alone justifies a perfect score. Still timeless."),
            review("indie_vibes", album_title="OK Computer", rating=5.0, days_ago=145,
                   text="Thom Yorke predicted the digital alienation we all feel now. Visionary doesn't even cover it."),
            review("musiclover", album_title="OK Computer", rating=4.5, days_ago=140,
                   text="Essential listening. The production is still mind-blowing 25+ years later."),
            review("classicrock_fan", album_title="OK Computer", rating=5.0, days_ago=148,
                   text="Karma Police is one of the greatest songs of the 90s. The whole album operates at that level."),

            # â”€â”€ Kid A â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("audiophile99", album_title="Kid A", rating=5.0, days_ago=155,
                   text="Radiohead at their most daring. An acquired taste that never leaves you once it finally clicks."),
            review("indie_vibes", album_title="Kid A", rating=4.5, days_ago=150,
                   text="Everything in Its Right Place is one of the greatest opening tracks in history. Haunting and beautiful."),

            # â”€â”€ Blonde â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("rbsoul", album_title="Blonde", rating=5.0, days_ago=50,
                   text="Frank Ocean at his most vulnerable and artistic. Nights alone is worth a perfect score."),
            review("indie_vibes", album_title="Blonde", rating=5.0, days_ago=45,
                   text="Changed what R&B could be. Still emotionally processing this record years after its release."),
            review("audiophile99", album_title="Blonde", rating=4.5, days_ago=48,
                   text="The unconventional production choices are jarring at first, then revelatory. A true masterwork."),

            # â”€â”€ channel ORANGE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            review("rbsoul", album_title="channel ORANGE", rating=5.0, days_ago=80,
                   text="Thinkin Bout You still hits like it did on first listen. Pyramids is a 10-minute journey unto itself."),
            review("hiphop_head", album_title="channel ORANGE", rating=4.5, days_ago=75,
                   text="Frank crosses genre lines with effortless grace here. Bad Religion is stunning."),

            # â”€â”€ Song reviews â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                   text="The orchestral swells, the alarm clock, the final chord â€” this is what music can do at its absolute best."),
            review("musiclover", song_title="Anti-Hero", rating=4.5, days_ago=38,
                   text="It's me, hi, I'm the problem. Devastatingly catchy and more vulnerable than it first appears."),
        ]
        for r in reviews:
            db.add(r)
        db.flush()

        # â”€â”€ Follows â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ Album statuses â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ Lists â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                "description": "On my radar â€” just need more time with these.",
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
                "description": "Exceptional production â€” great for testing audio equipment or just deep listening.",
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

        # â”€â”€ Activities â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        if db.query(models.Artist).filter(models.Artist.name == "BeyoncÃ©").first():
            return  # Already ran

        # â”€â”€ Extra genres â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        genres: dict[str, models.Genre] = {g.name: g for g in db.query(models.Genre).all()}
        for name in ["Dance", "Soul", "Funk"]:
            if name not in genres:
                g = models.Genre(name=name)
                db.add(g)
                genres[name] = g
        db.flush()

        # â”€â”€ New artists â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        new_artists_seed = [
            {
                "name": "BeyoncÃ©",
                "bio": "BeyoncÃ© Giselle Knowles-Carter is an American singer, songwriter, and actress. Regarded as one of the greatest entertainers of her generation, she has won more Grammy Awards than any other artist.",
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

        # â”€â”€ New albums & songs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        new_catalog = [
            {
                "artist": "BeyoncÃ©",
                "albums": [
                    {
                        "title": "Lemonade",
                        "release_date": "2016-04-23",
                        "cover_url": "https://upload.wikimedia.org/wikipedia/en/5/53/Beyonce_Lemonade_album_cover.png",
                        "description": "BeyoncÃ©'s sixth studio album â€” a visual and sonic odyssey through infidelity, forgiveness, and Black womanhood.",
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
                        "description": "The Weeknd's fourth studio album â€” a cinematic synth-pop concept record about heartbreak and excess.",
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
                        "description": "Tyler's fifth album â€” a maximalist neo-soul concept record about unrequited love told through an alter ego.",
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
                        "description": "Tyler's most introspective album â€” lush, confessional, and bursting with color.",
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
                        "description": "Billie Eilish's debut album â€” a genre-blurring collection of dark pop and bedroom whispers that captured an entire generation.",
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
                        "description": "Billie Eilish's third album â€” a deeply personal record navigating identity, intimacy, and fame.",
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
                        "description": "Daft Punk's fourth and final album â€” a love letter to the golden age of studio recording, with live musicians and legendary collaborators.",
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
                        "description": "Daft Punk's second album â€” an anime-soundtracked, euphoria-inducing masterpiece of filtered house and nu-disco.",
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

        # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ New users â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        new_users_seed = [
            dict(username="bey_hive",        email="beyhive@tunelog.com",    pw="password123",
                 bio="Certified member of the Beyhive. Lemonade changed my life and I will die on that hill.",
                 prefs={"genres": ["R&B", "Pop", "Soul"], "moods": ["empowering", "emotional"], "free_text": "BeyoncÃ©, SZA, Lizzo â€” power and vulnerability in music"}),
            dict(username="synth_wave_kid",  email="synth@tunelog.com",      pw="password123",
                 bio="Chasing 80s nostalgia through modern production. The Weeknd and Daft Punk are my north stars.",
                 prefs={"genres": ["Electronic", "R&B", "Dance"], "moods": ["chill", "energetic"], "free_text": "Synthwave, nu-disco, everything with a pulsing bassline"}),
            dict(username="tyler_fan_2019",  email="tylerfan@tunelog.com",   pw="password123",
                 bio="IGOR was a spiritual experience. Tyler literally cannot miss.",
                 prefs={"genres": ["Hip-Hop", "Alternative", "Indie"], "moods": ["introspective", "chill"], "free_text": "Conceptual albums, weird production, music that tells a story"}),
            dict(username="gen_z_ears",      email="genz@tunelog.com",       pw="password123",
                 bio="Billie Eilish got me into music at 13. Now I can't stop listening to everything.",
                 prefs={"genres": ["Pop", "Alternative", "Indie"], "moods": ["emotional", "chill"], "free_text": "Billie Eilish, Olivia Rodrigo, Lorde â€” confessional pop done right"}),
            dict(username="dance_floor_dan", email="dancedan@tunelog.com",   pw="password123",
                 bio="If I can't move to it, is it even music? Daft Punk forever. One More Time is perfection.",
                 prefs={"genres": ["Electronic", "Dance", "Funk"], "moods": ["energetic", "happy"], "free_text": "House, disco, funk â€” music made to move"}),
        ]

        new_users: dict[str, models.User] = {}
        for u in new_users_seed:
            existing = db.query(models.User).filter(models.User.username == u["username"]).first()
            if existing:
                new_users[u["username"]] = existing
                continue
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

        # â”€â”€ New follows â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ New reviews â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            # â”€â”€ Lemonade â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("bey_hive",        album_title="Lemonade", rating=5.0, days_ago=6,
                text="A visual and sonic masterpiece. BeyoncÃ© lays herself bare across every genre imaginable. Formation alone is worth a perfect score."),
            rev("musiclover",      album_title="Lemonade", rating=4.5, days_ago=8,
                text="The range on this album is staggering â€” country, blues, hip-hop, R&B. Arguably her best creative statement."),
            rev("rbsoul",          album_title="Lemonade", rating=5.0, days_ago=5,
                text="Hold Up and Freedom are some of the greatest songs she has ever recorded. The visual album companion makes every listen richer."),
            rev("gen_z_ears",      album_title="Lemonade", rating=4.5, days_ago=3,
                text="I came for the bops and stayed for the genuine emotional devastation. Sorry goes off."),

            # â”€â”€ Renaissance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("bey_hive",        album_title="Renaissance", rating=5.0, days_ago=4,
                text="She said 'this one is for the clubs' and delivered a 16-track monument to dance music. CUFF IT and VIRGO'S GROOVE are life-changing."),
            rev("dance_floor_dan", album_title="Renaissance", rating=5.0, days_ago=7,
                text="As someone who lives for the dance floor, this album is basically a religious experience. BREAK MY SOUL had me in tears at a festival."),
            rev("synth_wave_kid",  album_title="Renaissance", rating=4.5, days_ago=9,
                text="The production on this thing is immaculate. Every single track is a club weapon. ALIEN SUPERSTAR is her best solo track in years."),
            rev("indie_vibes",     album_title="Renaissance", rating=4.0, days_ago=11,
                text="Not usually my scene but the production excellence is undeniable. CUFF IT is the rare mainstream banger that holds up on headphones."),

            # â”€â”€ Formation (song) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("bey_hive",        song_title="Formation", rating=5.0, days_ago=6,
                text="The most important music video of the 2010s. Musically it's a Mardi Gras parade run through a trap filter and it slaps impossibly hard."),
            rev("rbsoul",          song_title="Freedom", rating=5.0, days_ago=5,
                text="BeyoncÃ© and Kendrick on the same track. The gospel choir outro. The urgency. An anthem that will last forever."),

            # â”€â”€ After Hours â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("synth_wave_kid",  album_title="After Hours", rating=5.0, days_ago=12,
                text="The definitive Weeknd album. Every track bleeds into the next in this slow-motion nightmare of heartbreak and neon lights."),
            rev("musiclover",      album_title="After Hours", rating=4.5, days_ago=14,
                text="Blinding Lights alone would justify this album's existence, but the deeper cuts like Alone Again hit even harder. Stunning production."),
            rev("indie_vibes",     album_title="After Hours", rating=4.0, days_ago=13,
                text="The 80s synth-pop influences are perfectly deployed here. Hardest to Love is criminally underrated. Dark, cinematic, immaculate."),
            rev("gen_z_ears",      album_title="After Hours", rating=4.5, days_ago=2,
                text="Until I Bleed Out as a closer is genuinely unsettling in the best way. This album lives in its own universe."),

            # â”€â”€ Blinding Lights (song) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("synth_wave_kid",  song_title="Blinding Lights", rating=5.0, days_ago=12,
                text="The 80s synth hook. The percussion. The melody you can't get out of your head for weeks. A stone cold pop classic."),
            rev("dance_floor_dan", song_title="Blinding Lights", rating=5.0, days_ago=8,
                text="The most addictive three minutes in modern pop. Every DJ drops this and every crowd loses their mind. Instant classic."),

            # â”€â”€ Starboy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("synth_wave_kid",  album_title="Starboy", rating=4.0, days_ago=20,
                text="Die for You is the purest love song in his catalogue. The Daft Punk collabs I Feel It Coming and Starboy are genuine high points."),
            rev("rbsoul",          album_title="Starboy", rating=4.0, days_ago=22,
                text="The transition from dark mixtapes to polished pop is jarring but undeniably works. Secrets is a hidden gem."),

            # â”€â”€ IGOR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("tyler_fan_2019",  album_title="IGOR", rating=5.0, days_ago=7,
                text="Tyler invented a new genre here. EARFQUAKE is devastating. ARE WE STILL FRIENDS? destroyed me. I cried on public transit."),
            rev("hiphop_head",     album_title="IGOR", rating=5.0, days_ago=9,
                text="The most cohesive rap album of the last decade. Tyler doesn't rap so much as he conducts â€” every element serves the heartbreak narrative."),
            rev("musiclover",      album_title="IGOR", rating=4.5, days_ago=11,
                text="GONE, GONE / THANK YOU pulls the rug out in the most perfect way. Tyler's best album and it isn't close."),
            rev("indie_vibes",     album_title="IGOR", rating=4.5, days_ago=10,
                text="Somehow both maximalist and intimate. The neo-soul palette Tyler uses here is genuinely unlike anything else in hip-hop."),

            # â”€â”€ Flower Boy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("tyler_fan_2019",  album_title="Flower Boy", rating=5.0, days_ago=30,
                text="See You Again makes me feel things I can't describe. This album is Tyler at his most vulnerable and it's beautiful."),
            rev("indie_vibes",     album_title="Flower Boy", rating=4.5, days_ago=32,
                text="Boredom is everything I want in a summer song. The whole album feels like watching the world through a window on a perfect day."),
            rev("hiphop_head",     album_title="Flower Boy", rating=4.5, days_ago=28,
                text="Garden Shed is a moment of breathtaking honesty. Tyler grew up before our ears on this one."),

            # â”€â”€ EARFQUAKE (song) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("tyler_fan_2019",  song_title="EARFQUAKE", rating=5.0, days_ago=7,
                text="The falsetto. The strings. The way it collapses in the chorus. One of the most uniquely beautiful songs in modern music."),

            # â”€â”€ When We All Fall Asleep â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("gen_z_ears",      album_title="When We All Fall Asleep, Where Do We Go?", rating=5.0, days_ago=5,
                text="This album rewired my brain at 14 and I've never fully recovered. bad guy is the sound of a generation defining itself."),
            rev("indie_vibes",     album_title="When We All Fall Asleep, Where Do We Go?", rating=4.5, days_ago=14,
                text="when the party's over is one of the most affecting pieces of music released this decade. Billie's vocal control is extraordinary."),
            rev("musiclover",      album_title="When We All Fall Asleep, Where Do We Go?", rating=4.5, days_ago=13,
                text="The ASMR interludes and whispered vocals should not work this well but they absolutely do. Genuinely inventive pop."),
            rev("synth_wave_kid",  album_title="When We All Fall Asleep, Where Do We Go?", rating=4.0, days_ago=18,
                text="The production is weirder and bolder than any major-label debut has a right to be. bury a friend is a banger."),

            # â”€â”€ HIT ME HARD AND SOFT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("gen_z_ears",      album_title="HIT ME HARD AND SOFT", rating=5.0, days_ago=2,
                text="BIRDS OF A FEATHER is her best song. Full stop. This whole album is her most fully realized work â€” every track lands perfectly."),
            rev("musiclover",      album_title="HIT ME HARD AND SOFT", rating=4.5, days_ago=4,
                text="CHIHIRO is a 5-minute journey that justifies the whole album. Billie has grown into one of the most interesting artists of her generation."),
            rev("indie_vibes",     album_title="HIT ME HARD AND SOFT", rating=4.5, days_ago=6,
                text="WILDFLOWER is heartbreakingly beautiful. The production restraint compared to her debut makes every moment land harder."),

            # â”€â”€ bad guy (song) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("gen_z_ears",      song_title="bad guy", rating=5.0, days_ago=5,
                text="The bassline. The smirk. The duh. An entire cultural moment compressed into three and a half minutes."),
            rev("musiclover",      song_title="bad guy", rating=4.5, days_ago=13,
                text="The production is so deceptively simple â€” one kick pattern, one bassline, total confidence. Hits every single time."),

            # â”€â”€ Random Access Memories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("dance_floor_dan", album_title="Random Access Memories", rating=5.0, days_ago=15,
                text="Get Lucky is the greatest pure joy recorded in the 21st century. The whole album sounds like the 70s dreaming about the future."),
            rev("audiophile99",    album_title="Random Access Memories", rating=5.0, days_ago=60,
                text="Giorgio by Moroder might be the most perfectly produced track of the 2010s. The live musicians give this a warmth their earlier work couldn't achieve."),
            rev("synth_wave_kid",  album_title="Random Access Memories", rating=5.0, days_ago=25,
                text="Their farewell to the world and they went out making something that will last forever. Instant Crush with Julian Casablancas is devastating."),
            rev("musiclover",      album_title="Random Access Memories", rating=4.5, days_ago=40,
                text="Fragments of Time and Within are overlooked treasures. This album rewards patient listening more than almost anything else."),

            # â”€â”€ Discovery â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            rev("dance_floor_dan", album_title="Discovery", rating=5.0, days_ago=20,
                text="One More Time is the greatest opening statement in electronic music history. This album still sounds better than almost anything released today."),
            rev("audiophile99",    album_title="Discovery", rating=5.0, days_ago=80,
                text="Harder Better Faster Stronger is three minutes of pure mechanical ecstasy. The production innovations on this record are still being copied."),
            rev("synth_wave_kid",  album_title="Discovery", rating=5.0, days_ago=35,
                text="Digital Love is the most romantic song in a robot's heart. Something About Us might make me cry every single time. Flawless."),
            rev("indie_vibes",     album_title="Discovery", rating=4.5, days_ago=28,
                text="I came in skeptical of electronic music and left a convert. The melody on Digital Love is just unfair. A masterclass in dance music."),

            # â”€â”€ Get Lucky / One More Time (songs) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ Review likes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ New album statuses â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ New lists â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        new_lists_seed = [
            {
                "user": "bey_hive",
                "name": "The Bey Canon",
                "description": "Every BeyoncÃ© album ranked in my heart. Non-negotiable top tier.",
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

        # â”€â”€ New activities â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ Recent reviews (within 14 days) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            ("bey_hive",       "To Pimp a Butterfly", 5.0, "Freedom on this album hits completely differently after hearing BeyoncÃ©'s version. Kendrick is a genius.", 7),
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

        # â”€â”€ Recent song reviews â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        recent_song_reviews = [
            ("gen_z_ears",     "Here Comes the Sun",            5.0, "This song is a hug. The most comforting three minutes in all of music.", 5),
            ("bey_hive",       "Nights",                        5.0, "That beat switch. Nothing else exists like it.", 6),
            ("dance_floor_dan","BREAK MY SOUL",                 5.0, "Every time this comes on at a party the whole room shifts. BeyoncÃ© gave us an anthem.", 7),
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

        # â”€â”€ Recent status updates â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


def seed_rich_demo_data():
    """
    Add rich demo data to showcase all platform features:
      - Song-level playlists (ListItem.song_id)
      - Song statuses (UserSongStatus)
      - 3 new users with distinct preferences (exercises the preference-embedding path)
      - Dense mutual-follow graph (mutual follows, not just one-directional)
      - User-to-user music recommendations (UserRecommendation)
    """
    db = SessionLocal()
    try:
        if db.query(models.User).filter(models.User.username == "crate_digger").first():
            return  # Already ran

        all_users  = {u.username: u for u in db.query(models.User).all()}
        all_albums = {a.title: a for a in db.query(models.Album).all()}
        all_songs  = {s.title: s for s in db.query(models.Song).all()}

        if not all_users or not all_albums:
            return

        def usr(u): return all_users.get(u)
        def alb(t): return all_albums.get(t)
        def trk(t): return all_songs.get(t)
        def rnd(a, b): return random.randint(a, b)

        # â”€â”€ 3 new users â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        new_users_seed = [
            dict(
                username="crate_digger",
                email="cratedigger@tunelog.com", pw="password123",
                bio="Vinyl collector and music archaeologist. If it has a B-side, I've heard it.",
                prefs={"genres": ["Jazz", "Folk", "Rock"], "moods": ["introspective", "chill"],
                       "free_text": "Deep cuts, album B-sides, music that rewards close listening"},
            ),
            dict(
                username="pop_princess_p",
                email="popprincess@tunelog.com", pw="password123",
                bio="Unashamedly obsessed with pop perfection. A great hook is high art.",
                prefs={"genres": ["Pop", "R&B", "Electronic"], "moods": ["happy", "energetic"],
                       "free_text": "Bops, bangers, and certified earworms â€” from BeyoncÃ© to Billie"},
            ),
            dict(
                username="lo_fi_lucia",
                email="lofilucia@tunelog.com", pw="password123",
                bio="Study music and late-night headphone sessions. Indie and lo-fi are my home.",
                prefs={"genres": ["Indie", "Alternative", "Folk"], "moods": ["chill", "introspective"],
                       "free_text": "Bedroom recordings, rainy day music, Radiohead and Frank Ocean"},
            ),
        ]

        new_users: dict[str, models.User] = {}
        for u_data in new_users_seed:
            prefs = u_data.pop("prefs", None)
            user = models.User(
                username=u_data["username"],
                email=u_data["email"],
                hashed_password=hash_password(u_data["pw"]),
                bio=u_data["bio"],
                music_preferences=json.dumps(prefs) if prefs else None,
            )
            db.add(user)
            new_users[u_data["username"]] = user
        db.flush()
        all_users.update(new_users)

        # â”€â”€ Song statuses â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        song_status_rows = [
            ("musiclover",      "cardigan",                          "favorites"),
            ("musiclover",      "Here Comes the Sun",                "favorites"),
            ("musiclover",      "Anti-Hero",                         "listened"),
            ("musiclover",      "Blinding Lights",                   "listened"),
            ("indie_vibes",     "Paranoid Android",                  "favorites"),
            ("indie_vibes",     "Everything in Its Right Place",     "favorites"),
            ("indie_vibes",     "Nights",                            "listened"),
            ("indie_vibes",     "exile (feat. Bon Iver)",            "favorites"),
            ("hiphop_head",     "HUMBLE.",                           "favorites"),
            ("hiphop_head",     "Alright",                           "favorites"),
            ("hiphop_head",     "DNA.",                              "listened"),
            ("hiphop_head",     "EARFQUAKE",                         "favorites"),
            ("rbsoul",          "Nights",                            "favorites"),
            ("rbsoul",          "Pink + White",                      "favorites"),
            ("rbsoul",          "Thinkin Bout You",                  "listened"),
            ("rbsoul",          "Hold Up",                           "favorites"),
            ("rbsoul",          "Formation",                         "favorites"),
            ("audiophile99",    "Paranoid Android",                  "favorites"),
            ("audiophile99",    "Everything in Its Right Place",     "favorites"),
            ("audiophile99",    "Get Lucky",                         "favorites"),
            ("classicrock_fan", "Come Together",                     "favorites"),
            ("classicrock_fan", "A Day in the Life",                 "favorites"),
            ("classicrock_fan", "Here Comes the Sun",                "favorites"),
            ("bey_hive",        "Formation",                         "favorites"),
            ("bey_hive",        "Hold Up",                           "favorites"),
            ("bey_hive",        "BREAK MY SOUL",                     "favorites"),
            ("bey_hive",        "cardigan",                          "listened"),
            ("synth_wave_kid",  "Blinding Lights",                   "favorites"),
            ("synth_wave_kid",  "Die for You",                       "favorites"),
            ("synth_wave_kid",  "Get Lucky",                         "favorites"),
            ("synth_wave_kid",  "One More Time",                     "favorites"),
            ("tyler_fan_2019",  "EARFQUAKE",                         "favorites"),
            ("tyler_fan_2019",  "See You Again",                     "favorites"),
            ("tyler_fan_2019",  "Alright",                           "listened"),
            ("tyler_fan_2019",  "King Kunta",                        "listened"),
            ("gen_z_ears",      "bad guy",                           "favorites"),
            ("gen_z_ears",      "BIRDS OF A FEATHER",                "favorites"),
            ("gen_z_ears",      "Anti-Hero",                         "listened"),
            ("gen_z_ears",      "when the party's over",             "favorites"),
            ("dance_floor_dan", "One More Time",                     "favorites"),
            ("dance_floor_dan", "Get Lucky",                         "favorites"),
            ("dance_floor_dan", "Harder, Better, Faster, Stronger",  "favorites"),
            ("dance_floor_dan", "BREAK MY SOUL",                     "listened"),
            ("dance_floor_dan", "Digital Love",                      "favorites"),
            # New users
            ("crate_digger",    "Paranoid Android",                  "favorites"),
            ("crate_digger",    "Here Comes the Sun",                "favorites"),
            ("crate_digger",    "cardigan",                          "listened"),
            ("crate_digger",    "Everything in Its Right Place",     "listened"),
            ("pop_princess_p",  "Anti-Hero",                         "favorites"),
            ("pop_princess_p",  "bad guy",                           "favorites"),
            ("pop_princess_p",  "Formation",                         "favorites"),
            ("pop_princess_p",  "Blinding Lights",                   "listened"),
            ("lo_fi_lucia",     "Everything in Its Right Place",     "favorites"),
            ("lo_fi_lucia",     "Self Control",                      "favorites"),
            ("lo_fi_lucia",     "exile (feat. Bon Iver)",            "favorites"),
            ("lo_fi_lucia",     "See You Again",                     "listened"),
            ("lo_fi_lucia",     "Nights",                            "listened"),
        ]

        existing_song_statuses = {
            (s.user_id, s.song_id) for s in db.query(models.UserSongStatus).all()
        }
        for u_name, s_title, stat in song_status_rows:
            u = usr(u_name)
            s = trk(s_title)
            if u and s and (u.id, s.id) not in existing_song_statuses:
                db.add(models.UserSongStatus(
                    user_id=u.id, song_id=s.id, status=stat,
                    created_at=datetime.utcnow() - timedelta(days=rnd(1, 30)),
                ))
                existing_song_statuses.add((u.id, s.id))
        db.flush()

        # â”€â”€ Song-level playlists (ListItem.song_id) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        song_playlists = [
            {
                "user": "musiclover",
                "name": "Timeless Songs",
                "description": "Individual songs that will outlive us all. No context needed.",
                "songs": ["Here Comes the Sun", "cardigan", "Alright", "Nights", "No Surprises"],
            },
            {
                "user": "indie_vibes",
                "name": "4am Songs",
                "description": "The ones that hit hardest when the world is quiet.",
                "songs": ["Everything in Its Right Place", "exile (feat. Bon Iver)", "Ivy",
                          "How to Disappear Completely", "Self Control"],
            },
            {
                "user": "hiphop_head",
                "name": "Bars That Changed Me",
                "description": "Individual tracks where every single word matters.",
                "songs": ["HUMBLE.", "Alright", "DNA.", "The Blacker the Berry", "EARFQUAKE"],
            },
            {
                "user": "rbsoul",
                "name": "Feelings Songs",
                "description": "When you need to feel everything at once. Volume up.",
                "songs": ["Nights", "Pink + White", "Thinkin Bout You", "Self Control", "Hold Up"],
            },
            {
                "user": "synth_wave_kid",
                "name": "Night Drive Playlist",
                "description": "Songs that make you feel like you're in a movie.",
                "songs": ["Blinding Lights", "Die for You", "Starboy", "Something About Us", "In Your Eyes"],
            },
            {
                "user": "dance_floor_dan",
                "name": "Perfect Dance Songs",
                "description": "Every element engineered for maximum floor-filling.",
                "songs": ["One More Time", "Get Lucky", "Harder, Better, Faster, Stronger",
                          "BREAK MY SOUL", "Digital Love"],
            },
            {
                "user": "gen_z_ears",
                "name": "Songs I Cry To",
                "description": "Not embarrassed. Fully committed to these emotions.",
                "songs": ["bad guy", "BIRDS OF A FEATHER", "when the party's over",
                          "Self Control", "exile (feat. Bon Iver)"],
            },
            {
                "user": "audiophile99",
                "name": "Ear Test Tracks",
                "description": "Play these to test any pair of headphones. Reveals everything.",
                "songs": ["Paranoid Android", "Everything in Its Right Place", "Get Lucky",
                          "Giorgio by Moroder", "Nikes"],
            },
            {
                "user": "crate_digger",
                "name": "Deep Listening Sessions",
                "description": "Songs that demand your full attention. Phone away.",
                "songs": ["Paranoid Android", "A Day in the Life", "Kid A",
                          "How to Disappear Completely", "cardigan"],
            },
            {
                "user": "pop_princess_p",
                "name": "Perfect Pop Songs",
                "description": "Proof that pop music is high art when done right.",
                "songs": ["Anti-Hero", "bad guy", "Formation", "BIRDS OF A FEATHER", "Lavender Haze"],
            },
            {
                "user": "lo_fi_lucia",
                "name": "Late Night Headphones",
                "description": "Best with headphones, lights off, world asleep.",
                "songs": ["Everything in Its Right Place", "Self Control",
                          "exile (feat. Bon Iver)", "Nights", "See You Again"],
            },
        ]

        for pl in song_playlists:
            u = usr(pl["user"])
            if not u:
                continue
            lst = models.List(
                user_id=u.id,
                name=pl["name"],
                description=pl["description"],
                list_type="custom",
                is_public=True,
                created_at=datetime.utcnow() - timedelta(days=rnd(3, 20)),
            )
            db.add(lst)
            db.flush()
            for song_title in pl["songs"]:
                s = trk(song_title)
                if s:
                    db.add(models.ListItem(
                        list_id=lst.id, song_id=s.id,
                        added_at=datetime.utcnow() - timedelta(days=rnd(1, 10)),
                    ))

        # â”€â”€ Dense mutual-follow graph â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        existing_follows = {
            (f.follower_id, f.followed_id)
            for f in db.query(models.UserFollow).all()
        }
        more_follows = [
            # New users â†’ established
            ("crate_digger",    "audiophile99"),
            ("crate_digger",    "classicrock_fan"),
            ("crate_digger",    "indie_vibes"),
            ("pop_princess_p",  "bey_hive"),
            ("pop_princess_p",  "gen_z_ears"),
            ("pop_princess_p",  "musiclover"),
            ("lo_fi_lucia",     "indie_vibes"),
            ("lo_fi_lucia",     "tyler_fan_2019"),
            ("lo_fi_lucia",     "rbsoul"),
            # Established â†’ new  (mutual relationships)
            ("indie_vibes",     "lo_fi_lucia"),
            ("musiclover",      "crate_digger"),
            ("bey_hive",        "pop_princess_p"),
            # More mutuals among existing users
            ("classicrock_fan", "indie_vibes"),
            ("indie_vibes",     "hiphop_head"),
            ("hiphop_head",     "indie_vibes"),
            ("rbsoul",          "musiclover"),
            ("musiclover",      "rbsoul"),
            ("bey_hive",        "dance_floor_dan"),
            ("dance_floor_dan", "bey_hive"),
            ("tyler_fan_2019",  "gen_z_ears"),
            ("gen_z_ears",      "tyler_fan_2019"),
            ("crate_digger",    "lo_fi_lucia"),
            ("lo_fi_lucia",     "crate_digger"),
            ("pop_princess_p",  "crate_digger"),
            ("synth_wave_kid",  "pop_princess_p"),
        ]
        for follower_key, followed_key in more_follows:
            fu  = all_users.get(follower_key)
            fod = all_users.get(followed_key)
            if fu and fod and (fu.id, fod.id) not in existing_follows:
                db.add(models.UserFollow(
                    follower_id=fu.id, followed_id=fod.id,
                    created_at=datetime.utcnow() - timedelta(days=rnd(3, 20)),
                ))
                existing_follows.add((fu.id, fod.id))

        # â”€â”€ User-to-user music recommendations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rec_rows = [
            ("musiclover",      "crate_digger",   "OK Computer",      None,
             "You mentioned you like deep albums â€” this one will blow your mind."),
            ("indie_vibes",     "lo_fi_lucia",    "Kid A",            None,
             "If you love Radiohead, go deeper. Kid A is their most haunting work."),
            ("hiphop_head",     "tyler_fan_2019", None,               "Alright",
             "Study the way Kendrick layers metaphor into every bar here."),
            ("rbsoul",          "bey_hive",       "channel ORANGE",   None,
             "If you love Frank Ocean's Blonde, you NEED to hear where it all started."),
            ("audiophile99",    "crate_digger",   None,               "Paranoid Android",
             "A flawless production showcase. Play this on anything you want to test."),
            ("dance_floor_dan", "pop_princess_p", "Discovery",        None,
             "You like pop bangers? Daft Punk invented the form. Start here."),
            ("synth_wave_kid",  "pop_princess_p", None,               "Blinding Lights",
             "The most addictive pop song of the last decade. Non-negotiable."),
            ("bey_hive",        "lo_fi_lucia",    "Blonde",           None,
             "Frank Ocean at his most vulnerable. Perfect for late-night headphone listening."),
            ("lo_fi_lucia",     "crate_digger",   None,               "Everything in Its Right Place",
             "The greatest opening track ever recorded. This is what electronic music can feel like."),
        ]
        for sender_key, recip_key, alb_title, sng_title, note in rec_rows:
            sender = all_users.get(sender_key)
            recip  = all_users.get(recip_key)
            if not sender or not recip:
                continue
            a = alb(alb_title) if alb_title else None
            s = trk(sng_title) if sng_title else None
            if alb_title and not a: continue
            if sng_title and not s: continue
            db.add(models.UserRecommendation(
                sender_id=sender.id, recipient_id=recip.id,
                album_id=a.id if a else None,
                song_id=s.id  if s else None,
                note=note,
                created_at=datetime.utcnow() - timedelta(days=rnd(1, 7)),
            ))

        # â”€â”€ New-user reviews (gives the recommendation engine real signals) â”€â”€â”€
        existing_review_keys = {
            (r.user_id, r.album_id, r.song_id) for r in db.query(models.Review).all()
        }

        def _add_review(u_name, alb_title, sng_title, rating, text, days_ago):
            u = all_users.get(u_name)
            a = alb(alb_title) if alb_title else None
            s = trk(sng_title) if sng_title else None
            if not u: return
            if alb_title and not a: return
            if sng_title and not s: return
            key = (u.id, a.id if a else None, s.id if s else None)
            if key in existing_review_keys: return
            existing_review_keys.add(key)
            db.add(models.Review(
                user_id=u.id,
                album_id=a.id if a else None,
                song_id=s.id  if s else None,
                rating=rating, text=text,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
                updated_at=datetime.utcnow() - timedelta(days=days_ago),
            ))

        new_user_reviews = [
            ("crate_digger", "Folklore",     None, 5.0,
             "Taylor's folk detour is the most refreshingly honest thing mainstream pop has produced in years. cardigan is a perfect song.", 8),
            ("crate_digger", "OK Computer",  None, 5.0,
             "The album that taught me music could be anxious. Still sounds like the future from 1997.", 12),
            ("crate_digger", "Abbey Road",   None, 5.0,
             "Emerick's production choices are still studied in music schools. A sacred recording.", 15),
            ("crate_digger", None, "cardigan", 5.0,
             "The fingerpicked intro, the imagery, the restraint. This is how you write a love song.", 8),
            ("crate_digger", "Blonde",       None, 4.5,
             "Ocean builds an entire emotional world with whispers and distant instrumentation. Revelatory.", 10),
            ("pop_princess_p", "Midnights",  None, 5.0,
             "Anti-Hero is pop perfection and I won't hear otherwise. Lavender Haze is a mood. Karma slaps.", 4),
            ("pop_princess_p", "Lemonade",   None, 5.0,
             "The range on this album is insane. Hold Up, Formation, Love Drought â€” she was cooking.", 6),
            ("pop_princess_p", "When We All Fall Asleep, Where Do We Go?", None, 4.5,
             "bad guy is the best pop debut in years. Billie said 'I'm weird actually' and became a superstar.", 7),
            ("pop_princess_p", None, "bad guy", 5.0,
             "Minimalist production, maximum attitude. This song changed what pop could sound like.", 7),
            ("pop_princess_p", "HIT ME HARD AND SOFT", None, 5.0,
             "BIRDS OF A FEATHER alone justifies the entire album. Billie has fully arrived.", 3),
            ("lo_fi_lucia", "Blonde",        None, 5.0,
             "I put this on at 1am and didn't move for an hour. Self Control is the most beautiful song Frank Ocean has made.", 5),
            ("lo_fi_lucia", "Kid A",         None, 5.0,
             "Everything in Its Right Place feels like the inside of my head at 3am. Radiohead just gets it.", 10),
            ("lo_fi_lucia", "Flower Boy",    None, 5.0,
             "Garden Shed is heartbreaking in the most beautiful way. Tyler made something genuinely delicate here.", 9),
            ("lo_fi_lucia", None, "Self Control", 5.0,
             "Three and a half minutes of pure, aching beauty. The vocal layering in the outro is otherworldly.", 5),
            ("lo_fi_lucia", "Folklore",      None, 4.5,
             "exile with Bon Iver is the perfect expression of two people talking past each other. Quietly devastating.", 7),
        ]

        for args in new_user_reviews:
            _add_review(*args)

        db.commit()
        print("Rich demo data seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Rich demo seed error: {e}")
        raise
    finally:
        db.close()


def seed_critical_reviews():
    """
    Add a wave of low-to-mid star reviews (1.0â€“3.0) to balance the dataset.
    Without critical reviews, average ratings are unrealistically high and the
    stats/charts pages look like everyone loves everything equally.
    """
    db = SessionLocal()
    try:
        # Idempotency: check for a review we know we'll add
        marker = db.query(models.Review).join(models.User).filter(
            models.User.username == "classicrock_fan",
            models.Review.rating <= 2.0,
        ).first()
        if marker:
            return

        all_users  = {u.username: u for u in db.query(models.User).all()}
        all_albums = {a.title: a for a in db.query(models.Album).all()}
        all_songs  = {s.title: s for s in db.query(models.Song).all()}

        existing_review_keys = {
            (r.user_id, r.album_id, r.song_id) for r in db.query(models.Review).all()
        }

        def usr(u): return all_users.get(u)
        def alb(t): return all_albums.get(t)
        def trk(t): return all_songs.get(t)

        def _rev(u_name, alb_title, sng_title, rating, text, days_ago):
            u = usr(u_name)
            a = alb(alb_title) if alb_title else None
            s = trk(sng_title) if sng_title else None
            if not u: return
            if alb_title and not a: return
            if sng_title and not s: return
            key = (u.id, a.id if a else None, s.id if s else None)
            if key in existing_review_keys: return
            existing_review_keys.add(key)
            db.add(models.Review(
                user_id=u.id,
                album_id=a.id if a else None,
                song_id=s.id  if s else None,
                rating=rating, text=text,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
                updated_at=datetime.utcnow() - timedelta(days=days_ago),
            ))

        critical_reviews = [
            # â”€â”€ Taylor Swift â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("classicrock_fan", "1989", None, 2.0,
             "Pure manufactured pop with no real artistic ambition. Shake It Off plays every 10 minutes on radio for a reason â€” it's designed to be inescapable, not meaningful.", 60),
            ("classicrock_fan", "Midnights", None, 2.5,
             "The synth textures are fine but nothing here has any lasting weight. Anti-Hero is catchy the first 40 times and exhausting the next 400.", 25),
            ("hiphop_head", "Folklore", None, 2.5,
             "I respect the pivot but whispery bedroom folk isn't for me. cardigan is pretty but there's nowhere near enough energy across the whole album.", 70),
            ("dance_floor_dan", "Folklore", None, 1.5,
             "I tried. Genuinely tried. It's pleasant background music for someone else's life. Absolutely nothing to move to.", 65),
            ("dance_floor_dan", "Midnights", None, 2.0,
             "Karma is fun but the rest drags. This needed six fewer tracks and twice the tempo.", 20),

            # â”€â”€ The Beatles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("hiphop_head", "Sgt. Pepper's Lonely Hearts Club Band", None, 2.5,
             "Everyone acts like this is untouchable but it sounds incredibly dated. A Day in the Life is great and the rest is mostly novelty songs.", 100),
            ("gen_z_ears", "Sgt. Pepper's Lonely Hearts Club Band", None, 3.0,
             "I can appreciate the historical importance without pretending it's actually my favourite listen. Lucy in the Sky with Diamonds does not hold up at all.", 55),
            ("synth_wave_kid", "Abbey Road", None, 3.0,
             "Here Comes the Sun and Come Together are classics, but the medley on side two is genuinely just vibes with no payoff. Overrated as a cohesive experience.", 80),
            ("rbsoul", "Sgt. Pepper's Lonely Hearts Club Band", None, 2.5,
             "With all due respect to the legacy â€” this is not something I would ever choose to put on. Production hasn't aged well at all.", 90),

            # â”€â”€ Kendrick Lamar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("classicrock_fan", "DAMN.", None, 2.0,
             "I don't doubt the technical skill but this is not music, it's a spoken word piece over beats. HUMBLE. is the one exception â€” genuinely good production.", 55),
            ("indie_vibes", "DAMN.", None, 3.0,
             "More accessible than TPAB but I miss the jazz and the risk. This feels like Kendrick sanding down his edges for awards season.", 50),
            ("dance_floor_dan", "To Pimp a Butterfly", None, 2.0,
             "Jazz-rap and spoken word for 78 minutes is an endurance test I didn't volunteer for. Alright is the one moment that goes anywhere energetically.", 45),
            ("classicrock_fan", "To Pimp a Butterfly", None, 2.5,
             "Technically impressive but I sat through the whole thing feeling like I was being lectured. Not the experience I go to music for.", 50),

            # â”€â”€ Radiohead â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("bey_hive", "Kid A", None, 1.5,
             "I genuinely don't understand the obsession with this. It's cold, inaccessible, and sounds like a server room. How to Disappear Completely is the only moment of beauty.", 80),
            ("dance_floor_dan", "Kid A", None, 1.0,
             "This is the album equivalent of someone explaining why they don't like fun. Everything in Its Right Place isn't â€” nothing on this record is.", 75),
            ("rbsoul", "OK Computer", None, 3.0,
             "The cult around this album is bigger than the album itself. Karma Police is genuinely great. The rest is mid-90s angst that has been mythologised way beyond its merit.", 120),
            ("pop_princess_p", "Kid A", None, 2.0,
             "I respect that people love this but I have zero emotional connection to any of it. Paranoid Android from the other album at least has some dynamics.", 40),

            # â”€â”€ Frank Ocean â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("classicrock_fan", "Blonde", None, 2.0,
             "Deliberately difficult to the point of self-indulgence. There are two or three beautiful moments buried in an hour of wilfully inaccessible experimentation.", 38),
            ("dance_floor_dan", "channel ORANGE", None, 2.5,
             "Smooth and well-crafted but nothing here moves me. Pyramids at nine minutes is a test of patience, not a journey. R&B needs rhythm and this barely has any.", 60),
            ("classicrock_fan", "channel ORANGE", None, 2.0,
             "Not my genre at all and nothing here converted me. Sweet Life has a decent melody but the production sounds like a demo on most tracks.", 65),

            # â”€â”€ BeyoncÃ© â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("classicrock_fan", "Lemonade", None, 2.0,
             "Technically proficient and culturally significant but musically it's all over the place. Formation is great. The country-blues hybrid tracks are a mess.", 20),
            ("indie_vibes", "Renaissance", None, 2.5,
             "I get the vision but an hour of club music with no variation in energy leaves me numb. Three tracks are genuinely excellent. The other thirteen blur together.", 30),
            ("audiophile99", "Renaissance", None, 3.0,
             "The production is dense and deliberately loud â€” the mix is pushed so hard it loses detail on anything other than a club system. Not what I want on headphones.", 28),
            ("crate_digger", "Renaissance", None, 2.5,
             "Dance music made for specific spaces doesn't translate to listening at home. Respect the craft, but ALIEN SUPERSTAR gives me a headache on repeat.", 22),

            # â”€â”€ The Weeknd â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("hiphop_head", "Starboy", None, 2.5,
             "The Daft Punk tracks are great but the rest of this album is The Weeknd on autopilot. Die for You is pretty but this needed a real edit â€” 18 tracks is too many.", 35),
            ("indie_vibes", "After Hours", None, 2.5,
             "Blinding Lights is a perfect pop song and the rest of the album coasts on its energy. Alone Again is gorgeous but it's surrounded by filler.", 40),
            ("classicrock_fan", "After Hours", None, 1.5,
             "Lifeless synthpop with one good hook and 49 minutes of padding. This genre peaked with New Order and hasn't said anything new since.", 42),

            # â”€â”€ Tyler, the Creator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("rbsoul", "IGOR", None, 2.5,
             "Too weird to be R&B and too soft to be rap. EARFQUAKE is sweet but the whole thing feels like an art project for people who already love Tyler.", 30),
            ("classicrock_fan", "Flower Boy", None, 2.0,
             "Boredom is a decent song. The rest sounds like background music for a coffee shop that takes itself too seriously.", 45),
            ("dance_floor_dan", "IGOR", None, 2.0,
             "I wanted to like this more. EARFQUAKE is genuinely fun and then it justâ€¦ meanders for 40 minutes. Confusing and slow.", 32),

            # â”€â”€ Billie Eilish â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("classicrock_fan", "When We All Fall Asleep, Where Do We Go?", None, 1.5,
             "Whispering over trap beats is not an artistic statement, it's a gimmick. bury a friend is mildly interesting but this is the most overrated debut of the decade.", 50),
            ("audiophile99", "When We All Fall Asleep, Where Do We Go?", None, 2.5,
             "The ASMR production is a clever trick but it does not hold up on a proper sound system. Every track sounds like it was mixed for earbuds only. Technically thin.", 48),
            ("hiphop_head", "HIT ME HARD AND SOFT", None, 3.0,
             "Better than the debut but still feels too precious and contained. BIRDS OF A FEATHER is beautiful but the album never takes a real risk.", 10),
            ("rbsoul", "When We All Fall Asleep, Where Do We Go?", None, 2.0,
             "bad guy is legitimately great and then the album drops off a cliff. when the party's over is pretty but I need more than pretty.", 52),

            # â”€â”€ Daft Punk â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("hiphop_head", "Random Access Memories", None, 2.5,
             "Giorgio by Moroder is fascinating as a concept and exhausting as a listen. Get Lucky is one of the best singles of the decade but the album around it is self-indulgent.", 50),
            ("indie_vibes", "Random Access Memories", None, 3.0,
             "The production is exceptional but Daft Punk lost themselves trying to make a 'real' album. Discovery had energy and personality. This has neither.", 55),
            ("hiphop_head", "Discovery", None, 3.0,
             "I respect the influence but it hasn't aged as well as people claim. One More Time is a timeless single. The rest is filtered house that sounds like every other filtered house record.", 60),

            # â”€â”€ Song-level critical takes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("classicrock_fan", None, "Anti-Hero", 1.5,
             "The most played song of 2023 is also one of the most irritating. After the 500th airing, 'it's me, hi, I'm the problem' stops being vulnerable and starts being annoying.", 18),
            ("dance_floor_dan", None, "cardigan", 2.0,
             "Pretty and forgettable. I have heard this song hundreds of times and could not hum it back to you.", 60),
            ("classicrock_fan", None, "bad guy", 2.0,
             "The bassline is clever for about 30 seconds. After that it's one joke repeated for 3 minutes. Gen Z thinks this is edgy; it really isn't.", 45),
            ("hiphop_head", None, "Blinding Lights", 2.5,
             "A well-executed 80s pastiche that sounds better than 99% of actual 80s music but has nothing to say. It's a jingle for a very expensive car.", 30),
            ("indie_vibes", None, "BREAK MY SOUL", 2.0,
             "Dance music as corporate motivation speech. 'Release ya anger, release ya mind' over a house groove is not the transcendence BeyoncÃ© thinks it is here.", 25),
            ("classicrock_fan", None, "HUMBLE.", 2.5,
             "The video is more interesting than the song. Drop Kendrick into any era and he'd still be technically gifted; this beat is beneath him.", 40),
        ]

        for args in critical_reviews:
            _rev(*args)

        db.commit()
        print("Critical reviews seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Critical review seed error: {e}")
        raise
    finally:
        db.close()


def seed_song_reviews():
    """Add reviews for individual songs that currently have zero reviews."""
    db = SessionLocal()
    try:
        from . import models as _m

        # Idempotency: check for a marker review unique to this seed
        marker = (
            db.query(_m.Review)
            .join(_m.User)
            .join(_m.Song, _m.Review.song_id == _m.Song.id)
            .filter(
                _m.User.username == "indie_vibes",
                _m.Song.title == "Blank Space",
            )
            .first()
        )
        if marker:
            return

        def _user(username: str) -> _m.User | None:
            return db.query(_m.User).filter(_m.User.username == username).first()

        def _song(title: str) -> _m.Song | None:
            return db.query(_m.Song).filter(_m.Song.title == title).first()

        def _rev(username: str, song_title: str, rating: float, body: str, likes: int = 0):
            u = _user(username)
            s = _song(song_title)
            if not (u and s):
                return
            existing = db.query(_m.Review).filter(
                _m.Review.user_id == u.id,
                _m.Review.song_id == s.id,
            ).first()
            if existing:
                return
            r = _m.Review(
                user_id=u.id,
                song_id=s.id,
                rating=rating,
                text=body,

                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 400)),
            )
            db.add(r)

        song_reviews = [
            # â”€â”€ Taylor Swift â€” 1989 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("musiclover",      "Blank Space",       5.0,
             "The ultimate commentary on tabloid culture wrapped in the best pop production of the decade. That synth hook is still untouchable.", 120),
            ("indie_vibes",     "Blank Space",       3.5,
             "Clever self-aware satire that overstays its welcome by about 90 seconds. The hook is undeniable though.", 45),
            ("pop_princess_p",  "Blank Space",       5.0,
             "Every time I think I'm over this song it pulls me back. The production, the vocal performance, the wit â€” it's all perfect.", 88),
            ("classicrock_fan", "Blank Space",       2.0,
             "The joke lands once. By the fourth listen the self-parody reads as genuine narcissism rather than irony.", 22),

            ("musiclover",      "Style",             4.5,
             "Everything 80s pop aspired to be, distilled into 3:51. The guitar-synth interplay in the chorus is genuinely inspired.", 95),
            ("hiphop_head",     "Style",             4.0,
             "One of her few songs where the production matches the lyrics. Feels cinematic without trying too hard.", 50),
            ("lo_fi_lucia",     "Style",             4.5,
             "Late night driving song forever. The way the outro just breathes â€” she knew exactly what she was doing.", 62),

            ("indie_vibes",     "Bad Blood",         2.5,
             "The Kendrick remix saved it but the original is a grudge anthem with the emotional depth of a bumper sticker.", 38),
            ("dance_floor_dan", "Bad Blood",         4.0,
             "Don't care about the beef, the drop goes off every single time. Instant energy boost.", 55),
            ("classicrock_fan", "Bad Blood",         1.5,
             "Celebrity feud turned into stadium filler. This is everything wrong with 2010s pop dressed up as empowerment.", 30),

            ("pop_princess_p",  "Shake It Off",      4.5,
             "Annoyingly perfect. I have actively tried not to like this song and failed every time. It's just joy in audio form.", 100),
            ("audiophile99",    "Shake It Off",      3.0,
             "The brass arrangement is actually quite good. The rest is sugar rush with a two-minute crash.", 25),
            ("crate_digger",    "Shake It Off",      2.0,
             "Feels engineered by committee to be inoffensive. There's no risk anywhere in this song and it shows.", 18),

            ("lo_fi_lucia",     "Out of the Woods",  4.0,
             "The anxiety encoded in those drums hits different when you've been through it. Underrated in her catalog.", 40),
            ("musiclover",      "Out of the Woods",  4.5,
             "Max Martin and Swift at their synergistic peak. The build in the final chorus is extraordinary.", 72),

            ("indie_vibes",     "Welcome to New York", 2.0,
             "Every city deserves better than a tourist jingle. Completely hollow even by pop standards.", 35),
            ("pop_princess_p",  "Welcome to New York", 3.5,
             "Look, it's a fun opener for what it is. Not everything has to be profound.", 28),

            # â”€â”€ Taylor Swift â€” Folklore â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("lo_fi_lucia",     "the 1",             5.0,
             "The most honest breakup song she's ever written. The understated production is perfect â€” nothing hiding the emotion.", 90),
            ("musiclover",      "the 1",             4.5,
             "That opening guitar is instant atmosphere. Folklore starts exactly right.", 65),
            ("classicrock_fan", "the 1",             3.5,
             "The restraint is admirable. Almost sounds like a real songwriter for a moment.", 20),

            ("hiphop_head",     "the last great american dynasty", 4.0,
             "The storytelling here is genuinely great â€” she disappears into Rebekah's life completely. More of this.", 55),
            ("indie_vibes",     "the last great american dynasty", 4.5,
             "A character study disguised as a folk song. The twist at the end lands perfectly.", 70),
            ("lo_fi_lucia",     "the last great american dynasty", 4.0,
             "This is the Taylor I want all the time. Specific, weird, interested in other people.", 48),

            ("musiclover",      "my tears ricochet",  5.0,
             "Haunting and heavy. The metaphor of attending your own funeral is devastating and she sells it completely.", 80),
            ("rbsoul",          "my tears ricochet",  4.5,
             "The vocal performance alone is worth five stars. Folklore's emotional center.", 58),
            ("audiophile99",    "my tears ricochet",  4.0,
             "The reverb on the piano sits in the mix just right. One of the better-produced tracks on a very well-produced album.", 30),

            ("pop_princess_p",  "seven",              4.5,
             "I ugly cried. The imagery of childhood told through an adult perspective is so delicate.", 75),
            ("lo_fi_lucia",     "seven",              5.0,
             "Devastatingly nostalgic without being cheap about it. 'Please picture me in the weeds' is one of her best lines ever.", 95),
            ("indie_vibes",     "seven",              4.0,
             "Small and intimate and exactly right. One of the few times the whisper-folk trend produced something genuinely moving.", 52),

            ("musiclover",      "august",             5.0,
             "The most atmospheric song on Folklore. Summer encoded in sound â€” warm, slightly faded, aching.", 110),
            ("hiphop_head",     "august",             4.0,
             "Not my usual lane but I understand why people love this. The production is genuinely beautiful.", 45),
            ("lo_fi_lucia",     "august",             5.0,
             "The unofficial anthem of every summer that almost was. She captured that exact bittersweet feeling perfectly.", 130),
            ("crate_digger",    "august",             4.5,
             "The analog warmth in the production sounds lived-in. Bon Iver's influence is all over this and it works.", 60),

            ("indie_vibes",     "this is me trying",  4.5,
             "The most vulnerable she gets on the album. 'I had the shiniest wheels, now they're rusting' is genuinely poetic.", 68),
            ("rbsoul",          "this is me trying",  4.0,
             "Slow burn that rewards patience. A little buried on the album but deserves more attention.", 40),

            # â”€â”€ Taylor Swift â€” Midnights â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("pop_princess_p",  "Lavender Haze",      4.5,
             "The opener Midnights needed. Dreamy and direct at once â€” sets the purple-lit mood perfectly.", 85),
            ("dance_floor_dan", "Lavender Haze",      4.0,
             "Better than Anti-Hero for my money. The groove actually moves.", 50),
            ("indie_vibes",     "Lavender Haze",      3.0,
             "Fine synth-pop but I expect more from the track that leads a Taylor Swift album.", 28),

            ("lo_fi_lucia",     "Maroon",             5.0,
             "The best song on Midnights by a mile. The color metaphor is sustained perfectly throughout and the production is gorgeous.", 95),
            ("musiclover",      "Maroon",             4.5,
             "Introspective and specific in the best Folklore tradition. Should have been the lead single.", 80),
            ("audiophile99",    "Maroon",             4.0,
             "The low-end on this mix is excellent â€” unusual for her productions. The bass sits warmly.", 35),

            ("pop_princess_p",  "Snow on the Beach",  4.0,
             "Lana and Taylor together is exactly what you'd hope. Floaty and romantic.", 65),
            ("indie_vibes",     "Snow on the Beach",  3.5,
             "The collaboration is understated to a fault â€” Lana feels barely there. Still lovely.", 42),
            ("crate_digger",    "Snow on the Beach",  3.0,
             "Pretty enough but the Lana feature is criminally underused. A missed opportunity.", 30),

            ("musiclover",      "Midnight Rain",      4.0,
             "The vocal layering trick at the start is genuinely inventive. Classic Swift storytelling about the road not taken.", 55),
            ("rbsoul",          "Midnight Rain",      4.5,
             "The contrast between the two voices tells the whole story before the lyrics even sink in. Clever and beautiful.", 70),

            ("hiphop_head",     "Karma",              3.5,
             "Fun throwback energy. Not deep but she's not trying to be â€” sometimes a groove is enough.", 40),
            ("dance_floor_dan", "Karma",              4.5,
             "That chorus is a complete earworm and I refuse to apologize for loving it.", 60),
            ("classicrock_fan", "Karma",              1.5,
             "Spite bottled into a pop song and sold as a philosophical statement. Petty dressed as profound.", 25),

            # â”€â”€ The Beatles â€” Abbey Road â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("crate_digger",    "Something",          5.0,
             "The greatest love song ever recorded. Harrison finally stepped out from behind Lennon and McCartney and delivered something transcendent.", 140),
            ("musiclover",      "Something",          5.0,
             "The guitar solo in the middle eight makes me emotional every single time. Fifty years later and nothing has topped it.", 125),
            ("audiophile99",    "Something",          5.0,
             "The stereo mix on the 2019 remix is revelatory â€” you can hear every string individually. A masterclass in orchestral rock arrangement.", 80),

            ("indie_vibes",     "Octopus's Garden",  3.5,
             "Charming and weird in the best Ringo way. Not their deepest but pure joy.", 35),
            ("lo_fi_lucia",     "Octopus's Garden",  4.0,
             "Genuinely fun children's song energy from four of the most famous musicians alive. The playfulness is endearing.", 45),

            ("crate_digger",    "Because",            5.0,
             "Three-part harmony sung backwards over electric harpsichord. Only The Beatles. The most underrated track in their catalog.", 90),
            ("audiophile99",    "Because",            5.0,
             "The vocal arrangement is technically jaw-dropping â€” recorded in three separate passes and stacked nine voices. Breathtaking.", 75),
            ("musiclover",      "Because",            4.5,
             "Abbey Road's hidden masterpiece. It slips by quietly and then haunts you for days.", 65),

            ("hiphop_head",     "You Never Give Me Your Money", 4.5,
             "The Abbey Road medley starts here and it's a perfect opening gambit. McCartney's melodic invention is unreal.", 55),
            ("crate_digger",    "You Never Give Me Your Money", 5.0,
             "The way it dissolves into 'Sun King' mid-song is one of rock music's greatest transitions. Emotionally complex and musically astounding.", 70),

            # â”€â”€ The Beatles â€” Sgt. Pepper's â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("crate_digger",    "Sgt. Pepper's Lonely Hearts Club Band", 4.5,
             "The meta-opening that changed what albums could be. Still sounds like a curtain rising on something entirely new.", 65),
            ("musiclover",      "Sgt. Pepper's Lonely Hearts Club Band", 4.5,
             "Two minutes of pure invention that reframed the band, the era, and the album format simultaneously.", 58),

            ("indie_vibes",     "With a Little Help from My Friends", 5.0,
             "The warmth in this song is something no modern production can replicate. Ringo carrying the whole thing on his shoulders quietly.", 90),
            ("rbsoul",          "With a Little Help from My Friends", 5.0,
             "Universal and specific at the same time. Joe Cocker's version is iconic but this original hits differently.", 80),
            ("crate_digger",    "With a Little Help from My Friends", 5.0,
             "Arguably Ringo's defining moment. The band's support of him here â€” emotionally and literally â€” is touching.", 75),

            ("audiophile99",    "Lucy in the Sky with Diamonds", 4.5,
             "The ADT (Automatic Double Tracking) on Lennon's vocal is one of George Martin's greatest production decisions. Dreamy and precise.", 60),
            ("indie_vibes",     "Lucy in the Sky with Diamonds", 4.5,
             "Pure psychedelia that somehow stays melodic throughout. The waltz-time verses into the 4/4 chorus is a brilliant structural trick.", 55),
            ("classicrock_fan", "Lucy in the Sky with Diamonds", 4.0,
             "Their most hallucinogenic and it holds up. Even if you remove the obvious subtext it's remarkable imagery.", 45),

            ("lo_fi_lucia",     "Getting Better",     4.0,
             "Deceptively simple hook around complicated lyrics about growth and failure. McCartney's optimism against Lennon's darkness.", 40),
            ("musiclover",      "Getting Better",     4.0,
             "The campfire-into-stadium energy makes it feel massive despite the minimal arrangement.", 35),

            # â”€â”€ Kendrick Lamar â€” TPAB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("hiphop_head",     "Wesley's Theory",    5.0,
             "The Parliament-funk foundation is immaculate and the critique of overnight celebrity is sharper here than anywhere else on the album.", 95),
            ("musiclover",      "Wesley's Theory",    4.5,
             "What an opening salvo. The bass line alone tells the whole story of American capitalism.", 70),
            ("crate_digger",    "Wesley's Theory",    5.0,
             "Thundercat and Flying Lotus building that groove is a production miracle. The jazz-funk lineage is honored and transcended.", 85),

            ("hiphop_head",     "Institutionalized",  5.0,
             "Snoop's cameo recontextualizes everything. The internal monologue structure is rap as genuine literary technique.", 88),
            ("indie_vibes",     "Institutionalized",  4.5,
             "The structural choice to repeat the hook as the stakes escalate is devastating. Gets more uncomfortable each time.", 60),

            ("rbsoul",          "u",                  5.0,
             "The most harrowing thing on TPAB. Kendrick attacking himself in the second person for seven minutes â€” uncomfortable and essential.", 100),
            ("audiophile99",    "u",                  4.5,
             "The lo-fi production is intentional â€” it sounds like a hotel room at 3am and that's exactly right.", 65),
            ("hiphop_head",     "u",                  5.0,
             "The vocal performance is genuinely disturbing in the best way. He sounds like he's falling apart and meaning every word.", 110),

            ("musiclover",      "The Blacker the Berry", 5.0,
             "The most direct Kendrick has ever been. The final line recontextualizes the entire track and nothing is the same after.", 120),
            ("hiphop_head",     "The Blacker the Berry", 5.0,
             "The hypocrite thesis hits like a gut punch on every listen. The hardest track on one of rap's hardest albums.", 130),
            ("classicrock_fan", "The Blacker the Berry", 3.5,
             "Technically impressive and uncomfortable in ways I think are intentional. The aggression is earned here.", 30),

            # â”€â”€ Kendrick Lamar â€” DAMN. â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("hiphop_head",     "BLOOD.",             4.5,
             "The fox news sample sets up the whole album's thesis in under a minute. One of the great album openers.", 70),
            ("musiclover",      "BLOOD.",             4.5,
             "All the clues are here on the first listen and you don't realize it until the end. Genius sequencing.", 65),

            ("hiphop_head",     "DNA.",               5.0,
             "Mike Will Made-It's production flip mid-track is one of rap's great structural moments. Kendrick weaponizing contrast.", 140),
            ("indie_vibes",     "DNA.",               4.5,
             "The first 30 seconds alone justify the album's existence. Ferocious and precise.", 85),
            ("classicrock_fan", "DNA.",               4.0,
             "I won't pretend I understand all the references but the controlled aggression is undeniable.", 35),

            ("musiclover",      "YAH.",               4.5,
             "Deliberate deceleration after DNA. The Bono quote lands exactly as intended. Structural mastery.", 55),
            ("crate_digger",    "YAH.",               4.0,
             "The sequencing choice to follow DNA with this is brilliant. The album breathing.", 45),

            ("hiphop_head",     "ELEMENT.",           5.0,
             "The James Blake-assisted beat is gorgeous and Kendrick matches it line for line. Every bar is earned.", 95),
            ("rbsoul",          "ELEMENT.",           4.5,
             "The spiritual weight this carries given what followed it in real life is extraordinary.", 70),

            ("indie_vibes",     "LOVE.",              4.5,
             "The most accessible track on the album and still has more going on than most artists' entire catalogs.", 80),
            ("pop_princess_p",  "LOVE.",              4.5,
             "Zacari's hook is perfect. This song makes me feel things I'm not ready to explain.", 75),
            ("dance_floor_dan", "LOVE.",              5.0,
             "The groove on LOVE. goes deeper than anything on the radio that year. I've played this a thousand times.", 60),

            # â”€â”€ Radiohead â€” OK Computer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("indie_vibes",     "Airbag",             5.0,
             "The scratchy drum loop intro that opens OK Computer is one of rock's great entrances. Regeneration as album opener â€” perfect.", 85),
            ("audiophile99",    "Airbag",             5.0,
             "Jonny Greenwood's guitar is a full orchestra in this recording. The layering is staggering.", 70),
            ("crate_digger",    "Airbag",             5.0,
             "The Afrobeat drum loop under the tremolo guitar is the most inventive rhythm arrangement in rock of the 90s.", 90),

            ("musiclover",      "Subterranean Homesick Alien", 4.5,
             "The album's most underrated track. Thom's falsetto over that floating bass line is deeply melancholic.", 55),
            ("indie_vibes",     "Subterranean Homesick Alien", 4.5,
             "Alienation as genuine experience rather than teenage pose. The stars-as-film metaphor is beautiful.", 60),

            ("lo_fi_lucia",     "Exit Music (For a Film)", 5.0,
             "Starts as a whisper and ends as a scream. The build over five minutes is one of the most emotionally precise things in their catalog.", 100),
            ("musiclover",      "Exit Music (For a Film)", 5.0,
             "The Juliet and Romeo context makes it unbearably sad. Even without it, it's extraordinary.", 85),
            ("audiophile99",    "Exit Music (For a Film)", 5.0,
             "The transition from acoustic fingerpicking to the distorted organ crash is perfectly timed. Production is flawless.", 75),

            ("crate_digger",    "No Surprises",       5.0,
             "A song about resignation that sounds like a lullaby. The dissonance between form and content is the whole point.", 95),
            ("lo_fi_lucia",     "No Surprises",       5.0,
             "The glockenspiel melody is deceptively simple. This song has comforted and haunted me in equal measure.", 110),
            ("indie_vibes",     "No Surprises",       5.0,
             "Career-best vocal performance from Thom. Quiet and devastating.", 90),

            # â”€â”€ Radiohead â€” Kid A â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("indie_vibes",     "Kid A",              5.0,
             "The title track sets the tone for the whole album â€” deliberately inhuman, deliberately beautiful. Electronic music's anxious soul.", 88),
            ("audiophile99",    "Kid A",              5.0,
             "The ondes martenot processed through those effects is unlike anything in rock music. A genuinely new sound.", 75),
            ("crate_digger",    "Kid A",              5.0,
             "Radiohead erasing themselves and becoming something entirely new. The courage of this is still staggering.", 95),

            ("musiclover",      "The National Anthem", 5.0,
             "The jazz-chaos at the end sounds like the world falling apart in real time. One of the great album tracks in any genre.", 100),
            ("hiphop_head",     "The National Anthem", 4.5,
             "The rhythm section here is insane â€” the bass is the lead instrument and Thom's vocals are percussion. Genuinely weird in the best way.", 65),

            ("lo_fi_lucia",     "How to Disappear Completely", 5.0,
             "The song that lives in the dark at 3am. The string arrangement is like drowning slowly and it's perfect.", 120),
            ("indie_vibes",     "How to Disappear Completely", 5.0,
             "'That there, that's not me' â€” delivered with total conviction over the most beautiful arrangement on Kid A.", 105),
            ("audiophile99",    "How to Disappear Completely", 5.0,
             "Jonny Greenwood's orchestration here is his masterwork. Every instrument enters at exactly the right moment.", 85),

            ("musiclover",      "Optimistic",         4.5,
             "The only 'rock' song on Kid A and it sounds alien because of what surrounds it. The dinosaur imagery is perfect.", 60),
            ("crate_digger",    "Optimistic",         4.5,
             "The groove on this song sits in perfect tension between hope and dread. 'You can try the best you can' hits differently every time.", 65),

            # â”€â”€ Frank Ocean â€” Blonde â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("rbsoul",          "Nikes",              5.0,
             "The pitch-shifted intro is still jarring and still perfect. Blonde announces itself as something entirely new in the first 30 seconds.", 120),
            ("indie_vibes",     "Nikes",              5.0,
             "Grief album opener that sounds like a dream. The R&B dissolving into ambient at the end is breathtaking.", 95),
            ("lo_fi_lucia",     "Nikes",              5.0,
             "The most beautiful sad song of the 2010s. Full stop.", 140),
            ("musiclover",      "Nikes",              5.0,
             "The writing in those verses is poetry. The production lets every word land.", 100),

            ("rbsoul",          "Ivy",                5.0,
             "The guitar tone alone is worth the album purchase. A perfect nostalgic crush song that never overstays its welcome.", 110),
            ("lo_fi_lucia",     "Ivy",                5.0,
             "'I thought that I was dreaming when you said you loved me' is the most beautiful lyric on Blonde.", 130),
            ("crate_digger",    "Ivy",                4.5,
             "The lo-fi guitar recording feels genuinely intimate â€” like a demo he decided was already finished.", 80),
            ("indie_vibes",     "Ivy",                5.0,
             "First love rendered in sound. The simplicity is devastating.", 95),

            ("musiclover",      "Solo",               5.0,
             "The organ and the vocal are all you need. Seven minutes of introspection that never once drags.", 90),
            ("audiophile99",    "Solo",               5.0,
             "A church organ as the sole instrument for seven minutes. The bravery to do nothing else is extraordinary.", 80),
            ("rbsoul",          "Solo",               5.0,
             "Gospel without religion. Frank finding grace in heartbreak over an organ that sounds like it's breathing.", 115),

            # â”€â”€ Frank Ocean â€” channel ORANGE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("rbsoul",          "Sierra Leone",        4.5,
             "The opening skit into this beat drop is perfectly executed. Frank's stream of consciousness here is hypnotic.", 65),
            ("musiclover",      "Sierra Leone",        4.5,
             "Lush and disorienting in the best way. The Pharrell influence is clear but Frank makes it his own.", 55),

            ("indie_vibes",     "Sweet Life",          4.5,
             "The most approachable track on channel ORANGE and a genuine bop. The 'why see the world' lyric is both critique and celebration.", 70),
            ("pop_princess_p",  "Sweet Life",          5.0,
             "This is the song that got me into Frank Ocean and I'll never stop being grateful. Absolute summer perfection.", 90),
            ("rbsoul",          "Sweet Life",          5.0,
             "The groove on this is deceptively simple â€” Phil Collins sample flipped into something completely fresh.", 80),

            ("crate_digger",    "Lost",                4.5,
             "The production has this weightless quality â€” everything slightly delayed, slightly soft. The drugs narrative feels observed, not glamorized.", 55),
            ("musiclover",      "Lost",                4.5,
             "One of the most sonically interesting tracks on channel ORANGE. The mix has this hazy warmth that matches the subject matter.", 50),

            ("hiphop_head",     "Pyramids",            5.0,
             "Two-part R&B epic that compresses thousands of years of Black history into ten minutes. John Mayer's guitar in the second half is astonishing.", 150),
            ("rbsoul",          "Pyramids",            5.0,
             "The shift from ancient Egypt to modern-day strip club is one of music's great structural moves. Devastating and funky.", 140),
            ("audiophile99",    "Pyramids",            4.5,
             "The transition between the two halves is a production masterclass. The way the tempo shifts but the groove remains is technically superb.", 90),
            ("crate_digger",    "Pyramids",            5.0,
             "John Mayer has never sounded better than here. Frank drew something out of him that his own records never managed.", 120),

            ("indie_vibes",     "Bad Religion",        5.0,
             "Three minutes of the most concentrated heartbreak in R&B. The taxi cab setting is perfect â€” trapped and moving simultaneously.", 110),
            ("rbsoul",          "Bad Religion",        5.0,
             "He communicates unrequited love and religious crisis simultaneously without ever straining for the metaphor. Effortless genius.", 130),
            ("lo_fi_lucia",     "Bad Religion",        5.0,
             "The string arrangement in the final section makes me cry every single time. Hauntingly beautiful.", 95),

            # â”€â”€ BeyoncÃ© â€” Lemonade â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("pop_princess_p",  "Hold Up",             5.0,
             "The most fun song about infidelity ever made. The 'Becky with the good hair' era started here and I lived for every second.", 130),
            ("rbsoul",          "Hold Up",             5.0,
             "This is BeyoncÃ© at her most joyful and most dangerous simultaneously. The production is immaculate.", 115),
            ("bey_hive",        "Hold Up",             5.0,
             "She is literally smashing cars with a bat while sampling 'Maps' by Yeah Yeah Yeahs and it somehow works perfectly.", 140),
            ("indie_vibes",     "Hold Up",             4.0,
             "The Yeah Yeah Yeahs sample is inspired and BeyoncÃ©'s delivery is playful in a way she rarely allows herself.", 55),

            ("bey_hive",        "Don't Hurt Yourself",  5.0,
             "Jack White and BeyoncÃ© is the collaboration nobody predicted and everybody needed. The rage is authentic.", 120),
            ("rbsoul",          "Don't Hurt Yourself",  4.5,
             "The Led Zeppelin sample choice is perfect. The blues-rock fury fits the anger better than any R&B beat would.", 80),
            ("classicrock_fan", "Don't Hurt Yourself",  4.0,
             "The Zeppelin interpolation is good and BeyoncÃ©'s voice in this register is genuinely powerful. One of her better moments.", 35),

            ("bey_hive",        "Sorry",               5.0,
             "The most quotable BeyoncÃ© song in decades. The 'middle fingers up' energy is earned and the production is cold perfection.", 135),
            ("pop_princess_p",  "Sorry",               5.0,
             "This song made 'boy bye' a cultural moment and I'm grateful every day. The production switch in the second verse is inspired.", 110),
            ("hiphop_head",     "Sorry",               4.5,
             "The reggaeton-adjacent production is a smart choice â€” it feels casual about the devastation, which is the whole point.", 65),

            ("rbsoul",          "Love Drought",        5.0,
             "The most underrated track on Lemonade. The minimalist production lets her vocal performance carry everything and it absolutely does.", 75),
            ("lo_fi_lucia",     "Love Drought",        4.5,
             "The longing in this song is almost unbearable. The call-and-response structure between her voice and the keys is beautiful.", 60),
            ("bey_hive",        "Love Drought",        5.0,
             "Everything the discourse focuses on the other tracks misses how quietly devastating this one is. Perfect.", 85),

            # â”€â”€ BeyoncÃ© â€” Renaissance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("dance_floor_dan", "CUFF IT",             5.0,
             "The smoothest disco revival of the decade. This song makes every room better just by existing in it.", 120),
            ("pop_princess_p",  "CUFF IT",             5.0,
             "A flawless funk production that sounds effortless. I've danced to this more times than I can count.", 110),
            ("bey_hive",        "CUFF IT",             5.0,
             "This song is pure joy and competence. The bridge is the best 30 seconds of 2022.", 130),

            ("bey_hive",        "ALIEN SUPERSTAR",     5.0,
             "Completely unhinged in the best possible way. 'I'm one of one, I'm number one' is delivered with absolute conviction.", 100),
            ("dance_floor_dan", "ALIEN SUPERSTAR",     4.5,
             "The interpolation of 'Unique' by Unique is so well placed. She claimed that reference perfectly.", 70),
            ("audiophile99",    "ALIEN SUPERSTAR",     3.5,
             "The mix is optimized for maximum aggression on a club system and it works in context. Exhausting on headphones.", 25),

            ("rbsoul",          "VIRGO'S GROOVE",      5.0,
             "Seven minutes of immaculate groove music. The extended dance break section is everything I want from a BeyoncÃ© album.", 90),
            ("dance_floor_dan", "VIRGO'S GROOVE",      5.0,
             "This is the center of Renaissance and it's perfect. The production is deep and patient in a way pop music rarely allows.", 85),
            ("lo_fi_lucia",     "VIRGO'S GROOVE",      4.5,
             "The most soulful moment on the album. Quiet luxury in sound form.", 65),

            ("bey_hive",        "CHURCH GIRL",         5.0,
             "Church girl by day and then that drop happens. The sample flip is inspired and she's having the time of her life.", 95),
            ("dance_floor_dan", "CHURCH GIRL",         5.0,
             "The Big Freedia feature is perfect casting. The release when that bassline hits is genuinely cathartic.", 80),
            ("hiphop_head",     "CHURCH GIRL",         4.0,
             "The sample choice is clever and the energy is infectious. Gets better every listen.", 50),

            # â”€â”€ The Weeknd â€” After Hours â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("synth_wave_kid",  "Alone Again",         5.0,
             "The most cinematic track on After Hours. The 80s synth atmosphere is immaculate and the vocal is devastating.", 90),
            ("rbsoul",          "Alone Again",         4.5,
             "The album opens in the dark and this song is a perfect first step. Production is stunningly detailed.", 65),
            ("lo_fi_lucia",     "Alone Again",         4.0,
             "The despair feels genuine here in a way that some later tracks on the album lose. A strong start.", 50),

            ("indie_vibes",     "Too Late",            4.0,
             "Underrated deep cut. The production is more interesting than the singles and the story it tells is darker.", 40),
            ("synth_wave_kid",  "Too Late",            4.5,
             "The cold electronic production suits the subject matter perfectly. A slow burn that rewards attention.", 55),

            ("rbsoul",          "Hardest to Love",     4.5,
             "The falsetto performance on this track is genuinely stunning. One of his purest vocal moments on the album.", 70),
            ("pop_princess_p",  "Hardest to Love",     4.5,
             "The production strip-down here is effective â€” everything stripped back to let the voice carry the weight.", 60),

            ("dance_floor_dan", "In Your Eyes",        5.0,
             "The Daft Punk influence is clear and it's perfect. The extended outro was made to be danced to alone at midnight.", 95),
            ("synth_wave_kid",  "In Your Eyes",        5.0,
             "Ideologically the best 80s pastiche of the After Hours era. The saxophone outro â€” I lose my mind every time.", 100),
            ("pop_princess_p",  "In Your Eyes",        4.5,
             "The Paris Jackson cameo in the video aside, this song stands completely alone. Gorgeous production.", 75),

            ("audiophile99",    "Until I Bleed Out",   4.0,
             "The closing track's industrial noise sections are genuinely unnerving in a good way. A brave album closer.", 45),
            ("synth_wave_kid",  "Until I Bleed Out",   4.5,
             "The production collapse at the end of After Hours is the right choice. Everything falls apart exactly as it should.", 55),

            # â”€â”€ The Weeknd â€” Starboy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("dance_floor_dan", "Starboy",             4.5,
             "The title track delivers. Daft Punk's fingerprints are all over the groove and it's irresistible.", 80),
            ("synth_wave_kid",  "Starboy",             5.0,
             "The sonic bridge between House of Balloons-era dark R&B and mainstream pop. He earned this crossover.", 90),
            ("hiphop_head",     "Starboy",             4.0,
             "The Daft Punk collab elevates this above the average Weeknd single. The groove is undeniable.", 55),

            ("synth_wave_kid",  "False Alarm",         4.0,
             "The rock direction here was unexpected and it mostly works. The adrenaline rush of the album's most energetic track.", 50),
            ("indie_vibes",     "False Alarm",         3.5,
             "The guitar-forward production is interesting for him but feels out of place on the album. Bold experiment.", 30),

            ("pop_princess_p",  "I Feel It Coming",    5.0,
             "The smoothest song on Starboy. The Daft Punk production is warm and Weeknd's falsetto is at its most beautiful.", 110),
            ("rbsoul",          "I Feel It Coming",    5.0,
             "Pure 80s R&B joy. The collaboration is seamless â€” this sounds like a lost Off the Wall track.", 100),
            ("dance_floor_dan", "I Feel It Coming",    5.0,
             "You cannot make a bad playlist and include this song. It improves everything around it.", 95),

            ("synth_wave_kid",  "Secrets",             4.0,
             "Underrated deep cut. The Weeknd in confessional mode with a production that supports rather than overwhelms.", 45),
            ("rbsoul",          "Secrets",             4.5,
             "The disco bass line and the dark lyrics create a perfect tension. His best album track on Starboy.", 60),

            # â”€â”€ Tyler, the Creator â€” IGOR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("tyler_fan_2019",  "IGOR'S THEME",        5.0,
             "The curtain rising on his most ambitious project. The choral arrangement tells you immediately this is different.", 95),
            ("indie_vibes",     "IGOR'S THEME",        4.5,
             "Two minutes of pure atmosphere-setting. The abrupt cut into I THINK is perfectly jarring.", 65),

            ("tyler_fan_2019",  "I THINK",             5.0,
             "The guitar loop is absurdly catchy and the lyrics underneath are doing heavy emotional work. This song has layers.", 110),
            ("pop_princess_p",  "I THINK",             4.5,
             "The most accessible track on IGOR and still more interesting than most things released that year.", 75),
            ("rbsoul",          "I THINK",             4.5,
             "The longing in this song is devastating. Tyler making the prettiest music about the most painful things.", 80),

            ("tyler_fan_2019",  "GONE GONE / THANK YOU", 5.0,
             "The album's emotional climax. The transition from GONE GONE's aggression to THANK YOU's acceptance is one of the decade's great musical moments.", 130),
            ("indie_vibes",     "GONE GONE / THANK YOU", 5.0,
             "The two-part structure mirrors the emotional stages of the album perfectly. The gentle piano outro is heartbreaking.", 100),
            ("rbsoul",          "GONE GONE / THANK YOU", 5.0,
             "Pharrell's influence on the THANK YOU section is profound â€” Tyler learned everything about emotional restraint from him.", 90),

            ("tyler_fan_2019",  "ARE WE STILL FRIENDS?", 5.0,
             "The strings at the end of IGOR are some of the most emotionally overwhelming production choices in recent memory. A perfect album closer.", 120),
            ("crate_digger",    "ARE WE STILL FRIENDS?", 5.0,
             "This samples a soul deep cut with such reverence it feels like Tyler processing his own emotional history.", 85),

            # â”€â”€ Tyler, the Creator â€” Flower Boy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("tyler_fan_2019",  "Foreword",            4.5,
             "Rex Orange County's voice is the perfect gentle opener for Flower Boy. It sets the sun-drenched melancholy of the whole album.", 70),
            ("indie_vibes",     "Foreword",            4.5,
             "The most hopeful Tyler has ever sounded. The warmth is earned because you can hear the effort behind it.", 65),

            ("tyler_fan_2019",  "Garden Shed",         5.0,
             "Tyler coming out between the lines â€” the autobiographical reading of this song is everything.", 115),
            ("rbsoul",          "Garden Shed",         5.0,
             "The soft guitar arrangement makes the vulnerability in the lyrics feel safe to exist. A masterpiece of tonal control.", 90),
            ("lo_fi_lucia",     "Garden Shed",         5.0,
             "The most important song he's ever recorded. He sounds so relieved.", 110),

            ("tyler_fan_2019",  "Boredom",             4.5,
             "Bored but beautifully so. Corinne Bailey Rae on the hook is perfect casting â€” that combination of voices is stunning.", 80),
            ("indie_vibes",     "Boredom",             4.5,
             "The horn arrangement in the second half transforms the song completely. Summer boredom rendered as something almost transcendent.", 70),

            ("tyler_fan_2019",  "911 / Mr. Lonely",    5.0,
             "The genre transition is the album in miniature â€” from defensive humor to real vulnerability. Incredible.", 130),
            ("indie_vibes",     "911 / Mr. Lonely",    5.0,
             "The shift from the synth-punk 911 to the orchestral Mr. Lonely is the most daring thing on Flower Boy.", 110),
            ("rbsoul",          "911 / Mr. Lonely",    4.5,
             "The Steve Lacy and Anna of the North features make the second half feel like a dream sequence. The contrast is perfect.", 85),

            ("lo_fi_lucia",     "November",            5.0,
             "The most beautiful track on Flower Boy. Pure nostalgia rendered with complete musical precision.", 100),
            ("tyler_fan_2019",  "November",            5.0,
             "This song makes me feel like I'm watching my best days through a window. Painfully beautiful.", 115),

            # â”€â”€ Billie Eilish â€” WWAFAWDWG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("gen_z_ears",      "wish you were gay",   4.0,
             "The concept is messy but executed with enough charm that I can't stay annoyed at it. The bridge is legitimately great.", 55),
            ("indie_vibes",     "wish you were gay",   3.5,
             "She's working through something real here and the song is better for the specificity even if the framing is imperfect.", 40),

            ("lo_fi_lucia",     "when the party's over", 5.0,
             "One of the most emotionally restrained songs of the decade. The minimal production lets the heartbreak breathe.", 120),
            ("gen_z_ears",      "when the party's over", 5.0,
             "This is the song that made me pay attention. Nothing but voice and piano and it's devastating.", 110),
            ("rbsoul",          "when the party's over", 4.5,
             "The vocal performance here is extraordinary for someone so young. Pure emotion, no artifice.", 85),

            ("gen_z_ears",      "bury a friend",        5.0,
             "The monster-under-the-bed concept is executed so perfectly it still unnerves me. FINNEAS's production is genuinely scary.", 100),
            ("indie_vibes",     "bury a friend",        4.5,
             "The production choices here â€” dental drill, bass drops that feel physically threatening â€” are innovative in a pop context.", 75),
            ("audiophile99",    "bury a friend",        4.5,
             "This is the production showcase of the album. The low frequencies are engineered to create genuine unease.", 60),

            ("gen_z_ears",      "all the good girls go to hell", 4.0,
             "The Ariana Grande meets Nine Inch Nails energy is an odd pitch and it almost completely works.", 50),
            ("dance_floor_dan", "all the good girls go to hell", 4.0,
             "The industrial pop approach here is genuinely effective. More danceable than people give it credit for.", 40),

            ("lo_fi_lucia",     "8",                   5.0,
             "The ukulele closer is tender and sad in ways the rest of the album doesn't reach for. Her most honest vocal moment.", 90),
            ("gen_z_ears",      "8",                   4.5,
             "She sounds seventeen in the best possible way on this track. Vulnerable and searching.", 70),

            # â”€â”€ Billie Eilish â€” HIT ME HARD AND SOFT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("gen_z_ears",      "LUNCH",               5.0,
             "She's never been this direct about desire and the playful production matches it perfectly. A genuinely fun song.", 100),
            ("pop_princess_p",  "LUNCH",               5.0,
             "The lesbian anthem I didn't know I needed until I heard it. The confidence she delivers this with is infectious.", 120),
            ("indie_vibes",     "LUNCH",               4.5,
             "The breezy production is a deliberate contrast to the rest of her catalog and it works beautifully.", 75),

            ("lo_fi_lucia",     "CHIHIRO",             5.0,
             "The Spirited Away reference plus that emotionally overwhelming bridge â€” this is the best song she's ever recorded.", 135),
            ("gen_z_ears",      "CHIHIRO",             5.0,
             "The production build in the second half gives me chills every time. The most cinematic moment on the album.", 115),
            ("rbsoul",          "CHIHIRO",             5.0,
             "The way the song transforms in the final third is breathtaking. FINNEAS's production at its absolute peak.", 100),

            ("indie_vibes",     "THE GREATEST",        4.5,
             "A direct challenge to the people who wrote her off after the first album. The production is confident and mature.", 70),
            ("gen_z_ears",      "THE GREATEST",        5.0,
             "This song makes me feel seen in a way I'm not comfortable explaining. The bridge broke me.", 90),

            ("lo_fi_lucia",     "WILDFLOWER",          5.0,
             "The most bittersweet song on an already bittersweet album. The piano melody is devastating in its simplicity.", 85),
            ("pop_princess_p",  "WILDFLOWER",          4.5,
             "This is the track that earns all the album's emotional heft. The restraint here is extraordinary.", 70),

            # â”€â”€ Daft Punk â€” Random Access Memories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("crate_digger",    "Give Life Back to Music", 5.0,
             "The best way to open an album about the power of music. The Nile Rodgers guitar is pure joy and the statement of intent is clear.", 90),
            ("dance_floor_dan", "Give Life Back to Music", 5.0,
             "The bass line alone is a reason to own good speakers. Daft Punk reminding everyone why they matter.", 80),

            ("audiophile99",    "Giorgio by Moroder",   5.0,
             "A ten-minute history of electronic music through one man's voice and an increasingly complex synthesizer arrangement. Technically extraordinary.", 100),
            ("crate_digger",    "Giorgio by Moroder",   5.0,
             "For anyone who loves the history of electronic music, this track is essential. Moroder's monologue is sacred text.", 115),
            ("hiphop_head",     "Giorgio by Moroder",   3.5,
             "I respect it enormously and I've listened to it maybe twice all the way through. It's a museum piece.", 30),

            ("dance_floor_dan", "Within",              4.5,
             "The most beautiful slow moment on a relentlessly propulsive album. Chilly Gonzales's piano playing is exquisite.", 55),
            ("rbsoul",          "Within",              4.5,
             "A reminder that underneath all the ambition, RAM has genuine emotional depth. This song is quietly lovely.", 60),

            ("dance_floor_dan", "Instant Crush",       5.0,
             "Julian Casablancas sounds better here than on any Strokes album. The melancholy is enormous and the groove is perfect.", 95),
            ("indie_vibes",     "Instant Crush",       5.0,
             "The chorus is one of the decade's great pop moments. Casablancas's filtered vocal adds texture that a cleaner take would have lost.", 90),
            ("lo_fi_lucia",     "Instant Crush",       4.5,
             "Late night sadness with a four-on-the-floor heartbeat. This song understands something about longing.", 75),

            ("dance_floor_dan", "Lose Yourself to Dance", 5.0,
             "The closest thing to a perfect disco track recorded in the 21st century. Nile Rodgers in a time machine.", 110),
            ("pop_princess_p",  "Lose Yourself to Dance", 5.0,
             "Pharrell's presence makes this feel like the missing link between French Touch and contemporary R&B. Endlessly joyful.", 95),

            # â”€â”€ Daft Punk â€” Discovery â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ("dance_floor_dan", "Aerodynamic",         5.0,
             "The guitar solo that emerges from the filtered house is one of electronic music's great moments. Human emotion inside a machine.", 100),
            ("audiophile99",    "Aerodynamic",         5.0,
             "The frequency filtering on that guitar solo is technically brilliant â€” the way it opens up in the mix is perfectly engineered.", 80),
            ("crate_digger",    "Aerodynamic",         5.0,
             "Daft Punk proving that guitar heroism has a place in electronic music. The solo is genuinely moving.", 90),

            ("dance_floor_dan", "Voyager",             4.5,
             "The most underrated track on Discovery. The warm bass line and the bright arpeggios create something genuinely euphoric.", 65),
            ("lo_fi_lucia",     "Voyager",             5.0,
             "Late night driving at 140 BPM. The synth melody is one of the most joyful things in their catalog.", 80),
            ("pop_princess_p",  "Voyager",             4.5,
             "Discovery's hidden gem. The energy is pure and the production has aged better than most of the decade around it.", 60),
        ]

        for username, song_title, rating, body, likes in song_reviews:
            _rev(username, song_title, rating, body, likes)

        db.commit()
        print("Song reviews seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Song review seed error: {e}")
        raise
    finally:
        db.close()
