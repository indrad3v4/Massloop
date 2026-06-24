"""System prompts for the Massloop music orchestrator agent."""

MUSIC_ORCHESTRATOR_SYSTEM_PROMPT = """\
You are Massloop, an expert AI DJ and music producer for underground electronic music.
Your job is to translate performance context into precise Suno generation parameters.

You have access to these tools:
- get_style_suggestions: returns style tags for a given BPM, energy, and venue.
- generate_track: submits a generation task to CometAPI Suno and returns a task_id.
- poll_track: polls CometAPI until the track is ready and returns the audio URL.

Rules:
1. Keep prompts under 400 characters when possible.
2. Always generate instrumental tracks for live DJ use unless vocals are explicitly requested.
3. Match BPM to the requested range. Do not invent BPMs outside the artist's range.
4. Use concrete, sensory language: "analog synth pads", "distorted 909 kick", "tape hiss".
5. Avoid mainstream EDM clichés. Favor underground textures: industrial, dub, acid, hypnotic.
6. When in doubt, prefer minimal and groovy over busy and maximal.
7. Return a clear decision: generate, extend, or mix.

Output format:
- decision: one of [generate, extend, mix]
- reasoning: one sentence
- prompt: the Suno gpt_description_prompt
- tags: comma-separated style tags
- title: short track title
- mv: Suno model version (default chirp-v4)
"""

STYLE_GUIDE = {
    "raw_techno": "stripped-down warehouse techno, distorted kick, industrial hats, no melody",
    "acid_techno": "Roland TB-303 acid bassline, squelch, 909 drums, hypnotic loop",
    "industrial": "dark mechanical techno, metal percussion, distorted synth stabs, claustrophobic",
    "dub_techno": "deep chords, delay and reverb, sub bass, sparse percussion, underwater atmosphere",
    "hypnotic": "repetitive loops, subtle modulation, trance-inducing, minimal percussion",
    "minimal": "microhouse elements, subtle clicks, deep bass, reduced arrangement",
    "hardgroove": "fast rolling percussion, driving bassline, high energy, club pressure",
    "schranz": "aggressive distorted kick, harsh industrial textures, extreme energy",
    "deep_house": "warm analog pads, gentle kick, soft hats, sunrise vibe, soulful",
}


def build_orchestrator_context(
    bpm: int,
    energy: float,
    venue: str,
    style: str,
    theme: str = "",
    crowd_energy: float = 0.5,
    artist_brand: dict | None = None,
) -> str:
    """Build a concise context string for the orchestrator agent."""
    lines = [
        f"BPM: {bpm}",
        f"Energy: {energy:.2f}",
        f"Crowd energy: {crowd_energy:.2f}",
        f"Venue: {venue}",
        f"Style: {style}",
    ]
    if theme:
        lines.append(f"Theme: {theme}")

    # Inject artist brand identity if provided
    if artist_brand:
        name = artist_brand.get("artist_name", "") or artist_brand.get("name", "")
        genre = artist_brand.get("artist_genre", "") or artist_brand.get("genre", "")
        signature = artist_brand.get("artist_signature", "") or artist_brand.get("signature", "")
        tone = artist_brand.get("artist_tone", "") or artist_brand.get("tone", "")
        negative_tags = artist_brand.get("artist_negative_tags", "") or artist_brand.get("negative_tags", "")
        bpm_min = artist_brand.get("artist_bpm_min")
        bpm_max = artist_brand.get("artist_bpm_max")

        lines.append("")
        lines.append("--- Artist Identity ---")
        if name:
            lines.append(f"Artist: {name}")
        if genre:
            lines.append(f"Genre: {genre}")
        if signature:
            lines.append(f"Signature sound: {signature}")
        if tone:
            lines.append(f"Tone: {tone}")
        if negative_tags:
            lines.append(f"Avoid: {negative_tags}")
        if bpm_min is not None or bpm_max is not None:
            bpm_min_str = str(bpm_min) if bpm_min is not None else "?"
            bpm_max_str = str(bpm_max) if bpm_max is not None else "?"
            lines.append(f"BPM range: {bpm_min_str}-{bpm_max_str}")
        lines.append("")

    return "\n".join(lines)
