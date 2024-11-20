# Performance Test with SqLite

CPUs:
- 8: `50.256s` (utilization ~400%)
- 16: `48.015225799999996` 
- 128: `41.4836961` (utilization ~360%)


# Pure Compression time
# No batched queue
Time taken for first loop: 349.204719 seconds
# 30 Batched queue
Time taken for first loop: 334.229981 seconds
# 50 batched queue
Time taken for first loop: 323.895515 seconds
# 100 batched queue
Time taken for first loop: 320.250131 seconds
Time taken for first loop: 309.254996 seconds
# 250
Time taken for first loop: 330.104581 seconds


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

# Size of 4000 batch, batched submission for items
Batched Processing, RAM Cache, Compressed Images, took 244.14075
Batched Processing, RAM Cache, Uncompressed Images, took -1s
Batched Processing, Disk Cache, Compressed Images, took 480.714968
Batched Processing, Disk Cache, Uncompressed Images, took -1s
Item Processing, RAM Cache, Compressed Images, took 242.806917
Item Processing, RAM Cache, Uncompressed Images, took -1s
Item Processing, Disk Cache, Compressed Images, took 495.819392
Item Processing, Disk Cache, Uncompressed Images, took -1s

# Size of 4000, batched submission, 4 gpu, 14 cpu
Batched Processing, RAM Cache, Compressed Images, took 267.546793
Batched Processing, RAM Cache, Uncompressed Images, took -1s
Batched Processing, Disk Cache, Compressed Images, took 630.154396
Batched Processing, Disk Cache, Uncompressed Images, took -1s
Item Processing, RAM Cache, Compressed Images, took 289.922815
Item Processing, RAM Cache, Uncompressed Images, took -1s
Item Processing, Disk Cache, Compressed Images, took 632.633869
Item Processing, Disk Cache, Uncompressed Images, took -1s

# Size of 4000 batch, batched submission for items, 2 gpu, 14 cpu
Batched Processing, RAM Cache, Compressed Images, took 263.797665
Batched Processing, RAM Cache, Uncompressed Images, took -1s
Batched Processing, Disk Cache, Compressed Images, took 578.785628
Batched Processing, Disk Cache, Uncompressed Images, took -1s
Item Processing, RAM Cache, Compressed Images, took 279.641388
Item Processing, RAM Cache, Uncompressed Images, took -1s
Item Processing, Disk Cache, Compressed Images, took 581.069106
Item Processing, Disk Cache, Uncompressed Images, took -1s

# Stats large workbench -> Too large. Takes about one week:
Dir_a, Dir_b, dups
(193216, 192742, 3905)

# Stats with a 40'000 x 40'000 images benchmark
(41318, 41586, 857)