import argparse
import json
import math
import re
import sys
from pathlib import Path


def add_vendor_paths(paths: list[str]) -> None:
    for path in reversed(paths):
        if path and Path(path).exists():
            sys.path.insert(0, path)


def import_deps():
    try:
        import av
        import numpy as np
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise SystemExit(
            "Missing or unreadable transcription dependencies. "
            "Install faster-whisper into a vendor dir or run with permissions that can read the cache. "
            f"Original error: {exc}"
        ) from exc
    return av, np, WhisperModel


def safe_name(text: str) -> str:
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", text).strip(" ._")
    return text or "audio_transcript"


def fmt_ts(seconds: float, srt: bool = False) -> str:
    millis = int(round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    sep = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{ms:03d}"


def load_audio_mono_16k(path: Path, av, np):
    container = av.open(str(path))
    stream = next(s for s in container.streams if s.type == "audio")
    resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)
    chunks = []
    for frame in container.decode(stream):
        resampled = resampler.resample(frame)
        if resampled is None:
            continue
        if not isinstance(resampled, list):
            resampled = [resampled]
        for out_frame in resampled:
            chunks.append(out_frame.to_ndarray().reshape(-1).astype(np.float32) / 32768.0)
    if not chunks:
        return np.zeros(0, dtype=np.float32), 16000
    return np.concatenate(chunks), 16000


def estimate_pitch_hz(samples, sample_rate: int, np) -> float | None:
    if samples.size < sample_rate // 5:
        return None
    samples = samples - float(np.mean(samples))
    rms = float(np.sqrt(np.mean(samples * samples)))
    if rms < 0.005:
        return None

    frame_size = int(sample_rate * 0.04)
    hop = int(sample_rate * 0.02)
    min_lag = int(sample_rate / 320)
    max_lag = int(sample_rate / 70)
    pitches = []
    for start in range(0, max(1, samples.size - frame_size), hop):
        frame = samples[start : start + frame_size]
        if frame.size < frame_size:
            break
        frame = frame * np.hanning(frame.size)
        if float(np.sqrt(np.mean(frame * frame))) < 0.003:
            continue
        corr = np.correlate(frame, frame, mode="full")[frame.size - 1 :]
        if corr[0] <= 0:
            continue
        window = corr[min_lag:max_lag]
        if window.size == 0:
            continue
        lag = int(np.argmax(window) + min_lag)
        strength = float(corr[lag] / corr[0])
        if strength >= 0.25:
            pitches.append(sample_rate / lag)
    if not pitches:
        return None
    return float(np.median(pitches))


def speaker_for_segment(audio, sample_rate: int, start: float, end: float, args, np):
    left = max(0, int((start + 0.05) * sample_rate))
    right = min(audio.size, int((end - 0.05) * sample_rate))
    pitch = estimate_pitch_hz(audio[left:right], sample_rate, np) if right > left else None
    if pitch is None or math.isnan(pitch):
        return args.unknown_speaker, None
    speaker = args.high_speaker if pitch >= args.pitch_threshold else args.low_speaker
    return speaker, pitch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe local audio with faster-whisper.")
    parser.add_argument("--audio", required=True, help="Input audio/video file path.")
    parser.add_argument("--out-dir", required=True, help="Output directory.")
    parser.add_argument("--title", default="audio_transcript", help="Title/base filename for outputs.")
    parser.add_argument("--language", default="zh", help="Whisper language code, default zh.")
    parser.add_argument("--model", default="small", help="faster-whisper model name, default small.")
    parser.add_argument("--device", default="cpu", help="Device, default cpu.")
    parser.add_argument("--compute-type", default="int8", help="Compute type, default int8.")
    parser.add_argument("--model-dir", default=r"C:\tmp\newbi_whisper_models", help="Model download/cache root.")
    parser.add_argument("--vendor-dir", action="append", default=[], help="Extra dependency vendor dir; can repeat.")
    parser.add_argument("--low-speaker", default="低声部", help="Label for lower-pitch voice.")
    parser.add_argument("--high-speaker", default="高声部", help="Label for higher-pitch voice.")
    parser.add_argument("--unknown-speaker", default="未知", help="Label when pitch cannot be estimated.")
    parser.add_argument("--pitch-threshold", type=float, default=155.0, help="Hz threshold for low/high voice split.")
    parser.add_argument("--no-speakers", action="store_true", help="Disable speaker labeling.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audio_path = Path(args.audio)
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    vendor_paths = args.vendor_dir + [r"C:\tmp\newbi_whisper_vendor"]
    add_vendor_paths(vendor_paths)
    av, np, WhisperModel = import_deps()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    title = safe_name(args.title)

    audio, sample_rate = load_audio_mono_16k(audio_path, av, np)
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        download_root=args.model_dir,
    )
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=args.language,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=True,
    )

    segments = []
    for seg in segments_iter:
        text = seg.text.strip()
        if not text:
            continue
        if args.no_speakers:
            speaker, pitch = "", None
        else:
            speaker, pitch = speaker_for_segment(audio, sample_rate, seg.start, seg.end, args, np)
        segments.append(
            {
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "speaker": speaker,
                "pitch_hz": round(pitch, 1) if pitch else None,
                "text": text,
            }
        )

    speaker_note = (
        "Speaker labels are an automatic first pass based on pitch. Review short, noisy, or overlapping speech."
        if not args.no_speakers
        else "Speaker labeling disabled."
    )
    payload = {
        "source": str(audio_path),
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "speaker_note": speaker_note,
        "segments": segments,
    }

    json_path = out_dir / f"{title}_transcript.json"
    md_path = out_dir / f"{title}_转写稿.md"
    srt_path = out_dir / f"{title}_转写稿.srt"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# {args.title} 音频转写",
        "",
        f"> {speaker_note}",
        "",
    ]
    for seg in segments:
        prefix = f"**{seg['speaker']}**：" if seg["speaker"] else ""
        md_lines.append(f"- `{fmt_ts(seg['start'])}` {prefix}{seg['text']}")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    srt_lines = []
    for idx, seg in enumerate(segments, 1):
        prefix = f"{seg['speaker']}：" if seg["speaker"] else ""
        srt_lines.extend(
            [
                str(idx),
                f"{fmt_ts(seg['start'], True)} --> {fmt_ts(seg['end'], True)}",
                f"{prefix}{seg['text']}",
                "",
            ]
        )
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "duration": info.duration,
                "segments": len(segments),
                "markdown": str(md_path),
                "srt": str(srt_path),
                "json": str(json_path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
