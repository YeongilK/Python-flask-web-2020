from flask import Flask, render_template
app = Flask(__name__)

@app.route('/hello')
@app.route('/hello/<name>')
def hello(name=None):
    xdt = {'key1': 'value1', 'key2': 'value2'}   # xdt['key1'], xdt.key1
    return render_template('06_hello.html', name=name, dt=xdt)

if __name__ == '__main__':
    app.run(debug=True)