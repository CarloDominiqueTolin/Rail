from pathlib import Path
import sys
import os

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from ultralytics.utils.plotting import Annotator, colors

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages
from utils.general import (
    Profile,
    check_img_size,
    cv2,
    non_max_suppression,
    scale_boxes,
)
from utils.segment.general import process_mask
from utils.torch_utils import select_device
from utils.augmentations import letterbox
import torch
import numpy as np

# Load model
device = select_device("")
print(os.getcwd())
model = DetectMultiBackend("Model.pt", device=device, dnn=False, data="data/coco128.yaml", fp16=False)
stride, names, pt = model.stride, model.names, model.pt
imgsz = check_img_size((640, 640), s=stride)  # check image size

bs = 1
model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
seen, windows, dt = 0, [], (Profile(device=device), Profile(device=device), Profile(device=device))


def inference(source,seen=seen):
    im0 = source
    im = letterbox(im0, (640, 640), stride=stride, auto=True)[0]  # padded resize
    im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
    im = np.ascontiguousarray(im)  # contiguous
    s=''
    with dt[0]:
        im = torch.from_numpy(im).to(model.device)
        im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim

    # Inference
    with dt[1]:
        pred, proto = model(im, augment=False, visualize=False)[:2]

    # NMS
    with dt[2]:
        pred = non_max_suppression(pred, 0.25, 0.45, None, False, max_det=1000, nm=32)

    # Process predictions
    for i, det in enumerate(pred):  # per image
        seen += 1
        im0 = im0.copy()

        annotator = Annotator(im0, line_width=3, example=str(names))
        if len(det):
            masks = process_mask(proto[i], det[:, 6:], det[:, :4], im.shape[2:], upsample=True)  # HWC
            det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()  # rescale boxes to im0 size

            # Print results
            for c in det[:, 5].unique():
                n = (det[:, 5] == c).sum()  # detections per class
                s += f"{n} {names[int(c)]}, "  # add to string
            print(s)

            # Mask plotting
            annotator.masks(
                masks,
                colors=[colors(x, True) for x in det[:, 5]],
                im_gpu=torch.as_tensor(im0, dtype=torch.float16).to(device).permute(2, 0, 1).flip(0).contiguous()
                / 255
                if False else im[i],
            )

            for j, (*xyxy, conf, cls) in enumerate(reversed(det[:, :6])):
                c = int(cls)  # integer class
                label = (names[c] if False else f"{names[c]} {conf:.2f}")
                annotator.box_label(xyxy, label, color=colors(c, True))
            
        else:
            print('No Detection')
        # Stream results
        im0 = annotator.result()
    return im0, s

