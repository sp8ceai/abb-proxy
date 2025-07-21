#!/usr/bin/env python3
import os
import re
import time
import subprocess
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from interpreter import COMMANDS_FOLDER

# ─── Load .env ────────────────────────────────────────────
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
PASSWORD = SECRET_KEY  # simple password
NAME_PATTERN = re.compile(r'^[A-Za-z0-9_]+$')

# ─── Flask setup ─────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ─── Auth decorator ───────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Rate‑limit lock ───────────────────────────────────────
last_op = 0
LOCK_DURATION = 5  # seconds

def block_if_recent():
    global last_op
    now = time.time()
    if now - last_op < LOCK_DURATION:
        flash('Please wait a few seconds between operations.', 'error')
        return False
    last_op = now
    return True

# ─── Routes ──────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pwd = request.form.get('password', '')
        if pwd == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash('Incorrect password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
@login_required
def index():
    try:
        files = os.listdir(COMMANDS_FOLDER)
    except FileNotFoundError:
        files = []
    commands = sorted(
        os.path.splitext(f)[0]
        for f in files
        if f.lower().endswith('.csv')
    )
    return render_template('index.html', commands=commands)

@app.route('/add', methods=['POST'])
@login_required
def add_command():
    if not block_if_recent():
        return redirect(url_for('index'))
    name = request.form.get('name', '').strip()
    content = request.form.get('content', '').strip()
    if not NAME_PATTERN.match(name):
        flash('Invalid name: only letters, numbers, and underscores allowed.', 'error')
        return redirect(url_for('index'))
    dest = os.path.join(COMMANDS_FOLDER, f"{name}.csv")
    if os.path.exists(dest):
        flash(f'Command "{name}" already exists.', 'error')
        return redirect(url_for('index'))
    try:
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(content)
        flash(f'Added command "{name}".', 'success')
    except Exception as e:
        flash(f'Failed to save: {e}', 'error')
    time.sleep(LOCK_DURATION)
    return redirect(url_for('index'))

@app.route('/run/<command_name>', methods=['POST'])
@login_required
def run_command(command_name):
    if not block_if_recent():
        return redirect(url_for('index'))
    if not NAME_PATTERN.match(command_name):
        flash('Invalid command name.', 'error')
        return redirect(url_for('index'))
    # Build payload string for ROS2 publish
    payload = "{data: '" + command_name + "'}"
    cmd = [
        'ros2', 'topic', 'pub',
        '/abb_proxy', 'std_msgs/String',
        payload,
        '--once'
    ]
    try:
        subprocess.run(cmd, check=True)
        flash(f'Published "{command_name}".', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'ROS2 publish failed: {e}', 'error')
    time.sleep(LOCK_DURATION)
    return redirect(url_for('index'))

@app.route('/delete/<command_name>', methods=['POST'])
@login_required
def delete_command(command_name):
    if not block_if_recent():
        return redirect(url_for('index'))
    if not NAME_PATTERN.match(command_name):
        flash('Invalid command name.', 'error')
        return redirect(url_for('index'))
    path = os.path.join(COMMANDS_FOLDER, f"{command_name}.csv")
    try:
        os.remove(path)
        flash(f'Deleted "{command_name}".', 'success')
    except FileNotFoundError:
        flash(f'Command not found.', 'error')
    except Exception as e:
        flash(f'Error deleting: {e}', 'error')
    time.sleep(LOCK_DURATION)
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port)
