from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Temporary list to hold complaints in memory
complaints = []

@app.route('/')
def index():
    return render_template('index.html', complaints=complaints)

@app.route('/submit', methods=['POST'])
def submit():
    text = request.form.get('complaint')
    if text:
        complaints.append(text)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
