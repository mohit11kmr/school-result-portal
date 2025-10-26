from flask import Flask, render_template_string, request, send_file, redirect
import pandas as pd
from fpdf import FPDF
import io
import os
import json
from datetime import datetime

app = Flask(__name__)

# Simple home page
@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>School Result Portal</title>
        <style>
            body { font-family: Arial; margin: 40px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
            .container { max-width: 600px; margin: 100px auto; text-align: center; }
            h1 { font-size: 48px; margin-bottom: 20px; }
            .btn { display: inline-block; padding: 15px 30px; margin: 10px; background: #27ae60; color: white; 
                   text-decoration: none; border-radius: 8px; font-size: 18px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 School Portal</h1>
            <p style="font-size: 20px; margin-bottom: 30px;">Successfully Deployed on Render!</p>
            <a href="/admin" class="btn">🏫 Admin Panel</a>
            <a href="/student" class="btn">👨‍🎓 Student Portal</a>
        </div>
    </body>
    </html>
    '''

@app.route('/admin')
def admin():
    return '<h2>🏫 Admin Panel</h2><p>School management features coming soon!</p><a href="/">← Home</a>'

@app.route('/student')  
def student():
    return '<h2>👨‍🎓 Student Portal</h2><p>Result checking features coming soon!</p><a href="/">← Home</a>'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)