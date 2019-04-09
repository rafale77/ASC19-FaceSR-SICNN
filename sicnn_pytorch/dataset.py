import torch.utils.data as data
import cv2, sys
import numpy as np
import torch

from os import listdir
from os.path import join
from PIL import Image

def is_image_file(filename):
    return any(filename.endswith(extension) for extension in [".png", ".jpg", ".jpeg"])

def load_img(filepath):
    return cv2.imdecode(np.fromfile(filepath, np.uint8), 1)

class TrainDatasetFromFolder(data.Dataset):
    def __init__(self, HR_image_dir, LR_image_dir):
        super(TrainDatasetFromFolder, self).__init__()
        self.HR_image_dir = HR_image_dir
        self.LR_image_dir = LR_image_dir
        self.image_filenames = [x for x in listdir(LR_image_dir) if is_image_file(x)]

    def __getitem__(self, index):
        input = load_img(join(self.LR_image_dir, self.image_filenames[index]))
        target = load_img(join(self.HR_image_dir, self.image_filenames[index]))
        input = input.transpose(2, 0, 1).reshape((3, 28, 24))
        input = (input - 127.5) / 128.0
        target = target.transpose(2, 0, 1).reshape((3, 112, 96))
        target = (target - 127.5) / 128.0
        input = torch.from_numpy(input).float()
        target = torch.from_numpy(target).float()
        return input, target

    def __len__(self):
        return len(self.image_filenames)

class TestDatasetFromFolder(data.Dataset):
    def __init__(self, HR_image_dir, LR_image_dir):
        super(TestDatasetFromFolder, self).__init__()
        self.HR_image_dir = HR_image_dir
        self.LR_image_dir = LR_image_dir
        self.image_filenames = [x for x in listdir(LR_image_dir) if is_image_file(x)]

    def __getitem__(self, index):
        input = load_img(join(self.LR_image_dir, self.image_filenames[index]))
        target = load_img(join(self.HR_image_dir, self.image_filenames[index]))
        input = input.transpose(2, 0, 1).reshape((3, 28, 24))
        input = (input - 127.5) / 128.0
        target = target.transpose(2, 0, 1).reshape((3, 112, 96))
        target = (target - 127.5) / 128.0
        input = torch.from_numpy(input).float()
        target = torch.from_numpy(target).float()
        return input, target, self.image_filenames[index]

    def __len__(self):
        return len(self.image_filenames)
