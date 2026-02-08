# CatchUp v1

Automatisk transkripsjon og oppsummering av Panopto-forelesninger.

## Funksjoner

- 🎥 Last ned forelesninger fra Panopto
- 🎤 Voice Activity Detection (VAD) for å fjerne lange stillhetsperioder
- 📝 Automatisk transkripsjon med Voxtral (Mistral)
- 📚 2-pass oppsummering med Mistral Small
- 🌐 Web UI for å administrere og se forelesninger
- 💾 SQLite database som Source of Truth
- ✅ Omfattende testsuite (unit, integration, live tests)

## Arkitektur

```
CatchUp/
├── src/catchup/
│   ├── api/           # FastAPI application
│   ├── core/          # Core models, config, parsing
│   ├── db/            # Database layer
│   ├── clients/       # External service clients (yt-dlp, Mistral)
│   └── pipeline/      # Processing pipeline
├── tests/
│   ├── unit/          # Fast unit tests (no I/O)
│   ├── integration/   # Integration tests (local only)
│   └── live/          # Live API tests (opt-in)
├── data/              # Lecture data (git-ignored)
└── main.py            # Entry point
```

## Oppsett

### 1. Krav

- Python 3.10+
- ffmpeg (for lydkonvertering)
- yt-dlp (installeres via pip)
- Mistral API key

### 2. Installasjon

```bash
# Klon repository
git clone <repo-url>
cd CatchUp

# Opprett virtual environment
python -m venv venv
source venv/bin/activate  # På Windows: venv\Scripts\activate

# Installer dependencies
pip install -r requirements.txt
```

### 3. Konfigurasjon

Kopier `.env.example` til `.env` og fyll inn:

```bash
cp .env.example .env
```

Rediger `.env`:

```env
MISTRAL_API_KEY=your_api_key_here
DATA_DIR=./data
SQLITE_PATH=./catchup.sqlite
```

### 4. Panopto Authentication

For å laste ned fra Panopto trenger du en `cookies.txt` fil:

1. Installer en browser extension som "Get cookies.txt LOCALLY" (Chrome/Firefox)
2. Logg inn på Panopto i browseren
3. Eksporter cookies til `cookies.txt` i prosjektroten

## Bruk

### Start server

```bash
python main.py
```

Serveren starter på `http://localhost:8000`

### Web UI

Åpne `http://localhost:8000` i browseren for å:
- Lime inn Panopto URL
- Se jobbstatus i sanntid
- Bla gjennom behandlede forelesninger
- Lese oppsummeringer med LaTeX-støtte

### API Endpoints

#### Metadata
```bash
GET /metadata?url=<panopto-url>
```

#### Start job
```bash
POST /jobs
{
  "url": "<panopto-url>",
  "language": "auto|no|en"
}
```

#### Job status
```bash
GET /jobs/{job_id}
```

#### Bla gjennom
```bash
GET /courses
GET /courses/{course_code}/dates
GET /courses/{course_code}/{date}/lectures
GET /lectures/{lecture_id}
```

#### Render oppsummering
```bash
GET /render/{lecture_id}
```

## Testing

### Kjør alle tester (offline only)

```bash
pytest
```

Dette kjører:
- ✅ Unit tests (rask, ren logikk)
- ✅ Integration tests (bruker fakes, ingen nettverk)
- ❌ Skipper live tests (krever API credentials)

### Kjør live tests (bruker API credits)

```bash
RUN_LIVE_TESTS=1 pytest -m live
```

⚠️ **Advarsel**: Dette koster API credits!

### Kjør spesifikke test-typer

```bash
# Kun unit tests
pytest -m unit

# Kun integration tests
pytest -m integration

# Alt unntatt live
pytest -m "not live"
```

## Utviklingsnotater

### Fake Clients

For testing og utvikling bruker systemet "fake clients" som ikke gjør eksterne kall:
- `FakeDownloader`: Simulerer nedlasting
- `FakeMediaConverter`: Kopierer filer
- `FakeVadProcessor`: Simulerer VAD
- `FakeTranscriberClient`: Returnerer deterministisk tekst
- `FakeSummarizerClient`: Returnerer deterministisk markdown

Dette gjør at hele pipelineen kan testes uten å bruke API credits.

### Dependency Injection

Alle eksterne avhengigheter er definert som interfaces (ABC) i `pipeline/interfaces.py`:
- `Downloader`
- `MediaConverter`
- `VadProcessor`
- `TranscriberClient`
- `SummarizerClient`

Dette gjør koden testbar og modulær.

### Database

SQLite er Source of Truth (SoT) og inneholder:
- **lectures**: Alle behandlede forelesninger
- **jobs**: Job historikk og status
- **artifacts**: Fil-tracker (audio, transkripsjon, oppsummering)

### Idempotens

Samme Panopto-URL kan behandles flere ganger:
- `source_uid` identifiserer unikt hver forelesning
- Eksisterende forelesning returneres (ingen overskriving)
- Ny job opprettes for hver behandling

## Diskstruktur

```
data/
  ELE130/
    2026-02-08/
      a1b2c3d4/
        source_url.txt
        metadata.json
        audio_original.wav
        audio_vad.wav
        transcript/
          raw_transcript.txt
          transcript_chunks.json
        summary/
          summary.md
          summary.json
        logs/
          pipeline.log
```

## Status

### ✅ Implementert

- [x] Repo struktur og konfigurasjon
- [x] SQLite database med schema
- [x] Data models (Lecture, Job, Artifact)
- [x] Metadata extraction (yt-dlp)
- [x] Job runner med status transitions
- [x] FastAPI endpoints
- [x] Frontend UI
- [x] Fake clients for testing
- [x] Unit tests for parsing

### 🚧 Under arbeid

- [ ] Real downloader (yt-dlp)
- [ ] ffmpeg media converter
- [ ] Silero VAD implementation
- [ ] Voxtral transcription client
- [ ] Mistral summarization client
- [ ] Integration tests
- [ ] Live tests

### 📋 TODO

- [ ] Logging system
- [ ] Error handling improvements
- [ ] Proper markdown rendering (instead of simple HTML)
- [ ] Resume interrupted jobs
- [ ] Delete/reprocess functionality
- [ ] Better progress tracking
- [ ] Batch processing

## Lisens

Internal project - not for public distribution.
