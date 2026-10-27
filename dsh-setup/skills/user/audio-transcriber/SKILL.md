---
name: audio-transcriber
description: Transcribe local audio or extracted video audio into timestamped Markdown, SRT, and JSON outputs using faster-whisper when available. Use when the user asks for 录音转写, 音频转文字, transcription, speech-to-text, meeting/call transcript, subtitle generation, or speaker-labeled Chinese audio; supports optional male/female speaker mapping such as 男的是我、女的是JoJo.
---

# Audio Transcriber

## Workflow

Use this skill for local audio transcription tasks, especially Chinese meeting or call recordings.

1. Confirm the source audio file exists and note its size/duration when possible.
2. Prefer local transcription with `scripts/transcribe_audio.py`.
3. Reuse the known local cache first:
   - vendor: `C:\tmp\newbi_whisper_vendor`
   - models: `C:\tmp\newbi_whisper_models`
4. If `faster_whisper` imports fail because the cache is unreadable, try an escalated run before reinstalling dependencies.
5. Generate outputs into a project-local folder, not beside the source audio unless the user asks.
6. Report the Markdown transcript path first, then SRT/JSON paths, duration, segment count, and any speaker-label caveat.

## Quick Command

Run with the bundled Python when available:

```powershell
& 'C:\Users\邓庆帅\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  'C:\Users\邓庆帅\.codex\skills\audio-transcriber\scripts\transcribe_audio.py' `
  --audio 'C:\path\to\recording.m4a' `
  --out-dir 'C:\path\to\workspace\transcript_output' `
  --title '录音转写' `
  --low-speaker '我' `
  --high-speaker 'JoJo'
```

## Speaker Labels

For two-speaker male/female audio, pass:

- `--low-speaker` for the lower-pitch voice, usually male.
- `--high-speaker` for the higher-pitch voice, usually female.
- `--pitch-threshold` to tune the split; default is `155` Hz.

Always describe these labels as automatic first-pass diarization. Short utterances, overlapping speech, background noise, or unusual vocal pitch can require manual correction.

If the user gives explicit names, preserve them exactly in output labels. For example, "男的是我，女的是JoJo" maps to `--low-speaker '我' --high-speaker 'JoJo'`.

## Dependency Notes

The script needs `faster_whisper`, `av`, and `numpy`. On this machine, prior project work may already have installed them under `C:\tmp\newbi_whisper_vendor` with model cache under `C:\tmp\newbi_whisper_models`.

If dependencies are missing and the user allows installation, install into a scoped temp/vendor directory rather than global Python:

```powershell
& '<python.exe>' -m pip install --target 'C:\tmp\audio_transcriber_vendor' faster-whisper numpy
```

Then run the script with `--vendor-dir 'C:\tmp\audio_transcriber_vendor'`.

## Output Contract

The script writes:

- `<safe_title>_转写稿.md`: human-readable timestamped transcript.
- `<safe_title>_转写稿.srt`: subtitle format with speaker labels.
- `<safe_title>_transcript.json`: structured metadata and segments.

Keep raw audio files untouched.
