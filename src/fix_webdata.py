import os
import webdataset as wds
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from datasets import Image as DatasetsImage
import multiprocessing
from functools import partial


def is_valid_image(image_bytes):
    try:
        datasets_image = DatasetsImage()
        image_data = {"bytes": image_bytes, "path": "dummy_path.jpg"}
        pil_image = datasets_image.decode_example(image_data)
        pil_image.load()
        return True
    except Exception as e:
        return False


def process_file(file_name, input_dir, output_dir, log_queue):
    input_path = os.path.join(input_dir, file_name)
    base_name = os.path.splitext(file_name)[0]
    output_path = os.path.join(output_dir, f"fixed_{base_name}.tar")

    corrupt_images_found = False
    valid_samples = []
    local_log = []

    try:
        for sample in wds.WebDataset(input_path).decode():
            if "jpg" in sample:
                if is_valid_image(sample["jpg"]):
                    valid_samples.append(sample)
                else:
                    corrupt_images_found = True
                    local_log.append(
                        f"Corrupt image in {file_name}: {sample['__key__']}\n"
                    )
            else:
                valid_samples.append(sample)
    except Exception as e:
        print(f"Error processing {file_name}: {str(e)}")
        return

    if corrupt_images_found:
        with wds.TarWriter(output_path) as sink:
            for sample in valid_samples:
                sink.write(sample)
        print(f"Created fixed version of {file_name}")
    else:
        print(f"No corrupt images found in {file_name}, skipping")

    if local_log:
        log_queue.put("".join(local_log))


def fix_webdataset_files(input_dir, output_dir, num_processes=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_names = sorted(os.listdir(input_dir))

    manager = multiprocessing.Manager()
    log_queue = manager.Queue()

    # 지정된 프로세스 수가 없으면 CPU 코어 수를 사용
    if num_processes is None:
        num_processes = multiprocessing.cpu_count()

    print(f"Using {num_processes} processes")

    with multiprocessing.Pool(processes=num_processes) as pool:
        process_func = partial(
            process_file,
            input_dir=input_dir,
            output_dir=output_dir,
            log_queue=log_queue,
        )
        list(tqdm(pool.imap(process_func, file_names), total=len(file_names)))

    with open(os.path.join(output_dir, "corrupt_images.log"), "w") as log_file:
        while not log_queue.empty():
            log_file.write(log_queue.get())

    print(
        "처리가 완료되었습니다. 'corrupt_images.log' 파일에서 손상된 이미지 정보를 확인할 수 있습니다."
    )


if __name__ == "__main__":
    # input_dir = "/Jupyter/dataset/food-images/webdataset"
    # output_dir = "/Jupyter/dataset/food-images/webdataset_fix"
    input_dir = "/Jupyter/tmp"
    output_dir = "/Jupyter/tmp_fix"
    num_processes = 1  # 원하는 프로세스 수를 지정하세요. None으로 설정하면 CPU 코어 수를 사용합니다.
    fix_webdataset_files(input_dir, output_dir, num_processes)
