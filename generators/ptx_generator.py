import os
from pt_api import ProToolsSession, TimecodeEngine

def create_markers_ptx(markers, output_path):
    """
    Creates a PTX file with markers from the parsed Excel data.
    Uses 'template_markers.ptx' as the base session.
    """
    # Chemin vers le fichier template à la racine
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, 'template_markers.ptx')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Le fichier de base '{template_path}' est introuvable. Veuillez le placer à la racine de l'application.")
        
    # Ouvrir la session via l'API
    session = ProToolsSession(template_path)
    engine = TimecodeEngine(session.sample_rate, session.frame_rate_enum)
    
    # Injecter les markers
    for marker in markers:
        tc = marker['tc_in']
        name = marker.get('comment', 'Marker')
        if not name:
            name = "Marker"
            
        # S'assurer du format HH:MM:SS:FF
        tc = tc.replace(';', ':')
        parts = tc.split(':')
        if len(parts) >= 4:
            hh, mm, ss, ff = map(int, parts[:4])
            
            # Tronquer le nom si trop long pour Pro Tools (généralement 255 chars max)
            name = name[:250]
            
            # Convertir le timecode en samples
            tc_samples = engine.timecode_to_samples(hh, mm, ss, ff)
            
            session.add_marker(name, tc_samples)
        
    # Sauvegarder la session finale
    session.save(output_path)
