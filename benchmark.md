# Benchmarking for the FastDiffPy Library

## Testing smart algorithm for if directory b is set

### SQLite No Smart Increment.
Duration: [121.199162, 122.175527, 122.338559]
Average: 121.90441600000001
Variance :0.25312150776200093

### SQLite Smart Increment.
Duration: [119.36452, 119.261464, 119.839884]    
Average: 119.48862266666667   
Variance :0.06346235200355459 

### MariaDB Workers, No Smart Increment
Duration: [155.088985, 152.427414, 154.882693]
Average: 154.13303066666666
Variance :1.4616568383495565

### NariaDB Workers, Smart Increment
Duration: [159.543273, 154.541188, 157.256275]
Average: 157.11357866666665
Variance :4.1803235129775445