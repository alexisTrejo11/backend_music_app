# 🎵 Music Streaming API

A comprehensive music streaming platform API built with Django and GraphQL, inspired by Spotify. This robust system handles artists, albums, songs, playlists, user interactions, and personalized recommendations.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![GraphQL](https://img.shields.io/badge/GraphQL-Enabled-E10098.svg)](https://graphql.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [GraphQL API](#-graphql-api)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Future Implementations](#-future-implementations)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Functionality

- **User Management**

  - Authentication with JWT tokens
  - Social authentication (Google, Facebook, Spotify)
  - User profiles with avatars and bios
  - Subscription tiers (Free, Premium, Family, Student)
  - User preferences and settings
  - Email verification and password recovery

- **Music Library**

  - Artists with detailed profiles and social links
  - Albums with metadata (ISRC, UPC, copyright)
  - Songs with audio features (tempo, energy, danceability)
  - Featured artists and collaborations
  - Genre hierarchy with parent-child relationships
  - Multi-language support

- **Playlists**

  - User-created playlists
  - Collaborative playlists
  - Editorial/curated playlists
  - Playlist followers and sharing
  - Ordered track listings
  - Auto-generated cover images

- **User Interactions**

  - Listening history with playback analytics
  - Like/unlike songs
  - Follow artists and users
  - Save albums
  - Rate and review albums/songs
  - Share functionality

- **Discovery & Recommendations**

  - Personalized radio stations
  - Algorithm-based recommendations
  - User taste profiling
  - Similar artists/songs suggestions
  - Trending charts (daily, weekly, all-time)
  - Genre-based discovery

- **Search**

  - Full-text search with Elasticsearch
  - Advanced filtering (genre, year, mood, language)
  - Autocomplete suggestions
  - Search history

- **Analytics**
  - Play count tracking
  - Monthly listeners statistics
  - User engagement metrics
  - Artist popularity rankings

### Advanced Features

- Real-time notifications (WebSocket)
- Audio streaming with quality selection
- Lyrics display
- Queue management
- Crossfade and gapless playback support
- Offline mode (download for premium users)
- Social features (user profiles, following)
- Content moderation tools
- Admin dashboard with analytics

## 🛠 Tech Stack

### Backend

- **Framework**: Django 5.0+
- **API**: GraphQL (Graphene-Django)
- **Database**: PostgreSQL 15+
- **Cache**: Redis
- **Task Queue**: Celery with Redis broker
- **Search**: Elasticsearch 8.0+
- **Storage**: AWS S3 (via django-storages)
- **Authentication**: JWT, OAuth2, Social Auth

### Additional Tools

- **Audio Processing**: Mutagen, PyDub
- **Image Processing**: Pillow, ImageKit
- **Machine Learning**: scikit-learn (recommendations)
- **Payments**: Stripe
- **Monitoring**: Sentry
- **WebSockets**: Django Channels
- **Email**: Django Anymail
- **Testing**: Pytest, Factory Boy

## 📁 Project Structure

```
music_api/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Base settings
│   │   ├── development.py       # Dev environment
│   │   ├── production.py        # Production environment
│   │   └── testing.py           # Test environment
│   ├── urls.py                  # Root URL configuration
│   ├── schema.py                # Root GraphQL schema
│   ├── wsgi.py
│   └── asgi.py                  # ASGI for WebSocket
│
├── apps/
│   ├── users/
│   │   ├── models.py            # User, UserPreferences
│   │   ├── schema.py            # GraphQL queries/mutations
│   │   ├── managers.py          # Custom managers
│   │   ├── services.py          # Business logic
│   │   ├── tasks.py             # Celery tasks
│   │   └── tests/
│   │
│   ├── artists/
│   │   ├── models.py            # Artist, ArtistMember
│   │   ├── schema.py
│   │   ├── services.py
│   │   ├── signals.py           # Django signals
│   │   └── tests/
│   │
│   ├── music/
│   │   ├── models.py            # Genre, Album, Song
│   │   ├── schema.py
│   │   ├── services.py
│   │   ├── audio_utils.py       # Audio processing
│   │   ├── metadata_extractor.py
│   │   └── tests/
│   │
│   ├── playlists/
│   │   ├── models.py            # Playlist, PlaylistSong
│   │   ├── schema.py
│   │   ├── services.py
│   │   └── tests/
│   │
│   ├── interactions/
│   │   ├── models.py            # Likes, Follows, History, Reviews
│   │   ├── schema.py
│   │   ├── services.py
│   │   ├── analytics.py         # Analytics functions
│   │   └── tests/
│   │
│   ├── recommendations/
│   │   ├── models.py            # UserTaste, Radio
│   │   ├── schema.py
│   │   ├── engine.py            # Recommendation algorithms
│   │   ├── ml_models.py         # ML-based recommendations
│   │   └── tests/
│   │
│   ├── search/
│   │   ├── documents.py         # Elasticsearch documents
│   │   ├── indices.py           # Index definitions
│   │   ├── schema.py
│   │   └── tests/
│   │
│   ├── notifications/
│   │   ├── models.py            # Notification
│   │   ├── consumers.py         # WebSocket consumers
│   │   ├── schema.py
│   │   └── tests/
│   │
│   ├── subscriptions/
│   │   ├── models.py            # Subscription, Payment
│   │   ├── schema.py
│   │   ├── stripe_handlers.py   # Stripe integration
│   │   └── tests/
│   │
│   └── core/
│       ├── models.py            # Abstract base models
│       ├── mixins.py            # Reusable mixins
│       ├── permissions.py       # GraphQL permissions
│       ├── validators.py        # Custom validators
│       ├── utils.py             # Helper functions
│       └── exceptions.py        # Custom exceptions
│
├── media/                       # Local media files (dev)
│   ├── songs/
│   ├── images/
│   └── covers/
│
├── static/                      # Static files
├── templates/                   # Email templates
├── logs/                        # Application logs
├── docs/                        # Additional documentation
│   ├── api.md                   # API documentation
│   ├── architecture.md          # Architecture decisions
│   └── deployment.md            # Deployment guide
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── testing.txt
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── scripts/
│   ├── setup.sh                 # Initial setup script
│   ├── seed_data.py            # Seed database
│   └── deploy.sh               # Deployment script
│
├── .env.example                 # Environment variables template
├── .gitignore
├── pytest.ini                   # Pytest configuration
├── pyproject.toml              # Black, isort config
├── manage.py
└── README.md
```

## 🗄 Database Schema

### Core Entities

#### Users

```
User
├── id (PK)
├── email (unique)
├── username (unique)
├── password (hashed)
├── profile_image
├── bio
├── birth_date
├── country
├── is_artist
├── is_verified
├── subscription_type (free/premium/family/student)
├── subscription_start
├── subscription_end
├── created_at
└── updated_at

UserPreferences
├── id (PK)
├── user_id (FK → User)
├── explicit_content
├── autoplay
├── audio_quality (low/normal/high)
├── language
└── private_session
```

#### Artists

```
Artist
├── id (PK)
├── name
├── slug (unique)
├── bio
├── profile_image
├── cover_image
├── verified
├── monthly_listeners
├── website
├── social_links (spotify, instagram, twitter)
├── country
├── genres (M2M → Genre)
├── created_at
└── updated_at

ArtistMember
├── id (PK)
├── artist_id (FK → Artist)
├── name
├── role
├── image
├── join_date
└── leave_date
```

#### Music

```
Genre
├── id (PK)
├── name (unique)
├── slug (unique)
├── description
└── parent_id (FK → Genre, self-referencing)

Album
├── id (PK)
├── title
├── slug
├── artist_id (FK → Artist)
├── album_type (album/single/ep/compilation)
├── release_date
├── cover_image
├── description
├── label
├── total_duration
├── total_tracks
├── play_count
├── is_explicit
├── copyright
├── upc
├── created_at
└── updated_at

Song
├── id (PK)
├── title
├── slug
├── artist_id (FK → Artist)
├── album_id (FK → Album)
├── featured_artists (M2M → Artist)
├── audio_file
├── audio_url
├── duration
├── track_number
├── disc_number
├── isrc
├── lyrics
├── is_explicit
├── genre_id (FK → Genre)
├── mood
├── language
├── play_count
├── like_count
├── Audio Features:
│   ├── tempo (BPM)
│   ├── key
│   ├── energy (0-1)
│   ├── danceability (0-1)
│   └── valence (0-1)
├── created_at
└── updated_at
```

#### Playlists

```
Playlist
├── id (PK)
├── name
├── slug
├── description
├── user_id (FK → User)
├── cover_image
├── is_public
├── is_collaborative
├── is_editorial
├── follower_count
├── total_duration
├── created_at
└── updated_at

PlaylistSong
├── id (PK)
├── playlist_id (FK → Playlist)
├── song_id (FK → Song)
├── added_by (FK → User)
├── position
└── created_at

PlaylistFollower
├── id (PK)
├── user_id (FK → User)
├── playlist_id (FK → Playlist)
└── created_at
```

#### Interactions

```
ListeningHistory
├── id (PK)
├── user_id (FK → User)
├── song_id (FK → Song)
├── played_at
├── duration_played
├── completed
├── source (playlist/album/radio/search)
└── source_id

LikedSong
├── id (PK)
├── user_id (FK → User)
├── song_id (FK → Song)
└── created_at

FollowedArtist
├── id (PK)
├── user_id (FK → User)
├── artist_id (FK → Artist)
└── created_at

SavedAlbum
├── id (PK)
├── user_id (FK → User)
├── album_id (FK → Album)
└── created_at

Review
├── id (PK)
├── user_id (FK → User)
├── album_id (FK → Album, nullable)
├── song_id (FK → Song, nullable)
├── rating (1-5)
├── comment
├── helpful_count
├── created_at
└── updated_at
```

#### Recommendations

```
UserTaste
├── id (PK)
├── user_id (FK → User)
├── favorite_genres (M2M → Genre)
├── top_artists (M2M → Artist)
├── energy_preference (0-1)
├── danceability_preference (0-1)
├── valence_preference (0-1)
└── last_updated

Radio
├── id (PK)
├── user_id (FK → User)
├── name
├── seed_artist_id (FK → Artist, nullable)
├── seed_song_id (FK → Song, nullable)
├── seed_genre_id (FK → Genre, nullable)
├── created_at
└── updated_at
```

### Indexes & Optimization

- **Primary Keys**: All tables use auto-increment integers or UUIDs
- **Foreign Keys**: Indexed for JOIN performance
- **Search Fields**: `title`, `name`, `username`, `email` are indexed
- **Composite Indexes**:
  - `(user_id, created_at)` for user activity queries
  - `(artist_id, release_date)` for artist discography
  - `(play_count)` for trending/popular queries
- **Unique Constraints**: Email, username, slug fields, composite uniques for M2M tables

## 🔌 GraphQL API

### Authentication

#### Mutations

```graphql
# Register new user
mutation {
  register(
    email: "user@example.com"
    username: "musiclover"
    password: "SecurePass123!"
    firstName: "John"
    lastName: "Doe"
  ) {
    user {
      id
      email
      username
    }
    token
    refreshToken
  }
}

# Login
mutation {
  login(email: "user@example.com", password: "SecurePass123!") {
    user {
      id
      username
      subscriptionType
    }
    token
    refreshToken
  }
}

# Refresh token
mutation {
  refreshToken(refreshToken: "your_refresh_token") {
    token
    refreshToken
  }
}

# Update profile
mutation {
  updateProfile(
    bio: "Music enthusiast"
    profileImage: "base64_image_data"
    country: "US"
  ) {
    user {
      id
      bio
      profileImage
    }
  }
}
```

### Users

#### Queries

```graphql
# Get current user
query {
  me {
    id
    email
    username
    subscriptionType
    profileImage
    preferences {
      audioQuality
      explicitContent
      autoplay
    }
    followedArtists {
      id
      name
    }
    playlists {
      id
      name
      totalDuration
    }
  }
}

# Get user by username
query {
  user(username: "musiclover") {
    id
    username
    bio
    profileImage
    publicPlaylists {
      id
      name
      followerCount
    }
    followedArtistsCount
    followerCount
  }
}

# Get user preferences
query {
  userPreferences {
    audioQuality
    explicitContent
    autoplay
    language
    privateSession
  }
}
```

#### Mutations

```graphql
# Update preferences
mutation {
  updatePreferences(
    audioQuality: HIGH
    explicitContent: false
    autoplay: true
  ) {
    preferences {
      audioQuality
      explicitContent
    }
  }
}

# Follow user
mutation {
  followUser(userId: "123") {
    success
    user {
      id
      followerCount
    }
  }
}
```

### Artists

#### Queries

```graphql
# Get artist details
query {
  artist(id: "123") {
    id
    name
    bio
    profileImage
    coverImage
    verified
    monthlyListeners
    genres {
      id
      name
    }
    albums {
      id
      title
      releaseDate
      coverImage
    }
    topSongs(limit: 10) {
      id
      title
      playCount
      duration
    }
    members {
      name
      role
      image
    }
    socialLinks {
      website
      spotify
      instagram
      twitter
    }
  }
}

# Search artists
query {
  searchArtists(query: "Beatles", limit: 20, offset: 0) {
    edges {
      node {
        id
        name
        profileImage
        monthlyListeners
        verified
      }
    }
    totalCount
  }
}

# Get trending artists
query {
  trendingArtists(timeRange: WEEK, limit: 50) {
    id
    name
    profileImage
    monthlyListeners
    genres {
      name
    }
  }
}

# Get similar artists
query {
  similarArtists(artistId: "123", limit: 20) {
    id
    name
    profileImage
    genres {
      name
    }
  }
}
```

#### Mutations

```graphql
# Follow artist
mutation {
  followArtist(artistId: "123") {
    success
    artist {
      id
      followersCount
    }
  }
}

# Unfollow artist
mutation {
  unfollowArtist(artistId: "123") {
    success
  }
}

# Create artist (admin/artist users)
mutation {
  createArtist(
    name: "New Band"
    bio: "Rock band from NYC"
    profileImage: "base64_data"
    genres: ["rock", "alternative"]
  ) {
    artist {
      id
      name
      slug
    }
  }
}
```

### Music (Albums & Songs)

#### Queries

```graphql
# Get album details
query {
  album(id: "456") {
    id
    title
    artist {
      id
      name
    }
    albumType
    releaseDate
    coverImage
    totalDuration
    totalTracks
    songs {
      id
      title
      trackNumber
      duration
      isExplicit
    }
    reviews {
      user {
        username
      }
      rating
      comment
    }
  }
}

# Get song details
query {
  song(id: "789") {
    id
    title
    artist {
      id
      name
    }
    album {
      id
      title
      coverImage
    }
    featuredArtists {
      id
      name
    }
    duration
    audioUrl
    lyrics
    isExplicit
    genre {
      name
    }
    playCount
    likeCount
    audioFeatures {
      tempo
      key
      energy
      danceability
      valence
    }
  }
}

# Search songs
query {
  searchSongs(
    query: "love"
    filters: { genre: "pop", year: 2023, isExplicit: false }
    limit: 50
  ) {
    edges {
      node {
        id
        title
        artist {
          name
        }
        duration
        playCount
      }
    }
    totalCount
  }
}

# Get new releases
query {
  newReleases(albumType: ALBUM, limit: 20) {
    id
    title
    artist {
      name
    }
    releaseDate
    coverImage
  }
}

# Get song recommendations
query {
  recommendedSongs(limit: 30, basedOn: LISTENING_HISTORY) {
    id
    title
    artist {
      name
    }
    album {
      coverImage
    }
  }
}
```

#### Mutations

```graphql
# Upload song (artist/admin)
mutation {
  uploadSong(
    title: "My New Song"
    artistId: "123"
    albumId: "456"
    audioFile: "base64_audio_data"
    duration: 240
    trackNumber: 5
    genre: "pop"
    isExplicit: false
    lyrics: "Song lyrics here..."
  ) {
    song {
      id
      title
      audioUrl
    }
  }
}

# Like song
mutation {
  likeSong(songId: "789") {
    success
    song {
      id
      likeCount
    }
  }
}

# Unlike song
mutation {
  unlikeSong(songId: "789") {
    success
  }
}

# Play song (track listening history)
mutation {
  playSong(songId: "789", source: PLAYLIST, sourceId: "playlist_123") {
    success
    song {
      playCount
    }
  }
}

# Add review
mutation {
  addReview(songId: "789", rating: 5, comment: "Amazing track!") {
    review {
      id
      rating
      comment
      user {
        username
      }
    }
  }
}
```

### Playlists

#### Queries

```graphql
# Get playlist details
query {
  playlist(id: "321") {
    id
    name
    description
    coverImage
    user {
      id
      username
    }
    isPublic
    isCollaborative
    followerCount
    totalDuration
    songs {
      position
      song {
        id
        title
        artist {
          name
        }
        duration
      }
      addedBy {
        username
      }
      createdAt
    }
  }
}

# Get user playlists
query {
  myPlaylists {
    id
    name
    coverImage
    totalDuration
    songs {
      song {
        id
      }
    }
  }
}

# Get featured playlists
query {
  featuredPlaylists(limit: 20) {
    id
    name
    description
    coverImage
    followerCount
  }
}
```

#### Mutations

```graphql
# Create playlist
mutation {
  createPlaylist(
    name: "My Workout Mix"
    description: "High energy tracks"
    isPublic: true
    coverImage: "base64_data"
  ) {
    playlist {
      id
      name
      slug
    }
  }
}

# Update playlist
mutation {
  updatePlaylist(playlistId: "321", name: "Updated Name", isPublic: false) {
    playlist {
      id
      name
      isPublic
    }
  }
}

# Add song to playlist
mutation {
  addSongToPlaylist(playlistId: "321", songId: "789", position: 5) {
    playlistSong {
      position
      song {
        title
      }
    }
  }
}

# Remove song from playlist
mutation {
  removeSongFromPlaylist(playlistId: "321", songId: "789") {
    success
  }
}

# Reorder playlist songs
mutation {
  reorderPlaylistSongs(playlistId: "321", songId: "789", newPosition: 3) {
    success
  }
}

# Follow playlist
mutation {
  followPlaylist(playlistId: "321") {
    success
    playlist {
      followerCount
    }
  }
}

# Delete playlist
mutation {
  deletePlaylist(playlistId: "321") {
    success
  }
}
```

### Recommendations & Discovery

#### Queries

```graphql
# Get personalized recommendations
query {
  recommendations(limit: 30) {
    songs {
      id
      title
      artist {
        name
      }
    }
    reason
  }
}

# Get radio station
query {
  radio(seedArtist: "123", limit: 50) {
    id
    name
    songs {
      id
      title
      artist {
        name
      }
    }
  }
}

# Get discover weekly
query {
  discoverWeekly {
    id
    songs {
      id
      title
      artist {
        name
      }
      album {
        coverImage
      }
    }
    refreshDate
  }
}

# Get user taste profile
query {
  myTasteProfile {
    favoriteGenres {
      name
    }
    topArtists {
      name
    }
    energyPreference
    danceabilityPreference
    valencePreference
  }
}
```

#### Mutations

```graphql
# Create radio station
mutation {
  createRadio(name: "My Rock Radio", seedGenre: "rock") {
    radio {
      id
      name
    }
  }
}

# Update taste profile
mutation {
  updateTasteProfile(favoriteGenres: ["rock", "alternative", "indie"]) {
    tasteProfile {
      favoriteGenres {
        name
      }
    }
  }
}
```

### Search

#### Queries

```graphql
# Universal search
query {
  search(query: "beatles", types: [ARTIST, ALBUM, SONG, PLAYLIST], limit: 20) {
    artists {
      id
      name
      profileImage
    }
    albums {
      id
      title
      artist {
        name
      }
      coverImage
    }
    songs {
      id
      title
      artist {
        name
      }
    }
    playlists {
      id
      name
      user {
        username
      }
    }
  }
}

# Autocomplete
query {
  autocomplete(query: "beat", limit: 5) {
    suggestions
  }
}
```

### Analytics & Stats

#### Queries

```graphql
# Get listening history
query {
  listeningHistory(limit: 100, timeRange: MONTH) {
    song {
      id
      title
      artist {
        name
      }
    }
    playedAt
    durationPlayed
    completed
  }
}

# Get top artists (for user)
query {
  myTopArtists(timeRange: MONTH, limit: 20) {
    artist {
      id
      name
      profileImage
    }
    playCount
  }
}

# Get top songs
query {
  myTopSongs(timeRange: YEAR, limit: 50) {
    song {
      id
      title
      artist {
        name
      }
    }
    playCount
  }
}

# Get trending charts
query {
  trendingCharts(type: GLOBAL, timeRange: WEEK) {
    songs {
      position
      song {
        id
        title
        artist {
          name
        }
      }
      playCount
    }
  }
}
```

### Subscriptions (WebSocket)

```graphql
# Subscribe to notifications
subscription {
  notifications {
    id
    type
    title
    message
    createdAt
    read
  }
}

# Subscribe to now playing (for friends/followers)
subscription {
  nowPlaying(userId: "123") {
    user {
      username
    }
    song {
      title
      artist {
        name
      }
    }
    timestamp
  }
}
```

## 🚀 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Elasticsearch 8.0+
- Node.js 18+ (for frontend if needed)
- AWS S3 account (for production storage)

### Local Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/music-api.git
cd music-api
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements/development.txt
```

4. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start required services**

```bash
# Using Docker Compose
docker-compose up -d postgres redis elasticsearch

# Or start services individually
# PostgreSQL on port 5432
# Redis on port 6379
# Elasticsearch on port 9200
```

6. **Run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create superuser**

```bash
python manage.py createsuperuser
```

8. **Seed database (optional)**

```bash
python scripts/seed_data.py
```

9. **Run development server**

```bash
python manage.py runserver
```

10. **Start Celery worker (separate terminal)**

```bash
celery -A config worker -l info
```

11. **Start Celery beat (separate terminal)**

```bash
celery -A config beat -l info
```

The API will be available at:

- GraphQL Playground: `http://localhost:8000/graphql`
- Admin Panel: `http://localhost:8000/admin`

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/music_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_DSL_HOSTS=localhost:9200

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Sentry
SENTRY_DSN=https://xxx@sentry.io/xxx

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=15  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days

# Social Auth
GOOGLE_OAUTH_CLIENT_ID=xxx
GOOGLE_OAUTH_CLIENT_SECRET=xxx
FACEBOOK_APP_ID=xxx
FACEBOOK_APP_SECRET=xxx
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=xxx

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Database Configuration

PostgreSQL settings in `config/settings/base.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
    }
}
```

## 📝 Usage Examples

### cURL Examples

#### Register User

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { register(email: \"user@example.com\", username: \"musiclover\", password: \"SecurePass123!\", firstName: \"John\", lastName: \"Doe\") { token user { id username } } }"
  }'
```

#### Search Songs

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "query { searchSongs(query: \"love\", limit: 10) { edges { node { id title artist { name } } } } }"
  }'
```

#### Create Playlist

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "mutation { createPlaylist(name: \"My Playlist\", isPublic: true) { playlist { id name } } }"
  }'
```

### Python Client Example

```python
import requests

# GraphQL endpoint
url = "http://localhost:8000/graphql"

# Login
login_query = """
mutation {
  login(email: "user@example.com", password: "SecurePass123!") {
    token
    user {
      id
      username
    }
  }
}
"""

response = requests.post(url, json={'query': login_query})
token = response.json()['data']['login']['token']

# Search songs with authentication
headers = {'Authorization': f'Bearer {token}'}
search_query = """
query {
  searchSongs(query: "Beatles", limit: 5) {
    edges {
      node {
        id
        title
        artist {
          name
        }
      }
    }
  }
}
"""

response = requests.post(url, json={'query': search_query}, headers=headers)
songs = response.json()['data']['searchSongs']['edges']
```

### JavaScript Client Example

```javascript
// Using fetch API
const graphqlUrl = "http://localhost:8000/graphql";
const token = "YOUR_JWT_TOKEN";

async function searchSongs(query) {
  const response = await fetch(graphqlUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      query: `
        query SearchSongs($query: String!, $limit: Int) {
          searchSongs(query: $query, limit: $limit) {
            edges {
              node {
                id
                title
                artist {
                  name
                }
                duration
              }
            }
          }
        }
      `,
      variables: {
        query: query,
        limit: 20,
      },
    }),
  });

  const data = await response.json();
  return data.data.searchSongs.edges;
}

