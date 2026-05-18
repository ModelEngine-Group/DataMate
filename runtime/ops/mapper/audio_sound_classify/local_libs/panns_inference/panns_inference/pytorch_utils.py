"""This pytorch_utils.py contains functions from:
https://github.com/qiuqiangkong/audioset_tagging_cnn/blob/master/pytorch/pytorch_utils.py
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


def move_data_to_device(x, device):
    if 'float' in str(x.dtype):
        x = torch.Tensor(x)
    elif 'int' in str(x.dtype):
        x = torch.LongTensor(x)
    else:
        return x

    return x.to(device)


class Interpolator(nn.Module):
    def __init__(self, ratio, interpolate_mode='nearest'):
        """Interpolate the sound event detection result along the time axis.

        Args:
            ratio: int
            interpolate_mode: str

        """
        super(Interpolator, self).__init__()

        if interpolate_mode == 'nearest':
            self.interpolator = NearestInterpolator(ratio)

    def forward(self, x):
        """Interpolate the sound event detection result along the time axis.
        
        Args:
            x: (batch_size, time_steps, classes_num)

        Returns:
            (batch_size, new_time_steps, classes_num)
        """
        return self.interpolator(x)


class NearestInterpolator(nn.Module):
    def __init__(self, ratio):
        """Nearest interpolate the sound event detection result along the time axis.

        Args:
            ratio: int
        """
        super(NearestInterpolator, self).__init__()

        self.ratio = ratio

    def forward(self, x):
        """Interpolate the sound event detection result along the time axis.
        
        Args:
            x: (batch_size, time_steps, classes_num)

        Returns:
            upsampled: (batch_size, new_time_steps, classes_num)
        """
        (batch_size, time_steps, classes_num) = x.shape
        upsampled = x[:, :, None, :].repeat(1, 1, self.ratio, 1)
        upsampled = upsampled.reshape(batch_size, time_steps * self.ratio, classes_num)
        return upsampled


def pad_framewise_output(framewise_output, frames_num):
    """Pad framewise_output to the same length as input frames.
    Args:
      framewise_output: (batch_size, frames_num, classes_num)
      frames_num: int, number of frames to pad
    Outputs:
      output: (batch_size, frames_num, classes_num)
    """
    pad = framewise_output[:, -1 :, :].repeat(1, frames_num - framewise_output.shape[1], 1)
    """tensor for padding"""

    output = torch.cat((framewise_output, pad), dim=1)
    """(batch_size, frames_num, classes_num)"""

    return output


def do_mixup(x, mixup_lambda):
    out = x[0::2].transpose(0, -1) * mixup_lambda[0::2] + \
        x[1::2].transpose(0, -1) * mixup_lambda[1::2]
    return out.transpose(0, -1)