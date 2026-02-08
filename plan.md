# CatchUp – plan.md (v1)

> **Formål:** Dette dokumentet er den kanoniske planen for CatchUp v1.  
> Det skal være “Claude/Codex-ready”: presis, testbar, deterministisk og designet for å minimere API-kostnader.

BRUK FØLGENDE URLer FOR Å TESTE 

vanlig forelesning
https://uis.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=3d2aa282-fecf-4a38-a71a-b3e900743f41

eksempel på to forelesninger på samme dag
https://uis.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=2dcb2447-ed9c-40f3-ad53-b3bb00812d0a

https://uis.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=9ebcd13c-081c-470d-a2a6-b3bb0081812a

---

## 0) Låste beslutninger (v1)

1. **Audioformat:** Kun WAV. Alle artifacts og hele pipeline bruker `.wav`.
2. **Unik identitet:** Bruk `source_uid` (Panopto-ID hvis tilgjengelig, ellers stabil hash av URL) for kollisjonssikkerhet.
3. **Diskstruktur:** `data/{COURSE}/{DATE}/{SOURCE_UID_SHORT}/...` (støtter flere forelesninger samme dag uten overskriving).
4. **Database:** SQLite er Source of Truth (SoT) for historikk, job-status og artifact-index.
5. **Språk:** Default språk per kurs (ELE130, MAT200). Bruker kan override (auto/no/en).
6. **Tidsstempler:** Ingen tidsstempler i transkripsjon eller summary (bevisst valgt).
7. **Kilde:** Panopto er eneste kilde i v1 (ingen andre providers).
8. **Kreditt-sparing:** Standard testsuite skal aldri bruke eksterne API-kall. Live/credits-tester er eksplisitt opt-in.

---

## 1) Mål og leveranser

### 1.1 Mål
- Bruker limer inn Panopto-URL → systemet:
  1) henter metadata
  2) laster ned laveste format som inneholder audio
  3) produserer `audio_original.wav`
  4) kjører Silero VAD med “bevar naturlige pauser”-policy → `audio_vad.wav`
  5) transkriberer med Voxtral (chunking, robust for 3–4 timer) → `raw_transcript.txt` + `transcript_chunks.json`
  6) oppsummerer med Mistral Small (2-pass: chunk summaries + merge) → `summary.md`
  7) gjør resultatet tilgjengelig i web UI (rendered markdown + LaTeX)

### 1.2 Leveranser (artifacts)
Minimum per forelesning:
- `metadata.json`
- `audio_original.wav`
- `audio_vad.wav`
- `transcript/raw_transcript.txt`
- `transcript/transcript_chunks.json`
- `summary/summary.md`

Valgfritt (for debugging / prompt-stabilitet):
- `summary/summary.json` (inkl. prompt version/hash, modellnavn, input-lengder)
- `logs/pipeline.log`

---

## 2) Negative requirements (hva CatchUp v1 IKKE skal være)

Dette er eksplisitte “negative prompts” for å hindre scope creep og feil design:

### 2.1 Ikke dette (produkt)
- Ikke en full LMS-klient: **ingen** kalender-integrasjon, **ingen** timeplan-sync.
- Ikke en editor: bruker **skal ikke** redigere oppsummering i v1.
- Ikke en RAG/Q&A-tjeneste i v1: vi **lagrer** rå transkripsjon/metadata for senere, men bygger ikke retrieval/indexering nå.
- Ikke multi-source: **ingen** YouTube/Vimeo/Zoom/etc i v1.

### 2.2 Ikke dette (output)
- Ikke tidsstempler (hverken i transkripsjon eller markdown).
- Ikke “hallusinerte” fakta i oppsummering: modellen skal aldri fylle inn manglende innhold.
- Ikke referanser til “transkripsjonen” eller prosessen i output (ingen metakommentarer).

### 2.3 Ikke dette (arkitektur / drift)
- Ikke eksterne køsystemer (Kafka/Redis/Celery) i v1; hold det enkelt i prosess + SQLite.
- Ikke “magisk” global state som gjør tester flakey. Alt skal være DI-vennlig (dependency injection).
- Ikke hardkode credentials i kode; kun `.env`.
- Ikke nettverkskall i standard test-run (zero credits i CI).

---

## 3) Rammeverk og teknisk basis

