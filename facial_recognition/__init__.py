# credit to https://github.com/jrosebr1/imutils/issues/82
import os
from werkzeug.utils import secure_filename
from agent_pi.utils import FACE_RECOG_ENABLED
from datetime import datetime
import simplejson
import numpy

if FACE_RECOG_ENABLED():
    import imutils
    from imutils import video, paths
    import cv2
    import face_recognition


class FaceFile:
    instance_dir_path = None

    video_dir_name = 'face_uploads'
    session_video_name = 'face_upload_path'

    capture_dir_name = 'datasets'

    classifier = "haarcascade_frontalface_default.xml"

    def __init__(self, dir_path):
        FaceFile.instance_dir_path = dir_path

    def get_video_file_path(self, filename):
        time_now = str(datetime.now())
        filename = secure_filename(time_now + filename)
        upload_dir = os.path.join(FaceFile.instance_dir_path,
                                  FaceFile.video_dir_name)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        return os.path.join(upload_dir, filename)

    def get_dataset_path(self, username):
        save_dir = os.path.join(FaceFile.instance_dir_path,
                                FaceFile.capture_dir_name,
                                secure_filename(username))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        return save_dir

    def get_classifier_file_path(self):
        if FACE_RECOG_ENABLED():
            f_path = os.path.join(FaceFile.instance_dir_path,
                                  FaceFile.classifier)
            if not os.path.exists(f_path):
                raise Exception(
                    "{} does not exist, but is needed by Facial Recognition".
                    format(f_path))
            return f_path
        return ""


class FaceEncoding:
    count_limit = 20
    DETECTION_METHOD = "hog"

    def __init__(self, videopath, dataset_path, classifier_path):
        self.videopath = videopath
        self.dataset_path = dataset_path
        self.classifier_path = classifier_path
        self.encodings = []

    def capture(self):
        # load video from file path
        cam = video.FileVideoStream(path=self.videopath).start()
        face_detector = cv2.CascadeClassifier(self.classifier_path)
        # capture frames from video
        img_counter = 0
        count = 0
        # TODO handle exception if video ends before face_count reached
        while img_counter <= FaceEncoding.count_limit:
            print("face_cap: {} - count: {}".format(img_counter, count))
            frame = cam.read()
            # skip every n frames to increse diversity of frames captured
            n = 2
            count += 1
            if count % n != 0:
                continue
            # rotate
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.3, 5)
            if (len(faces) == 0):
                # TODO let user select which faces are there's on website
                continue
            for (x, y, w, h) in faces:
                # cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                img_name = "{:04}.jpg".format(img_counter)
                img_path = os.path.join(self.dataset_path, img_name)
                frame_crop = frame[y:y + h, x:x + w]
                cv2.imwrite(img_path, frame_crop)
                img_counter += 1
        cam.stop()
        # success

    def encode(self):
        known_encodings = []
        # load images from user's dataset
        image_paths = paths.list_images(self.dataset_path)
        for (i, img_path) in enumerate(image_paths):
            image = cv2.imread(img_path)
            # convert from cv2 BGR ordering to dlib RGB ordering
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # get bounding box coordinates for each face in image
            boxes = face_recognition.face_locations(
                rgb, model=self.DETECTION_METHOD)
            # compute facial embeddings for each face
            encodings = face_recognition.face_encodings(rgb, boxes)
            known_encodings.extend(encodings)
        # dump face encodings into new pickle
        # assign new pickle to self.pickle
        self.encodings = known_encodings

    def create(self):
        """Capture face from video, create facial recog encoding for face.\n
        returns str of encodings array serialised into json string"""
        if FACE_RECOG_ENABLED():
            self.capture()
            self.encode()
        return self.to_json_str(self.encodings)

    # credit to https://stackoverflow.com/questions/26646362/numpy-array-is-not-
    # json-serializable
    @staticmethod
    def to_json_str(encodings):
        e_list = [a.tolist() for a in encodings]
        return simplejson.dumps(e_list)

    @staticmethod
    def from_json_str(json_str):
        encodings = simplejson.loads(json_str)
        return [numpy.array(a) for a in encodings]


class FacialRecognition(FaceEncoding):
    RESIZE = 240

    def __init__(self, encodings, callback, heartbeat, killed):
        self.user_encodings = encodings
        self.callback = callback
        self.heartbeat = heartbeat
        self.killed = killed

    def run(self):
        print("started facial recognition")
        vs = video.VideoStream(src=0).start()
        match_found = False
        while not match_found and self.heartbeat():
            frame = vs.read()

            # raspberry pi camera sensor is flipped 180
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            # convert from bgr to rgb then shrink to speed up detection
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb = imutils.resize(rgb, width=self.RESIZE)

            # get bounding box coordinates for each face in image
            boxes = face_recognition.face_locations(
                rgb, model=self.DETECTION_METHOD)
            # compute facial embeddings for each face
            encodings = face_recognition.face_encodings(rgb, boxes)

            # look for user in faces found in video frame
            for encoding in encodings:
                # find how many user face encodings match with the captured face
                matches = face_recognition.compare_faces(
                    self.user_encodings, encoding)
                perc = matches.count(True) / len(matches)
                print("{} % match for user found".format(perc * 100))
                # matches with atleast 25% of user encodings
                if perc >= 0.25:
                    # match found
                    print("sending unlock request")
                    match_found = True
                    break
        if match_found:
            # execute callback
            self.callback()
        self.killed()
