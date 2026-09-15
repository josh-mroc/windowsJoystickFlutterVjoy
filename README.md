# vJoy Touchpad

A minimal, touch-friendly dual joystick for Windows 11. It sends the left stick to
vJoy **Y** and the right stick to **RY**. Multi-touch, mouse dragging, and
keyboard fallback are supported.

The **Two Paddle input** checkbox controls the RY stick orientation. It starts
unchecked, displaying RY as a horizontal control while continuing to send the
same RY axis. The horizontal control is the original vertical RY control rotated
90 degrees to the right, so positive RY points left. Check the box to restore the
original vertical RY control.

Two vertical selector switches at the top control vJoy buttons **1–5**. The first
switch selects between **ARMED** (button 1) and **Disarmed** (button 2). The second
selects **Auto** (button 3), **Manual** (button 4), or **HOLD** (button 5). It
starts at HOLD, and selecting Disarmed also moves it to HOLD.

The vertical **X** slider beside the mode switch is twice as long as the first
switch. It starts at zero at the bottom; drag it upward to send progressively
more right X-axis input, reaching full right at the top.

## Which file do I run?

Run **`main.py`** from the repository's top-level folder. Do not run
`vjoy_pad/app.py` directly.

```powershell
py main.py
```

Complete the setup below first so that the same Python interpreter has all of
the required dependencies installed.

## Setup

1. Install the vJoy driver and configure device **1** with Y and RY axes.
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

The app opens as a transparent, always-on-top overlay, with tall, narrow joystick
tracks that make their vertical-only movement clear. The sticks sit near the
bottom-left and bottom-right corners for maximum separation. Use two fingers to
move both sticks at once. Press
**Esc** to exit. For desktop testing, drag a stick with the mouse; **W/S** moves
the left stick. The left/right arrow keys move the horizontal RY stick; when
**Two Paddle input** is checked, the up/down arrow keys move the vertical RY stick.

Use another configured vJoy device or open a normal resizable window with:

```powershell
py main.py --device 2 --windowed
```

If vJoy or `pyvjoy` cannot connect, the app stays open in preview mode and displays
the error. Verify that the selected virtual device exists, is enabled, and exposes
both axes. Closing the app resets both axes to center.

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
