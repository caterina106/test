from ultralytics import YOLO
import cv2

model = YOLO("./yolov8n.pt")

cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

while True:
    ret, frame = cap.read()
    if not ret:
        print("No frame")
        break

    results = model(frame, verbose=False, imgsz=320)

    person = False
    phone = False

  
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            name = model.names[cls_id]

            if name == "person":
                person = True
            if name == "cell phone":
                phone = True

   
    annotated_frame = results[0].plot()


    if person and phone:
        text = "someone is playing phone"
        color = (0, 0, 0)  
    elif person:
        text = "Just a normal people"
        color = (0, 0, 0)  # green
    else:
        text = "Find..."
        color = (0, 0, 0)

    cv2.putText(
        annotated_frame,
        text,
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        2
    )

    cv2.imshow("Freenove AI Vision", annotated_frame)

  
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()