// Usage
searchSongs("Beatles").then((songs) => {
  console.log(songs);
});
```

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Module

```bash
pytest apps/users/tests/
```

### Run with Coverage

```bash
pytest --cov=apps --cov-report=html
```

### Run Specific Test

```bash
pytest apps/music/tests/test_models.py::TestSongModel::test_create_song
```

### Testing Structure

```
apps/users/tests/
├── __init__.py
├── conftest.py           # Pytest fixtures
├── factories.py          # Factory Boy factories
├── test_models.py        # Model tests
├── test_schema.py        # GraphQL schema tests
├── test_services.py      # Business logic tests
└── test_mutations.py     # Mutation tests
```

### Example Test

```python
import pytest
from apps.users.tests.factories import UserFactory
from apps.music.tests.factories import SongFactory

@pytest.mark.django_db
class TestLikeSongMutation:
    def test_like_song_success(self, graphql_client):
        user = UserFactory()
        song = SongFactory()

        query = """
            mutation LikeSong($songId: ID!) {
                likeSong(songId: $songId) {
                    success
                    song {
                        id
                        likeCount
                    }
                }
            }
        """

        response = graphql_client.execute(
            query,
            variables={'songId': song.id},
            user=user
        )

        assert response['data']['likeSong']['success'] is True
        assert response['data']['likeSong']['song']['likeCount'] == 1
