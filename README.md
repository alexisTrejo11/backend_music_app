# Music Streaming API

GraphQL backend for a Spotify-style music platform—catalog, playlists, social interactions, and explainable recommendations. Deployed on AWS with Docker and Amazon RDS PostgreSQL.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Django 4.2](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)
[![GraphQL](https://img.shields.io/badge/API-GraphQL-e10098.svg)](https://graphql.org/)

---

## Table of contents

- [About](#about)
- [Features](#features)
- [Documentation](#documentation)
- [Tech stack](#tech-stack)
- [Architecture at a glance](#architecture-at-a-glance)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [Project structure](#project-structure)
- [Deployment](#deployment)
- [Testing](#testing)
- [Maintaining documentation](#maintaining-documentation)
- [Contributing](#contributing)
- [Security & compliance](#security--compliance)
- [License](#license)

---

## About

This project is a **Django + Graphene** backend for streaming music applications. It exposes a unified GraphQL schema for artists, albums, songs, user playlists, likes and reviews, listening history, and NumPy-powered personalized recommendations with human-readable “why this song” reasons.

The production deployment model targets **AWS**: the application runs in Docker (EC2 or ECS) behind an ALB, with **Amazon RDS PostgreSQL** as the managed database (`DATABASE_URL`). Local development runs the app, PostgreSQL, and Redis with Docker Compose.

| | |
|---|---|
| **Version** | 1.0.0 |
| **Status** | Stable (core GraphQL paths); JWT GraphQL middleware still TODO |
| **Primary API** | `POST /graphql/` |
| **GraphiQL (dev)** | [http://127.0.0.1:8000/graphql/](http://127.0.0.1:8000/graphql/) |
| **Admin** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) |

---

## Features

Short list for the README; full detail lives in generated docs.

- **GraphQL catalog** — songs, albums, genres, search, trending, likes, and play tracking
- **Playlists** — CRUD, collaborators, follows, reordering, and duplication
- **Recommendations** — personalized songs with scores/reasons, Discover Weekly, mood, radio, taste profiles
- **Docker + AWS** — prod compose runs app only against external RDS; local compose includes Postgres + Redis

See [Project Features](docs/generated/ProjectFeature.md) for the complete feature breakdown.

---

## Documentation

The documentation for this project is externally hosted in my personal website: [alexis-trejo.com](https://alexis-trejo.com).

### Documentation hub

| Document | What you will find | Read |
|----------|-------------------|------|
| **Overview** | Problem, solution, metrics, links | [ProjectOverview.md](https://alexis-trejo.com/projects/music-streaming-api/overview) |
| **API schema** | GraphQL operations, auth, examples | [APISchema.md](https://alexis-trejo.com/projects/music-streaming-api/api-schema) |
| **Architecture** | Layers, patterns, diagram, data flows | [ProjectArchitecture.md](https://alexis-trejo.com/projects/music-streaming-api/architecture) |
| **Infrastructure** | Docker, ECS/EC2, RDS, Redis, cloud services | [ProjectInfrastructure.md](https://alexis-trejo.com/projects/music-streaming-api/infrastructure) |
| **Features** | Feature cards, snippets, status per area | [ProjectFeature.md](https://alexis-trejo.com/projects/music-streaming-api/features) |
| **Code showcase** | Curated code examples from the codebase | [ProjectCodeShowCase.md](https://alexis-trejo.com/projects/music-streaming-api/code-showcase) |
| **Generated index** | Auto-generated hub linking all of the above | [docs/generated/README.md](https://alexis-trejo.com/projects/music-streaming-api/generated-index) |


---

## Tech stack

- **Runtime:** Python 3.12, Django 4.2.11
- **API:** Graphene-Django 3.2 (GraphQL), Django REST Framework (secondary)
- **Auth:** SimpleJWT (tokens on login/register; GraphQL Bearer middleware pending)
- **Database:** PostgreSQL locally and on Amazon RDS in production
- **Cache / tasks:** Redis locally; ElastiCache + Celery planned
- **ML / scoring:** NumPy in recommendation services
- **Deploy:** Docker multi-stage image, Gunicorn, WhiteNoise, AWS ALB + RDS

---

## Architecture at a glance

Clients call **GraphQL over HTTPS** through an AWS ALB into a Gunicorn/Django container. The app reads and writes catalog and user data on **RDS PostgreSQL**. Media files and async workers (Celery) are planned for S3 and ElastiCache respectively.

```mermaid
flowchart LR
  Client[Web / mobile clients] --> ALB[AWS ALB]
  ALB --> API[Django GraphQL in Docker]
  API --> RDS[(Amazon RDS PostgreSQL)]
  API --> Redis[(ElastiCache Redis — planned)]
  API --> S3[S3 + CloudFront media — planned]
```

Full diagram, layers, and decisions: [ProjectArchitecture.md](docs/generated/ProjectArchitecture.md).

---

## Prerequisites

- Python 3.12+
- pip / venv
- Docker & Docker Compose v2 (recommended)
- PostgreSQL via Docker Compose for local development or RDS for production
- NumPy-compatible environment (included in `requirements.txt`)

---

## Quick start

### Local development

```bash
git clone https://github.com/alexisTrejo11/music-streaming-api
cd music-streaming-api
cp .env.example .env
docker compose up --build
```

- GraphiQL: http://127.0.0.1:8000/graphql/
- Admin: http://127.0.0.1:8000/admin/

Create a superuser in another terminal:

```bash
docker compose exec web python manage.py createsuperuser
```

The Compose stack runs the Django app at `http://127.0.0.1:8000`, PostgreSQL at `localhost:5432`, and Redis at `localhost:6379`. Source code is mounted into the app container and Gunicorn reloads after Python changes.

---

## Configuration

Copy [`.env.example`](.env.example) to `.env`.

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret (required) |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` or `config.settings.production` |
| `DATABASE_URL` | Full PostgreSQL URL; host-local by default and overridden by Compose for the app container |
| `ALLOWED_HOSTS` | Comma-separated domains |
| `CORS_ALLOWED_ORIGINS` | Frontend origins for GraphQL clients |
| `WEB_PORT` | Host port mapped to container 8000 |
| `SECURE_SSL_REDIRECT` | Enable when TLS terminates at the app (usually `False` behind ALB) |

`docker compose up --build` starts the complete local stack.

---

## API overview

| Area | GraphQL operations | Doc |
|------|-------------------|-----|
| Auth | `registerUser`, `loginUser`, `me`, `updateProfile` | [APISchema.md](docs/generated/APISchema.md#auth) |
| Music | `searchSongs`, `trendingSongs`, `song`, `playSong` | [APISchema.md](docs/generated/APISchema.md#music) |
| Playlists | `myPlaylists`, `createPlaylist`, `addSongToPlaylist` | [APISchema.md](docs/generated/APISchema.md#playlists) |
| Recommendations | `recommendedSongs`, `discoverWeekly`, `createRadio` | [APISchema.md](docs/generated/APISchema.md#recommendations) |
| Artists | `searchArtists`, `artist`, `createArtist` | [APISchema.md](docs/generated/APISchema.md#artists) |
| Interactions | `trackPlay`, `addReview`, `likedSongs` | [APISchema.md](docs/generated/APISchema.md#interactions) |

All operations use **`POST /graphql/`** with a JSON `{ "query": "...", "variables": {} }` body. Explore the schema in GraphiQL during development.

---

## Project structure

```
music-streaming-api/
├── apps/
│   ├── users/            # Auth, profiles, preferences
│   ├── artists/          # Artist catalog
│   ├── music/            # Songs, albums, genres
│   ├── playlists/        # Playlists & collaboration
│   ├── interactions/     # Likes, reviews, history
│   ├── recommendations/  # Taste, radio, Discover Weekly
│   └── core/             # Decorators, logging, base mutations
├── config/               # Settings, urls, merged GraphQL schema
├── Dockerfile            # Production image definition
├── docker-compose.yml    # Local app, PostgreSQL, and Redis stack
├── entrypoint.sh         # Migration and static-file startup tasks
├── docs/
│   ├── source/           # YAML source docs (edit these)
│   ├── generated/        # Readable Markdown (generated)
│   └── yaml_to_markdown.py
├── requirements.txt
└── manage.py
```

---

## Deployment

Build the root `Dockerfile` for production. It defaults to `config.settings.production`; point `DATABASE_URL` at your **existing Amazon RDS** PostgreSQL instance, set `SECRET_KEY`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS`, and run it behind an ALB. If you pass an environment file to the container, set `DJANGO_SETTINGS_MODULE=config.settings.production`. Plan separate work for S3 media, ElastiCache Redis, Celery workers, and JWT GraphQL middleware before high-traffic launch.

Details: [ProjectInfrastructure.md](docs/generated/ProjectInfrastructure.md).

---

## Testing

```bash
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py test
```

Schema and service tests live under `apps/*/tests/`.

---

## Maintaining documentation

1. Edit YAML in `docs/source/<Section>.md` (keep fields aligned with [`docs/source/schema.ts`](docs/source/schema.ts)).
2. Run `python docs/yaml_to_markdown.py`.
3. Commit both `docs/source/` and `docs/generated/` so docs render on GitHub without running the script.

Optional notes that are not part of the schema (warnings, TODOs) go in the **Markdown body** below the closing `---` in each source file—they appear under **Additional notes** in generated files.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit with clear messages
4. Open a pull request

Issues and PRs welcome via [GitHub](https://github.com/alexisTrejo11/music-streaming-api).

---

## Security & compliance

Do not commit `.env` or RDS credentials. Disable GraphiQL and restrict CORS in production. JWT tokens are issued on login but **Bearer authentication for GraphQL is not fully wired**—treat session-based GraphiQL testing and token-based SPA clients differently until middleware is added. Report vulnerabilities privately to the repository owner.

---

## License

MIT License — see [LICENSE](LICENSE) file.

---

## Links

| Resource | URL |
|----------|-----|
| Repository | [github.com/alexisTrejo11/music-streaming-api](https://github.com/alexisTrejo11/music-streaming-api) |
| Documentation hub | [docs/generated/README.md](docs/generated/README.md) |
| GraphiQL (local) | [http://127.0.0.1:8000/graphql/](http://127.0.0.1:8000/graphql/) |
