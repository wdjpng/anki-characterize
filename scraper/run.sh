#!/bin/bash

# Run the browsybrowse.py script
mkdir -p scraper/images
# python3 scraper/browsybrowse.py

# Create tar.xz archive
cd scraper/images && tar -cJf ../components.tar.xz * && cd ../..

# Upload to server using scp
scp scraper/components.tar.xz lukas:/var/www/html/mandarin/