```

## 🐳 Deployment

### Docker Deployment

1. **Build image**

```bash
docker build -t music-api:latest .
```

2. **Run with Docker Compose**

```bash
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use environment variables for all secrets
- [ ] Set up SSL/TLS certificates
- [ ] Configure CDN for static/media files
- [ ] Set up database backups
- [ ] Configure Redis persistence
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure rate limiting
- [ ] Set up log aggregation
- [ ] Configure firewall rules
- [ ] Set up CI/CD pipeline
- [ ] Run security audit
- [ ] Set up auto-scaling (if using cloud)

### AWS Deployment Example

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Deploy to Elastic Beanstalk
eb init -p python-3.11 music-api
eb create music-api-env
eb deploy
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/music-api/static/;
    }

    location /media/ {
        alias /var/www/music-api/media/;
    }
}
```

## 🔮 Future Implementations

### Phase 1: Enhanced Features

- [ ] Podcast support with episodes and series
- [ ] Audio books integration
- [ ] Live streaming events/concerts
- [ ] Karaoke mode with lyrics sync
- [ ] DJ mode with crossfade and mixing
- [ ] Voice commands integration
- [ ] Smart speaker support (Alexa, Google Home)
- [ ] Car mode interface
- [ ] Sleep timer and alarm features

### Phase 2: Social Features

- [ ] User profiles with activity feed
- [ ] Friend system and social listening
- [ ] Group playlists and collaborative sessions
- [ ] Music sharing to social media
- [ ] In-app messaging
- [ ] Artist verification system
- [ ] Fan clubs and exclusive content
- [ ] Concert ticket integration
- [ ] Merchandise store

### Phase 3: Advanced Analytics

- [ ] Detailed listening statistics dashboard
- [ ] Year-end wrapped feature (like Spotify Wrapped)
- [ ] Artist analytics for musicians
- [ ] A/B testing framework for recommendations
- [ ] User behavior prediction models
- [ ] Churn prediction and retention strategies
- [ ] Revenue analytics for subscriptions

### Phase 4: AI & Machine Learning

- [ ] Advanced recommendation engine with deep learning
- [ ] Mood-based playlist generation
- [ ] Auto-tagging songs with AI
- [ ] Voice recognition for song search
- [ ] Auto-generated radio stations
- [ ] Similar song detection (audio fingerprinting)
- [ ] Copyright detection system
- [ ] AI-powered music mastering

### Phase 5: Content Creation

- [ ] Built-in audio editor
- [ ] Remix creation tools
- [ ] Collaborative music creation
- [ ] Soundboard and sampling tools
- [ ] Beat matching and tempo sync
- [ ] Audio effects library
- [ ] Export to DAWs integration

### Phase 6: Monetization

- [ ] Ad-supported free tier
- [ ] Premium subscription with hi-fi audio
- [ ] Family plan sharing
- [ ] Student discount verification
- [ ] Gift subscriptions
- [ ] Artist royalty distribution system
- [ ] Tipping system for artists
- [ ] NFT music integration

### Phase 7: Mobile & Platform Expansion

- [ ] Native iOS app
- [ ] Native Android app
- [ ] Desktop applications (Windows, macOS, Linux)
- [ ] Apple Watch app
- [ ] Android Wear app
- [ ] TV apps (Apple TV, Android TV, Roku)
- [ ] Game console integration
- [ ] Web Audio API player

### Phase 8: Enterprise Features

- [ ] Business accounts for venues/restaurants
- [ ] White-label solution
- [ ] API marketplace for third-party integrations
- [ ] Licensing management system
- [ ] Multi-tenant architecture
- [ ] Custom branding options

### Phase 9: Accessibility

- [ ] Screen reader optimization
- [ ] Audio descriptions for visual content
- [ ] Keyboard navigation improvements
- [ ] High contrast themes
- [ ] Dyslexia-friendly fonts
- [ ] Multiple language support (i18n)
- [ ] Right-to-left (RTL) language support

### Phase 10: Infrastructure

- [ ] GraphQL subscriptions for real-time updates
- [ ] Microservices architecture migration
- [ ] Kubernetes orchestration
- [ ] Multi-region deployment
- [ ] CDN optimization
- [ ] Database sharding
- [ ] Read replicas for scaling
- [ ] Message queue system (RabbitMQ/Kafka)

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**

```bash
git checkout -b feature/amazing-feature
```

3. **Make your changes and commit**

```bash
git commit -m "Add amazing feature"
```

4. **Push to your branch**

```bash
git push origin feature/amazing-feature
```

5. **Open a Pull Request**

### Code Style

- Follow PEP 8 guidelines
- Use Black for formatting: `black .`
- Use isort for imports: `isort .`
- Run linting: `flake8 .`
- Write docstrings for all functions/classes
- Add type hints where applicable

### Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

Example:

```
feat(playlists): add collaborative playlist support

- Allow multiple users to edit playlists
- Add permission system for collaborators
- Update GraphQL schema with new mutations
```

### Testing Requirements

- All new features must include tests
- Maintain minimum 80% code coverage
- All tests must pass before merging

### Documentation

- Update README.md if adding new features
- Add inline comments for complex logic
- Update API documentation in `docs/`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - _Initial work_ - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Inspired by Spotify, Apple Music, and YouTube Music
- Thanks to the Django and GraphQL communities
- Special thanks to all contributors

## 📞 Support

- **Documentation**: [docs.yourdomain.com](https://docs.yourdomain.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/music-api/issues)
- **Email**: support@yourdomain.com
- **Discord**: [Join our community](https://discord.gg/yourserver)

## 🔗 Links

- [API Documentation](https://api.yourdomain.com/docs)
- [GraphQL Playground](https://api.yourdomain.com/graphql)
- [Status Page](https://status.yourdomain.com)
- [Blog](https://blog.yourdomain.com)

---

**Note**: This is a comprehensive music streaming API built for learning and production use. Feel free to customize and extend based on your needs.

⭐ If you find this project useful, please consider giving it a star on GitHub!
