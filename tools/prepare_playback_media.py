"""Create verified browser videos from the hash-pinned 8x Nyx recordings.

Example (the output directory may be resumed with the same encoding profile):
    python tools/prepare_playback_media.py --source-map verified-source-map.json \
        --output playback --ffmpeg /path/to/ffmpeg --ffprobe /path/to/ffprobe \
        --ids H1S-01 H1S-03 --workers 4

No source recording is modified. The public manifest contains relative media
paths and source hashes, while local per-record receipts support safe resumption.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
RECEIPT_SCHEMA = "robo-si-browser-media-receipt/1"


class MediaError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaError(f"{Path(args[0]).name} failed: {type(exc).__name__}") from exc
    if result.returncode:
        # Tool diagnostics can contain local paths. Keep them out of receipts and
        # public manifests; the command's exit code identifies the failing stage.
        lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
        safe_lines = []
        for line in lines[-8:]:
            for arg in args:
                if "/" in arg or "\\" in arg:
                    line = line.replace(arg, Path(arg).name)
            safe_lines.append(line)
        detail = " | ".join(safe_lines)[-1400:]
        raise MediaError(f"{Path(args[0]).name} exited {result.returncode}: {detail}")
    return result


def locate_tool(explicit: str | None, mapped: str | None, name: str) -> str:
    candidates = [explicit] if explicit else [mapped, shutil.which(name)]
    for candidate in candidates:
        if candidate:
            path = Path(candidate).expanduser()
            if path.is_file():
                return str(path.resolve())
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
    raise MediaError(f"{name} was not found; pass --{name} with its executable path")


def positive_number(value, name: str) -> float:
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise MediaError(f"Missing or invalid {name}") from exc
    if not math.isfinite(result) or result <= 0:
        raise MediaError(f"Missing or invalid {name}")
    return result


def probe(path: Path, ffprobe: str | None, timeout: int) -> dict:
    if ffprobe is None:
        import av
        try:
            with av.open(str(path)) as container:
                stream = container.streams.video[0]
                codec = stream.codec_context
                duration = (float(stream.duration * stream.time_base)
                            if stream.duration is not None else float(container.duration / av.time_base))
                return {
                    "codec": codec.name, "pix_fmt": codec.format.name,
                    "width": codec.width, "height": codec.height,
                    "fps": positive_number(float(stream.average_rate), "frame rate"),
                    "duration_s": positive_number(duration, "duration"),
                    "frames": stream.frames or None,
                    "level": None, "profile": codec.profile,
                }
        except (IndexError, TypeError, ValueError, AttributeError, av.FFmpegError) as exc:
            raise MediaError("PyAV could not read complete video metadata") from exc
    result = run([
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries",
        "stream=codec_name,profile,level,pix_fmt,width,height,avg_frame_rate,r_frame_rate,duration,nb_frames:format=duration,size",
        "-of", "json", str(path),
    ], timeout)
    try:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        fmt = data.get("format", {})
        rate = stream.get("avg_frame_rate", "0/0")
        if rate in ("0/0", "0", "N/A"):
            rate = stream.get("r_frame_rate", "0/0")
        fps = float(Fraction(rate))
        duration = stream.get("duration")
        if duration in (None, "N/A"):
            duration = fmt.get("duration")
        return {
            "codec": stream["codec_name"], "pix_fmt": stream.get("pix_fmt"),
            "width": int(stream["width"]), "height": int(stream["height"]),
            "fps": positive_number(fps, "frame rate"),
            "duration_s": positive_number(duration, "duration"),
            "frames": int(stream["nb_frames"]) if stream.get("nb_frames", "N/A") != "N/A" else None,
            "level": stream.get("level"), "profile": stream.get("profile"),
        }
    except (KeyError, ValueError, IndexError, ZeroDivisionError, TypeError) as exc:
        raise MediaError("ffprobe returned incomplete video metadata") from exc


def probe_image(path: Path, ffprobe: str | None, timeout: int) -> dict:
    if ffprobe is None:
        import av
        try:
            with av.open(str(path)) as container:
                codec = container.streams.video[0].codec_context
                return {"codec_name": codec.name, "width": codec.width, "height": codec.height}
        except (IndexError, av.FFmpegError) as exc:
            raise MediaError("PyAV could not read the generated poster") from exc
    result = run([ffprobe, "-v", "error", "-select_streams", "v:0",
                  "-show_entries", "stream=codec_name,width,height", "-of", "json", str(path)], timeout)
    try:
        return json.loads(result.stdout)["streams"][0]
    except (ValueError, KeyError, IndexError) as exc:
        raise MediaError("ffprobe returned incomplete poster metadata") from exc


def faststart(path: Path) -> bool:
    """Check top-level MP4 atoms, including extended and end-of-file sizes."""
    length = path.stat().st_size
    offset, moov, mdat = 0, None, None
    with path.open("rb") as stream:
        while offset + 8 <= length:
            stream.seek(offset)
            size, kind = struct.unpack(">I4s", stream.read(8))
            header = 8
            if size == 1:
                raw = stream.read(8)
                if len(raw) != 8:
                    return False
                size, header = struct.unpack(">Q", raw)[0], 16
            elif size == 0:
                size = length - offset
            if size < header or offset + size > length:
                return False
            if kind == b"moov" and moov is None:
                moov = offset
            if kind == b"mdat" and mdat is None:
                mdat = offset
            offset += size
    return moov is not None and mdat is not None and moov < mdat


def target_geometry(source: dict, profile: dict) -> tuple[int, int]:
    scale = min(1.0, profile["max_width"] / source["width"], profile["max_height"] / source["height"])
    width = max(2, math.floor(source["width"] * scale / 2) * 2)
    height = max(2, math.floor(source["height"] * scale / 2) * 2)
    return width, height


def expected_hash(record: dict) -> str:
    value = str(record.get("source_8x_sha256", "")).lower()
    if not HASH_RE.fullmatch(value):
        raise MediaError("Immutable recording manifest lacks a valid source hash")
    return value


def cached_record(receipt: Path, output: Path, source_hash: str, profile: dict) -> dict | None:
    if not receipt.is_file():
        return None
    try:
        data = read_json(receipt)
        record = data["record"]
        if data.get("schema") != RECEIPT_SCHEMA or data.get("profile") != profile:
            return None
        if record["source_sha256"] != source_hash or not all(record.get(k) is True for k in ("full_decode_verified", "faststart")):
            return None
        for kind in ("video", "poster"):
            relative = Path(record[f"{kind}_path"])
            target = (output / relative).resolve()
            if relative.is_absolute() or not target.is_relative_to(output.resolve()):
                return None
            if not target.is_file() or sha256(target) != record[f"{kind}_sha256"]:
                return None
        return record
    except (OSError, ValueError, KeyError, TypeError):
        return None


def prepare_one(mapped: dict, original: dict, output: Path, profile: dict,
                ffmpeg: str, ffprobe: str | None, threads: int, timeout: int) -> tuple[dict, bool, float]:
    started = time.monotonic()
    rid = mapped["record_id"]
    source_path = Path(mapped.get("input_path") or mapped["source_path"]).expanduser()
    if not source_path.is_file():
        raise MediaError("Verified source recording is missing")
    source_hash = expected_hash(original)
    for field in ("source_sha256", "actual_sha256"):
        if mapped.get(field) != source_hash:
            raise MediaError(f"Source-map {field} differs from the immutable recording manifest")
    if sha256(source_path) != source_hash:
        raise MediaError("Source bytes differ from the immutable recording manifest")
    receipt = output / "receipts" / f"{rid}.json"
    cached = cached_record(receipt, output, source_hash, profile)
    if cached:
        return cached, True, time.monotonic() - started

    source = probe(source_path, ffprobe, timeout)
    if source["width"] != int(mapped["width"]) or source["height"] != int(mapped["height"]):
        raise MediaError("Probed source dimensions differ from the verified source map")
    if abs(source["fps"] - float(mapped["fps"])) > .01:
        raise MediaError("Probed source frame rate differs from the verified source map")
    source_duration = float(mapped["duration_s"])
    if abs(source["duration_s"] - source_duration) > 1 / source["fps"] + .005:
        raise MediaError("Probed source duration differs from the verified source map")
    frozen_duration = original.get("source_8x_duration_s")
    if frozen_duration and abs(source_duration - float(frozen_duration)) > 1 / source["fps"] + .005:
        raise MediaError("Source-map duration differs from the immutable recording manifest")

    width, height = target_geometry(source, profile)
    target_fps = min(source["fps"], profile["max_fps"])
    macroblocks_per_second = math.ceil(width / 16) * math.ceil(height / 16) * target_fps
    level = "4.2" if macroblocks_per_second > 245760 else "4.1"
    filters = []
    if (width, height) != (source["width"], source["height"]):
        filters.append(f"scale={width}:{height}:flags=lanczos")
    if source["fps"] > profile["max_fps"] + .0001:
        filters.append(f"fps=fps={profile['max_fps']}:round=near")
    video_rel = f"media/videos/{rid}.mp4"
    poster_rel = f"media/posters/{rid}.jpg"
    video, poster = output / video_rel, output / poster_rel
    video.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    temporary_video = video.with_name(f".{rid}.{token}.partial.mp4")
    temporary_poster = poster.with_name(f".{rid}.{token}.partial.jpg")
    try:
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                   "-filter_threads", "1", "-i", str(source_path), "-map", "0:v:0"]
        if filters:
            command += ["-vf", ",".join(filters)]
        command += ["-c:v", "libx264", "-preset", profile["preset"], "-crf", str(profile["crf"]),
                    "-pix_fmt", "yuv420p", "-profile:v", "high", "-level:v", level,
                    "-threads", str(threads), "-fps_mode", "passthrough", "-an",
                    "-map_metadata", "-1", "-t", f"{source_duration:.9f}",
                    "-movflags", "+faststart", str(temporary_video)]
        run(command, timeout)
        encoded = probe(temporary_video, ffprobe, timeout)
        if encoded["codec"] != "h264" or encoded["pix_fmt"] != "yuv420p":
            raise MediaError("Browser derivative is not H.264 yuv420p")
        if (encoded["width"], encoded["height"]) != (width, height):
            raise MediaError("Browser derivative has unexpected dimensions")
        if encoded["width"] > source["width"] or encoded["height"] > source["height"]:
            raise MediaError("Browser derivative was unexpectedly upscaled")
        if abs(encoded["fps"] - target_fps) > .01:
            raise MediaError("Browser derivative has unexpected frame rate")
        tolerance = 1 / encoded["fps"] + .005
        if abs(encoded["duration_s"] - source_duration) > tolerance:
            raise MediaError(f"Browser derivative duration {encoded['duration_s']:.9f}s differs from source "
                             f"{source_duration:.9f}s by more than one output frame ({tolerance:.9f}s)")
        if not faststart(temporary_video):
            raise MediaError("Browser MP4 does not place moov before mdat")
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-xerror",
             "-i", str(temporary_video), "-map", "0:v:0", "-an", "-f", "null", "-"], timeout)

        selected_time = mapped.get("poster_time_s")
        origin = "source-map" if selected_time is not None else "ten-percent-fallback"
        selected_time = float(selected_time) if selected_time is not None else source_duration * .1
        if not math.isfinite(selected_time) or selected_time < 0:
            raise MediaError("Source-map poster timestamp is invalid")
        poster_time = min(selected_time, max(0.0, encoded["duration_s"] - 1 / encoded["fps"]))
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
             "-ss", f"{poster_time:.9f}", "-i", str(temporary_video), "-map", "0:v:0",
             "-frames:v", "1", "-q:v", "2", "-update", "1", str(temporary_poster)], timeout)
        image = probe_image(temporary_poster, ffprobe, timeout)
        if image.get("codec_name") != "mjpeg" or (int(image["width"]), int(image["height"])) != (width, height):
            raise MediaError("Poster does not match the browser video resolution")

        record = {
            "record_id": rid, "video_path": video_rel, "poster_path": poster_rel,
            "video_sha256": sha256(temporary_video), "poster_sha256": sha256(temporary_poster),
            "source_sha256": source_hash,
            "source_resolution": [source["width"], source["height"]],
            "source_fps": source["fps"], "source_duration_s": source_duration,
            "width": width, "height": height, "fps": encoded["fps"],
            "duration_s": encoded["duration_s"], "bytes": temporary_video.stat().st_size,
            "poster_bytes": temporary_poster.stat().st_size,
            "codec": encoded["codec"], "pix_fmt": encoded["pix_fmt"], "level": level,
            "full_decode_verified": True, "faststart": True,
            "duration_error_s": round(encoded["duration_s"] - source_duration, 9),
            "poster_time_s": poster_time, "poster_time_origin": origin,
        }
        os.replace(temporary_video, video)
        os.replace(temporary_poster, poster)
        atomic_json(receipt, {
            "schema": RECEIPT_SCHEMA, "profile": profile, "record": record,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(time.monotonic() - started, 3),
        })
        return record, False, time.monotonic() - started
    finally:
        # These two uniquely named files are created by this worker only.
        temporary_video.unlink(missing_ok=True)
        temporary_poster.unlink(missing_ok=True)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-map", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/video-gallery.json")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe", help="Metadata executable; uses installed PyAV when omitted and FFprobe is unavailable")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--threads", type=int, default=2, help="FFmpeg encoder threads per worker")
    parser.add_argument("--ids", nargs="+", help="Record IDs separated by spaces or commas; default: every source-map record")
    parser.add_argument("--max-fps", type=float, default=30)
    parser.add_argument("--max-height", type=int, default=1080)
    parser.add_argument("--max-width", type=int, default=1920)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="medium", choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"])
    parser.add_argument("--timeout", type=int, default=7200, help="Timeout in seconds for each FFmpeg/FFprobe command")
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 32 or not 1 <= args.threads <= 64:
        parser.error("--workers must be 1–32 and --threads must be 1–64")
    if not 1 <= args.max_fps <= 60 or not 2 <= args.max_height <= 1080 or not 2 <= args.max_width <= 1920:
        parser.error("Browser profile limits are 1–60 fps, height 2–1080 and width 2–1920")
    if not 0 <= args.crf <= 51 or args.timeout < 1:
        parser.error("--crf must be 0–51 and --timeout positive")
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    started = time.monotonic()
    try:
        source_map = read_json(args.source_map)
        catalog = read_json(args.manifest)
        if source_map.get("all_verified") is not True:
            raise MediaError("Source map must be marked all_verified")
        manifest_hash = sha256(args.manifest)
        if source_map.get("source_manifest_sha256") != manifest_hash:
            raise MediaError("Source map was verified against a different recording manifest")
        originals = {r["record_id"]: r for r in catalog["records"]}
        mapped = {r["record_id"]: r for r in source_map["records"]}
        if len(mapped) != len(source_map["records"]):
            raise MediaError("Duplicate record IDs in source map")
        if not all(ID_RE.fullmatch(rid) for rid in mapped):
            raise MediaError("Source map contains an unsafe record ID")
        selected = list(dict.fromkeys(part for value in args.ids for part in value.split(",") if part)) if args.ids else list(mapped)
        if not selected or set(selected) - mapped.keys() or set(selected) - originals.keys():
            raise MediaError("Requested record IDs are absent from the verified map or immutable manifest")
        ffmpeg = locate_tool(args.ffmpeg, source_map.get("ffmpeg_path"), "ffmpeg")
        try:
            ffprobe = locate_tool(args.ffprobe, source_map.get("ffprobe_path"), "ffprobe")
        except MediaError:
            if args.ffprobe:
                raise
            try:
                import av  # noqa: F401 — optional local metadata reader
            except ImportError as exc:
                raise MediaError("Metadata reader unavailable; pass --ffprobe or install PyAV") from exc
            ffprobe = None
        encoder_version = run([ffmpeg, "-version"], 30).stdout.splitlines()[0]
        profile = {
            "encoder": "libx264", "crf": args.crf, "preset": args.preset,
            "max_width": args.max_width, "max_height": args.max_height,
            "max_fps": args.max_fps, "pixel_format": "yuv420p", "scale_filter": "lanczos",
            "timeline": "sealed-source-duration",
            "audio": False, "poster": "source-map-time-jpeg-q2", "ffmpeg_version": encoder_version,
        }
        output = args.output.expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        completed, failures, cache_hits = {}, [], 0
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(prepare_one, mapped[rid], originals[rid], output, profile,
                                   ffmpeg, ffprobe, args.threads, args.timeout): rid for rid in selected}
            for future in as_completed(futures):
                rid = futures[future]
                try:
                    record, cached, elapsed = future.result()
                    completed[rid] = record
                    cache_hits += int(cached)
                    print(json.dumps({"record_id": rid, "status": "cached" if cached else "prepared",
                                      "bytes": record["bytes"], "elapsed_s": round(elapsed, 2)}, ensure_ascii=False), flush=True)
                except Exception as exc:
                    failure = {"record_id": rid, "error": str(exc) if isinstance(exc, MediaError) else type(exc).__name__}
                    failures.append(failure)
                    print(json.dumps({**failure, "status": "error"}, ensure_ascii=False), flush=True)
        prepared = [completed[rid] for rid in selected if rid in completed]
        public = {"schema": "robo-si-browser-media/1", "source_manifest_sha256": manifest_hash,
                  "profile": profile, "records": prepared}
        atomic_json(output / "playback-media.json", public)
        report = {
            "requested": len(selected), "prepared": len(prepared), "cache_hits": cache_hits,
            "complete": not failures, "video_bytes": sum(r["bytes"] for r in prepared),
            "poster_bytes": sum(r["poster_bytes"] for r in prepared),
            "source_duration_s": round(sum(r["source_duration_s"] for r in prepared), 6),
            "output_duration_s": round(sum(r["duration_s"] for r in prepared), 6),
            "max_duration_error_s": max((abs(r["duration_error_s"]) for r in prepared), default=0),
            "elapsed_s": round(time.monotonic() - started, 3), "errors": failures,
        }
        atomic_json(output / "prepare-report.json", report)
        print(json.dumps({"summary": report}, ensure_ascii=False), flush=True)
        return 1 if failures else 0
    except (OSError, ValueError, KeyError, MediaError) as exc:
        print(f"Preparation stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
