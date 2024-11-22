from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)

# Замените 'data.txt' на желаемый путь к файлу
data_file = 'db\\users.db'

@app.route('/writedata')
def write_data():
  try:
    name = request.args.get('name')
    datapulse = request.args.get('datapulse')
    emotions = request.args.get('emotions')

    if not name or not datapulse or not emotions:
      return jsonify({'error': 'Не все параметры указаны'}), 400

    with open(data_file, 'a') as f:
      f.write(f"Имя: {name}, Пульс: {datapulse}, Эмоции: {emotions}\n")

    return jsonify({'message': 'Данные успешно записаны'}), 200

  except Exception as e:
    return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
  app.run(debug=True, port=8080)