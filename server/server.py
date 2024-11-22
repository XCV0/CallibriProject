from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)

# Замените 'data.txt' на желаемый путь к файлу\
data_file = "server\\db\\users.db"

#connection = sqlite3.connect(data_file)
#cursor = connection.cursor()

@app.route('/writedata')
def write_data():
  try:
    name = request.args.get('name')
    datapulse = request.args.get('datapulse')
    emotions = request.args.get('emotions')
    
    values = [
      (name),(datapulse),(emotions)
    ]
    
    if not name or not datapulse or not emotions:
      return jsonify({'error': 'Не все параметры указаны'}), 400
    
    with sqlite3.connect("server\\db\\users.db") as db:
      cursor = db.cursor()
      
    cursor.execute("INSERT INTO users(nickname, pulse_data, emotions_data) VALUES(?, ?, ?)", values)
    db.commit()
    
    return jsonify({'message': 'Данные успешно записаны'}), 200

  except Exception as e:
    return jsonify({'error': str(e)}), 500

  
@app.route('/writestatus')  
def write_status():
  try:
    name = request.args.get('name')
    status = request.args.get('status')
    
    if not name:
      return jsonify({'error': 'Не все параметры указаны'}), 400
    
    with sqlite3.connect("server\\db\\users.db") as db:
      cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE nickname = ?", (name,))
    exists = cursor.fetchone()[0] > 0
    
    if exists:
      cursor.execute(f"UPDATE users SET status_now = '{status}' WHERE nickname = ?", (name,))
    
    
    db.commit()
    return jsonify({'message': 'Данные успешно записаны'}), 200

  except Exception as e:
    return jsonify({'error': str(e)}), 500
  
  
if __name__ == '__main__':
  app.run(debug=True, port=8080)