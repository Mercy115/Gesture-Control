import cv2
import mediapipe as mp

class HandDetection:
    def __init__(self,
                 mode=False,
                 maxHands=2,
                 min_detection_confidence=0.6,
                 min_tracking_confidence=0.6):

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=mode,
            max_num_hands=maxHands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.results = None

    def findHands(self, frame, draw=True):
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(
                        frame, handLms, self.mpHands.HAND_CONNECTIONS)
        return frame

    def findHandsPosition(self, frame):
        allHands = []

        if self.results and self.results.multi_hand_landmarks:
            for idx, handLms in enumerate(self.results.multi_hand_landmarks):
                lmList = []
                h, w, _ = frame.shape

                for id, lm in enumerate(handLms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])

                handType = self.results.multi_handedness[idx].classification[0].label
                allHands.append({"type": handType, "lmList": lmList})

        return allHands