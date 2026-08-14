"""Build a Playback Notes Sync-style Pro Tools session from its CSV export."""

import csv
import os
import re

from pt_api import ProToolsSession, TimecodeEngine


CLIP_GROUP_DURATION_TC = (0, 0, 2, 0)
PTX_START_HOURS = 10

# CSV header name -> exact track name in pb_notes_sync_template.ptx.
TRACK_BY_CSV_COLUMN = {
    "MIX": "MIX",
    "DIAL": "DIAL",
    "FX": "SFX",
    "STP": "STEPS",
    "FOL": "FOLEY",
    "ADR": "ADR",
    "CON": "CONCEP",
}
CSV_REQUIRED_COLUMNS = ("TIME CODE", *TRACK_BY_CSV_COLUMN.keys(), "DONE", "NOTES")


def _parse_elapsed_seconds(value, row_number):
    """Parse current compact MMSS and legacy session-timecode CSV exports."""
    raw_value = value
    value = value.strip()

    # Earlier Playback Notes Sync exports use the session time directly, e.g.
    # ``10:41:12:``. Convert it back to elapsed seconds because the PTX writer
    # applies the template's 10-hour session offset below.
    timecode_match = re.fullmatch(r"(\d+)[;:](\d{1,2})[;:](\d{1,2})[;:]?", value)
    if timecode_match:
        hours, minutes, seconds = map(int, timecode_match.groups())
        if minutes >= 60 or seconds >= 60:
            raise ValueError(
                f"Ligne {row_number}: TIME CODE « {raw_value} » est impossible "
                "(minutes et secondes doivent être entre 00 et 59)."
            )
        elapsed_seconds = (hours - PTX_START_HOURS) * 3600 + minutes * 60 + seconds
        if elapsed_seconds < 0:
            raise ValueError(
                f"Ligne {row_number}: TIME CODE doit commencer à {PTX_START_HOURS:02d}:00:00:."
            )
        return elapsed_seconds

    # Excel and Numbers can serialize an integer CSV value as ``4112.0`` or
    # ``4112,0``; copy/paste may also introduce regular or non-breaking spaces.
    # These remain the exact same compact MMSS value as Playback Notes Sync's
    # canonical ``4112`` output, so normalize only those harmless variants.
    value = "".join(value.split())
    value = value.lstrip("'")
    match = re.fullmatch(r"(\d+)(?:[.,]0+)?", value)
    if not match:
        raise ValueError(
            f"Ligne {row_number}: TIME CODE « {raw_value} » doit être un entier MMSS "
            "exporté par Playback Notes Sync (ex. 4112) ou un timecode (ex. 10:41:12:)."
        )

    minutes, seconds = divmod(int(match.group(1)), 100)
    if seconds >= 60:
        raise ValueError(f"Ligne {row_number}: les secondes de TIME CODE doivent être entre 00 et 59.")
    return minutes * 60 + seconds


def parse_pb_notes_csv(csv_path):
    """Return validated Playback Notes Sync notes from a UTF-8 CSV export.

    The mobile app exports a 29-column CSV; only its first ten meaningful
    columns are needed here. Extra trailing empty columns are deliberately
    retained as compatible input rather than interpreted as note data.
    """
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        rows = csv.reader(csv_file)
        try:
            header = next(rows)
        except StopIteration as error:
            raise ValueError("Le fichier CSV est vide.") from error

        normalized_header = [cell.strip().upper() for cell in header]
        missing_columns = [
            column for column in CSV_REQUIRED_COLUMNS if column not in normalized_header
        ]
        if missing_columns:
            raise ValueError(
                "Le CSV ne correspond pas à un export Playback Notes Sync. "
                f"Colonnes manquantes : {', '.join(missing_columns)}."
            )
        indexes = {column: normalized_header.index(column) for column in CSV_REQUIRED_COLUMNS}

        notes = []
        for row_number, row in enumerate(rows, start=2):
            if not any(cell.strip() for cell in row):
                continue

            def value(column):
                index = indexes[column]
                return row[index] if index < len(row) else ""

            elapsed_seconds = _parse_elapsed_seconds(value("TIME CODE"), row_number)
            selected_columns = [
                column
                for column in TRACK_BY_CSV_COLUMN
                if value(column).strip().upper() == "X"
            ]
            if len(selected_columns) != 1:
                raise ValueError(
                    f"Ligne {row_number}: sélectionnez exactement une catégorie (X)."
                )

            text = value("NOTES").strip()
            if not text:
                raise ValueError(f"Ligne {row_number}: NOTES ne peut pas être vide.")

            notes.append({
                "elapsed_seconds": elapsed_seconds,
                "track": TRACK_BY_CSV_COLUMN[selected_columns[0]],
                "text": text,
            })

    if not notes:
        raise ValueError("Le CSV ne contient aucune note à exporter.")
    return sorted(notes, key=lambda note: note["elapsed_seconds"])


def create_pb_notes_ptx(csv_path, output_path):
    """Create a PTX session matching Playback Notes Sync's native export."""
    notes = parse_pb_notes_csv(csv_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, "pb_notes_sync_template.ptx")
    if not os.path.isfile(template_path):
        raise FileNotFoundError("Le template Playback Notes Sync est introuvable.")

    session = ProToolsSession(template_path)
    engine = TimecodeEngine(session.sample_rate, session.frame_rate_enum)
    duration_samples = engine.duration_to_samples(*CLIP_GROUP_DURATION_TC)

    used_names = set()
    prepared_notes = []
    for note in notes:
        base_name = note["text"]
        group_name = base_name
        suffix = 2
        while group_name in used_names:
            group_name = f"{base_name} ({suffix})"
            suffix += 1
        used_names.add(group_name)

        elapsed_hours, remainder = divmod(note["elapsed_seconds"], 3600)
        minutes, seconds = divmod(remainder, 60)
        prepared_notes.append({
            "track": note["track"],
            "group_name": group_name,
            "start_samples": engine.timecode_to_samples(
                PTX_START_HOURS + elapsed_hours, minutes, seconds, 0
            ),
        })

    visible_tracks = [
        track for track in TRACK_BY_CSV_COLUMN.values()
        if any(note["track"] == track for note in prepared_notes)
    ]
    session.set_visible_tracks(visible_tracks)

    created_groups = [
        session.create_empty_clip_group(
            note["track"], note["group_name"], note["start_samples"], duration_samples
        )
        for note in prepared_notes
    ]
    session.save(output_path)

    return {
        "group_count": len(created_groups),
        "track_names": visible_tracks,
        "duration_samples": duration_samples,
    }
