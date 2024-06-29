import os, sys, time, subprocess

from datetime import datetime
from main.loggers import logger

# Configuration
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "academy"
DB_USER = "postgres"
DB_PASSWORD = "root"
BACKUP_DIR = "D:/OTHERS/practice_project/backup"
pg_dump_path = "/mnt/c/Program Files/PostgreSQL/14/bin/pg_dump.exe"

import os, sys, time
import subprocess

def create_backup():
    try:
        db_params = {
            'host': 'localhost',
            'port': 5432,
            'dbname': 'academy',
            'user': 'postgres',
            'password': 'root',
        }

        if 'win' in sys.platform:
            pg_dump_path = rf"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe"
            backup_file_path= rf"D:\\OTHERS\\practice_project\\backup\\{DB_NAME}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
            # backup_filename = f"{DB_NAME}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"

            ps = "set PGPASSWORD=root"
            os.system(ps)
        else:
            # pg_dump_path = r"C:/Program Files/PostgreSQL/14/bin/pg_dump.exe"
            pg_dump_path = rf"/mnt/c/Program Files/PostgreSQL/14/bin/pg_dump.exe"
            backup_filename = f"{DB_NAME}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
            backup_file_path = os.path.join(BACKUP_DIR, backup_filename)
            
            ps = "export PGPASSWORD=root"
            os.system(ps)

        print(f"{backup_file_path} is getting generated")
#         os.environ["PGPASSFILE"] = os.path.join(os.path.dirname(__file__), "pgpass.txt")
        backup_command = [
                        pg_dump_path,
                        f"--host={DB_HOST}",
                        f"--port={DB_PORT}",
                        f"--dbname={DB_NAME}",
                        f"--username={DB_USER}",
                        f"--file={backup_file_path}",
                        # f"--password={os.environ['DATABASE_PASSWORD']}",
                    ]

        password = "root"

        try:
#             logger.info("backup start")
            os.environ["PGPASSWORD"] = db_params['password']

            process = subprocess.Popen(backup_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=password)

            if process.returncode == 0:
                print("Database backup completed successfully.")
                for file in os.listdir(BACKUP_DIR):
                    print(file, backup_filename)
                    if ('sql' in file.split('.')) & (file!=backup_filename):
                        os.remove(os.path.join(BACKUP_DIR, file))
            else:
                print("Error during database backup:", stderr)
        except subprocess.CalledProcessError as e:
            print("Error during database backup:", e)
        
        return ({'status':200, 'msg':'success'})
    
    except Exception as e:
        return ({'status':200, 'msg':e})

# while True:
#     create_backup()
#     time.sleep(3600)

create_backup()