- Backend: Python + FastAPI
- Frontend: HTML + CSS + vanilla JS (single-page UI med dynamiske jobbkort)
- DB: SQLite (SoT)
- Download: yt-dlp (må bruke `--cookies cookies.txt` i prosjektroten)
- Media: ffmpeg
- VAD: Silero VAD
- ASR: Voxtral (Mistral)
- Summarization: Mistral Small

---

## 4) Kurs og språk

### 4.1 Kurskode
- Kurskode er ALLTID de 6 første tegnene i tittel/filnavn: `^[A-Z]{3}\d{3}`.
- Hvis mismatch: `course_code="UNKNOWN"` (pipeline skal fortsatt kjøre).

### 4.2 Dato parsing
- Parse dato fra tittel om mulig (støtt minst):
  - `YYYY-MM-DD`
  - `DD.MM.YYYY`
  - `DD/MM/YYYY`
- Hvis ikke funnet: `lecture_date="unknown"`.

### 4.3 Default språk per kurs
- ELE130 → `no`
- MAT200 → `no`
- UNKNOWN → `auto`

Regel:
- Hvis bruker velger `no/en`: respekter.
- Hvis bruker velger `auto`: bruk kurs-default hvis kjent ellers `auto`.

---

## 5) Identitet, idempotens og kollisjonsfri lagring

### 5.1 source_uid
- Primær: Panopto-unik ID (hent fra URL eller yt-dlp metadata hvis tilgjengelig).
- Fallback: stabil hash av URL (f.eks `sha1(url)`), lagret som hex.
- `source_uid_short`: første 8–10 tegn for mappenavn (full UID lagres i metadata/DB).

### 5.2 lecture_id
Kanonisk:
- `lecture_id = "{course_code}_{lecture_date}_{source_uid_short}"`

### 5.3 Idempotens
- Hvis samme URL behandles flere ganger:
  - DB finner eksisterende lecture via `source_uid`
  - policy v1: enten
    - returner eksisterende lecture og lag ny job, eller
    - returner “already processed” og tilby “re-run” med ny job
  - **Ingen overskriving** av artifacts uten eksplisitt re-run policy.

---

## 6) Diskstruktur (kanonisk)

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
  MAT200/
    ...
