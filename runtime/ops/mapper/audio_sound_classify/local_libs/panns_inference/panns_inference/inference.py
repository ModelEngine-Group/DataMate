import os
import numpy as np
import argparse
import librosa
import torch
from pathlib import Path

from .pytorch_utils import move_data_to_device
from .models import Cnn14, Cnn14_DecisionLevelMax
from .config import labels, classes_num


def _torch_load_checkpoint(path, map_location):
    try:
        return torch.load(path, map_location=map_location, weights_only=False)
    except TypeError:
        return torch.load(path, map_location=map_location)


def _resolve_inference_device(device):
    """Resolve device string for inference: cpu | cuda | npu | auto."""
    d = (device or "cpu").lower()
    if d == "auto":
        if torch.cuda.is_available():
            return "cuda"
        try:
            import torch_npu  # noqa: F401

            if hasattr(torch, "npu") and torch.npu.is_available():
                return "npu"
        except Exception:
            pass
        return "cpu"
    if d == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if d == "npu":
        try:
            import torch_npu  # noqa: F401

            if hasattr(torch, "npu") and torch.npu.is_available():
                return "npu"
        except Exception:
            pass
        return "cpu"
    return "cpu"


def create_folder(fd):
    if not os.path.exists(fd):
        os.makedirs(fd)
        
        
def get_filename(path):
    path = os.path.realpath(path)
    na_ext = path.split('/')[-1]
    na = os.path.splitext(na_ext)[0]
    return na


class AudioTagging(object):
    def __init__(self, model=None, checkpoint_path=None, device='cuda'):
        """Audio tagging inference wrapper.
        """
        if not checkpoint_path:
            checkpoint_path='{}/panns_data/Cnn14_mAP=0.431.pth'.format(str(Path.home()))
        print('Checkpoint path: {}'.format(checkpoint_path))
        
        if not os.path.exists(checkpoint_path) or os.path.getsize(checkpoint_path) < 3e8:
            create_folder(os.path.dirname(checkpoint_path))
            zenodo_path = 'https://zenodo.org/record/3987831/files/Cnn14_mAP%3D0.431.pth?download=1'
            os.system('wget -O "{}" "{}"'.format(checkpoint_path, zenodo_path))

        self.device = _resolve_inference_device(device)
        
        self.labels = labels
        self.classes_num = classes_num

        # Model
        if model is None:
            self.model = Cnn14(sample_rate=32000, window_size=1024, 
                hop_size=320, mel_bins=64, fmin=50, fmax=14000, 
                classes_num=self.classes_num)
        else:
            self.model = model

        checkpoint = _torch_load_checkpoint(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model'])

        # Parallel
        if self.device == 'cuda':
            self.model.to(self.device)
            print('GPU number: {}'.format(torch.cuda.device_count()))
            self.model = torch.nn.DataParallel(self.model)
        elif self.device == 'npu':
            self.model.to(self.device)
            print('Using NPU.')
        else:
            print('Using CPU.')

    def inference(self, audio):
        audio = move_data_to_device(audio, self.device)

        with torch.no_grad():
            self.model.eval()
            output_dict = self.model(audio, None)

        clipwise_output = output_dict['clipwise_output'].data.cpu().numpy()
        embedding = output_dict['embedding'].data.cpu().numpy()

        return clipwise_output, embedding


class SoundEventDetection(object):
    def __init__(self, model=None, checkpoint_path=None, device='cuda', interpolate_mode='nearest'):
        """Sound event detection inference wrapper.

        Args:
            model: None | nn.Module
            checkpoint_path: str
            device: str, 'cpu' | 'cuda'
            interpolate_mode, 'nearest' |'linear'
        """
        if not checkpoint_path:
            checkpoint_path='{}/panns_data/Cnn14_DecisionLevelMax.pth'.format(str(Path.home()))
        print('Checkpoint path: {}'.format(checkpoint_path))

        if not os.path.exists(checkpoint_path) or os.path.getsize(checkpoint_path) < 3e8:
            create_folder(os.path.dirname(checkpoint_path))
            os.system('wget -O "{}" https://zenodo.org/record/3987831/files/Cnn14_DecisionLevelMax_mAP%3D0.385.pth?download=1'.format(checkpoint_path))

        self.device = _resolve_inference_device(device)
        
        self.labels = labels
        self.classes_num = classes_num

        # Model
        if model is None:
            self.model = Cnn14_DecisionLevelMax(sample_rate=32000, window_size=1024, 
                hop_size=320, mel_bins=64, fmin=50, fmax=14000, 
                classes_num=self.classes_num, interpolate_mode=interpolate_mode)
        else:
            self.model = model
        
        checkpoint = _torch_load_checkpoint(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model'])

        # Parallel
        if self.device == 'cuda':
            self.model.to(self.device)
            print('GPU number: {}'.format(torch.cuda.device_count()))
            self.model = torch.nn.DataParallel(self.model)
        elif self.device == 'npu':
            self.model.to(self.device)
            print('Using NPU.')
        else:
            print('Using CPU.')

    def inference(self, audio):
        audio = move_data_to_device(audio, self.device)

        with torch.no_grad():
            self.model.eval()
            output_dict = self.model(
                input=audio, 
                mixup_lambda=None
            )

        framewise_output = output_dict['framewise_output'].data.cpu().numpy()

        return framewise_output
