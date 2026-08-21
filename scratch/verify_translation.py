import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.idml_parser import extract_stories

translated_idml = 'outputs/VF20_VST600-FW82_OM_r1_1_D_web_translated.idml'
stories = extract_stories(translated_idml)

print(f"Total stories extracted: {len(stories)}")
for story in stories[:5]:
    print(f"\nStory ID: {story['story_id']}")
    for p in story['paragraphs'][:3]:
        print(f"  [{p['style']}]: {p['text'].strip()}")
