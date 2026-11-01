Essential for running: 

train.ipynb - code to train the model (~80 minutes in colab and 5070GPU, chance of thermal throttling if done locally -> trained model already in /runs)
check_mAP.ipynb - gives an overview of the model performance
model_deployment.ipynb - code to process the video of the referees and the ball, extra adjustments to remove players and make the patterns connect more
runs/detect/soccer_training/ball_detector_640/weights/best.pt - the trained model
videos/ - contains the video files

Extra:

archive.zip - contains the training, testing, and validation data
check_dataset.ipynb - counts the images and cross checks labels for mistakes
check_annotations.ipynb - counts the invalid annotations in the labels
convert_annotations.ipynb - fixes the invalid annotations
check_GPU.ipynb - checks if the local GPU has CUDA available
limit_GPU.ipynb - extra file pasted again in train.ipynb, if used in a process it limits the GPU usage to 85%
