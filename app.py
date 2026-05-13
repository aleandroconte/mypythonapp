from flask import Flask, request, render_template_string, redirect, Response
import subprocess

app = Flask(__name__)

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

SUBNETS = [
    "DMZ: 10.0.13.0/24",
    "VPN Clients: 10.8.0.0/24",
    "MISOP WS: <MISOP_WS_SUBNET>",
    "MGMT WS: <MGMT_WS_SUBNET>",
    "IT WS: <IT_WS_SUBNET>",
    "BLUE WS: <BLUE_WS_SUBNET>",
    "MISBLUE WS: <MISBLUE_WS_SUBNET>"
]

HOSTS = [
    "DMZ-VPN-01",
    "DMZ-BAST-01",
    "MISOP-MCWINWS-01",
    "MISOP-SPECWINWS-01",
    "MISOP-ACUWINWS-01",
    "MGMT-WINWS-01",
    "IT-WINWS-01",
    "BLUE-WINWS-01",
    "MISBLUE-WINWS-01"
]

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def require_auth():
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="VPN Gateway Admin"'}
    )

@app.route("/")
def index():
    return redirect("/status")

@app.route("/status")
def status():
    try:
        with open("/var/log/openvpn/status.log", "r") as f:
            vpn_status = f.read()
    except Exception as e:
        vpn_status = f"Cannot read OpenVPN status: {e}"

    return render_template_string("""
    <html><body>
        <h1>VPN Gateway Status</h1>
        <h2>Internal Subnets</h2>
        <ul>{% for s in subnets %}<li>{{ s }}</li>{% endfor %}</ul>
        <h2>Known Hosts</h2>
        <ul>{% for h in hosts %}<li>{{ h }}</li>{% endfor %}</ul>
        <h2>OpenVPN Status</h2>
        <pre>{{ vpn_status }}</pre>
    </body></html>
    """, subnets=SUBNETS, hosts=HOSTS, vpn_status=vpn_status)

@app.route("/admin")
def admin():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return require_auth()

    return render_template_string("""
    <html><body>
        <h1>VPN Gateway Admin</h1>
        <h2>Diagnostics</h2>
        <form action="/admin/ping" method="get">
            <label>Host to ping:</label>
            <input type="text" name="host" value="127.0.0.1">
            <input type="submit" value="Ping">
        </form>
        <h2>Logs</h2>
        <a href="/admin/logs">View OpenVPN Logs</a>
    </body></html>
    """)

@app.route("/admin/ping")
def admin_ping():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return require_auth()

    host = request.args.get("host", "127.0.0.1")
    cmd = f"ping -c 4 {host}"
    result = subprocess.getoutput(cmd)

    return render_template_string("""
    <html><body>
        <h1>Ping Diagnostics</h1>
        <p>Command executed:</p>
        <pre>{{ cmd }}</pre>
        <h2>Result</h2>
        <pre>{{ result }}</pre>
        <a href="/admin">Back</a>
    </body></html>
    """, cmd=cmd, result=result)

@app.route("/admin/logs")
def admin_logs():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return require_auth()

    log_files = [
        "/var/log/openvpn/openvpn.log",
        "/var/log/openvpn/status.log",
        "/var/log/nginx/access.log",
        "/var/log/nginx/error.log"
    ]

    output = ""
    for lf in log_files:
        output += f"\n\n===== {lf} =====\n"
        try:
            with open(lf, "r") as f:
                output += f.read()[-5000:]
        except Exception as e:
            output += f"Cannot read {lf}: {e}"

    return render_template_string("""
    <html><body>
        <h1>VPN Gateway Logs</h1>
        <pre>{{ output }}</pre>
        <a href="/admin">Back</a>
    </body></html>
    """, output=output)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
