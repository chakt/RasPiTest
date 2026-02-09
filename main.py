# main.py
import customtkinter as ctk
import platform
import threading

from app_state import AppState
from ui_panels import build_main_panel

# ---- Servo controller selection ----
if platform.system() == "Linux":
    try:
        from servo_controller_pi import ServoControllerPi
        ServoController = ServoControllerPi
        IS_PI = True
    except Exception as e:
        print("⚠️ Failed to load real Pi servo controller:", e)
        from servo_controller_mock import ServoControllerMock
        ServoController = ServoControllerMock
        IS_PI = False
else:
    from servo_controller_mock import ServoControllerMock
    ServoController = ServoControllerMock
    IS_PI = False

STEP_DEFAULT = 5

def looks_like_placeholder(s: str) -> bool:
    s = (s or "").strip()
    if not s:
        return True
    # 你而家 upload git 會變成 ********
    if set(s) == {"*"}:
        return True
    if "PASTE_" in s.upper():
        return True
    return False

def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    state = AppState(step=STEP_DEFAULT)

    # =========================
    # SmartThings (OPTIONAL)
    # If token/ids are placeholder -> DO NOT START
    # =========================
    ST_TOKEN = "**************"
    ST_LEFT_ID = "**************"   # servo_left deviceId
    ST_RIGHT_ID = "**************"  # servo_right deviceId

    # Create servo controller (Pi-only)
    servo = ServoController(
        pan_gpio=18,
        tilt_gpio=19,
        pan_safe=(state.pan_min, state.pan_max),
        tilt_safe=(state.tilt_min, state.tilt_max),
        home=(state.pan, state.tilt),
    )

    app = ctk.CTk()
    app.title("Pi Servo Test")
    app.geometry("640x320")

    panel, pan_slider, tilt_slider, refresh_pos = build_main_panel(app, state, servo)
    panel.pack(fill="both", expand=True, padx=12, pady=12)

    # --- Keyboard & UI sync helpers ---
    def apply_and_sync():
        pan_slider.set(servo.pan_angle)
        tilt_slider.set(servo.tilt_angle)
        refresh_pos()

    # =========================
    # SmartThings polling thread (NON-BLOCKING, OPTIONAL)
    # =========================
    st = None
    if looks_like_placeholder(ST_TOKEN) or looks_like_placeholder(ST_LEFT_ID) or looks_like_placeholder(ST_RIGHT_ID):
        print("ℹ️ SmartThings disabled (token/deviceId placeholder).")
    else:
        try:
            from smartthings_controller import SmartThingsController

            st = SmartThingsController(
                token=ST_TOKEN,
                left_device_id=ST_LEFT_ID,
                right_device_id=ST_RIGHT_ID,
                poll_interval=5.0,     # 建議 >= 1.0，避免 429
                cooldown_sec=0.25,
                step_deg=state.step,
                enabled=True,
            )

            def st_left(step):
                servo.nudge(d_pan=-step)
                app.after(0, apply_and_sync)  # UI thread-safe

            def st_right(step):
                servo.nudge(d_pan=step)
                app.after(0, apply_and_sync)

            threading.Thread(target=st.run, args=(st_left, st_right), daemon=True).start()
            print("✅ SmartThings polling started (LEFT/RIGHT)")

        except Exception as e:
            # Absolutely do not block program
            print("ℹ️ SmartThings disabled (init failed). Continue without it:", e)
            st = None

    # --- Keyboard controls ---
    def on_key(event):
        k = event.keysym

        if k == "Left":
            servo.nudge(d_pan=-state.step)
        elif k == "Right":
            servo.nudge(d_pan=state.step)
        elif k == "Up":
            servo.nudge(d_tilt=state.step)
        elif k == "Down":
            servo.nudge(d_tilt=-state.step)
        elif k in ("a", "A"):
            servo.nudge(d_pan=-state.step)
        elif k in ("d", "D"):
            servo.nudge(d_pan=state.step)
        elif k in ("w", "W"):
            servo.nudge(d_tilt=state.step)
        elif k in ("s", "S"):
            servo.nudge(d_tilt=-state.step)
        elif k == "space":
            servo.home(90, 90)
        elif k == "Escape":
            app.destroy()
            return

        apply_and_sync()

    app.bind("<KeyPress>", on_key)
    app.focus_force()

    # Clean exit
    def on_close():
        try:
            try:
                if st:
                    st.stop()
            except Exception:
                pass
            servo.close()
        finally:
            app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()

if __name__ == "__main__":
    main()
