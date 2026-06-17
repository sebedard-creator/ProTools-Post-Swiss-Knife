# -----------------------------------------------------------------------------
# Enhanced AAF Converter for Pro Tools Compatibility
# 
# This version includes proper audio file descriptors and metadata
# that Pro Tools expects for successful import
# -----------------------------------------------------------------------------

import re
import sys
import math
import wave
import tempfile
import os
from fractions import Fraction
from pathlib import Path

import aaf2 as aaf
from aaf2.exceptions import AAFError


def make_silence_wav(duration_seconds, sample_rate, bit_depth):
    """
    Generate a temporary silent WAV file. Used to embed silent audio essence
    into each MasterMob so that clips are 'online' (not offline) in Pro Tools,
    even though no original source media is available.
    Returns the path to the temp file; caller is responsible for deleting it.
    """
    fd, path = tempfile.mkstemp(suffix='.wav', prefix='aaf_silence_')
    os.close(fd)
    num_samples = int(duration_seconds * sample_rate)
    bytes_per_sample = bit_depth // 8
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)  # mono
        wf.setsampwidth(bytes_per_sample)
        wf.setframerate(sample_rate)
        wf.writeframes(b'\x00' * num_samples * bytes_per_sample)
    return path

# --- Timecode & Frame Rate Logic ---

def get_frame_rate(edl_content):
    """Parses the frame rate from the EDL header."""
    rate_match = re.search(r'TIMECODE FORMAT:\s*([\d\.]+)\s*Frame', edl_content)
    if rate_match:
        return float(rate_match.group(1))
    return 24.0

def get_session_start_tc(edl_content):
    """Parses the session start timecode from the EDL header."""
    tc_match = re.search(r'SESSION START TIMECODE:\s*(\d{2}:\d{2}:\d{2}:\d{2})', edl_content)
    if tc_match:
        return tc_match.group(1)
    return "00:00:00:00"

def timecode_to_frames(tc_str, frame_rate_float):
    """
    Converts a timecode string (HH:MM:SS:FF) to total frames.
    For 23.976 fps, returns the DISPLAY frame count (at 24 fps base) without adjustment.
    The AAF edit_rate (24000/1001) will handle the actual playback rate.
    """
    base_frame_rate = 24.0 
    
    parts = list(map(int, re.split(r'[:;]', tc_str.strip())))
    if len(parts) != 4:
        raise ValueError("Invalid timecode format (HH:MM:SS:FF expected)")
    h, m, s, f = parts
    
    total_frames = (h * 3600 + m * 60 + s) * base_frame_rate + f
    
    # For non-fractional frame rates, adjust
    # For 23.976, we DON'T adjust - the edit_rate handles it
    if not math.isclose(frame_rate_float, 23.976, rel_tol=0.001) and not math.isclose(frame_rate_float, base_frame_rate):
        return int(round(total_frames * (frame_rate_float / base_frame_rate)))
    
    return int(total_frames)


def timecode_to_display_frames(tc_str):
    """
    Converts timecode to display frame count (always at 24fps base, no adjustment).
    This is used for setting the timecode track start value.
    """
    parts = list(map(int, re.split(r'[:;]', tc_str.strip())))
    if len(parts) != 4:
        raise ValueError("Invalid timecode format (HH:MM:SS:FF expected)")
    h, m, s, f = parts
    return (h * 3600 + m * 60 + s) * 24 + f


