"""Summarization client using Mistral Small with 2-pass strategy."""
from typing import List
from mistralai import Mistral

from ..pipeline.interfaces import SummarizerClient
from ..core.config import settings


# Prompt version for tracking/debugging
CHUNK_SUMMARY_PROMPT_VERSION = "v1.0"
MERGE_SUMMARY_PROMPT_VERSION = "v1.0"


class MistralSummarizer(SummarizerClient):
    """
    Mistral Small summarizer with 2-pass strategy.

    Pass 1: Summarize each transcript chunk
    Pass 2: Merge chunk summaries into final summary

    Includes negative prompts to prevent hallucinations.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.mistral_api_key
        self.client = Mistral(api_key=self.api_key)
        self.model = "mistral-small-latest"

    async def summarize(
        self,
        transcript: str,
        chunks: List[dict],
        language: str
    ) -> str:
        """
        2-pass summarization strategy.

        1. Summarize each chunk
        2. Merge chunk summaries into final summary
        """
        # Pass 1: Chunk summaries
        chunk_summaries = []
        for chunk in chunks:
            summary = await self._summarize_chunk(chunk['text'], language)
            chunk_summaries.append(summary)

        # Pass 2: Merge summaries
        final_summary = await self._merge_summaries(chunk_summaries, language)

        return final_summary

    async def _summarize_chunk(self, text: str, language: str) -> str:
        """
        Pass 1: Summarize a single chunk.

        Uses strict negative prompts to prevent hallucinations.
        """
        is_norwegian = language == "no"

        if is_norwegian:
            prompt = f"""Du er en presis notat-taker for akademiske forelesninger. Oppsummer følgende transkripsjon i strukturert markdown-format.

VIKTIGE REGLER (NEGATIVT PROMPT):
- Ikke spekuler eller gjett informasjon som ikke er i teksten
- Ikke legg til fakta som ikke står eksplisitt i transkripsjonen
- Ikke referer til prosessen ("i transkripsjonen sies...", "lyden viser...")
- Ikke skriv tidsstempler
- Ikke bruk lange avsnitt uten struktur
- Hvis noe er uklart: skriv "Uklart: ..." i stedet for å gjette

FORMAT:
- Bruk markdown overskrifter (##, ###)
- Bruk LaTeX for matematiske uttrykk: $inline$ eller $$display$$
- Bruk bullet points for lister
- Hold språket presist og akademisk

TRANSKRIPSJON:
{text}

OPPSUMMERING:"""
        else:
            prompt = f"""You are a precise note-taker for academic lectures. Summarize the following transcription in structured markdown format.

IMPORTANT RULES (NEGATIVE PROMPT):
- Do NOT speculate or guess information not in the text
- Do NOT add facts not explicitly stated in the transcription
- Do NOT refer to the process ("the transcription says...", "the audio shows...")
- Do NOT write timestamps
- Do NOT use long paragraphs without structure
- If something is unclear: write "Unclear: ..." instead of guessing

FORMAT:
- Use markdown headings (##, ###)
- Use LaTeX for mathematical expressions: $inline$ or $$display$$
- Use bullet points for lists
- Keep language precise and academic

TRANSCRIPTION:
{text}

SUMMARY:"""

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"Chunk summarization failed: {e}") from e

    async def _merge_summaries(
        self,
        chunk_summaries: List[str],
        language: str
    ) -> str:
        """
        Pass 2: Merge chunk summaries into final summary.

        Uses negative prompts to maintain accuracy.
        """
        is_norwegian = language == "no"

        combined_summaries = "\n\n---\n\n".join([
            f"DEL {i+1}:\n{summary}"
            for i, summary in enumerate(chunk_summaries)
        ])

        if is_norwegian:
            prompt = f"""Du skal merge flere del-oppsummeringer fra en forelesning til ett sammenhengende dokument.

VIKTIGE REGLER (NEGATIVT PROMPT):
- Ikke introduser nye temaer som ikke finnes i del-oppsummeringene
- Ikke "normaliser" uklare punkter til noe som virker riktig - behold usikkerhet eksplisitt
- Ikke endre språk tilfeldig; hold norsk
- Ikke legg til konklusjoner eller analyser som ikke er i oppsummeringene

OPPGAVE:
1. Les alle del-oppsummeringene
2. Organiser innholdet i en logisk struktur med:
   - # Tittel (hovedoverskrift for forelesningen)
   - ## Hovedtemaer (kort oversikt)
   - ## Detaljert innhold (med underoverskrifter)
   - ## Konklusjon (hvis eksplisitt nevnt i oppsummeringene)
3. Behold all viktig informasjon
4. Fjern overflødige repetisjoner
5. Bruk LaTeX for matematikk
6. Bruk markdown-formatering

DEL-OPPSUMMERINGER:
{combined_summaries}

ENDELIG SAMMENDRAG:"""
        else:
            prompt = f"""You are merging multiple chunk summaries from a lecture into one coherent document.

IMPORTANT RULES (NEGATIVE PROMPT):
- Do NOT introduce new topics not found in the chunk summaries
- Do NOT "normalize" unclear points to something that seems right - keep uncertainty explicit
- Do NOT randomly change language; keep English
- Do NOT add conclusions or analyses not in the summaries

TASK:
1. Read all chunk summaries
2. Organize content into logical structure with:
   - # Title (main heading for the lecture)
   - ## Main Topics (brief overview)
   - ## Detailed Content (with subheadings)
   - ## Conclusion (if explicitly mentioned in summaries)
3. Keep all important information
4. Remove redundant repetitions
5. Use LaTeX for mathematics
6. Use markdown formatting

CHUNK SUMMARIES:
{combined_summaries}

FINAL SUMMARY:"""

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"Summary merge failed: {e}") from e
