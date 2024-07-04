import os
import json
import glob
from datasets import load_dataset
from tqdm import tqdm
import pandas as pd
import webdataset as wds
from PIL import Image
from io import BytesIO


def create_webdataset(jsonl_path, image_root, output_path, samples_per_shard=20000):

    sample_count = 0
    shard_count = 0
    writer = wds.TarWriter(f"{output_path}_{shard_count:05d}.tar")

    with open(jsonl_path, "r") as f:
        for line in tqdm(f):
            data = json.loads(line)
            image_path = os.path.join(image_root, data["file_name"])

            if not os.path.exists(image_path):
                print(f"Warning: Image not found - {image_path}")
                continue

            # 이미지를 바이트로 읽기
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()

            # WebDataset 샘플 생성
            sample = {
                "__key__": f"sample_{sample_count}",
                "jpg": image_bytes,
                "json": json.dumps(data),
            }
            writer.write(sample)

            sample_count += 1

            # 새 샤드 시작
            if sample_count % samples_per_shard == 0:
                writer.close()
                shard_count += 1
                writer = wds.TarWriter(f"{output_path}_{shard_count:05d}.tar")
                # break

    writer.close()
    print(f"Created {shard_count + 1} shards with {sample_count} samples in total.")


jsonl_path = "/home/work/llm_data/datasets/food-images/metadata.jsonl"
image_root = "/home/work/llm_data/datasets/food-images/Training"
output_path = "/home/work/llm_data/datasets/food-images/webdataset/data"

create_webdataset(jsonl_path, image_root, output_path)
