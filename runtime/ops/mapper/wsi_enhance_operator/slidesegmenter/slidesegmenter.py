#    Copyright 2023 Ruben T Lucassen, UMC Utrecht, The Netherlands 
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""
Utility class for instance segmentation of tissue cross-sections 
and semantic segmentation of pen markings.
"""

import json
import os
from math import ceil, floor
from pathlib import Path
from typing import Optional, Union

import torch
try:
    import torch_npu  # noqa: F401
except Exception:
    torch_npu = None
import numpy as np
from huggingface_hub import hf_hub_download
from scipy.ndimage import gaussian_filter, maximum_filter

from ._model_utils import get_model
from . import model_files


class SlideSegmenter:
    """
    Class for segmenting tissue and pen markings in low resolution (1.25x)
    whole slide images. The class is responsible for:
    (1) preprocessing (i.e., padded to a valid size).
    (2) running model inference to get the segmentations.
    (3) post-processing (i.e., cropping to the original size and optionally 
        separating tissue cross-sections).
    """
    
    available_models = {
        '2023-08-13': {'model_filename': 'model_state_dict.pth', 
                       'settings_filename': 'settings.json'},
        '2024-01-10': {'model_filename': 'model_state_dict.pth', 
                       'settings_filename': 'settings.json'},
        '2025-10-18': {'model_filename': 'model_state_dict.pth', 
                       'settings_filename': 'settings.json'},
    }

    def __init__(
        self, 
        channels_last: bool = True,
        tissue_segmentation: bool = True,
        pen_marking_segmentation: bool = True,
        separate_cross_sections: bool = False,
        device: str = 'cpu', 
        model_folder: str = 'latest',
        alternative_directory: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Initialize SlideSegmenter instance.

        Args:
            channels_last:  Indicates whether the input is expected to have 
                the channels dimension after the spatial dimension. If False, 
                channels first is assumed.
            tissue_segmentation:  Indicates whether tissue is segmented.
            pen_marking_segmentation:  Indicates whether pen markings are segmented.
            separate_cross_sections:  Indicates whether the segmented tissue 
                cross-sections are separated. 
            device:  Specifies whether model inference is performed on the cpu or gpu.
            model_folder:  Name of model subfolder in model_files folder of the package
                ('latest' selects the latest model).
            alternative_directory:  Optionally define an alternative directory
                to store the downloaded model files (relevant in case an error
                is thrown when the path length to the cache folder exceeds 
                the maximum lengthon Windows systems).
        """
        # create instance attributes
        self.channels_last = channels_last
        self.tissue_segmentation = tissue_segmentation
        self.pen_marking_segmentation = pen_marking_segmentation
        self.separate_cross_sections = separate_cross_sections
        self.device = device
        self.model_folder = model_folder
        self.alternative_directory = alternative_directory
        self.model = None
        self.divisor = None
        self.hyperparameters = {}

        # check if the combination of the selected predictive tasks is valid
        if not (self.tissue_segmentation or self.pen_marking_segmentation):
            raise ValueError('Atleast one of the segmentation tasks must be selected.')
        if self.separate_cross_sections and not self.tissue_segmentation:
            raise ValueError('The separation of cross-sections can only be '
                             'performed if the tissue is segmented.')
        
        # convert path of alternative directory to Path instance
        if isinstance(self.alternative_directory, str):
            self.alternative_directory = Path(alternative_directory)

        # load and configure model
        self._load_model()
       
    def _load_model(
        self, 
        model: Optional[torch.nn.Module] = None,
        model_path: Optional[Union[Path, str]] = None, 
        settings_path: Optional[Union[Path, str]] = None,
    ) -> None:
        """
        Loads and configures model.
        
        Args:
            model:  Model class.
            model_path:  Path(s) to (model) state dictionary.
            settings_path:  Path to model settings JSON.
        """
        # check whether the combination of input arguments is valid
        if model is None and model_path is None and settings_path is None:
            # get the latest model folder
            if self.alternative_directory is not None:
                directory = self.alternative_directory
            else:
                directory = Path(model_files.__file__).parent
            # select the latest model
            if self.model_folder == 'latest':
                self.model_folder = sorted(list(self.available_models.keys()))[-1]
            # check if the model has to be downloaded
            downloaded = True
            if self.model_folder not in os.listdir(directory):
                downloaded = False
            else:
                for file in self.available_models[self.model_folder].values():
                    if file not in os.listdir(directory / self.model_folder):
                        downloaded = False
            # download the model if necessary
            if not downloaded:
                print((f'Start downloading the "{self.model_folder}" '
                        'model parameters and configuration settings'))
                self._download_model(self.model_folder, directory)
            # define the model path and settings path
            model_filename = self.available_models[self.model_folder]['model_filename']
            model_path = directory / self.model_folder / model_filename
            settings_filename = self.available_models[self.model_folder]['settings_filename']
            settings_path = directory / self.model_folder / settings_filename
        elif model_path is not None and settings_path is not None:
            pass
        else:
            raise ValueError('Invalid combination of inputs')

        # load model settings
        with open(settings_path, 'r') as f:
            settings = json.load(f)

        # select model
        if model is None:
            model = get_model(settings['model_name'])

        # store hyperparameters
        if 'hyperparameters' in settings:
            self.hyperparameters = settings['hyperparameters']
        
        # load the model parameters
        model_state_dict = torch.load(
            model_path, 
            map_location=torch.device(self.device),
        )
        # check if 'model_state_dict' is one of the keys
        if 'model_state_dict' in model_state_dict:
            model_state_dict = model_state_dict['model_state_dict']

        # remove keywords from settings
        keywords = [
            'attach_tissue_decoder', 
            'attach_pen_decoder', 
            'attach_distance_decoder',
        ]
        settings['model'] = {
            k:v for k, v in settings['model'].items() if k not in keywords
        }
        # configure model
        self.model = model(
            **settings['model'], 
            attach_tissue_decoder=self.tissue_segmentation,
            attach_pen_decoder=self.pen_marking_segmentation, 
            attach_distance_decoder=self.separate_cross_sections,
        )
        # remove excess layers from the model state dictionary (in case the pen 
        # or distance decoder are not used) and load it
        model_state_dict = {
            name: model_state_dict[name] for name, _ in self.model.named_parameters()
        }
        self.model.load_state_dict(model_state_dict)
        self.model.to(self.device)
        self.model.eval()

        # determine by what value the image height and width must be divisible
        self.divisor = np.prod(settings['model']['downsample_factors'])

    def _download_model(
        self,
        model_folder: str,
        local_dir: Union[str, Path],
    ) -> None:
        """
        Download the model parameters and configuration settings from the HuggingFace Hub.
        """
        etag_timeout = float(os.environ.get('SLIDESEGMENTER_HF_ETAG_TIMEOUT', '120'))
        filenames = list(self.available_models[model_folder].values())
        for filename in filenames:
            hf_hub_download(
                repo_id='rtlucassen/slidesegmenter',
                filename=filename,
                subfolder=model_folder,
                local_dir=local_dir,
                force_download=False,
                etag_timeout=etag_timeout,
                resume_download=True,
                local_dir_use_symlinks=False,
            )

    def change_device(self, device: str) -> None:
        """
        Change the device for model inference.

        Args:
            device:  Specifies whether model inference is performed on the cpu or gpu.
        """
        self.device = device
        self.model.to(self.device)

    def segment(
        self, 
        image: Union[np.ndarray, torch.Tensor],
        tissue_threshold: Optional[Union[float, str]] = 'default',
        pen_marking_threshold: Optional[Union[float, str]] = 'default',
        return_distance_maps: bool = False,
    ) -> Union[np.ndarray, tuple]:
        """
        Steps in segmentation pipeline:
        (1) Preprocess the image by adding padding to make the length of the 
            height and width valid.
        (2) Predict the tissue and pen marking segmentation for the image. 
        (3) Post-process the segmentation by cropping it to the original size.
        (4) Optionally divide the tissue segmentations into separate cross-sections.

        Args:
            image:  Whole slide image (at 1.25x) [0.0-1.0] as (height, width, channel)
                for channels last or (channel, height, width) for channels first.
            tissue_threshold:  Threshold value for binarizing the predicted 
                tissue segmentation ('default': the threshold value based on the 
                validation set is used, None: the segmentation is not thresholded).
            pen_marking_threshold:  Threshold value for binarizing the predicted 
                pen marking segmentation ('default': the threshold value based on the 
                validation set is used, None: the segmentation is not thresholded).
            return_distance_maps:  Indicates whether the distance maps are returned.
        
        Returns:
            prediction:  Dictionary with the following key-value pairs:
                tissue_segmentation:  Segmentation for whole slide image [0.0-1.0] 
                    (at 1.25x) as (height, width, channel) for channels last or 
                    (channel, height, width) for channels first.
                pen_marking_segmentation:  Segmentation for whole slide image [0.0-1.0] 
                    (at 1.25x) as (height, width, channel) for channels last or 
                    (channel, height, width) for channels first.
                distance_maps:  Image with predicted horizontal and vertical distance 
                    with respect to centroid as (height, width, channel) for channels last 
                    or (channel, height, width) for channels first.
        """
        # check image object type, convert to numpy array if necessary
        if isinstance(image, torch.Tensor):
            image = image.numpy()
        elif not isinstance(image, np.ndarray):
            raise TypeError('Invalid type of input argument for image.')
        
        # check if the image intensities are in the range of 0.0-1.0
        if np.min(image) < 0 or np.max(image) > 1:
            raise ValueError('Invalid image intensities (must be in the range 0.0-1.0)')

        # check if the image input argument is valid
        if len(image.shape) != 3:
            raise ValueError('Invalid number of dimensions for input argument.')
        
        # check if the tissue threshold for binarization is specified in case
        # the cross-sections should be separated.
        if self.separate_cross_sections and tissue_threshold is None:
            raise ValueError('The tissue threshold must be specified if the '
                             'cross-sections should be separated.')
        # check if distance maps can be returned
        if return_distance_maps and not self.separate_cross_sections:
            raise ValueError('Distance maps can only be returned when '
                             'cross-sections should be separated.')

        # change the channels dimension to be the first dimension if necessary
        if self.channels_last:
            image = image.transpose((2, 0, 1))

        # determine the height and width of the input image       
        channels, height, width = image.shape
        
        # check if the number of channels is valid:
        if channels != 3:
            raise ValueError('Invalid number of channels for input argument.') 
        
        # determine the total amount of padding necessary
        width_pad = (ceil(width / self.divisor)*self.divisor)-width
        height_pad = (ceil(height / self.divisor)*self.divisor)-height
        
        # determine the amount of padding on each side of the image
        padding = [
            (0,0),
            (floor(height_pad/2), ceil(height_pad/2)), 
            (floor(width_pad/2), ceil(width_pad/2)), 
        ]
        # add padding to image
        pad_kwargs = {
            'array': image,
            'pad_width': padding,
            'mode': self.hyperparameters['padding_mode'],
        }
        if self.hyperparameters['padding_mode'] == 'constant':
            pad_kwargs['constant_values'] = self.hyperparameters['padding_value']
        image = np.pad(**pad_kwargs)
        # convert the image to a torch Tensor
        image = torch.from_numpy(image).float()
        # get the model prediction
        with torch.no_grad():
            prediction = self.model(image[None, ...].to(self.device))

        # independent of the device, bring the prediction to the cpu, 
        # remove the batch dimension, and crop the padding
        top = padding[1][0]
        left = padding[2][0]
        prediction = {k:v.to('cpu')[0, :, top:top+height, left:left+width] 
                      for k, v in prediction.items()}
        
        # binarize the segmentations based on the threshold value
        if tissue_threshold == 'default':
            tissue_threshold = self.hyperparameters['tissue_threshold']
        if self.tissue_segmentation and tissue_threshold is not None: 
            prediction['tissue'] = torch.sigmoid(prediction['tissue'])
            prediction['tissue'] = torch.where(prediction['tissue'] >= tissue_threshold, 1, 0)

        if pen_marking_threshold == 'default':
            pen_marking_threshold = self.hyperparameters['pen_marking_threshold']
        if self.pen_marking_segmentation and pen_marking_threshold is not None:
            prediction['pen'] = torch.sigmoid(prediction['pen'])
            prediction['pen'] = torch.where(prediction['pen'] >= pen_marking_threshold, 1, 0)

        # convert to numpy arrays
        prediction = {k: v.numpy() for k, v in prediction.items()}

        # separate the cross-sections based on the predicted distance maps
        if self.separate_cross_sections:
            if tissue_threshold is None:
                raise ValueError('Unable to seperate cross-sections without '
                                 'binarizing the tissue segmentation.')
            else:
                separated_cross_sections, _ = self._separate_cross_sections(
                    prediction['tissue'][0, ...], 
                    prediction['distance'][0, ...], 
                    prediction['distance'][1, ...],
                )
                prediction['tissue'] = separated_cross_sections.transpose((2, 0, 1))

        # remove distance maps from prediction if necessary
        if not return_distance_maps and 'distance' in prediction:
            del prediction['distance']

        # change the last channel to the first channel
        if self.channels_last:
            prediction = {k: v.transpose((1, 2, 0)) for k, v in prediction.items()}

        return prediction

    def _separate_cross_sections(
        self,
        segmentation: np.ndarray, 
        horizontal_distance: np.ndarray,
        vertical_distance: np.ndarray, 
    ) -> tuple[np.ndarray, list[tuple[float, float]]]:
        """
        Separate cross-sections in the predicted segmentation map,
        based on the predicted horizontal and vertical distance maps.

        Args:
            segmentation:  Segmentation for whole slide image [uint8] (at 1.25x) 
                as (height, width).
            horizontal_distance:  Image with predicted horizontal distance [float32]
                with respect to centroid as (height, width).
            vertical_distance:  Image with predicted vertical distance [float32]
                with respect to centroid as (height, width).
        
        Returns:
            nearest_centroid_map:  Segmentation for whole slide image [uint8] 
                (at 1.25x) as (height, width, channel).
            centroid_coords:  Coordinates of extracted centroids.
        """
        # initialize a variable with the image shape
        image_shape = segmentation.shape

        # create a vector with the binarized segmentation result for masking    
        mask = segmentation.astype(bool).reshape((-1,))

        # create horizontal and vertical grid
        vertical_map, horizontal_map = np.meshgrid(
            np.linspace(0, image_shape[0]-1, image_shape[0]),
            np.linspace(0, image_shape[1]-1, image_shape[1]),
            indexing="ij",
        )
        # create the centroid maps
        distance_factor = self.hyperparameters['distance_factor']
        x_centroid_map = (horizontal_map - (horizontal_distance*distance_factor))
        y_centroid_map = (vertical_map - (vertical_distance*distance_factor))

        # flatten the centroid map and select only the tissue regions
        x_centroid_flat = x_centroid_map.reshape((-1,))[mask]
        y_centroid_flat = y_centroid_map.reshape((-1,))[mask]

        # get hyperparameter values from dictionary
        sigma = self.hyperparameters['sigma']
        percentile = self.hyperparameters['percentile']
        filter_size = self.hyperparameters['filter_size']
        pixels_per_bin = self.hyperparameters['pixels_per_bin']

        # determine the number of bins for the histogram
        bins = [image_shape[0]//pixels_per_bin, image_shape[1]//pixels_per_bin]
        x_centroid_flat = (x_centroid_flat/pixels_per_bin).astype(int)
        y_centroid_flat = (y_centroid_flat/pixels_per_bin).astype(int)
        # add the top left and bottom right point of the histogram
        # this prevents the histogram from removing empty rows and columns,
        # which would not change the output but can prevent confusion when
        # inspecting the histogram visually.
        if True:
            x_centroid_flat = np.concatenate([x_centroid_flat, np.array([0, bins[1]])])
            y_centroid_flat = np.concatenate([y_centroid_flat, np.array([0, bins[1]])])

        # create 2D histogram
        histogram, y_edges, x_edges = np.histogram2d(
            y_centroid_flat, 
            x_centroid_flat, 
            bins=bins,
            range=[[0, bins[0]-1], 
                   [0, bins[1]-1]],
        )
        # apply Gaussian filtering to decrease local peaks
        if sigma is not None:
            histogram = gaussian_filter(histogram, sigma=sigma)
        histogram_mask = np.where(histogram > np.percentile(histogram, percentile), 1, 0)
        max_filtered_histogram = maximum_filter(histogram, filter_size)
        maxima = np.where(histogram == max_filtered_histogram, 1, 0)*histogram_mask

        # convert the edges from ranges to the center value
        x_bins = np.array([sum(x_edges[i:i+2])/2 for i in range(bins[1])])
        y_bins = np.array([sum(y_edges[i:i+2])/2 for i in range(bins[0])])
        
        # get the centroid coordinates
        indices = np.argwhere(maxima)
        centroids = np.concatenate(
            [x_bins[indices[:, 1], None], y_bins[indices[:, 0], None]], 
            axis=1,
        )
        centroid_coords = list(zip((centroids[:, 0]), centroids[:, 1]))

        # combine the x and y centroid maps into one array
        predicted_centroids = [
            x_centroid_map[..., None, None], 
            y_centroid_map[..., None, None],
        ]
        predicted_centroid_array = np.concatenate(predicted_centroids, axis=-1)
        
        # flatten the array and select only the tissue regions
        predicted_centroid_flat = predicted_centroid_array.reshape((-1,1,2))[mask, ...]

        # for each pixel, determine the distance between the predicted centroid
        # and all extracted centroids. Broadcasting is used for efficiency:
        # - predicted_centroid_array: [x*y, 1, 2] -> [x*y, N_centroids, 2]
        # - centroid_array: [1, N_centroids, 2] ->  [x*y, N_centroids, 2]
        distance_flat = np.sum((predicted_centroid_flat-centroids[None, ...])**2, axis=-1)
        
        # determine for each pixel what the nearest centroid is
        nearest_centroid_flat = np.argmin(distance_flat, axis=-1)+1

        # get the x and y coordinates for the pixels in the segmentation for indexing
        horizontal_flat = horizontal_map.reshape((-1,)).astype(np.uint16)[mask]
        vertical_flat = vertical_map.reshape((-1,)).astype(np.uint16)[mask]
        
        # convert the nearest centroid vector to the image shape 
        nearest_centroid_map = np.zeros(image_shape, dtype=np.uint8)
        nearest_centroid_map[vertical_flat, horizontal_flat] = nearest_centroid_flat

        # assign each cross-section to a separate channel
        index_map = np.tile(
            np.arange(1, len(centroid_coords)+1)[None, None, ...], 
            (*image_shape, 1),
        )
        nearest_centroid_map = np.where(nearest_centroid_map[..., None] == index_map, 1, 0)

        return nearest_centroid_map, centroid_coords
