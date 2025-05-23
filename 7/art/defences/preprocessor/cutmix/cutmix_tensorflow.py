# MIT License
#
# Copyright (C) The Adversarial Robustness Toolbox (ART) Authors 2022
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
This module implements the CutMix data augmentation defence in TensorFlow.

| Paper link: https://arxiv.org/abs/1905.04899

| Please keep in mind the limitations of defences. For more information on the limitations of this defence,
    see https://arxiv.org/abs/1803.09868 . For details on how to evaluate classifier security in general, see
    https://arxiv.org/abs/1902.06705
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
from typing import Optional, Tuple, TYPE_CHECKING

import numpy as np
from tqdm.auto import tqdm

from art.defences.preprocessor.preprocessor import PreprocessorTensorFlowV2

if TYPE_CHECKING:
    # pylint: disable=C0412
    import tensorflow as tf

logger = logging.getLogger(__name__)


class CutMixTensorFlowV2(PreprocessorTensorFlowV2):
    """
    Implement the CutMix data augmentation defence approach in TensorFlow v2.

    | Paper link: https://arxiv.org/abs/1905.04899

    | Please keep in mind the limitations of defences. For more information on the limitations of this defence,
        see https://arxiv.org/abs/1803.09868 . For details on how to evaluate classifier security in general, see
        https://arxiv.org/abs/1902.06705
    """

    params = ["num_classes", "alpha", "probability", "channels_first", "verbose"]

    def __init__(
        self,
        num_classes: int,
        alpha: float = 1.0,
        probability: float = 0.5,
        channels_first: bool = False,
        apply_fit: bool = True,
        apply_predict: bool = False,
        verbose: bool = False,
    ) -> None:
        """
        Create an instance of a CutMix data augmentation object.

        :param num_classes: The number of classes used for one-hot encoding.
        :param alpha: The hyperparameter for sampling the combination ratio.
        :param probability: The probability of applying CutMix per sample.
        :param channels_first: Set channels first or last.
        :param apply_fit: True if applied during fitting/training.
        :param apply_predict: True if applied during predicting.
        :param verbose: Show progress bars.
        """
        super().__init__(is_fitted=True, apply_fit=apply_fit, apply_predict=apply_predict)
        self.num_classes = num_classes
        self.alpha = alpha
        self.probability = probability
        self.channels_first = channels_first
        self.verbose = verbose
        self._check_params()

    def forward(self, x: "tf.Tensor", y: Optional["tf.Tensor"] = None) -> Tuple["tf.Tensor", Optional["tf.Tensor"]]:
        """
        Apply CutMix data augmentation to sample `x`.

        :param x: Sample to augment with shape of `NCHW`, `NHWC`, `NCFHW` or `NFHWC`.
        :param y: Labels of `x` either one-hot or multi-hot encoded of shape `(nb_samples, nb_classes)`
                  or class indices of shape `(nb_samples,)`.
        :return: Data augmented sample. The returned labels will be probability vectors of shape
                 `(nb_samples, nb_classes)`.
        """
        import tensorflow as tf

        if y is None:
            raise ValueError("Labels `y` cannot be None.")

        # convert labels to one-hot encoding
        if len(y.shape) == 2:
            y_one_hot = y
        elif len(y.shape) == 1:
            y_one_hot = tf.one_hot(y, self.num_classes, on_value=1.0, off_value=0.0)
        else:
            raise ValueError(
                "Shape of labels not recognised. "
                "Please provide labels in shape (nb_samples,) or (nb_samples, nb_classes)"
            )

        x_ndim = len(x.shape)

        # NCHW/NHWC/NCFHW --> NFHWC
        if x_ndim == 4:
            if self.channels_first:
                # NCHW --> NHWC --> NFHWC
                x_nhwc = tf.transpose(x, (0, 2, 3, 1))
                x_nfhwc = tf.expand_dims(x_nhwc, axis=1)
            else:
                # NHWC --> NFHWC
                x_nfhwc = tf.expand_dims(x, axis=1)
        elif x_ndim == 5:
            if self.channels_first:
                # NCFHW --> NFHWC
                x_nfhwc = tf.transpose(x, (0, 2, 3, 4, 1))
            else:
                # NFHWC
                x_nfhwc = x
        else:
            raise ValueError("Unrecognized input dimension. CutMix can only be applied to image and video data.")

        n, _, height, width, _ = x_nfhwc.shape
        x_aug = tf.Variable(x_nfhwc, trainable=False)
        y_aug = tf.Variable(y_one_hot, trainable=False)

        # sample the combination ratio from the Beta distribution
        lmb = np.random.beta(self.alpha, self.alpha)
        cut_ratio = np.sqrt(1.0 - lmb)
        cut_height = int(height * cut_ratio)
        cut_width = int(width * cut_ratio)

        # randomly choose indices for samples to mix
        indices = tf.random.shuffle(tf.range(n))

        # generate a random bounding box per image
        for idx1, idx2 in enumerate(tqdm(indices, desc="CutMix", disable=not self.verbose)):
            prob = np.random.rand()
            if prob < self.probability:
                # uniform sampling
                center_y = tf.random.uniform(shape=[], maxval=height, dtype=tf.int32)  # pylint: disable=E1123
                center_x = tf.random.uniform(shape=[], maxval=width, dtype=tf.int32)  # pylint: disable=E1123
                bby1 = tf.clip_by_value(center_y - cut_height // 2, 0, height)
                bbx1 = tf.clip_by_value(center_x - cut_width // 2, 0, width)
                bby2 = tf.clip_by_value(center_y + cut_height // 2, 0, height)
                bbx2 = tf.clip_by_value(center_x + cut_width // 2, 0, width)

                # insert image bounding box
                x_aug[idx1, :, bbx1:bbx2, bby1:bby2, :].assign(x_nfhwc[idx2, :, bbx1:bbx2, bby1:bby2, :])
                # mix labels
                y_aug[idx1].assign(lmb * y_aug[idx1] + (1.0 - lmb) * y_one_hot[idx2])

        x_nfhwc = tf.convert_to_tensor(x_aug)
        y_aug = tf.convert_to_tensor(y_aug)

        # NCHW/NHWC/NCFHW <-- NFHWC
        if x_ndim == 4:
            if self.channels_first:
                # NHWC <-- NCHW <-- NFHWC
                x_nhwc = tf.squeeze(x_nfhwc, axis=1)
                x_aug = tf.transpose(x_nhwc, (0, 3, 1, 2))
            else:
                # NHWC <-- NFHWC
                x_aug = tf.squeeze(x_nfhwc, axis=1)
        elif x_ndim == 5:
            if self.channels_first:
                # NCFHW <-- NFHWC
                x_aug = tf.transpose(x_nfhwc, (0, 4, 1, 2, 3))
            else:
                # NFHWC
                x_aug = x_nfhwc

        return x_aug, y_aug

    def _check_params(self) -> None:
        if self.num_classes <= 0:
            raise ValueError("The number of classes must be positive")

        if self.alpha <= 0:
            raise ValueError("The combination ratio sampling parameter must be positive.")

        if self.probability < 0 or self.probability > 1:
            raise ValueError("The CutMix probability must be between 0 and 1.")
