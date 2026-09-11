# VS Code Time Tracker

A lightweight Windows desktop application that tracks the active time spent in Visual Studio Code.

This project was created as a learning project while studying Python and desktop application development.

## Features

- Tracks time only while Visual Studio Code is the active window
- Saves tracked time automatically
- Stores application data in JSON
- Runs in the Windows system tray
- Displays total tracked time in a small statistics window
- Draggable frameless statistics window
- Remembers the statistics window position
- Custom tray icon
- Periodic checkpoints to reduce time loss if the application closes unexpectedly

## Technologies

- Python
- Tkinter
- pywin32
- pystray
- Pillow
- threading
- JSON

## How it works

The application checks which window is currently active in Windows.

If Visual Studio Code is the active window, the tracker starts counting time. When the user switches to another application, the current session is stopped and the accumulated time is saved.

The application stores local data in:

```text
tracker_data.json
```

This file is generated automatically and is not included in the repository.

## Current status

The project is still under development.

Planned improvements include:

- Support for selecting which application to track
- Improved statistics
- Better Windows 11 integration
- Improved user interface
- Standalone executable build

## Author

Created by Radisonbe as a Python learning project.