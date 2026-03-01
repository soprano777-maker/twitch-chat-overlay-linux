#!/usr/bin/env python3
import sys
import asyncio
import re
from PyQt5 import QtCore, QtGui, QtWidgets

# ===== USTAWIENIA =====
CHANNEL = "soprano777gzx"   # bez #
HIDE_AFTER_MS = 12000       # po ilu ms znika wiadomość
MAX_MSGS = 12

FONT_SIZE = 22
PADDING = 14
LINE_SPACING = 6

WIN_X, WIN_Y = 50, 50
WIN_W, WIN_H = 900, 500

# toolbar pokazuje się na hover mimo click-through (poll globalnego kursora)
HOVER_POLL_MS = 50
HOVER_MARGIN = 0

# tło + ramka (gdy TŁO: ON) – rysowane ręcznie
BG_ALPHA = 80               # 0-255
FRAME_PX = 3
FRAME_ALPHA = 190           # 0-255
RADIUS_PX = 14

# resize bez ramek systemowych
RESIZE_MARGIN = 10          # px od krawędzi, gdzie łapie resize
MIN_W, MIN_H = 240, 140


def parse_irc_tags(tag_str: str) -> dict:
    out = {}
    if not tag_str:
        return out
    for kv in tag_str.split(";"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            out[k] = v
        else:
            out[kv] = ""
    return out


def parse_privmsg(line: str):
    tags = {}
    rest = line
    if rest.startswith("@"):
        sp = rest.find(" ")
        tags = parse_irc_tags(rest[1:sp])
        rest = rest[sp + 1:]
    if " PRIVMSG " not in rest:
        return None
    m = re.search(r"PRIVMSG\s+#\S+\s+:(.*)$", rest)
    if not m:
        return None
    text = m.group(1)
    name = tags.get("display-name") or "chat"
    return name, text


class MessageWidget(QtWidgets.QWidget):
    def __init__(self, user: str, text: str, hide_after_ms: int, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        name_lbl = QtWidgets.QLabel(f"{user}:")
        name_lbl.setStyleSheet("color: white; font-weight: 700;")
        name_lbl.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

        text_lbl = QtWidgets.QLabel(text)
        text_lbl.setStyleSheet("color: white; font-weight: 400;")
        text_lbl.setWordWrap(True)
        text_lbl.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

        layout.addWidget(name_lbl, 0, QtCore.Qt.AlignTop)
        layout.addWidget(text_lbl, 1)

        for lbl in (name_lbl, text_lbl):
            shadow = QtWidgets.QGraphicsDropShadowEffect()
            shadow.setBlurRadius(14)
            shadow.setOffset(0, 0)
            shadow.setColor(QtGui.QColor(0, 0, 0, 230))
            lbl.setGraphicsEffect(shadow)

        self.opacity = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)

        self.anim = QtCore.QPropertyAnimation(self.opacity, b"opacity", self)
        self.anim.setDuration(350)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)

        start_fade_ms = max(0, hide_after_ms - 350)
        QtCore.QTimer.singleShot(start_fade_ms, self.anim.start)
        QtCore.QTimer.singleShot(hide_after_ms, self._delete_self)

    def _delete_self(self):
        self.setParent(None)
        self.deleteLater()


