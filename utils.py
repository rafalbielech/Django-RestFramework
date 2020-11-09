import sys
import smtplib
import os
import datetime
import psutil
import time
import collections
import json
import requests
import socket
import numpy as np
from dateutil import relativedelta
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from random import randint

######################################################


def gen_powerball(num_start, num_end, pball_start, pball_end):
    numbers = []
    error_encountered = False
    while len(numbers) < 5:
        gen = randint(num_start, num_end)
        if gen not in numbers:
            numbers.append(gen)

    try:
        powerball_data = json.loads(
            requests.get(
                url="https://www.masslottery.com/data/json/games/lottery/10.json"
            ).text
        )
    except Exception as e:
        error_encountered = True
        powerball_data = {}
        print(e)
    return {
        "normal": sorted(numbers),
        "powerball": [randint(pball_start, pball_end)],
        "error": error_encountered,
        "data": powerball_data,
    }


def gen_mega_bucks_double(num_start, num_end):
    numbers = []
    error_encountered = False
    while len(numbers) < 6:
        gen = randint(num_start, num_end)
        if gen not in numbers:
            numbers.append(gen)
    try:
        mega_bucks_data = json.loads(
            requests.get(
                url="https://www.masslottery.com/data/json/games/lottery/11.json"
            ).text
        )
    except Exception as e:
        error_encountered = True
        mega_bucks_data = {}
        print(e)
    return {
        "normal": sorted(numbers),
        "error": error_encountered,
        "data": mega_bucks_data,
    }


def fan_control():
    import RPi.GPIO as GPIO

    print("Starting fan modulator..")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(5, GPIO.OUT)
    while True:
        cpu_temp = get_cpu_temp()
        if cpu_temp >= 50:
            GPIO.output(5, GPIO.HIGH)
        else:
            GPIO.output(5, GPIO.LOW)
        time.sleep(60)
    GPIO.cleanup()
    return


#################################################################################################
## Utils for getting raspberry pi parameters
#################################################################################################
def get_up_time():
    time_elapsed = collections.OrderedDict()
    return_string = []
    try:
        # get the difference between boot time and now,
        # save the difference into a dictionary that will be iterated to figure
        # the length of time
        boot_time = datetime.datetime.utcfromtimestamp(psutil.boot_time())
        now = datetime.datetime.utcfromtimestamp(time.time())
        difference = relativedelta.relativedelta(now, boot_time)
        time_elapsed["months"] = difference.months
        time_elapsed["days"] = difference.days
        time_elapsed["hours"] = difference.hours
        time_elapsed["minutes"] = difference.minutes
        # after all of the times have been added to the dictionary
        # iterate through the dictionary adn then combined it to make a return phrase
        for keys, val in time_elapsed.items():
            # pass if the time entity value is 0
            if val == 0:
                pass
            elif val == 1:
                # if the value is 1, then the time should be in a singular form
                keys = keys[:-1]
                return_string.append(str(val))
                return_string.append(keys)
            else:
                return_string.append(str(val))
                return_string.append(keys)
    except:
        return "ERROR getting up time"
    finally:
        return "Up: " + " ".join(return_string)


def get_ip_address():
    # Get the ip address by connectingn to the port 80
    # return the ip address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def format_datetime(string):
    # Replace all characters used to break up sentence with underscore
    # Will be used to save a sentence later
    temp = str(string)
    for item in ["-", " ", ":", "."]:
        temp = temp.replace(item, "_")
    return temp


def get_virtual_memory():
    # return virtual memory space
    mem = psutil.virtual_memory()
    total = mem.total / 1024 ** 2
    avail = mem.available / 1024 ** 2
    return avail, total


def get_cpu_5_min_load_avg():
    # load average over the last 5 minutes
    load = psutil.getloadavg()
    return load[1]


def get_cpu_temp():
    # cpu temperature
    x = psutil.sensors_temperatures(fahrenheit=False)
    return x["cpu_thermal"][0].current


def get_disk_usage():
    # return disk utilization
    dk = psutil.disk_usage("/")
    total = round(dk.total / 1024 ** 2, 1)
    avail = round(dk.free / 1024 ** 2, 1)
    perc = dk.percent
    return avail, total, perc


