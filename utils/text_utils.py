import re

def transform_track_name_for_excel(track_name):
    # Pattern to match: anything[anything]{anything}
    pattern = r'^([^\[]+)\[[^\]]*\]\{([^\}]+)\}$'
    match = re.match(pattern, track_name)
    
    if match:
        prefix = match.group(1).strip()
        suffix = match.group(2).strip()
        return f"{prefix} - {suffix}"
    return track_name

def extract_clip_name_and_comment(clip_name):
    if '{' in clip_name and '}' in clip_name:
        pattern = r'^(.+?)\{([^\}]*)\}\s*$'
        match = re.match(pattern, clip_name)
        if match:
            name = match.group(1).strip()
            comment = match.group(2).strip()
            return (name, comment)
    return (clip_name, "")

def format_text_for_pdf(text):
    text = text.replace('"', '')
    text = re.sub(r'\(([^)]+)\)', r'<i>(\1)</i>', text)
    return text

def extract_track_code_and_actor(track_name):
    pattern = r'^[^\[]+\[([^\]]+)\]\{([^\}]+)\}$'
    match = re.match(pattern, track_name)
    
    if match:
        code = match.group(1).strip()
        actor_name = match.group(2).strip()
        actor_name_underscore = actor_name.replace(' ', '_')
        return (code, actor_name, actor_name_underscore)
        
    actor_name_underscore = track_name.replace(' ', '_')
    return (None, track_name, actor_name_underscore)

def format_text_for_adr(text):
    text = text.replace('"', '')
    text = re.sub(r'\(([^)]+)\)', r'<i>(\1)</i>', text)
    return text

def tc_to_seconds(tc):
    parts = tc.strip().split(':')
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        pass
    return None
