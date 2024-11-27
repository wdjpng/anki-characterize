from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from aqt.browser import Browser
from aqt.gui_hooks import browser_menus_did_init
import requests
import os

def process_chinese_characters(browser, use_local=False):
    selected_notes = browser.selectedNotes()
    
    if not selected_notes:
        showInfo("Please select at least one note")
        return
    
    mw.checkpoint("Process Chinese Characters")
    
    for note_id in selected_notes:
        note = mw.col.get_note(note_id)
        if 'Chinese character' in note:
            chinese_chars = note['Chinese character']
            
            # Process each character
            html_parts = []
            image_containers = []
            
            html_parts.append('<div style="height: 10px;"></div>')
            for char in chinese_chars:
                if char in "。，、?.,!！？" or char.isspace():
                    html_parts.append(char)
                else:
                    unicode_value = ord(char)
                    char_id = f"char_{unicode_value}"
                    html_parts.append(f'<span class="clickable" onclick="showImage(\'{char_id}\')">{char}</span>')
                    
                    # Create image container for this character
                    container = (
                        f'<div id="{char_id}" class="image-container" style="display: flex; justify-content: center; align-items: center; width: 100%; margin: 0x 0;">'
                        f'<img src="https://www.strokeorder.com/assets/bishun/guide/{unicode_value}.png"'
                        f' alt="{char}" style="width: min(75vmin, 500px); display: none; margin: 0 auto;">'
                        f'</div>'
                    )
                    image_containers.append(container)
            
            # Combine everything
            final_html = f'{"".join(html_parts)}\n\n{"".join(image_containers)}'
            # Set the new field
            if 'Characters with strokes' in note:
                note['Characters with strokes'] = final_html
                note.flush()
    
    browser.model.reset()
    showInfo(f"Processed Chinese characters in {len(selected_notes)} notes")

def setup_menu(browser):
    action = QAction("Process Chinese Characters", browser)
    action.triggered.connect(lambda: process_chinese_characters(browser))
    browser.form.menuEdit.addAction(action)

browser_menus_did_init.append(setup_menu)