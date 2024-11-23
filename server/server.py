from flask import Flask, request, jsonify
import sqlite3
import json
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
     
    if(cursor.execute(f"SELECT * FROM users WHERE nickname = ?", (name,)).fetchone() is None):
       cursor.execute("INSERT INTO users(nickname, pulse_data, emotions_data) VALUES(?, ?, ?)", values)
       db.commit()
       return jsonify({'message': 'Данные успешно записаны'}), 200
    else:
      old_datapulse = cursor.execute("SELECT pulse_data FROM users WHERE nickname = ?", (name,)).fetchone()
      cursor.execute(f"UPDATE users SET pulse_data = '{old_datapulse} + ) + {datapulse}'")
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
  
  
@app.route('/get_online')  
def write_online():
  try:
    with sqlite3.connect("server\\db\\users.db") as db:
      cursor = db.cursor()
      
    query = "SELECT * FROM users WHERE status_now = ?"
    status_value = "online" 
    cursor.execute(query, (status_value,))


    
    columns = [column[0] for column in cursor.description] 
    rows = cursor.fetchall()

    
    data = [dict(zip(columns, row)) for row in rows]
    json_data = json.dumps(data, ensure_ascii=False, indent=4)
    return json_data

  except Exception as e:
    return jsonify({'error': str(e)}), 500
  
if __name__ == '__main__':
  app.run(host='25.8.42.226', debug=True, port=8080)