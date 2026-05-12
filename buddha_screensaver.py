"""
Buddha Mountain Screensaver - PyQt6 launcher
- Keyboard input works (types categories, gets wisdom)
- Mouse move >10px OR click exits
- Primary screen: Buddha HTML fullscreen
- Secondary screens: plain black covers (same bg color)
- Works on Python 3.10+
Build with build_buddha.bat
"""

import sys
import os


# ── Locate buddha.html ────────────────────────────────────────────────────────
def find_html():
    # PyInstaller bundle unpacks data files to sys._MEIPASS
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, 'buddha.html')
        if os.path.exists(p):
            return p

    # Running as plain .py — look next to this script
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    p = os.path.join(script_dir, 'buddha.html')
    if os.path.exists(p):
        return p

    raise FileNotFoundError(
        "buddha.html not found. "
        "Place it in the same folder as buddha_screensaver.py (or the .scr)."
    )


# ── Screensaver argument mode ─────────────────────────────────────────────────
def get_mode():
    args = " ".join(sys.argv[1:]).strip().lower()
    if args.startswith("/s") or args.startswith("-s") or args == "":
        return "screensaver"
    elif args.startswith("/p") or args.startswith("-p"):
        return "preview"
    elif args.startswith("/c") or args.startswith("-c"):
        return "config"
    return "screensaver"


def show_config():
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setWindowTitle("Buddha Mountain")
        msg.setText("No configuration needed.\n\nSit with the mountain.")
        msg.exec()
    except Exception:
        pass


def run_screensaver():
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    from PyQt6.QtCore import Qt, QUrl, QTimer, QObject, QEvent
    from PyQt6.QtGui import QColor

    html_path = find_html()

    app = QApplication(sys.argv)
    app.setOverrideCursor(Qt.CursorShape.BlankCursor)

    # ── Mouse exit guard ──────────────────────────────────────────────────────
    # Arms itself after the first MouseMove event (ignores the initial
    # position jitter Windows sometimes fires on screensaver start).
    # Quits on >10px movement or any mouse button press.
    # Does NOT intercept keyboard events — those pass straight through to
    # the WebEngineView so typing still works.

    class MouseGuard(QObject):
        def __init__(self, quit_fn):
            super().__init__()
            self._quit = quit_fn
            self._start = None

        def eventFilter(self, obj, event):
            t = event.type()
            if t == QEvent.Type.MouseMove:
                pos = event.globalPosition().toPoint()
                if self._start is None:
                    # Arm: record starting position, don't quit yet
                    self._start = pos
                else:
                    dx = abs(pos.x() - self._start.x())
                    dy = abs(pos.y() - self._start.y())
                    if dx > 10 or dy > 10:
                        self._quit()
            elif t in (
                QEvent.Type.MouseButtonPress,
                QEvent.Type.MouseButtonRelease,
            ):
                self._quit()
            # Never consume events — keyboard must reach the WebEngineView
            return False

    guard = MouseGuard(app.quit)
    app.installEventFilter(guard)

    # ── Primary screen: WebEngineView ─────────────────────────────────────────
    # Key insight: removing Qt.WindowType.Tool fixes keyboard focus on Windows.
    # Tool windows are specifically designed NOT to accept focus, which is
    # great for palette windows but fatal for an interactive screensaver.
    # FramelessWindowHint + WindowStaysOnTopHint is sufficient.

    view = QWebEngineView()
    view.settings().setAttribute(
        QWebEngineSettings.WebAttribute.JavascriptEnabled, True
    )
    # Allow Google Fonts CDN
    view.settings().setAttribute(
        QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
    )
    # Strong focus policy so the widget accepts keyboard input
    view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    view.setWindowFlags(
        Qt.WindowType.FramelessWindowHint |
        Qt.WindowType.WindowStaysOnTopHint
        # NOTE: Qt.WindowType.Tool intentionally omitted — it blocks keyboard focus
    )

    primary = app.primaryScreen()
    view.setGeometry(primary.geometry())
    view.showFullScreen()

    view.load(QUrl.fromLocalFile(html_path))

    # After page loads: activate the window for keyboard focus, then
    # use JS to focus the hidden input element the HTML uses for typing.
    def on_load_finished(ok):
        if ok:
            view.activateWindow()
            view.raise_()
            view.setFocus(Qt.FocusReason.OtherFocusReason)
            # Focus the invisible input element inside the page
            view.page().runJavaScript(
                "var el = document.getElementById('prompt-input');"
                "if (el) { el.focus(); }"
            )

    view.loadFinished.connect(on_load_finished)

    # Re-focus periodically in case Windows steals focus back
    # (common with screensaver process management)
    def refocus():
        if not view.isActiveWindow():
            view.activateWindow()
            view.raise_()
            view.page().runJavaScript(
                "var el = document.getElementById('prompt-input');"
                "if (el && document.activeElement !== el) { el.focus(); }"
            )

    focus_timer = QTimer()
    focus_timer.setInterval(2000)  # check every 2s
    focus_timer.timeout.connect(refocus)
    focus_timer.start()

    # ── Secondary screens: solid black covers ─────────────────────────────────
    # Spawn a plain black QWidget on every screen except the primary.
    # This matches the #0a0a0a body background of the HTML visually.
    # Using geometry().topLeft() + move() is the reliable way to place
    # widgets on specific screens in Qt6 (setScreen on QWidget works
    # but requires the widget to not yet be shown).

    black_covers = []
    for screen in app.screens():
        if screen is primary:
            continue
        cover = QWidget()
        cover.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Tool is fine here — no keyboard needed
        )
        # #0a0a0a matches the buddha.html body background
        cover.setStyleSheet("background-color: #0a0a0a;")
        cover.setGeometry(screen.geometry())
        cover.showFullScreen()
        # Move explicitly to the screen's top-left in case showFullScreen
        # defaulted to the primary screen
        cover.move(screen.geometry().topLeft())
        black_covers.append(cover)  # keep reference so GC doesn't destroy them

    # Safety: also quit via JS window.close() if ever called
    view.page().windowCloseRequested.connect(app.quit)

    app.exec()


if __name__ == '__main__':
    mode = get_mode()
    if mode == "config":
        show_config()
    elif mode == "preview":
        pass  # Windows preview pane thumbnail — skip
    else:
        run_screensaver()
