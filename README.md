# vJoy Touchpad

A minimal, touch-friendly dual joystick for Windows 11. It sends the left stick to
vJoy **X/Y** and the right stick to **RX/RY**. Multi-touch, mouse dragging, and
keyboard fallback are supported.

## Which file do I run?

Run **`main.py`** from the repository's top-level folder. Do not run
`vjoy_pad/app.py` directly.

```powershell
py main.py
```

Complete the setup below first so that the same Python interpreter has all of
the required dependencies installed.

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

The app opens as a transparent, always-on-top overlay, with each joystick's width
and height set to 33% of the screen's shorter dimension. The sticks sit near the
bottom-left and bottom-right corners for maximum separation. Use two fingers to
move both sticks at once. Press
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

If the displayed interpreter path contains `uv\python`, it is a Python installation
managed by uv and may not include pip. Create a project environment and install the
dependencies through uv instead:

```powershell
uv venv .venv
uv pip install --python .venv -r requirements.txt
```

Then select `.venv\Scripts\python.exe` in VS Code before running `main.py` again.
