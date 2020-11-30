from django.utils.timezone import now
from django.core.mail import EmailMessage
from .models import *
import sys
import os
import time
import cv2
import logging
import numpy as np
from threading import Thread
from queue import Queue

CLASSES = [
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]
logger = logging.getLogger(__name__)


class PersonDetection:
    def __init__(self, prototxt_loc, model_loc, conf, confidence):
        """
        model_loc - location of the model
        prototxt_loc - location of the prototxt
        confidence - how strongly do we feel about the detections
        """
        self.configuration = conf
        self.confidence = confidence
        """
        inputQueue holds up to 1 frame, that will then we sent to the thread that performs detection
        detectionQueue is a queue that holds detections after they have been classifed, email thread takes from this queue
        detectionMessageQueue, messageQueue, and threadQueue will hold messages that will be saved into the database
        Reason : DB lock error with threads reusing connection
        """
        self.inputQueue = Queue(maxsize=1)
        self.detectionQueue = Queue(maxsize=50)

        self.detectionMessageQueue = Queue(maxsize=10)
        self.messageQueue = Queue(maxsize=50)
        self.threadQueue = Queue(maxsize=50)

        self.model = self.load_files(model_loc, prototxt_loc)

    def load_files(self, model_path, prototxt_path):
        """
        Load_files function is responsible for loading caffe model and the txt definition of the model
        """
        model = None
        try:
            model = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        except Exception as e:
            logger.exception("load_files : {}".format(e))
        finally:
            return model

    def messagePasser(self):
        """
        Keep looking at the message queue, if something shows up, then write to database
        """
        while True:
            if not self.messageQueue.empty():
                saved_message = self.messageQueue.get()
                m = Message(
                    function=saved_message.get("function", "no function specified"),
                    message=saved_message.get("message", "no message"),
                )
                m.save()
                time.sleep(3)

    def detectionMessagePasser(self):
        """
        Keep looking at the detectionMessageQueue, if something shows up, then write to database
        """
        while True:
            if not self.detectionMessageQueue.empty():
                saved_message = self.detectionMessageQueue.get()
                d = CameraDetection(
                    calling_process=os.getpid(),
                    num_of_captures=saved_message.get("num_of_captures", 0),
                    receiver_address=saved_message.get("email", "empty@gmail.com"),
                )
                d.save()
                time.sleep(3)

    def threadActivityPasser(self):
        """
        Keep looking at the thread activity queue, if something shows up, then write to database
        """
        while True:
            if not self.threadQueue.empty():
                saved_message = self.threadQueue.get()
                ta = ThreadActivity(
                    thread_type=saved_message.get("thread_type", "no type specified"),
                    attribute_1=saved_message.get("attribute_1", ""),
                    attribute_2=saved_message.get("attribute_2", ""),
                    restart=saved_message.get("restart", False),
                )
                ta.save()
                time.sleep(3)

    def send_detections(self):
        """
        Keep reading the detection queue to determine if there are any detections that should be processed (emailed)
        If the size of the detection queue is as big as the min_size, then get all of the items in the detection queue and
        process.
        """
        min_size = self.configuration.get("surveillance_setting", {}).get("min_motion_frames", 3)
        frame_list = 0
        while True:
            if not self.detectionQueue.empty() and self.detectionQueue.qsize() >= min_size:
                """
                If there are enogh items in the detection queue, then append them to a list
                and pass that list to function to send out
                """
                msg = EmailMessage(
                    "Notification from {}".format(self.configuration.get("local").get("alias")),
                    "Attached are images that have been detected with people \n\n\n",
                    self.configuration.get("config", {}).get("email_address", None),
                    [self.configuration.get("config", {}).get("email_address", None)],
                )
                msg.content_subtype = "html"
                for _ in range(self.detectionQueue.qsize()):
                    try:
                        " add the captured file to the message "
                        file_path = self.detectionQueue.get()
                        msg.attach_file(file_path)
                        frame_list += 1
                        try:
                            os.remove(file_path)
                        except:
                            continue
                    except:
                        continue
                msg.send()

                if not self.detectionMessageQueue.full():
                    self.detectionMessageQueue.put(
                        {
                            "num_of_captures": frame_list,
                            "email": self.configuration.get("config", {}).get("email_address", "empty@gmail.com"),
                        }
                    )
                " Empty the framelist "
                frame_list = 0
            else:
                " Just sleep to avoid overflow "
                time.sleep(self.configuration.get("surveillance_setting", {}).get("detection_sleep_time", 1))

    def classify_frame(self):
        """
        Keep looping, if the input queue is not empty, then take that frame and try to classify it
        """
        while True:
            " Check to see if there is a frame in our input queue "
            if not self.inputQueue.empty():
                try:
                    " grab the frame from the input queue, resize it, and construct a blob from it "
                    frame_original = self.inputQueue.get()
                    frame = cv2.resize(frame_original, (300, 300))
                    blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)

                    """
                    set the blob as input to our deep learning object
                    detector and obtain the detections
                    """
                    self.model.setInput(blob)
                    detections = self.model.forward()

                    " check if a person was detected with some confidence, if yes, then write that frame to detectionQueue "
                    if detections is not None:
                        " loop over the detections "
                        person_detected = False
                        for i in np.arange(0, detections.shape[2]):
                            " extract the confidence (i.e., probability) associated with the prediction "
                            confidence = detections[0, 0, i, 2]
                            idx = int(detections[0, 0, i, 1])
                            if confidence >= self.confidence and CLASSES[idx] == "person":
                                person_detected = True
                                break

                        if person_detected:
                            " if the detection queue is not full, then add items to the queue "
                            " else just continue "
                            if not self.detectionQueue.full():
                                image_name = self.configuration["surveillance_setting"][
                                    "frame_file_path"
                                ] + "{}.jpg".format(now().strftime("%d_%m_%Y_at_%H_%M_%S"))

                                cv2.imwrite(image_name, frame_original)
                                self.detectionQueue.put(image_name)
                            else:
                                continue
                except Exception as e:
                    logger.exception("[ERROR] func classify_frame - {}".format(e))
                    continue
            " Just sleep to avoid overflow "
            time.sleep(self.configuration.get("surveillance_setting", {}).get("detection_sleep_time", 0.5))

    def start_capture(self, type, to_flip, url=None):
        """
        Start a video capture, either a RTSP or picamera
        If the input queue is empty, then add the frame to the queue
        to be classified
        """
        cap = None
        while True:
            if not self.messageQueue.full():
                self.messageQueue.put(
                    {
                        "function": "person_detection.start_capture",
                        "message": "Starting {} capture from {}".format(type, url),
                    }
                )

            if type == "picamera":
                cap = cv2.VideoCapture(0)
            elif type == "rtsp":
                cap = cv2.VideoCapture(url)

            while True:
                ret, frame = cap.read()

                " if the input queue *is* empty, give the current frame to "
                if ret:
                    if self.inputQueue.empty():
                        " check if the frame has to flipped "
                        if to_flip == "T":
                            frame = cv2.flip(frame, 0)

                        self.inputQueue.put(frame)
                else:
                    logger.error("[ERROR] breaking process at {}".format(now().strftime("%d_%m_%Y_at_%H_%M_%S")))
                    break

            logger.error("[ERROR] encountered, killing thread ...")
            cap.release()

    def start_system(self, delay):
        try:
            assert self.model != None
        except AssertionError:
            logger.error("Model is not loaded correctly, exiting ... ")
            sys.exit()

        logger.info("Starting video stream with {} second delay".format(delay))
        time.sleep(delay)

        """
        From the configuration file, get the type of capture and the urls (if rtsp)
        """
        capture_type = self.configuration.get("surveillance_setting", {}).get("type", "picamera")
        urls = self.configuration.get("surveillance_setting", {}).get("url", [])
        flip = self.configuration.get("surveillance_setting", {}).get("flip", "F")

        threads = []
        " Thread to capture frames and saving to inputQueue"
        if capture_type == "picamera":
            cc = Thread(
                target=self.start_capture,
                args=(
                    capture_type,
                    flip,
                ),
            )
            cc.daemon = True
            cc.start()
            threads.append(
                {
                    "thread": cc,
                    "capture_type": "picamera",
                    "type": "capture",
                }
            )
            self.threadQueue.put({"thread_type": "capture", "attribute_1": "picamera"})

        elif capture_type == "rtsp":
            for url in urls:
                cc = Thread(
                    target=self.start_capture,
                    args=(capture_type, flip, url),
                )
                cc.daemon = True
                cc.start()
                threads.append(
                    {
                        "thread": cc,
                        "capture_type": "rtsp",
                        "url": url,
                        "type": "capture",
                    }
                )

                self.threadQueue.put({"thread_type": "capture", "attribute_1": "rtsp", "attribute_2": url})

        " Thread to classify frames using pass results from detectionQueue to be mailed out"
        e = Thread(target=self.send_detections)
        e.daemon = True
        e.start()
        threads.append({"thread": e, "type": "email"})
        self.threadQueue.put(
            {
                "thread_type": "email",
            }
        )

        " Thread to classify frames using inputQueue & passing to detectionQueue"
        c = Thread(target=self.classify_frame)
        c.daemon = True
        c.start()
        threads.append({"thread": c, "type": "classify"})
        self.threadQueue.put(
            {
                "thread_type": "classify",
            }
        )

        " Thread to continually scan the messageQueue"
        m = Thread(target=self.messagePasser)
        m.daemon = True
        m.start()
        threads.append({"thread": m, "type": "message"})

        " Thread to continually scan the threadActivityQueue"
        ta = Thread(target=self.threadActivityPasser)
        ta.daemon = True
        ta.start()
        threads.append({"thread": ta, "type": "threadActivity"})

        " Thread to continually scan the detectionMessagePasser"
        dm = Thread(target=self.detectionMessagePasser)
        dm.daemon = True
        dm.start()
        threads.append({"thread": dm, "type": "detectionMessage"})

        while True:
            for index, t in enumerate(threads):
                if not t["thread"].is_alive():
                    if t["type"] == "classify":
                        c = Thread(target=self.classify_frame)
                        c.daemon = True
                        c.start()
                        threads[index] = {"thread": c, "type": "classify"}
                        self.threadQueue.put({"thread_type": "classify", "restart": True})

                    elif t["type"] == "email":
                        e = Thread(target=self.send_detections)
                        e.daemon = True
                        e.start()
                        threads[index] = {"thread": e, "type": "email"}
                        self.threadQueue.put({"thread_type": "email", "restart": True})

                    elif t["type"] == "capture":
                        capture_type = t["capture_type"]
                        url = t.get("url", "")

                        if capture_type == "picamera":
                            cc = Thread(
                                target=self.start_capture,
                                args=(
                                    capture_type,
                                    flip,
                                ),
                            )
                        elif capture_type == "rtsp":
                            cc = Thread(
                                target=self.start_capture,
                                args=(
                                    capture_type,
                                    flip,
                                    url,
                                ),
                            )
                        cc.daemon = True
                        cc.start()
                        threads[index] = {
                            "thread": cc,
                            "capture_type": capture_type,
                            "url": url,
                            "type": "capture",
                        }

                        self.threadQueue.put(
                            {"thread_type": "capture", "attribute_1": capture_type, "attribute_2": url, "restart": True}
                        )

                    logger.error("After restarting threads - {}".format(threads))
            time.sleep(60 * 5)