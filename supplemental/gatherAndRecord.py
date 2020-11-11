import sys
import os
import django
import speedtest
import psutil
import datetime
import traceback
from threading import Thread

sys.path.append(os.path.dirname(sys.path[0]))


MEGABYTE = 1024 ** 2
monitor_data = {}


def internet_speed_test(num_of_runs=5):
    download_list, upload_list = [], []
    try:
        internet_speed_test = speedtest.Speedtest()
        connection_server = internet_speed_test.get_best_server()
        # this returns dict_keys(['url', 'lat', 'lon', 'name', 'country', 'cc', 'sponsor', 'id', 'host', 'd', 'latency'])
        for _ in range(num_of_runs):
            download_list.append(internet_speed_test.download() / MEGABYTE)
            upload_list.append(internet_speed_test.upload() / MEGABYTE)

        download_speed = round(sum(download_list) / float(len(download_list)), 3)
        upload_speed = round(sum(upload_list) / float(len(upload_list)), 3)

        monitor_data["url_upload"] = connection_server["url"]
        monitor_data["location"] = "{}, {}".format(connection_server["name"], connection_server["country"])
        monitor_data["latency"] = connection_server["latency"]
        monitor_data["download"] = download_speed
        monitor_data["upload"] = upload_speed

        network_data = NetworkStat(
            url_upload=monitor_data.get("url_upload", "error.com"),
            location=monitor_data.get("location", "ERROR"),
            latency=monitor_data.get("latency", 0.0),
            download=monitor_data.get("download", 0.0),
            upload=monitor_data.get("upload", 0.0),
        )
        network_data.save()

    except Exception as e:
        print("Unable to find connection to internet server", e)
        traceback.print_exc()
        sys.exit()
    finally:
        return


def cpu_test():
    def get_cpu_load_avg():
        return [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()][1:]

    def get_cpu_temp():
        try:
            x = psutil.sensors_temperatures(fahrenheit=False)
            return x["cpu_thermal"][0].current
        except:
            return 0.0

    try:
        load_average = get_cpu_load_avg()
        monitor_data["cpu_percent_5_min"] = load_average[0]
        monitor_data["cpu_percent_15_min"] = load_average[1]
        monitor_data["cpu_temperature"] = get_cpu_temp()
        monitor_data["cpu_curr_freq"] = psutil.cpu_freq()[0]
        monitor_data["cpu_max_freq"] = psutil.cpu_freq()[2]
    except Exception as e:
        print("Unable to get CPU data", e)
        traceback.print_exc()
        sys.exit()

    finally:
        return


def memory_test():
    def get_memory():
        mem = psutil.virtual_memory()
        total = mem.total / MEGABYTE
        used = mem.used / MEGABYTE
        available = mem.available / MEGABYTE
        free = mem.free / MEGABYTE
        return total, used, available, free, mem.percent

    try:
        t, u, a, f, p = get_memory()
        monitor_data["memory_total"] = t
        monitor_data["memory_used"] = u
        monitor_data["memory_used"] = a
        monitor_data["memory_free"] = f
        monitor_data["memory_free_percentage"] = p
    except Exception as e:
        print("Unable to get memory data", e)
        traceback.print_exc()
        sys.exit()

    finally:
        return


def disk_test():
    def get_disk():
        disk = psutil.disk_usage("/")
        total = disk.total / MEGABYTE
        used = disk.used / MEGABYTE
        free = disk.free / MEGABYTE
        return used, total, free, disk.percent

    try:
        u, t, f, p = get_disk()
        monitor_data["disk_total"] = t
        monitor_data["disk_used"] = u
        monitor_data["disk_free"] = f
        monitor_data["disk_free_percentage"] = p
    except Exception as e:
        print("Unable to get disk data", e)
        traceback.print_exc()
        sys.exit()

    finally:
        return


def misc_test():
    try:
        monitor_data["boot_time"] = datetime.datetime.fromtimestamp(psutil.boot_time())
        monitor_data["num_pids"] = len(psutil.pids())
    except Exception as e:
        print("Unable to get misc data", e)
        traceback.print_exc()
        sys.exit()

    finally:
        return


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()
    from parameter_monitor.models import *

    try:
        threads = []
        for function in [misc_test, disk_test, memory_test, cpu_test]:
            process = Thread(target=function)
            process.start()
            threads.append(process)

        for process in threads:
            process.join()

        gs = GeneralSystemParameter(
            cpu_percent_5_min=monitor_data.get("cpu_percent_5_min", 0.0),
            cpu_percent_15_min=monitor_data.get("cpu_percent_15_min", 0.0),
            cpu_temperature=monitor_data.get("cpu_temperature", 0.0),
            cpu_curr_freq=monitor_data.get("cpu_curr_freq", 0.0),
            cpu_max_freq=monitor_data.get("cpu_max_freq", 0.0),
            memory_total=monitor_data.get("memory_total", 0.0),
            memory_used=monitor_data.get("memory_used", 0.0),
            memory_available=monitor_data.get("memory_available", 0.0),
            memory_free=monitor_data.get("memory_free", 0.0),
            memory_free_percentage=monitor_data.get("memory_free_percentage", 0.0),
            disk_total=monitor_data.get("disk_total", 0.0),
            disk_used=monitor_data.get("disk_used", 0.0),
            disk_free=monitor_data.get("disk_free", 0.0),
            disk_free_percentage=monitor_data.get("disk_free_percentage", 0.0),
            boot_time=monitor_data.get("boot_time", datetime.datetime.now()),
            num_pids=monitor_data.get("num_pids", 0),
        )
        gs.save()

        " start download & upload internet tester"
        process = Thread(target=internet_speed_test)
        process.start()
        process.join()

    except Exception as e:
        traceback.print_exc()
