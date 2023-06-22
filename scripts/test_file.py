from fast_diff_py import dif
import cv2
import numpy as np
import hashlib


if __name__ == "__main__":
    # dif_instance = dif(directory_A="/home/alisot2000/Desktop/SAMPLE_MIRA/Shiny stars/Alex", show_progress=True, show_output=True)

    img: np.array = cv2.imdecode(np.fromfile("/home/alisot2000/Desktop/SAMPLE_MIRA/Shiny stars/Sophia/0C2E9779-8E7C-4044-B2D3-07C8F8650527.jpeg", dtype=np.uint8), cv2.IMREAD_COLOR)

    sha_hash = hashlib.sha256()
    sha_hash.update(img.data)
    print(sha_hash.hexdigest())
    print(np.shape(img))

    np.rot90(img, k=1, axes=(0, 1))

    sha_hash2 = hashlib.sha256()
    sha_hash2.update(img.data)
    print(sha_hash2.hexdigest())

    print("------------------------------------------------")

    test_array = [[[]for __ in range(3)] for _ in range(3)]

    for i in range(3):
        for j in range(3):
            if i == j:
                test_array[i][j] = [8, 8, 8]
            else:
                test_array[i][j] = [32, 32, 32]

    na = np.array(test_array, dtype=np.uint8)

    print(na)
    res = np.right_shift(na, 3)
    print(na)
    print(res)
