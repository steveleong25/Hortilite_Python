import datetime
from crontab import CronTab
from db_connect import get_data_retrieval_time

# Initialize crontab for the current user
cron = CronTab(user=True)

intervalHour = get_data_retrieval_time().replace(" ", "")

cron.remove_all(comment='sensor_task')

# Create a new cron job with a hidden comment
job = cron.new(command='/home/pi/tms/bin/python3.7 /Desktop/Hortilite_Python/read_All_Devices.py >> /Desktop/Hortilite_Python/log/log.txt 2>&1', comment='sensor_task')
job.setall('0 ' + intervalHour + ' * * *')
cron.write()

print(f"\n ===== {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')} ===== \n")
print(f"Cron job added with comment 'sensor_task' at time {intervalHour}")