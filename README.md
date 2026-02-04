# Property Viewing Checklist - PWA

Mobile-first property viewing tracker with offline support.

## Quick Start

```bash
docker-compose up --build
```

Open `http://localhost:5000`

## Features

✅ Checkboxes with notes for all properties
✅ Drag-and-drop reordering
✅ Custom properties
✅ Currency selector (£/$/ €)
✅ Side-by-side comparison view
✅ Horizontal scrolling
✅ **PWA - Install as mobile app**
✅ **Works offline**

## Install on Mobile

### iOS (iPhone/iPad):
1. Open in Safari
2. Tap Share button
3. Tap "Add to Home Screen"
4. Tap "Add"

### Android:
1. Open in Chrome
2. Tap ⋮ menu
3. Tap "Add to Home Screen" or "Install app"
4. Tap "Install"

## PWA Features

- Installs like native app
- Works offline
- Appears on home screen
- Full-screen experience
- No app store needed

## Development

```bash
pip install flask
python app.py
```

## Tech Stack

- Backend: Python/Flask
- Frontend: Tailwind CSS
- PWA: Service Worker + Manifest
- Storage: SQLite