#################################################################################################
## Utils for sending email
#################################################################################################
def send_alert_email(conf, image_list):
    # conf --> configuration file
    # camera type --> location of the camera
    # image_list --> filepaths of the images that should be included in the email
    fromaddr = "address@gmail.com"
    toaddrs = conf["config"]["email_address"]
    subject = "Notification from {} camera".format(conf.get("local").get("alias"))

    # text = "Current Rpi status:\nDisk usage (Mb): free: {} percentage free {}%\nVirtual memory (Mb): free {} total {}\nCPU temperature (C): {}\nCPU load (5 min avg): {}%\nUp : {}\n\n".format(
    #     dk_free, dk_perc, vm_free, vm_total, temp, cpu_load, get_up_time())
    text = "Activity has been detected ...\n"
    message = "Subject: {}\n\n{}".format(subject, text)

    msg = MIMEMultipart()
    msg["From"] = fromaddr
    msg["To"] = toaddrs
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    msg.attach(MIMEText(text))
    # attach the pictures that were taken
    for f in image_list:
        with open(f, "rb") as file:
            part = MIMEApplication(file.read(), Name=basename(f))
            part["Content-Disposition"] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)
        try:
            os.remove(f)
            print("Successfully deleted {}".format(f))
        except:
            print("Error deleting {}".format(f))
            pass
    # once the files are attached to the email, then send it out using stmplib
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.starttls()
    server.login(conf["config"]["email_address"], conf["config"]["password"])
    server.sendmail(fromaddr, toaddrs, msg.as_string())
    server.quit()


def send_email(email_to, email_from, password, message_subject, message_body):
    try:
        stmp_object = smtplib.SMTP("smtp.gmail.com", 587)
        stmp_object.starttls()
        stmp_object.login(email_from, password)
        # Subject: ..... \n Body ....
        stmp_object.sendmail(
            email_from, email_to, "Subject: " + message_subject + "\n\n" + message_body
        )
        stmp_object.quit()
    except BaseException() as e:
        print("Some issue has occured with sending email: {}".format(e))


def send_email_with_video(
    email_to, email_from, password, message_subject, attachment_path
):
    try:
        msg = MIMEMultipart()
        msg["From"] = email_from
        msg["To"] = email_to
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = message_subject
        msg.attach(MIMEText("Video below"))
        for f in attachment_path:
            with open(f, "rb") as file:
                part = MIMEApplication(file.read(), Name=basename(f))
                part["Content-Disposition"] = 'attachment; filename="%s"' % basename(f)
                msg.attach(part)
                try:
                    os.remove(f)
                    print("Successfully deleted {}".format(f))
                except:
                    print("Error deleting {}".format(f))
                    pass
        stmp_object = smtplib.SMTP("smtp.gmail.com", 587)
        stmp_object.starttls()
        stmp_object.login(email_from, password)
        stmp_object.sendmail(email_from, email_to, msg.as_string())
        stmp_object.quit()
    except BaseException() as e:
        print("Some issue has occured with sending email: {}".format(e))


def capture_video_for_email(
    file_path, send_as_email, email_address, password, email_to, title
):
    import cv2

    return_statement = None
    try:
        start = time.time()
        capture = cv2.VideoCapture(0)
        # Define the codec and create VideoWriter object
        out = cv2.VideoWriter(file_path, 0x00000020, 24.0, (640, 480))

        # capture the video and start saving to file under file_path
        while capture.isOpened():
            # read in the frame
            ret, frame = capture.read()
            if ret == True:
                # flip the frame
                frame = cv2.flip(frame, 0)
                out.write(frame)
                # break after 30 seconds of capture
                if time.time() - start >= 30:
                    stop = time.time()
                    break
            else:
                break
        # Release everything after the job is finished
        capture.release()
        out.release()
        cv2.destroyAllWindows()
        return_statement = "done, saved file to {} with duration {} seconds".format(
            file_path, round(stop - start, 1)
        )
        if send_as_email:
            send_email_with_video(email_to, email_address, password, title, [file_path])
    except BaseException() as e:
        return_statement = e
    finally:
        return return_statement