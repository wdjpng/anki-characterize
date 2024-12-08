from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from aqt.browser import Browser
from aqt.gui_hooks import browser_menus_did_init, profile_did_open
import requests
import os
import tarfile
import urllib.request
from tempfile import NamedTemporaryFile
from email.utils import parsedate_to_datetime

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
            # Replace &nbsp; with actual whitespace
            chinese_chars = chinese_chars.replace('&nbsp;', ' ')
            # Process each character
            html_parts = []
            image_containers = []
            
            html_parts.append('<div style="height: 10px;"></div>')
            for char in chinese_chars:
                if char in "。，、?.,!！？":
                    html_parts.append(char)
                elif char.isspace():
                    html_parts.append(' ')  # Direct space character instead of escaped version
                else:
                    unicode_value = ord(char)
                    char_id = f"char_{unicode_value}"
                    html_parts.append(f'<span class="clickable" onclick="showImage(\'{char_id}\')">{char}</span>')
                    

                    # Check if component image exists in Anki's media collection
                    component_filename = f"charactrize/_component_{unicode_value}.png"
                    has_component = os.path.exists(os.path.join(mw.col.media.dir(), component_filename))
                    
                    # Create image container with stroke order and optional component
                    container = [
                        f'<div id="{char_id}" class="image-container" style="display: flex; justify-content: center; align-items: center; width: 100%; flex-direction: column; margin: 0x 0;">'
                        f'<img src="https://www.strokeorder.com/assets/bishun/guide/{unicode_value}.png"'
                        f' alt="{char}" style="width: min(30vmin, 200px); display: none; margin: 0 auto;">'
                    ]
                    
                    # Add component image if it exists
                    if has_component:
                        container.append(
                            f'<img src="{component_filename}"'
                            f' style="width: min(90vw, 700px); display: none; margin: 0 auto;">'
                        )
                    container.append('</div>')
                    image_containers.append(''.join(container))
            
            # Add JavaScript for image toggling
            script = """
            <script>
            function showImage(charId) {
                var clickedContainer = document.getElementById(charId);
                var clickedImages = clickedContainer.getElementsByTagName('img');
                var isCurrentlyShown = clickedImages[0].style.display === 'block';
                
                // Hide all images in all containers
                var allContainers = document.getElementsByClassName('image-container');
                for (var cont of allContainers) {
                    var imgs = cont.getElementsByTagName('img');
                    for (var img of imgs) {
                        img.style.display = 'none';
                    }
                }
                
                // If the clicked images weren't showing before, show them now
                if (!isCurrentlyShown) {
                    for (var img of clickedImages) {
                        img.style.display = 'block';
                    }
                }
            }
            </script>
            """
            
            # Combine everything
            final_html = f'{"".join(html_parts)}\n\n{"".join(image_containers)}\n{script}'
            
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

class ComponentDownloader(QThread):
    finished = pyqtSignal()
    
    def run(self):
        url = "https://lukasmuenzel.com/mandarin/components.tar.xz"
        media_dir = mw.col.media.dir()
        metadata_file = os.path.join(media_dir, "_components_metadata.txt")
        
        try:
            # Check if metadata exists and components are up-to-date
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    local_timestamp = float(f.read().strip())
                
                response = requests.head(url)
                server_timestamp = response.headers.get('last-modified')
                if server_timestamp:
                    server_time = parsedate_to_datetime(server_timestamp).timestamp()
                    if local_timestamp >= server_time:
                        return

            # Download and process
            with NamedTemporaryFile(suffix='.tar.xz', delete=False) as temp_file:
                urllib.request.urlretrieve(url, temp_file.name)
                
                charactrize_dir = os.path.join(media_dir, 'charactrize')
                os.makedirs(charactrize_dir, exist_ok=True)
                
                with tarfile.open(temp_file.name, 'r:xz') as tar:
                    tar.extractall(path=charactrize_dir)
                
                response = requests.head(url)
                if 'last-modified' in response.headers:
                    timestamp = parsedate_to_datetime(response.headers['last-modified']).timestamp()
                    with open(metadata_file, 'w') as f:
                        f.write(str(timestamp))
                    
            os.unlink(temp_file.name)
            
        except Exception as e:
            # Silently handle errors in background thread
            pass
        
        self.finished.emit()

def on_profile_loaded():
    downloader = ComponentDownloader()
    downloader.start()

profile_did_open.append(on_profile_loaded)
browser_menus_did_init.append(setup_menu)