class OverlayWindow(QtWidgets.QWidget):
    add_msg_signal = QtCore.pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat overlay")
        self.setGeometry(WIN_X, WIN_Y, WIN_W, WIN_H)
        self.setMinimumSize(MIN_W, MIN_H)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setMouseTracking(True)

        self.manual_locked = True
        self.bg_visible = True
        self._inside = False
        self._click_through = True

        self._dragging = False
        self._drag_pos = QtCore.QPoint(0, 0)

        self._resizing = False
        self._resize_dir = None
        self._resize_start_geo = QtCore.QRect()
        self._resize_start_pos = QtCore.QPoint()

        self.root = QtWidgets.QVBoxLayout(self)
        self.root.setContentsMargins(PADDING, PADDING, PADDING, PADDING)
        self.root.setSpacing(10)

        self.toolbar = QtWidgets.QWidget(self)
        tb = QtWidgets.QHBoxLayout(self.toolbar)
        tb.setContentsMargins(0, 0, 0, 0)
        tb.setSpacing(6)

        def mkbtn(txt):
            b = QtWidgets.QPushButton(txt)
            b.setCursor(QtCore.Qt.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton{color:white;background:rgba(0,0,0,140);"
                "border:1px solid rgba(255,255,255,120);border-radius:10px;"
                "padding:4px 10px;font-weight:800;}"
                "QPushButton:hover{background:rgba(0,0,0,210);}"
            )
            return b

        self.btn_lock = mkbtn("📌 ZABLOKUJ: ON")
        self.btn_bg = mkbtn("TŁO: ON")
        self.btn_close = mkbtn("ZAMKNIJ")

        tb.addWidget(self.btn_lock)
        tb.addWidget(self.btn_bg)
        tb.addStretch(1)
        tb.addWidget(self.btn_close)
        self.root.addWidget(self.toolbar)

        self.msg_container = QtWidgets.QWidget(self)
        self.msg_container.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.msg_layout = QtWidgets.QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(0, 0, 0, 0)
        self.msg_layout.setSpacing(LINE_SPACING)
        self.msg_layout.addStretch(1)
        self.root.addWidget(self.msg_container)

        font = QtGui.QFont()
        font.setPointSize(FONT_SIZE)
        self.setFont(font)

        self.add_msg_signal.connect(self.add_message)
        self.btn_lock.clicked.connect(self._toggle_manual_lock)
        self.btn_bg.clicked.connect(self._toggle_bg)
        self.btn_close.clicked.connect(QtWidgets.QApplication.quit)

        self.toolbar.setVisible(False)
        self.hover_timer = QtCore.QTimer(self)
        self.hover_timer.setInterval(HOVER_POLL_MS)
        self.hover_timer.timeout.connect(self._hover_poll)
        self.hover_timer.start()

        self._apply_effective_click_through()
        self.add_message("Overlay", "START — najedź na okno, pokażą się opcje")

    def _toggle_bg(self):
        self.bg_visible = not self.bg_visible
        self.btn_bg.setText("TŁO: ON" if self.bg_visible else "TŁO: OFF")
        self.update()

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if not self.bg_visible:
            return

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        rect = self.rect()
        half = FRAME_PX / 2.0
        r = QtCore.QRectF(rect).adjusted(half, half, -half, -half)

        bg = QtGui.QColor(0, 0, 0, BG_ALPHA)
        p.setBrush(bg)
        p.setPen(QtCore.Qt.NoPen)
        p.drawRoundedRect(r, RADIUS_PX, RADIUS_PX)

        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, FRAME_ALPHA))
        pen.setWidth(FRAME_PX)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRoundedRect(r, RADIUS_PX, RADIUS_PX)

    def _set_click_through(self, enable: bool):
        self._click_through = enable
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, enable)
        if enable:
            self._dragging = False
            self._resizing = False
            self._resize_dir = None
            self.unsetCursor()

    def _apply_effective_click_through(self):
        if self.manual_locked:
            self._set_click_through(True)
        else:
            self._set_click_through(not self._inside)

    def _toggle_manual_lock(self):
        self.manual_locked = not self.manual_locked
        self.btn_lock.setText("📌 ZABLOKUJ: ON" if self.manual_locked else "📌 ZABLOKUJ: OFF")
        self._apply_effective_click_through()

    def _hover_poll(self):
        pos = QtGui.QCursor.pos()
        geo = self.frameGeometry()
        geo = QtCore.QRect(
            geo.x() - HOVER_MARGIN,
            geo.y() - HOVER_MARGIN,
            geo.width() + 2 * HOVER_MARGIN,
            geo.height() + 2 * HOVER_MARGIN
        )
        inside = geo.contains(pos)

        self._inside = inside

        if inside:
            if not self.toolbar.isVisible():
                self.toolbar.setVisible(True)
        else:
            if self.toolbar.isVisible():
                self.toolbar.setVisible(False)

        self._apply_effective_click_through()

    def _hit_test_resize(self, local_pos: QtCore.QPoint):
        x, y = local_pos.x(), local_pos.y()
        w, h = self.width(), self.height()
        m = RESIZE_MARGIN

        left = x <= m
        right = x >= w - m
        top = y <= m
        bottom = y >= h - m

        if top and left:
            return "tl"
        if top and right:
            return "tr"
        if bottom and left:
            return "bl"
        if bottom and right:
            return "br"
        if left:
            return "l"
        if right:
            return "r"
        if top:
            return "t"
        if bottom:
            return "b"
        return None

    def _update_cursor(self, local_pos):
        if self._click_through:
            self.unsetCursor()
            return

        d = self._hit_test_resize(local_pos)
        if d in ("l", "r"):
            self.setCursor(QtCore.Qt.SizeHorCursor)
        elif d in ("t", "b"):
            self.setCursor(QtCore.Qt.SizeVerCursor)
        elif d in ("tl", "br"):
            self.setCursor(QtCore.Qt.SizeFDiagCursor)
        elif d in ("tr", "bl"):
            self.setCursor(QtCore.Qt.SizeBDiagCursor)
        else:
            self.unsetCursor()

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent):
        if self._click_through:
            return

        if self._resizing:
            self._do_resize(ev.globalPos())
            ev.accept()
            return

        if self._dragging and (ev.buttons() & QtCore.Qt.LeftButton):
            self.move(ev.globalPos() - self._drag_pos)
            ev.accept()
            return

        self._update_cursor(ev.pos())

    def mousePressEvent(self, ev: QtGui.QMouseEvent):
        if self._click_through:
            return

        if ev.button() == QtCore.Qt.LeftButton:
            d = self._hit_test_resize(ev.pos())
            if d:
                self._resizing = True
                self._resize_dir = d
                self._resize_start_geo = self.geometry()
                self._resize_start_pos = ev.globalPos()
                ev.accept()
                return

            self._dragging = True
            self._drag_pos = ev.globalPos() - self.frameGeometry().topLeft()
            ev.accept()

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent):
        if ev.button() == QtCore.Qt.LeftButton:
            self._dragging = False
            self._resizing = False
            self._resize_dir = None
            self.unsetCursor()
            ev.accept()

    def _do_resize(self, gpos: QtCore.QPoint):
        dx = gpos.x() - self._resize_start_pos.x()
        dy = gpos.y() - self._resize_start_pos.y()
        geo = QtCore.QRect(self._resize_start_geo)
        d = self._resize_dir or ""

        if "l" in d:
            new_x = geo.x() + dx
            new_w = geo.width() - dx
            if new_w >= MIN_W:
                geo.setX(new_x)
                geo.setWidth(new_w)
        if "r" in d:
            new_w = geo.width() + dx
            if new_w >= MIN_W:
                geo.setWidth(new_w)
        if "t" in d:
            new_y = geo.y() + dy
            new_h = geo.height() - dy
            if new_h >= MIN_H:
                geo.setY(new_y)
                geo.setHeight(new_h)
        if "b" in d:
            new_h = geo.height() + dy
            if new_h >= MIN_H:
                geo.setHeight(new_h)

        self.setGeometry(geo)

    @QtCore.pyqtSlot(str, str)
    def add_message(self, user: str, text: str):
        msg_widgets = [self.msg_layout.itemAt(i).widget() for i in range(self.msg_layout.count())]
        msg_widgets = [w for w in msg_widgets if isinstance(w, MessageWidget)]
        while len(msg_widgets) >= MAX_MSGS:
            w = msg_widgets.pop(0)
            w.setParent(None)
            w.deleteLater()

        w = MessageWidget(user, text, HIDE_AFTER_MS, self.msg_container)
        self.msg_layout.insertWidget(self.msg_layout.count() - 1, w)


async def twitch_loop(overlay: OverlayWindow):
    uri = "wss://irc-ws.chat.twitch.tv:443"
    import websockets

    async with websockets.connect(uri) as ws:
        await ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
        await ws.send("PASS SCHMOOPIIE")
        await ws.send(f"NICK justinfan{QtCore.QRandomGenerator.global_().bounded(100000)}")
        await ws.send(f"JOIN #{CHANNEL}")

        while True:
            data = await ws.recv()
            for line in str(data).split("\r\n"):
                if not line:
                    continue
                if line.startswith("PING"):
                    await ws.send("PONG :tmi.twitch.tv")
                    continue
                parsed = parse_privmsg(line)
                if parsed:
                    user, text = parsed
                    overlay.add_msg_signal.emit(user, text)


def run_async_in_thread(overlay: OverlayWindow):
    async def runner():
        try:
            await twitch_loop(overlay)
        except Exception as e:
            overlay.add_msg_signal.emit("Overlay", f"Błąd: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner())


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = OverlayWindow()
    w.show()

    t = QtCore.QThread()
    t.run = lambda: run_async_in_thread(w)
    t.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
