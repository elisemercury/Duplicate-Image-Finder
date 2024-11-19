# Performance Test with SqLite

CPUs:
- 8: `50.256s` (utilization ~400%)
- 16: `48.015225799999996` 
- 128: `41.4836961` (utilization ~360%)


# Size of 1000 batch, single submission for items
Batched Processing, RAM Cache, Compressed Images, took 293.026221
Batched Processing, RAM Cache, Uncompressed Images, took -1s
Batched Processing, Disk Cache, Compressed Images, took 561.340875
Batched Processing, Disk Cache, Uncompressed Images, took -1s
Item Processing, RAM Cache, Compressed Images, took 339.503905
Item Processing, RAM Cache, Uncompressed Images, took -1s
Item Processing, Disk Cache, Compressed Images, took 520.295318
Item Processing, Disk Cache, Uncompressed Images, took -1s


# Size of 1000 batch, batched submission for items
Batched Processing, RAM Cache, Compressed Images, took 245.59584
Batched Processing, RAM Cache, Uncompressed Images, took -1s
Batched Processing, Disk Cache, Compressed Images, took 472.612294
Batched Processing, Disk Cache, Uncompressed Images, took -1s
Item Processing, RAM Cache, Compressed Images, took 252.462715
Item Processing, RAM Cache, Uncompressed Images, took -1s
Item Processing, Disk Cache, Compressed Images, took 471.199621
Item Processing, Disk Cache, Uncompressed Images, took -1s
