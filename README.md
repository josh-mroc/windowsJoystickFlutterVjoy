# vJoy Touchpad

A minimal, touch-friendly dual joystick for Windows 11. It sends the left stick to
vJoy **X/Y** and the right stick to **RX/RY**. Multi-touch, mouse dragging, and
keyboard fallback are supported.

## Setup

1. Install the vJoy driver and configure device **1** with X, Y, RX, and RY axes.
2. Install 64-bit Python 3.10 or newer.
3. Open PowerShell in this folder and run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   py main.py
   ```

   `pygame-ce` provides the module named `pygame`; do not replace it with the
   separate `pygame` package. Always install and run with the same Python
   interpreter.

The app opens full-screen. Use two fingers to move both sticks at once. Press
**Esc** to exit. For desktop testing, drag a stick with the mouse; **WASD** moves
the left stick and the arrow keys move the right stick.

Use another configured vJoy device or open a normal resizable window with:

```powershell
py main.py --device 2 --windowed
```

If vJoy or `pyvjoy` cannot connect, the app stays open in preview mode and displays
the error. Verify that the selected virtual device exists, is enabled, and exposes
all four axes. Closing the app resets all axes to center.

## Troubleshooting `No module named 'pygame'`

This error means the interpreter running `main.py` does not have the project
dependencies installed. From the repository folder, activate the virtual
environment and reinstall them:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

In VS Code, run **Python: Select Interpreter** from the Command Palette and choose
`.venv\Scripts\python.exe`. The Python path shown when launching `main.py` should
then point into this repository's `.venv` folder.
