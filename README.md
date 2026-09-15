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
