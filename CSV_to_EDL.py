#!/usr/bin/env python3
"""
CSV to EDL Converter for Pro Tools
Converts a CSV cue sheet into a Pro Tools-compatible EDL format
"""

import sys
import csv
import re
from pathlib import Path


def normalize_timecode(tc_str):
    """
    Normalize timecode string to HH:MM:SS:FF format.
    Input might be like "10:00:06:" - need to add the frame part.
    """
    # Remove any whitespace
    tc_str = tc_str.strip()
    
    # Count colons
    parts = tc_str.split(':')
    
    # If it ends with a colon or has only 3 parts, add ":00" for frames
    if len(parts) == 3 or (len(parts) == 4 and parts[3] == ''):
        tc_str = tc_str.rstrip(':') + ':00'
    
    # Validate format
    if not re.match(r'^\d{2}:\d{2}:\d{2}:\d{2}$', tc_str):
        raise ValueError(f"Invalid timecode format: {tc_str}")
    
    return tc_str


def add_timecode(tc_str, duration_tc):
    """
    Add two timecodes together.
    Both should be in HH:MM:SS:FF format.
    """
    def tc_to_frames(tc, fps=24):
        parts = list(map(int, tc.split(':')))
        h, m, s, f = parts
        return (h * 3600 + m * 60 + s) * fps + f
    
    def frames_to_tc(frames, fps=24):
        f = frames % fps
        s = (frames // fps) % 60
        m = (frames // (fps * 60)) % 60
        h = (frames // (fps * 3600))
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"
    
    frames1 = tc_to_frames(tc_str)
    frames2 = tc_to_frames(duration_tc)
    total_frames = frames1 + frames2
    
    return frames_to_tc(total_frames)


def csv_to_edl(csv_file, output_edl, frame_rate=23.976, sample_rate=48000, bit_depth=24):
    """
    Convert CSV cue sheet to Pro Tools EDL format.
    """
    print(f"\n{'='*60}")
    print(f"CSV to EDL Converter")
    print(f"{'='*60}")
    print(f"Input:  {csv_file}")
    print(f"Output: {output_edl}")
    print(f"{'='*60}\n")
    
    # Read CSV file
    with open(csv_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.reader(f)
        rows = list(reader)
    
    if len(rows) < 2:
        print("ERROR: CSV file must have at least 2 rows (header + data)")
        sys.exit(1)
    
    # Parse header row
    headers = rows[0]
    print(f"Found {len(headers)} columns")
    
    # Find column indices
    timecode_col = 0  # First column is always timecode
    notes_col = None
    
    # Find NOTES column
    for i, header in enumerate(headers):
        if header.strip().upper() in ['NOTES', 'NOTE']:
            notes_col = i
            break
    
    if notes_col is None:
        print("ERROR: Could not find NOTES column")
        sys.exit(1)
    
    # Track columns are between timecode and notes (excluding DONE or similar)
    track_columns = []
    for i in range(1, len(headers)):
        if i >= notes_col:
            break
        header = headers[i].strip()
        # Skip empty headers or status columns like DONE
        if header and header.upper() not in ['DONE', 'STATUS', 'COMPLETE']:
            track_columns.append({'index': i, 'name': header})
    
    print(f"\nTrack columns found:")
    for track in track_columns:
        print(f"  - Column {track['index']}: {track['name']}")
    
    print(f"\nNotes column: {notes_col}")
    
    # Parse data rows and organize by track
    track_data = {track['name']: [] for track in track_columns}
    clip_duration = "00:00:01:00"  # Always 1 second
    
    print(f"\nProcessing rows...")
    for row_num, row in enumerate(rows[1:], start=2):  # Skip header
        # Skip empty rows
        if len(row) < 2 or not row[timecode_col].strip():
            continue
        
        try:
            # Get and normalize timecode
            tc = normalize_timecode(row[timecode_col])
            
            # Get clip name from NOTES column
            clip_name = row[notes_col].strip() if notes_col < len(row) else ""
            if not clip_name:
                clip_name = f"Clip_{tc.replace(':', '_')}"
            
            # Make clip name safe (remove special characters that might cause issues)
            # Replace quotes with single quotes, keep basic punctuation
            clip_name = clip_name.replace('"', "'")
            
            # Calculate end timecode
            tc_end = add_timecode(tc, clip_duration)
            
            # Check each track column for 'x' marker
            clips_found = 0
            for track in track_columns:
                col_idx = track['index']
                if col_idx < len(row):
                    cell_value = row[col_idx].strip().lower()
                    if cell_value == 'x':
                        # Add clip to this track
                        track_data[track['name']].append({
                            'timecode': tc,
                            'timecode_end': tc_end,
                            'duration': clip_duration,
                            'clip_name': clip_name
                        })
                        clips_found += 1
            
            if clips_found > 0:
                print(f"  Row {row_num}: TC {tc} - {clips_found} clip(s) - '{clip_name}'")
        
        except Exception as e:
            print(f"  WARNING: Error processing row {row_num}: {e}")
            continue
    
    # Count total clips
    total_clips = sum(len(clips) for clips in track_data.values())
    active_tracks = sum(1 for clips in track_data.values() if len(clips) > 0)
    
    print(f"\nSummary:")
    print(f"  Total clips: {total_clips}")
    print(f"  Active tracks: {active_tracks}")
    
    # Write EDL file
    print(f"\nWriting EDL file...")
    with open(output_edl, 'w', encoding='utf-8') as f:
        # Write header
        f.write("SESSION NAME:\tConverted_from_CSV\n")
        f.write(f"SAMPLE RATE:\t{sample_rate}\n")
        f.write(f"BIT DEPTH:\t{bit_depth}-bit\n")
        f.write("SESSION START TIMECODE:\t00:00:00:00\n")
        f.write(f"TIMECODE FORMAT:\t{frame_rate} Frame\n")
        f.write(f"# OF AUDIO TRACKS:\t{active_tracks}\n")
        f.write(f"# OF AUDIO CLIPS:\t{total_clips}\n")
        f.write(f"# OF AUDIO FILES:\t{total_clips}\n")  # Assume each clip is a unique file
        f.write("\n\n")
        
        # Write tracks
        for track_name, clips in track_data.items():
            if len(clips) == 0:
                continue  # Skip empty tracks
            
            f.write("T R A C K  L I S T I N G\n")
            f.write(f"TRACK NAME:\t{track_name}\n")
            f.write("COMMENTS:\t\n")
            f.write("USER DELAY:\t0 Samples\n")
            f.write("STATE: \n")
            f.write("CHANNEL \tEVENT   \tCLIP NAME                     \tSTART TIME    \tEND TIME      \tDURATION      \tSTATE\n")
            
            # Write clips for this track
            for i, clip in enumerate(clips, start=1):
                # Make clip name safe (remove problematic special characters but keep spaces)
                safe_clip_name = clip['clip_name']
                # Remove only truly problematic characters, keep spaces and basic punctuation
                safe_clip_name = re.sub(r'[^\w\s\-\'àâäçèéêëîïôùûüÿæœÀÂÄÇÈÉÊËÎÏÔÙÛÜŸÆŒ]', '', safe_clip_name)
                safe_clip_name = safe_clip_name.strip()
                
                if not safe_clip_name:
                    safe_clip_name = f"Clip_{i}"
                
                # Format line with proper spacing
                f.write(f"1       \t{i}       \t{safe_clip_name:30s}\t   {clip['timecode']}\t   {clip['timecode_end']}\t   {clip['duration']}\tUnmuted\n")
            
            f.write("\n\n")
    
    print(f"\n{'='*60}")
    print(f"✓ Conversion Complete!")
    print(f"✓ EDL file saved: {output_edl}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python CSV_to_EDL.py <input_csv_file> [frame_rate] [sample_rate] [bit_depth]")
        print("Example: python CSV_to_EDL.py cuesheet.csv 23.976 48000 24")
        print("\nDefaults: 23.976 fps, 48000 Hz, 24-bit\n")
        sys.exit(1)
    
    CSV_FILE = sys.argv[1]
    FRAME_RATE = float(sys.argv[2]) if len(sys.argv) > 2 else 23.976
    SAMPLE_RATE = int(sys.argv[3]) if len(sys.argv) > 3 else 48000
    BIT_DEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    
    # Generate output filename
    input_path = Path(CSV_FILE)
    OUTPUT_EDL = input_path.with_suffix('.edl')
    
    if not input_path.exists():
        print(f"\nERROR: File not found: {CSV_FILE}\n")
        sys.exit(1)
    
    try:
        csv_to_edl(CSV_FILE, OUTPUT_EDL, FRAME_RATE, SAMPLE_RATE, BIT_DEPTH)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
