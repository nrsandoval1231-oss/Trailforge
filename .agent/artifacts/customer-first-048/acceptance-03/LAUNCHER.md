# Local launcher verification

Task output launch_trailforge.py was executed with only webbrowser.open stubbed
to capture its requested URL (actual browser navigation remains CUA-controlled).
First run reused existing8766 desk; requested exactly http://127.0.0.1:8766.
Second run followed verified shutdown of the controller-owned desk process and
started a hidden new process through the launcher. GET /api/projects then returned
all4 real records, each integrity PASS and fuel locked. No data fabrication,
package reinstall, research-workbench interruption or external browser request.
Launcher log/PID live under task work/; current PID is in operator-live.pid.
The .cmd wrapper invokes the existing .venv Python with this adjacent script.
