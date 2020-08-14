from imutils.video import VideoStream
from pyzbar import pyzbar
# import imutils
import time

import cv2


class QRCodeRecognition:

    # 5 minutes in seconds
    TIME_LIMIT_SEC = 60 * 5

    def __init__(self, matchfound_callback):
        self.matchfound_callback = matchfound_callback
        self.end_time = time.time() + self.TIME_LIMIT_SEC

    def keep_going(self):
        return time.time() < self.end_time

    def run(self):
        vs = VideoStream(src=0).start()
        print("QRCode starting...")
        report_resolved = False
        while not report_resolved and self.keep_going():
            found = set()
            while not found and self.keep_going():
                print("{} - 0 codes found".format(time.asctime()))
                frame = vs.read()

                # Write the frame into the file 'output.avi'
                frame = cv2.rotate(frame, cv2.ROTATE_180)
                cv2.imshow('my webcam', frame)
                if cv2.waitKey(1) == 27:
                    break  # esc to quit

                # frame = imutils.resize(frame, width=400)

                # FOR TESTING WITH PNG FILES
                # img_path = 'code.png'

                # frame = cv2.imread(img_path)

                barcodes = pyzbar.decode(frame)

                for barcode in barcodes:
                    barcodeData = barcode.data.decode("utf-8")
                    barcodeType = barcode.type
                    if barcodeData not in found:
                        print("[FOUND] Type: {}, Data: {}".format(
                            barcodeType, barcodeData))
                        found.add(barcodeData)

                time.sleep(1)
            for barcode in found:
                result = self.matchfound_callback(barcode)
                if result and result.status == "200":
                    report_resolved = True
                else:
                    print("qr code invalid")
