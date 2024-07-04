import os
import webdataset as wds
from PIL import Image
from io import BytesIO
from tqdm import tqdm


def is_valid_image(image_bytes):
    try:
        Image.open(BytesIO(image_bytes)).verify()
        return True
    except:
        return False


def fix_webdataset_files(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    log_file = open(os.path.join(output_dir, "corrupt_images.log"), "w")

    for file_name in tqdm(sorted(os.listdir(input_dir))):
        input_path = os.path.join(input_dir, file_name)

        # 파일 이름에서 확장자 제거 (있는 경우)
        base_name = os.path.splitext(file_name)[0]
        output_path = os.path.join(output_dir, f"fixed_{base_name}.tar")

        corrupt_images_found = False
        valid_samples = []

        try:
            for sample in wds.WebDataset(input_path).decode():
                if "jpg" in sample:
                    if is_valid_image(sample["jpg"]):
                        valid_samples.append(sample)
                    else:
                        corrupt_images_found = True
                        log_file.write(
                            f"Corrupt image in {file_name}: {sample['__key__']}\n"
                        )
                else:
                    valid_samples.append(sample)
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
            continue

        if corrupt_images_found:
            with wds.TarWriter(output_path) as sink:
                for sample in valid_samples:
                    sink.write(sample)
            print(f"Created fixed version of {file_name}")
        else:
            print(f"No corrupt images found in {file_name}, skipping")

    log_file.close()
    print(
        "처리가 완료되었습니다. 'corrupt_images.log' 파일에서 손상된 이미지 정보를 확인할 수 있습니다."
    )


# 사용 예:
input_dir = "/Jupyter/dataset/food-images/webdataset"
output_dir = "/Jupyter/dataset/food-images/webdataset_fix"
fix_webdataset_files(input_dir, output_dir)
