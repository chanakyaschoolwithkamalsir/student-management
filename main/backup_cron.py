import os, sys, time
import subprocess
from .loggers import logger
from datetime import datetime

from django.http import JsonResponse


def backup_db(request):
    flag = True
    while flag:
        try:
            cmd = rf"python3 db_backup.py"
            logger.info(cmd)
            os.system(cmd)
            logger.info("Backup File Created")
            # time.slpeep(3600)
            return JsonResponse({'status':200,
                                'msg': 'Backup File Created'})
        except Exception as e:
            return JsonResponse({'status':200,
                                'msg': str(e)})