def frames_to_timecode(frames, frame_rate_float):
    """
    Converts timeline frames back to a timecode string (for display).
    For 23.976 fps with edit_rate 24000/1001, frames are already in display format.
    """
    base_frame_rate = 24.0
    
    # For 23.976, frames are already in display format (no adjustment needed)
    # For other non-24fps rates, reverse the adjustment
    if not math.isclose(frame_rate_float, 23.976, rel_tol=0.001) and not math.isclose(frame_rate_float, base_frame_rate):
        frames = int(round(frames * (base_frame_rate / frame_rate_float)))
        
    f = frames % base_frame_rate
    s = (frames // base_frame_rate) % 60
    m = (frames // (base_frame_rate * 60)) % 60
    h = (frames // (base_frame_rate * 3600))
    return f"{int(h):02}:{int(m):02}:{int(s):02}:{int(f):02}"


# --- Pro Tools Session (PTS) Style Parsing ---

def parse_pts_like_edl(edl_content, frame_rate):
    """
    Parses a Pro Tools Session style export, focusing on audio tracks and clips.
    Extracts events grouped by track.
    """
    print(f"Parsing EDL content (PTS Style) at {frame_rate} FPS...")
    
    track_data = {}
    current_track_name = None
    
    track_header_pattern = re.compile(r'TRACK NAME:\s*(.*)')
    clip_event_pattern = re.compile(
        r'^\s*(\d+)\s*\t\s*'  # 1. Channel + tab
        r'(\d+)\s*\t\s*'      # 2. Event Index + tab
        r'([^\t]+)\t\s*'      # 3. Clip Name (allows spaces, up to tab) + tab
        r'(\d{2}:\d{2}:\d{2}:\d{2})\s*\t\s*'  # 4. Start Time + tab
        r'(\d{2}:\d{2}:\d{2}:\d{2})\s*\t\s*'  # 5. End Time + tab
        r'(\d{2}:\d{2}:\d{2}:\d{2})'          # 6. Duration
    )

    for line in edl_content.splitlines():
        track_match = track_header_pattern.search(line)
        if track_match:
            current_track_name = track_match.group(1).strip()
            if current_track_name not in track_data:
                track_data[current_track_name] = {'events': [], 'current_rec_frame': 0}
            continue

        if current_track_name:
            clip_match = clip_event_pattern.match(line)
            if clip_match:
                channel, event_num, clip_name, rec_in_tc, rec_out_tc, duration_tc = clip_match.groups()
                clip_name = clip_name.strip()  # Remove any trailing spaces
                
                duration_frames = timecode_to_frames(duration_tc, frame_rate)
                rec_in_frames = timecode_to_frames(rec_in_tc, frame_rate)
                rec_out_frames = timecode_to_frames(rec_out_tc, frame_rate)
                
                track_data[current_track_name]['events'].append({
                    'clip_name': clip_name,
                    'reel': clip_name,
                    'src_in_frames': 0,
                    'duration_frames': duration_frames,
                    'rec_in_frames': rec_in_frames,
                    'rec_out_frames': rec_out_frames,
                    'rec_in_tc': rec_in_tc,  # Store original timecode string
                    'rec_out_tc': rec_out_tc,
                    'duration_tc': duration_tc,
                })
                
    total_events = sum(len(td['events']) for td in track_data.values())
    print(f"Successfully parsed {total_events} events across {len(track_data)} tracks.")
    return track_data


def create_aaf_from_edl(edl_track_data, output_filename, frame_rate, session_start_tc, sample_rate=48000, bit_depth=24):
    """
    Creates Pro Tools-compatible AAF with proper audio descriptors
    """
    print(f"\nBuilding Pro Tools-compatible AAF structure for {output_filename}...")
    print(f"Session Start TC: {session_start_tc}")
    print(f"Sample Rate: {sample_rate} Hz, Bit Depth: {bit_depth}-bit")
    
    # Find the earliest clip time to use as timeline reference
    earliest_clip_frames = float('inf')
    earliest_clip_tc = "00:00:00:00"
    for track_name, data in edl_track_data.items():
        for event in data['events']:
            if event['rec_in_frames'] < earliest_clip_frames:
                earliest_clip_frames = event['rec_in_frames']
                earliest_clip_tc = event['rec_in_tc']
    
    if earliest_clip_frames == float('inf'):
        earliest_clip_frames = 0
        earliest_clip_tc = "00:00:00:00"
    
    # Get the display timecode value (without 23.976 adjustment)
    earliest_clip_tc_display = timecode_to_display_frames(earliest_clip_tc)
    
    print(f"Earliest clip at: {earliest_clip_tc} ({earliest_clip_frames} timeline frames)")
    print(f"Timecode display value: {earliest_clip_tc_display} frames")
    print(f"Timeline will start at frame 0")
    
    # Use proper NTSC fraction for 23.976 fps to avoid cumulative timing errors.
    # edit_rate must be a Fraction object (not a string) for import_audio_essence.
    if math.isclose(frame_rate, 23.976, rel_tol=0.001):
        edit_rate = Fraction(24000, 1001)  # Standard NTSC rate
        print(f"Using NTSC edit rate: 24000/1001 (23.976 fps)")
    elif math.isclose(frame_rate, 24.0, rel_tol=0.001):
        edit_rate = Fraction(24, 1)
        print(f"Using edit rate: 24/1")
    else:
        # For other frame rates
        if frame_rate == int(frame_rate):
            edit_rate = Fraction(int(frame_rate), 1)
        else:
            edit_rate = Fraction(int(frame_rate * 1000), 1000)
        print(f"Using edit rate: {edit_rate}")

    # Compute silence duration needed: long enough to cover the longest clip + buffer.
    max_clip_duration_frames = 0
    for track_name, data in edl_track_data.items():
        for event in data['events']:
            max_clip_duration_frames = max(max_clip_duration_frames, event['duration_frames'])
    fps_float = float(edit_rate)
    silence_seconds = max(2.0, (max_clip_duration_frames / fps_float) + 1.0)
    print(f"Silence essence duration: {silence_seconds:.2f}s")

    silence_wav_path = None
    try:
        # Generate a single silent WAV file used for all master mobs
        silence_wav_path = make_silence_wav(silence_seconds, sample_rate, bit_depth)

        with aaf.open(output_filename, 'w') as f:

            # Create Master Mobs with EMBEDDED silent audio essence.
            # This is the key trick: because the audio is physically embedded in the AAF
            # file itself, Pro Tools finds the media and the clips are NEVER offline.
            # The clips just play silence, which is exactly what we want for spotting
            # cues that have no source audio.
            source_mobs = {}
            unique_reels = set()
            for track_name, data in edl_track_data.items():
                for event in data['events']:
                    unique_reels.add(event['reel'])

            for reel in unique_reels:
                master_mob = f.create.MasterMob(reel)
                f.content.mobs.append(master_mob)
                # import_audio_essence creates the FileSourceMob + PCMDescriptor,
                # embeds the WAV bytes as essence data, and wires a SourceClip in
                # the MasterMob pointing at it. Returns the MasterMob's slot.
                slot = master_mob.import_audio_essence(silence_wav_path, edit_rate=edit_rate)

                source_mobs[reel] = {
                    'master_mob': master_mob,
                    'audio_slot_id': slot.slot_id
                }
                print(f"Created MasterMob with embedded silence: {reel}")

            # Create Composition Mob (the timeline)
            comp_mob = f.create.CompositionMob("PTS_Export_Sequence")
            f.content.mobs.append(comp_mob)
            
            max_rec_frame = 0 
            track_id_counter = 1
            
            # Populate timeline tracks
            for track_name, data in edl_track_data.items():
                timeline_slot = comp_mob.create_sound_slot(edit_rate=edit_rate)
                timeline_slot.name = track_name
                timeline_slot.slot_id = track_id_counter
                
                track_sequence = timeline_slot.segment
                current_rec_frame = 0 

                print(f"\nProcessing Track: {track_name}")

                for i, event in enumerate(data['events']):
                    master_mob = source_mobs[event['reel']]['master_mob']
                    audio_slot_id = source_mobs[event['reel']]['audio_slot_id']
                    
                    # Calculate position relative to earliest clip (timeline frame 0)
                    rec_in_relative = event['rec_in_frames'] - earliest_clip_frames
                    rec_out_relative = event['rec_out_frames'] - earliest_clip_frames
                    
                    # Handle gaps
                    if rec_in_relative > current_rec_frame:
                        gap_duration = rec_in_relative - current_rec_frame
                        filler = f.create.from_name("Filler")
                        filler.media_kind = "sound"
                        filler.length = gap_duration
                        track_sequence.components.append(filler)
                        print(f"  Filler: {gap_duration} frames ({frames_to_timecode(gap_duration, frame_rate)})")

                    # Create source clip
                    clip = f.create.from_name("SourceClip")
                    clip.media_kind = "sound"
                    clip.length = event['duration_frames']
                    clip.start = event['src_in_frames']
                    clip.mob_id = master_mob.mob_id
                    clip.slot_id = audio_slot_id

                    track_sequence.components.append(clip)
                    original_tc = frames_to_timecode(event['rec_in_frames'], frame_rate)
                    print(f"  Clip {i+1}: '{event['clip_name']}' at TC {original_tc} (timeline frame {rec_in_relative})")
                    
                    current_rec_frame = rec_out_relative
                    max_rec_frame = max(max_rec_frame, rec_out_relative)

                track_id_counter += 1

            # Add timecode track
            tc_slot = comp_mob.create_timeline_slot(edit_rate=edit_rate)
            tc_slot.slot_id = track_id_counter
            tc_slot.name = "Timecode"
            
            tc_component = f.create.from_name("Timecode")
            tc_component.length = max_rec_frame
            tc_component.start = earliest_clip_tc_display  # Use display timecode value
            tc_slot.segment = tc_component
            
            print(f"\nTimecode track: starts at {earliest_clip_tc} (display value: {earliest_clip_tc_display} frames), length {max_rec_frame} frames")
            
            f.save()
            print(f"\n--- Pro Tools-compatible AAF created: '{output_filename}' ---")
            
    except AAFError as e:
        print(f"\n!!! AAF Error: {e} !!!", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n!!! Error: {e} !!!", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up the temporary silence WAV file
        if silence_wav_path and os.path.exists(silence_wav_path):
            try:
                os.unlink(silence_wav_path)
            except OSError:
                pass


# --- Main Execution ---

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python EDL_to_AAF_ProTools.py <input_edl_file> [sample_rate] [bit_depth]")
        print("Example: python EDL_to_AAF_ProTools.py input.EDL 48000 24")
        print("\nDefaults: 48000 Hz, 24-bit\n")
        sys.exit(1)
    
    EDL_FILE = sys.argv[1]
    SAMPLE_RATE = int(sys.argv[2]) if len(sys.argv) > 2 else 48000
    BIT_DEPTH = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    
    input_path = Path(EDL_FILE)
    OUTPUT_AAF = input_path.with_suffix('.aaf')
    
    print(f"\n{'='*60}")
    print(f"EDL to AAF Converter (Pro Tools Enhanced)")
    print(f"{'='*60}")
    print(f"Input:  {EDL_FILE}")
    print(f"Output: {OUTPUT_AAF}")
    print(f"{'='*60}\n")
    
    try:
        edl_content = input_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"\n!!! ERROR: File '{EDL_FILE}' not found !!!\n", file=sys.stderr)
        sys.exit(1)
        
    try:
        frame_rate = get_frame_rate(edl_content)
        session_start_tc = get_session_start_tc(edl_content)
        edl_track_data = parse_pts_like_edl(edl_content, frame_rate)
        
        if any(data['events'] for data in edl_track_data.values()):
            create_aaf_from_edl(edl_track_data, str(OUTPUT_AAF), frame_rate, session_start_tc, SAMPLE_RATE, BIT_DEPTH)
            print(f"\n{'='*60}")
            print(f"✓ Conversion Complete!")
            print(f"✓ Output: {OUTPUT_AAF}")
            print(f"{'='*60}\n")
        else:
            print("No valid EDL events found.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n!!! Error: {e} !!!", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
