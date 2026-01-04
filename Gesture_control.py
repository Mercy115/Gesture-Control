
import cv2
import numpy as np
import time
import math
import Hand_detection_module as hdm
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc

# ---------- AUDIO ----------
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
vMin, vMax = volume.GetVolumeRange()[0:2]


# ---------- CAMERA ----------
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

detector = hdm.HandDetection(maxHands=2)

# ---------- GESTURE LOCK VARIABLES ----------
gestureLocked = True
unlockStartTime = 0
lockStartTime = 0
holdTime = 1.5  # seconds

pTime = 0

while True:
    success, frame = cap.read()
    if not success:
        continue

    frame = detector.findHands(frame)
    hands = detector.findHandsPosition(frame)

    currentTime = time.time()

    for hand in hands:
        lmList = hand["lmList"]
        handType = hand["type"]  # Left / Right

        if len(lmList) < 9:
            continue

        # Thumb & Index
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        cx, cy = (x1 + x2)//2, (y1 + y2)//2

        cv2.circle(frame, (x1, y1), 10, (255,0,255), -1)
        cv2.circle(frame, (x2, y2), 10, (255,0,255), -1)
        cv2.line(frame, (x1,y1), (x2,y2), (255,0,255), 3)
        cv2.circle(frame, (cx, cy), 8, (255,0,255), -1)

        dist = math.hypot(x2-x1, y2-y1)

        # ---------- UNLOCK GESTURE (FIST) ----------
        if dist < 35:
            if unlockStartTime == 0:
                unlockStartTime = currentTime
            elif (currentTime - unlockStartTime) >= holdTime:
                gestureLocked = False
                unlockStartTime = 0
                lockStartTime = 0
        else:
            unlockStartTime = 0

        # ---------- LOCK GESTURE (WIDE PINCH) ----------
        if dist > 180:
            if lockStartTime == 0:
                lockStartTime = currentTime
            elif (currentTime - lockStartTime) >= holdTime:
                gestureLocked = True
                lockStartTime = 0
                unlockStartTime = 0
        else:
            lockStartTime = 0

        # ---------- CONTROLS (ONLY WHEN UNLOCKED) ----------
        if not gestureLocked:

            # RIGHT HAND → VOLUME
            if handType == "Right":
                volLevel = np.interp(dist, [40, 250], [vMin, vMax])
                volPercent = int(np.interp(dist, [40, 250], [0, 100]))
                volume.SetMasterVolumeLevel(volLevel, None)

                cv2.putText(frame, f"RIGHT HAND : VOLUME {volPercent}%",
                            (10, 80), cv2.FONT_HERSHEY_COMPLEX,
                            0.8, (0,255,0), 2)

            # LEFT HAND → BRIGHTNESS
            if handType == "Left":
                brightness = int(np.interp(dist, [40, 250], [0, 100]))
                brightness = max(0, min(100, brightness))
                sbc.set_brightness(brightness)

                cv2.putText(frame, f"LEFT HAND : BRIGHTNESS {brightness}%",
                            (10, 120), cv2.FONT_HERSHEY_COMPLEX,
                            0.8, (255,255,0), 2)

    # ---------- LOCK STATUS ----------
    statusText = "LOCKED 🔒" if gestureLocked else "UNLOCKED 🔓"
    statusColor = (0,0,255) if gestureLocked else (0,255,0)
    cv2.putText(frame, statusText, (420, 40),
                cv2.FONT_HERSHEY_COMPLEX, 1, statusColor, 2)

    # ---------- FPS ----------
    cTime = time.time()
    fps = 1/(cTime-pTime)
    pTime = cTime
    cv2.putText(frame, f"FPS : {int(fps)}",
                (10,40), cv2.FONT_HERSHEY_COMPLEX,
                1, (0,255,0), 2)

    cv2.imshow("Hand-Based Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('x'):
        break

cap.release()
cv2.destroyAllWindows()