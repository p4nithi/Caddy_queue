from flask import Flask, render_template, request, jsonify
import csv
import datetime


app = Flask(__name__)

# Store statuses
waiting_list = list(range(1, 152))  # Default to all numbers
status_1_tee = []
status_2_tee = []
on_leave = []

# Store logs in memory
logs = []

# Store last status of each number
last_status = {}

# Helper function to save log to CSV
def save_log_to_csv(log_entry):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"logs_{date_str}.csv"
    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(log_entry)

@app.route("/")

def index():
    # Count statuses
    counts = {
        "waiting": len(waiting_list),
        "status_1": len(status_1_tee),
        "status_2": len(status_2_tee),
        "on_leave": len(on_leave),
    }
    return render_template(
        "index.html",
        waiting_list=waiting_list,
        status_1=status_1_tee,
        status_2=status_2_tee,
        on_leave=on_leave,
        logs=logs,
        counts=counts,
    )
def home():
    return render_template("index.html")  # ตรวจสอบว่า index.html อยู่ในโฟลเดอร์ templates

# Handler สำหรับ Vercel Serverless
def handler(event, context):
    return app(event, context)
@app.route("/move", methods=["POST"])
def move():
    global waiting_list, status_1_tee, status_2_tee, on_leave, logs, last_status
    data = request.get_json()
    number = int(data["number"])
    force_leave = data.get("forceLeave", False)

    # Handle force leave
    if force_leave:
        if number in waiting_list:
            waiting_list.remove(number)
            on_leave.append(number)
            last_status[number] = "Waiting"
            old_status, new_status = "Waiting", "On Leave"
    else:
        # Normal status cycle (Double Click)
        if number in waiting_list:
            waiting_list.remove(number)
            status_1_tee.append(number)
            last_status[number] = "Waiting"
            old_status, new_status = "Waiting", "1 Tee"
        elif number in status_1_tee:
            status_1_tee.remove(number)
            status_2_tee.append(number)
            last_status[number] = "1 Tee"
            old_status, new_status = "1 Tee", "2 Tee"
        elif number in status_2_tee:
            status_2_tee.remove(number)
            waiting_list.append(number)
            last_status[number] = "2 Tee"
            old_status, new_status = "2 Tee", "Waiting"

    # Log the action
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = [timestamp, number, old_status, new_status]
    logs.append(log_entry)
    save_log_to_csv(log_entry)

    # Map new status to CSS class
    status_class_map = {"Waiting": "green", "1 Tee": "red", "2 Tee": "blue", "On Leave": "white"}
    return jsonify(success=True, new_status=status_class_map[new_status])

@app.route("/revert", methods=["POST"])
def revert_status():
    global waiting_list, status_1_tee, status_2_tee, on_leave, logs, last_status
    data = request.get_json()
    number = int(data["number"])

    # Revert status logic
    if number in last_status:
        current_status = None
        if number in waiting_list:
            waiting_list.remove(number)
            current_status = "Waiting"
        elif number in status_1_tee:
            status_1_tee.remove(number)
            current_status = "1 Tee"
        elif number in status_2_tee:
            status_2_tee.remove(number)
            current_status = "2 Tee"
        elif number in on_leave:
            on_leave.remove(number)
            current_status = "On Leave"

        # Restore to the last status
        restored_status = last_status.pop(number)
        if restored_status == "Waiting":
            waiting_list.append(number)
        elif restored_status == "1 Tee":
            status_1_tee.append(number)
        elif restored_status == "2 Tee":
            status_2_tee.append(number)
        elif restored_status == "On Leave":
            on_leave.append(number)

        # Log the action
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        log_entry = [timestamp, number, current_status, restored_status]
        logs.append(log_entry)
        save_log_to_csv(log_entry)

        return jsonify(success=True, new_status=restored_status)
    else:
        return jsonify(success=False, message="No previous status to revert to.")

if __name__ == "__main__":
    app.run()