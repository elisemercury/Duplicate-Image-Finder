FAQ
=====

.. _faq:

.. _How to make difPy faster?:

How to make difPy faster?
----------------

difPy's processing speed can increase or decrease, depending on which parameter configurations are used. Speeding up the comparison process can be especially relevant when using difPy to compare a large number of images. 

Below is a list of **configuration settings** that can make **difPy's processing faster**:

* Enable :ref:`fast_search` when searching for duplicates.
* Enable :ref:`limit_extensions`.
* Set :ref:`px_size` <= 50. Note: the lower the ``px_size``, the less precise the comparison will be. It is not recommended to go below a ``px_size`` of 20.

Searching for similar images will always take more processing time, than searching for duplicates. This is due to the fact that difPy has to compare each image to each other image to check if these are similar. Duplicate image searching is more efficient thanks to difPy's Fast Search Algorithm.

.. _Fast Search Algorithm (FSA):

What is FSA (Fast Search Algorithm)?
------------

.. note::

   🆕 difPy >= v3.x supports Fast Search Algorithm (FSA).

difPy's Fast Search Algorithm (FSA) can provide significant performance increases and time complexity reduction when searching for duplicates.

FSA can be enabled/disabled with the :ref:`fast_search` parameter.

About FSA
^^^^^^^^^^

With the classic difPy algorithm, each image would be compared to every other successive image (by order of images found in the directories). Comparing every image is a very precise option, but leads to high time complexity. When searching for duplicates, this time complexity can be reduced by applying FSA. With FSA, difPy compares an image until it finds a duplicate. This duplicate is classified as duplicate and then excluded from the succeeding search, leading to a lower average number of comparisons.

   *Example: in the first round, difPy searches for duplicates to imageA and finds imageB and imageC. In the next rounds, the search for duplicates of imageB and imageC will be skipped, since they are all duplicates and no further comparison is required.*

Due to its nature, FSA is very efficient when run on duplicate searches, but it is **not advised to be used when searching for similar images**, as the result might be inaccurate. **When searching for similar images, difPy's classic algorithm should be used by setting** :ref:`fast_search` **to** ``False``.

   *Example: imageA might be similar to imageB and imageC, but this does not imply that imageB is similar to imageC. Nevertheless, FSA would assume imageB and imageC to be equally similar and would therefore potentially return wrong results.*

**When searching for similar images, difPy automatically disables FSA** to ensure accurate search results. This applies when :ref:`similarity` is set to ``'similar'`` **or** if :ref:`similarity` is manually set to a value ``> 0``.