```

---

## 7) SQLite som Source of Truth (skjema)

### 7.1 lectures
- `lecture_id` TEXT PRIMARY KEY
- `course_code` TEXT
- `lecture_date` TEXT
- `title` TEXT
- `source_url` TEXT
- `source_uid` TEXT UNIQUE
- `created_at` TEXT ISO

### 7.2 jobs
- `job_id` TEXT PRIMARY KEY (uuid)
- `lecture_id` TEXT (FK)
- `status` TEXT ENUM:
  - `queued`, `downloading`, `converting`, `vad`, `transcribing`, `summarizing`, `done`, `error`
- `progress` REAL (0..1) (valgfritt men anbefalt)
- `error_message` TEXT NULL
- `started_at`, `finished_at` TEXT ISO

### 7.3 artifacts
- `artifact_id` TEXT PRIMARY KEY
- `lecture_id` TEXT (FK)
- `type` TEXT ENUM:
  - `metadata_json`, `audio_original_wav`, `audio_vad_wav`,
    `raw_transcript_txt`, `transcript_chunks_json`,
    `summary_md`, `summary_json`, `log`
- `path` TEXT
- `created_at` TEXT ISO

---

## 8) API-kontrakt (FastAPI)

### 8.1 Metadata
- `GET /metadata?url=...`
  - return:
    - `title`, `duration_sec`, `course_code`, `lecture_date`,
      `source_uid`, `source_uid_short`, `language_suggestion`

### 8.2 Jobs
- `POST /jobs`
  - body: `{ "url": "...", "language": "auto|no|en" }`
  - return: `{ "job_id": "...", "lecture_id": "..." }`

- `GET /jobs/{job_id}`
  - return: `{ status, progress, error_message, lecture_id, artifacts (when available) }`

### 8.3 Navigasjon
- `GET /courses` → liste kurs
- `GET /courses/{course_code}/dates` → liste datoer
- `GET /courses/{course_code}/{date}/lectures` → liste forelesninger den dagen
- `GET /lectures/{lecture_id}` → metadata + artifacts

### 8.4 Rendering
- `GET /render/{lecture_id}` → HTML (rendered markdown + MathJax)

---

## 9) Pipeline (detaljert)

### 9.1 Metadata (yt-dlp)
- Bruk `yt-dlp --dump-json` med `--cookies cookies.txt`
- Velg laveste format som har audio (eller laveste video med audio hvis nødvendig).

**Fail-fast:**
- Hvis `cookies.txt` mangler → tydelig error (ikke “silent fail”).

### 9.2 Download
- Nedlasting til lecture folder
- Konverter til `audio_original.wav` via ffmpeg om nødvendig
- Standard audioformat:
  - 16kHz
  - mono
  - PCM 16-bit

### 9.3 Silero VAD: “bevar naturlige pauser”
Mål: kutt bare LANGE stillheter, ikke “tenkepauser”.

Policy-parametre (konfig):
- `LONG_SILENCE_SEC` (default 1.6)
- `KEEP_SILENCE_SEC` (default 0.35)
- `PADDING_SEC` (default 0.2)

Algoritme:
1) Kjør VAD og få speech segments.
2) Legg padding før/etter hvert segment.
3) Merge segments hvis gap er lite.
4) Når gap > LONG_SILENCE_SEC:
   - reduser gap til KEEP_SILENCE_SEC i output (ikke fjern helt)
5) Skriv `audio_vad.wav`.

### 9.4 Transkribering (Voxtral) – chunking for 3–4 timer
- Chunk audio_vad.wav i 10–20 minutter (konfig), med overlapp 5–8 sek.
- Transkriber chunk-for-chunk.
- Skriv:
  - `transcript_chunks.json`: liste av chunks med {i, start_sec, end_sec, text, detected_language}
  - `raw_transcript.txt`: enkel concat (v1 kan tolerere litt overlapp-repetisjon)

### 9.5 Oppsummering (Mistral Small) – 2-pass
- Pass 1: chunk summaries (fra tekst chunks) med fast, stabil markdown-struktur.
- Pass 2: merge summary til endelig `summary.md`.

**Regler for oppsummering:**
- Ingen spekulasjon. Hvis uklart: “Uklart: …”.
- Ingen metakommentarer (“i transkripsjonen sies…”).
- LaTeX for matematiske uttrykk.

---

## 10) Prompts (inkl. negative prompts)

### 10.1 Summarization prompt (chunk pass)
**MÅL:** stabile notater, høy presisjon, ingen hallusinasjoner.

**Negative prompts (MÅ IKKE):**
- Ikke spekuler eller “gjett”.
- Ikke legg til fakta som ikke står i teksten.
- Ikke referer til prosessen (transkripsjon/lyd).
- Ikke skriv tidsstempler.
- Ikke bruk lange avsnitt uten struktur.

(Implementeres som en streng i kode med versjonsnummer.)

### 10.2 Summarization prompt (merge pass)
**Negative prompts (MÅ IKKE):**
- Ikke introduser nye temaer som ikke finnes i chunk-sammendragene.
- Ikke “normaliser” uklare punkter til noe som virker riktig—behold usikkerhet eksplisitt.
- Ikke endre språk tilfeldig; hold valgt språk.

---

## 11) Skuddsikker testplan (zero credits by default)

### 11.1 Prinsipp
- Standard `pytest` kjører FULLT offline: **ingen nettverk, ingen API calls**.
- Ekte Voxtral/Mistral/yt-dlp-nettverk testes kun med `RUN_LIVE_TESTS=1` og pytest-mark `@pytest.mark.live`.

### 11.2 Dependency Injection (obligatorisk for testbarhet)
Alt som gjør IO eller koster penger skal ligge bak interfaces:
- `Downloader`
- `MediaConverter`
- `VadProcessor`
- `TranscriberClient`
- `SummarizerClient`

I tests byttes de ut med fakes/mocks.

### 11.3 Testlag

#### A) Unit tests (raskt, deterministisk)
Mål: all ren logikk.

- Parsing:
  - kurskode = første 6 tegn
  - dato parsing (ulike mønstre)
  - source_uid extraction (Panopto-ID eller URL-hash)
  - lecture_id generation
- Chunk planning:
  - audio chunk plan (lengde, overlapp, siste chunk)
  - text chunk plan (for summarization)
- VAD policy (uten ML):
  - input segments → output “stitch plan”
  - verifiser at korte pauser ikke kuttes
  - verifiser at lange pauser komprimeres til KEEP_SILENCE
- DB:
  - get-or-create lecture
  - status transitions og constraints
  - artifact registrering

**Krav:** 100% offline, ingen ffmpeg, ingen filer.

#### B) Offline integration tests (ekte filer og ffmpeg, men ikke nett)
Mål: sikre at pipeline-komponenter fungerer sammen lokalt.

- ffmpeg wrapper:
  - konverter fixture audio til standard wav (16kHz mono)
  - assert output eksisterer, varighet innen toleranse
- pipeline med fake clients:
  - FakeDownloader leverer fixture `audio_original.wav`
  - FakeVadProcessor returner enten:
    - ferdig `audio_vad.wav` fixture, eller
    - kjør policy på mock segments og skriv wav (valgfritt)
  - FakeTranscriberClient returnerer deterministisk tekst
  - FakeSummarizerClient returnerer deterministisk markdown
  - assert:
    - artifacts finnes på disk
    - DB har riktige rader
    - status går til `done`

**Krav:** Ingen nettverk. Ingen credits.

#### C) Contract / snapshot tests
Mål: hindre utilsiktede formatendringer.

- API contract snapshots:
  - `/metadata` respons shape
  - `/jobs/{id}` respons shape
- Markdown contract:
  - `summary.md` inneholder forventede seksjoner og overskrifter
  - snapshot av “golden” markdown fra FakeSummarizerClient

#### D) Live tests (kostbare – eksplisitt opt-in)
Kjøres kun hvis:
- `RUN_LIVE_TESTS=1` og secrets er satt.

Testene skal være små og billige:
- Voxtral: 30–60 sek audio fixture (maks)
- Mistral: kort tekst (maks noen avsnitt)
- yt-dlp metadata: `--dump-json` på en stabil, intern test-URL (hvis tilgjengelig)

**Guardrails:**
- hard timeout
- rate limiting (1 kall per test)
- tydelig logg som viser at dette er live/credits

### 11.4 Anti-credit sikkerhetsmekanismer (obligatorisk)
- Implementer `NetworkGuard` i tests som feiler hvis kode forsøker nettverk i offline suites:
  - patch `requests`, `httpx`, `socket`
- Eksterne klienter må kreve eksplisitt `allow_live=True` eller env flag.

---

## 12) Job-modell og parallell kjøring

- Jobber skal kunne kjøre parallelt (flere forelesninger samtidig).
- SQLite brukes for status + historikk.
- Backend runner:
  - oppdaterer `jobs.status` på hvert steg
  - skriver progress (valgfritt men anbefalt)
- Ved restart:
  - jobs i “in-progress” kan settes til `error` eller `queued` (policy definert i code).

---

## 13) UI-krav (v1)

- Single-page UI:
  - URL input med auto metadata fetch
  - språkvalg
  - jobbkort per jobb med status/progress
- Navigasjon:
  - kursliste → dato → forelesning → view summary
- Markdown render:
  - støtte LaTeX via MathJax

**Negative UI requirements:**
- Ikke kompleks frontend-stack (ingen React/Next) i v1.
- Ikke redigering av summary.
- Ikke login-system i v1.

---

## 14) Konfig (env)

`.env`:
- `MISTRAL_API_KEY=...`
- `VOXTRAL_API_KEY=...`
- `DATA_DIR=./data`
- `SQLITE_PATH=./catchup.sqlite`
- `LONG_SILENCE_SEC=1.6`
- `KEEP_SILENCE_SEC=0.35`
- `PADDING_SEC=0.2`
- `CHUNK_MINUTES=15`
- `CHUNK_OVERLAP_SEC=6`

`cookies.txt` må ligge i repo root.

---

## 15) Milepæler (implementasjonsrekkefølge)

1) Repo scaffolding + config + DB init + models
2) `/metadata` med yt-dlp dump-json (kun metadata, ingen download)
3) Job runner + status transitions (dummy pipeline)
4) Download + ffmpeg → `audio_original.wav` (offline fixture test)
5) VAD policy + `audio_vad.wav` (mocks + offline integration)
6) Transcribe (fake client) + chunking + artifacts
7) Summarize (fake client) + markdown rendering
8) UI: jobs + browse + rendered markdown + MathJax
9) Live tests: tiny Voxtral + tiny Mistral (opt-in)

---

## 16) Done-kriterier (v1)

- Kan lime inn Panopto URL og få `summary.md` lagret og renderet i UI
- Flere jobber kan kjøre parallelt uten kollisjoner
- SQLite gir historikk over forelesninger og artifacts
- Standard testsuite:
  - kjører offline, deterministisk, uten credits
  - har nettverks-guard og tydelig live-test skille
