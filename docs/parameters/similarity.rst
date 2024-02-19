similarity (str, int)
++++++++++++

difPy compares the images to find duplicates or similarities, based on the MSE (Mean Squared Error) between both image tensors. The target similarity rate i. e. MSE value is set with the ``similarity`` parameter.

``"duplicates"`` = (default) searches for duplicates. MSE threshold is set to ``0``.

``"similar"`` = searches for similar images. MSE threshold is set to ``50``.

Depending on which use case you want to apply difPy for, the granularity for the classification of images can be adjusted.

**Manual setting**: the match MSE threshold can be adjusted manually by setting the ``similarity`` parameter to any ``int`` or ``float``. difPy will then search for images that match an MSE threshold **equal to or lower than** the one specified.

When searching for **similar** images, the choice of MSE threshold becomes very important. A threshold of ``50`` will usually find similarities in regular photographs well, but if applied to images containing for example text with a plain white background, an MSE threshold of ``50`` will usually be too high and difPy will consider all images to be similar, even though they are not. In this case, for more precision, the ``similarity`` parameter should be lowered. Additionally, the ``px_size`` parameter can also be increased to gain more precision (see :ref:`px_size`).