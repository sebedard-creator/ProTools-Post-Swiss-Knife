import re

def parse_cue_sheet(file_path):
    """Parse the Avid cue sheet text file"""
    encodings = ['macroman', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    content = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    
    session_name = ''
    session_match = re.search(r'SESSION NAME:\s*(.+)', content)
    if session_match:
        session_name = session_match.group(1).strip()
    
    tracks = []
    track_sections = re.split(r'TRACK NAME:\s*(.+)', content)[1:]
    
    for i in range(0, len(track_sections), 2):
        if i + 1 < len(track_sections):
            track_name = track_sections[i].strip()
            track_content = track_sections[i + 1]
            
            comments_match = re.search(r'COMMENTS:\s*(.+)', track_content)
            track_comments = comments_match.group(1).strip() if comments_match else ''
            
            events = []
            lines = track_content.split('\n')
            
            for line in lines:
                if line.strip() and line.split()[0].isdigit():
                    parts = line.split('\t')
                    if len(parts) >= 6:
                        try:
                            channel = parts[0].strip()
                            event_num = parts[1].strip()
                            clip_name = parts[2].strip()
                            start_time = parts[3].strip()[:-3]
                            end_time = parts[4].strip()[:-3]
                            duration = parts[5].strip()[:-3]
                            state = parts[6].strip() if len(parts) > 6 else 'Unmuted'
                            
                            if state.lower() == 'muted':
                                state_display = 'SI VOUS AVEZ LE TEMPS'
                            else:
                                state_display = ''
                            
                            events.append({
                                'channel': channel,
                                'event': event_num,
                                'clip_name': clip_name,
                                'start_time': start_time,
                                'end_time': end_time,
                                'duration': duration,
                                'state': state_display
                            })
                        except:
                            continue
            
            if events:
                tracks.append({
                    'name': track_name,
                    'comments': track_comments,
                    'events': events
                })
    
    return {
        'session_name': session_name,
        'tracks': tracks
    }

def parse_markers(file_path):
    """Parse markers from the Avid cue sheet text file"""
    encodings = ['macroman', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    content = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    
    markers = []
    marker_section_match = re.search(r'M A R K E R S\s+L I S T I N G\s*\n(.+?)(?:\n\n|\n[A-Z]|\Z)', content, re.DOTALL)
    
    if marker_section_match:
        marker_content = marker_section_match.group(1)
        lines = marker_content.split('\n')
        
        data_started = False
        for line in lines:
            if not data_started:
                if line.strip().startswith('#'):
                    data_started = True
                    continue
            
            if not data_started:
                continue
            
            if line.strip() and line.split()[0].isdigit():
                parts = line.split('\t')
                if len(parts) >= 6:
                    try:
                        marker_num = parts[0].strip()
                        location = parts[1].strip()
                        timecode = location[:-3] if len(location) > 3 else location
                        
                        marker_name = parts[4].strip() if len(parts) > 4 else ''
                        marker_comments = parts[7].strip() if len(parts) > 7 else ''
                        
                        marker_text = marker_name if marker_name else marker_comments
                        
                        if marker_text:
                            markers.append({
                                'number': marker_num,
                                'timecode': timecode,
                                'text': marker_text
                            })
                    except:
                        continue
    
    return markers
