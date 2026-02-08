# CatchUp v1 - Komplett Testplan

## Mål
Verifisere at hele CatchUp v1 systemet fungerer korrekt uten å bruke API credits.

## Testfaser

### Fase 1: Statisk Analyse
- [ ] Sjekk Python syntaks på alle filer
- [ ] Verifiser at alle imports kan løses
- [ ] Sjekk at alle avhengigheter er tilgjengelige

### Fase 2: Unit Tests
- [ ] Test parsing utilities (course code, date, source_uid, etc.)
- [ ] Test database operasjoner
- [ ] Test konfigurasjon loading

### Fase 3: Integration Tests
- [ ] Test full pipeline med fake clients
- [ ] Test database persistence
- [ ] Test artifact creation
- [ ] Test error handling

### Fase 4: API Tests
- [ ] Test FastAPI endpoints
- [ ] Test metadata endpoint
- [ ] Test job creation og status
- [ ] Test rendering endpoint

### Fase 5: Frontend Validation
- [ ] Sjekk at HTML er valid
- [ ] Verifiser at JavaScript ikke har syntaksfeil

### Fase 6: NetworkGuard Verification
- [ ] Verifiser at NetworkGuard blokkerer nettverkskall
- [ ] Sjekk at offline tests ikke gjør eksterne kall

## Suksesskriterier
- ✅ Alle unit tests bestått
- ✅ Alle integration tests bestått
- ✅ Ingen nettverkskall i offline tests
- ✅ Pipeline kjører fra start til slutt med fake clients
- ✅ Alle artifacts blir opprettet
- ✅ Database får korrekte data

## Ikke-mål
- ❌ Ingen live API tests (sparer credits)
- ❌ Ingen faktisk yt-dlp nedlasting
- ❌ Ingen faktisk VAD prosessering med ML
