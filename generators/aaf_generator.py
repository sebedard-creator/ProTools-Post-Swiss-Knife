import aaf2
import re

def timecode_to_frames(tc_str, framerate=23.976):
    """
    Convert a timecode string HH:MM:SS:FF to absolute frames.
    """
    # Remove any non-digit characters except standard separators
    tc_str = re.sub(r'[^\d:;.]', '', str(tc_str))
    parts = re.split(r'[:;.]', tc_str)
    
    if len(parts) >= 4:
        hh = int(parts[0])
        mm = int(parts[1])
        ss = int(parts[2])
        ff = int(parts[3])
        
        fps_int = int(round(framerate))
        total_frames = (hh * 3600 * fps_int) + (mm * 60 * fps_int) + (ss * fps_int) + ff
        return total_frames
    return 0

def create_markers_aaf(markers_data, output_path, framerate=23.976):
    """
    Creates a completely new AAF containing a DescriptiveMetadata timeline with CommentMarkers.
    """
    # Round framerate to fraction for AAF
    if abs(framerate - 23.976) < 0.01:
        edit_rate = "24000/1001"
    elif abs(framerate - 29.97) < 0.01:
        edit_rate = "30000/1001"
    else:
        edit_rate = f"{int(framerate)}/1"

    with aaf2.open(output_path, 'w') as f:
        # 1. Create a CompositionMob
        comp_mob = f.create.CompositionMob()
        comp_mob.name = "XLS Markers Export"
        comp_mob.usage = 'Usage_TopLevel'
        f.content.mobs.append(comp_mob)
        # 2. Get DescriptiveMetadata Dictionary
        descriptive_def = f.dictionary.lookup_datadef("DescriptiveMetadata")
        
        # First, find max_position to know the length of the dummy audio track
        max_position = 0
        for marker in markers_data:
            frames = timecode_to_frames(marker['tc_in'], framerate)
            if frames > max_position:
                max_position = frames
                
        total_length = max_position + 24000
        
        # 3. Create a dummy audio slot (Pro Tools ignores markers if there is no media track)
        audio_slot = comp_mob.create_sound_slot(edit_rate=edit_rate)
        audio_slot.name = "" # Empty name so Pro Tools doesn't append '- Dummy Audio -'
        audio_seq = f.create.Sequence(media_kind="Sound")
        audio_filler = f.create.Filler()
        audio_filler['DataDefinition'].value = f.dictionary.lookup_datadef("Sound")
        audio_filler['Length'].value = total_length
        audio_seq.components.append(audio_filler)
        audio_slot.segment = audio_seq
        
        # 4. Create an Event Slot for the markers
        event_slot = f.create.EventMobSlot()
        event_slot.edit_rate = edit_rate
        event_slot.name = "Markers"
        event_slot.slot_id = 2 # Audio slot is 1
        comp_mob.slots.append(event_slot)
        
        # 5. Create a Sequence for the markers
        seq = f.create.Sequence(media_kind="DescriptiveMetadata")
        event_slot.segment = seq
        
        # 6. Add markers
        for idx, marker in enumerate(markers_data):
            tc_str = marker['tc_in']
            comment = marker['comment']
            
            frames = timecode_to_frames(tc_str, framerate)
            
            # Create DescriptiveMarker
            c_marker = f.create.DescriptiveMarker()
            c_marker['DataDefinition'].value = descriptive_def
            
            c_marker['Position'].value = frames
            c_marker['Length'].value = 1 # Pro Tools markers are 1 frame long
            
            # Random color so they look nice in Pro Tools! (16-bit RGB, 0-65535)
            import random
            random_color = {
                'red': random.randint(10000, 65535),
                'green': random.randint(10000, 65535),
                'blue': random.randint(10000, 65535)
            }
            c_marker['CommentMarkerColor'].value = random_color
            
            # Pro Tools is very picky about mapping AAF fields to Name and Comment.
            # The Name field is populated by a TaggedValue named "Comment" in UserComments.
            # The Comments field is populated by CommentMarkerUser.
            short_name = comment if comment else ""
            
            c_marker['Comment'].value = short_name 
            c_marker['CommentMarkerUser'].value = comment if comment else "" 
            c_marker['DescribedSlots'].value = [audio_slot.slot_id] # Link marker to audio track!
            
            # Add TaggedValue "Comment" to UserComments so Pro Tools uses it for the Marker Name field
            if comment:
                c_marker['UserComments'].append(f.create.TaggedValue('Comment', short_name))
            
            seq.components.append(c_marker)
            
        # VERY IMPORTANT for Pro Tools: The Sequence needs a length
        seq.length = total_length
