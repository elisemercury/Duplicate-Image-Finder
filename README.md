# Duplicate Image Finder (DIF)
Tired of going through all images in a folder and comparing them manually to find if they are duplicates?
The Duplicate Image Finder (DIF) Python script automates this task for you!

Select which file folder the DIF should search through, and it will will compare all images in that folder whether these are duplicates, or not. 
It outputs all images it classifies as duplicates including the filename of the image having the lowest resolution of both, so you know which of the two images is safe to be deleted.

<p align="center">
  <img src="example_output.PNG" width="350" title="Example Output: Duplicate Image Finder">
</p>

## Usage

```ruby
require 'redcarpet'
markdown = Redcarpet.new("Hello World!")
puts markdown.to_html
```

Use 
```python
compare_images("C:/Path/to/Folder/")
``` 
to make DIF search for duplicate images in the folder.

## Additionnal Parameters

```compare_images(directory, show_imgs=True, similarity=)```

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
