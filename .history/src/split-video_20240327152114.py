from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg
import os

def split_video_into_scenes(video_path, output_path, threshold=27.0):
    # Open our video, create a scene manager, and add a detector.
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video, show_progress=True)
    scene_list = scene_manager.get_scene_list()
    ret = split_video_ffmpeg(video_path, scene_list, output_dir=output_path, show_progress=True)
    return ret

def split_video(folder_path, output_path):
    file_list = os.listdir(folder_path)
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        print(file_path, 'start......')
        try:
            ret = split_video_into_scenes(file_path, output_path)
            print(file_path, 'end......，ret %s' % ret)
        except Exception as e:
            print(file_path, 'end......，error %s' % e)


if __name__ == "__main__":
    folder_path = "/Users/flyeyas/Downloads/治愈书籍带货/动漫素材/动漫"
    output_path = "/Users/flyeyas/Downloads/治愈书籍带货/动漫素材镜头分割"
    split_video(folder_path, output_path)