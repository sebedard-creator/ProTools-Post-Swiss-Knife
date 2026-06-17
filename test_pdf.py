#!/usr/bin/env python3
"""
Standalone Test Script for ADR Recording PDF Generation
Run this script directly to test if PDF generation works
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import parse_cue_sheet, create_adr_acteur_pdf, create_adr_technicien_pdf, extract_track_code_and_actor

def test_pdf_generation(input_file):
    """Test PDF generation with a cue sheet file"""
    
    print("="*60)
    print("  STANDALONE PDF GENERATION TEST")
    print("="*60)
    print(f"\nInput file: {input_file}\n")
    
    if not os.path.exists(input_file):
        print(f"ERROR: File not found: {input_file}")
        return False
    
    try:
        # Parse the cue sheet
        print("Parsing cue sheet...")
        data = parse_cue_sheet(input_file)
        print(f"✓ Found {len(data['tracks'])} tracks\n")
        
        # Test with first track only
        track = data['tracks'][0]
        track_code, actor_name, actor_name_underscore = extract_track_code_and_actor(track['name'])
        
        print(f"Testing with: {actor_name}")
        print(f"Track code: {track_code}")
        print(f"Events: {len(track['events'])}\n")
        
        # Create test directory
        test_dir = 'test_output'
        os.makedirs(test_dir, exist_ok=True)
        
        # Generate ACTEUR PDF
        acteur_file = f"{test_dir}/TEST_ACTEUR.pdf"
        print(f"Generating ACTEUR PDF...")
        create_adr_acteur_pdf(track, track_code, actor_name, 'TEST', acteur_file)
        
        if os.path.exists(acteur_file):
            acteur_size = os.path.getsize(acteur_file)
            print(f"✓ ACTEUR PDF created: {acteur_size:,} bytes")
            
            if acteur_size < 1000:
                print("  ❌ WARNING: PDF is too small (< 1KB) - likely broken!")
                return False
            else:
                print("  ✓ PDF size looks good")
        else:
            print("❌ ACTEUR PDF was not created!")
            return False
        
        # Generate TECHNICIEN PDF
        tech_file = f"{test_dir}/TEST_TECHNICIEN.pdf"
        print(f"\nGenerating TECHNICIEN PDF...")
        create_adr_technicien_pdf(track, track_code, actor_name, 'TEST', tech_file)
        
        if os.path.exists(tech_file):
            tech_size = os.path.getsize(tech_file)
            print(f"✓ TECHNICIEN PDF created: {tech_size:,} bytes")
            
            if tech_size < 1000:
                print("  ❌ WARNING: PDF is too small (< 1KB) - likely broken!")
                return False
            else:
                print("  ✓ PDF size looks good")
        else:
            print("❌ TECHNICIEN PDF was not created!")
            return False
        
        print("\n" + "="*60)
        print("  ✅ TEST PASSED - PDFs Generated Successfully!")
        print("="*60)
        print(f"\nTest PDFs saved in: {os.path.abspath(test_dir)}/")
        print("Check the PDFs to verify they're readable.\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_pdf.py <path_to_cue_sheet.txt>")
        print("\nExample:")
        print("  python3 test_pdf.py Pelletier-1_002_tva_fr_ADR.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    success = test_pdf_generation(input_file)
    
    sys.exit(0 if success else 1)
