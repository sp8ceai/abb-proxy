#!/usr/bin/env python3
import os
import re
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from interpreter import COMMANDS_FOLDER

# ─── Load .env ────────────────────────────────────────────
load_dotenv()
# Secret key for flash messages (override in .env for production)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
NAME_PATTERN = re.compile(r'^[A-Za-z0-9_]+$')

# ─── Flask setup ─────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ─── Routes ──────────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    # Scan COMMANDS_FOLDER for .csv files
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
def add_command():
    name = request.form.get('name', '').strip()
    content = request.form.get('content', '').strip()

    # Validate name
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

    return redirect(url_for('index'))

@app.route('/run/<command_name>', methods=['POST'])
def run_command(command_name):
    # Validate name again
    if not NAME_PATTERN.match(command_name):
        flash('Invalid command name.', 'error')
        return redirect(url_for('index'))

    # Fire off the ROS2 CLI
    cmd = [
        'ros2', 'topic', 'pub',
        '/abb_proxy', 'std_msgs/String',
        f"{{data: '{command_name}'}}",
        '--once'
    ]
    try:
        subprocess.run(cmd, check=True)
        flash(f'Published "{command_name}".', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'ROS2 publish failed: {e}', 'error')

    return redirect(url_for('index'))

# ─── Run ─────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port)
