# Face Recognition on Pi
Train a machine learning model for real-time face recognition on the Raspberry Pi 4. As soon as the model recognizes an unknown person, it sends a notification including date, time and a picture of the person via Cisco Webex Teams. 

<p align="center">
  <img src="alert_bot_webex.png" width="350" title="Webex Teams Alert Notification">
</p>

No Raspberry Pi cam required, it worked for me with a Logitech webcam.

## Usage

For training the model, you will need a folder "dataset" containing at least two folders with images of faces. 
One folder should be renamed to your first name, the second folder should be renamed to "unknown".
The folders should contain at least 5 unknown images, and 10 images of you.

Change ```YOUR_NAME``` in line 91 in the file pi_face_recognition.py to your name, the same name as the subfolder with your images in the dataset folder.

Change ```TEAMS-TOKEN``` in line 5 in the file alert_teams.py to the token of your Webex Teams bot created [here](https://developer.webex.com/my-apps/new/bot). 

Change ```EMAIL``` in line 9 in the file alert_teams.py to the email adress to which the Webex Teams alert notification is sent to.

Train model with with 

```encode_faces.py --dataset dataset --encodings encodings.pickle --detection-method hog```

Run the model with real time face recognition and alerting with

```python3 pi_face_recognition.py --cascade haarcascade_frontalface_default.xml --encodings encodings.pickle```

## Sources

[Face Recognition on the Raspberry Pi](https://www.pyimagesearch.com/2018/06/25/raspberry-pi-face-recognition/) by Adrian Rosebrock 

[Cisco Webex for Developers](https://developer.webex.com/docs/bots)
