# main.py
import customtkinter as ctk
import platform


from app_state import AppState
from ui_panels import build_main_panel
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

def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    state = AppState(step=STEP_DEFAULT)

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

    # Size & center-ish
    app.geometry("640x320")

    panel, pan_slider, tilt_slider, refresh_pos = build_main_panel(app, state, servo)
    panel.pack(fill="both", expand=True, padx=12, pady=12)

    # --- Keyboard controls ---
    def apply_and_sync():
        # sync sliders with actual servo angles after clamps
        pan_slider.set(servo.pan_angle)
        tilt_slider.set(servo.tilt_angle)
        refresh_pos()

    def on_key(event):
        k = event.keysym

        # Arrow keys
        if k == "Left":
            servo.nudge(d_pan=-state.step)
        elif k == "Right":
            servo.nudge(d_pan=state.step)
        elif k == "Up":
            servo.nudge(d_tilt=state.step)
        elif k == "Down":
            servo.nudge(d_tilt=-state.step)

        # WASD
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
            servo.close()
        finally:
            app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_close)

    app.mainloop()

if __name__ == "__main__":
    main()
