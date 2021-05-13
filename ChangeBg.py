import cv2
import numpy as np
import time


class ChangeBg:
    def __init__(self):
        pass

    def generate(self, mask_addr, img_addr, save_path, bg_addr=None, scale=1., x=0, y=0):
        mask = cv2.imread(mask_addr, 0)
        img = cv2.imread(img_addr)

        if scale != 1.:
            img = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))
            mask = cv2.resize(mask, (int(mask.shape[1] * scale), int(mask.shape[0] * scale)))

        img_alpha = img.astype(float)
        mask_alpha = np.expand_dims(mask.astype(float) / 255, 2)
        fg = np.multiply(mask_alpha, img_alpha).astype('uint8')

        if bg_addr:
            bg = cv2.imread(bg_addr)
            result = self.move(fg, bg, mask, x, y)
            self.save(result, save_path)
        else:
            self.save(fg, save_path, mask=mask)

    def move(self, fg, bg, mask, x, y):
        h_fg, w_fg, _ = fg.shape
        h_bg, w_bg, _ = bg.shape
        coord = (x, y)

        x1_global, y1_global = (max(coord[0], 0), max(coord[1], 0))
        x2_global, y2_global = (min(coord[0]+w_fg, w_bg), min(coord[1]+h_fg, h_bg))

        x1_fg, y1_fg = (max(-coord[0], 0), max(-coord[1], 0))
        x2_fg, y2_fg = (min(w_fg, w_bg-coord[0]), min(h_fg, h_bg-coord[1]))

        crop_bg = bg[y1_global:y2_global, x1_global:x2_global, :]
        crop_fg = fg[y1_fg:y2_fg, x1_fg:x2_fg, :]
        crop_mask = mask[y1_fg:y2_fg, x1_fg:x2_fg]

        patch = np.multiply(1. - np.expand_dims(crop_mask.astype(float) / 255, 2), crop_bg).astype('uint8')
        patch = np.add(patch, crop_fg)
        result = bg
        result[y1_global:y2_global, x1_global:x2_global, :] = patch
        return result

    def save(self, img, save_path, mask=None):
        if mask is not None:
            result = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask
        else:
            result = img

        cv2.imwrite(save_path, result)


if __name__ == '__main__':
    img_path = "test_img.jpg"
    mask_path = "test_mask.jpg"
    bg_path = "bg.png"
    save_path = "save3.png"
    scale = 0.5
    x, y = (0, 0)  # x y

    start = time.time()

    img_set = ChangeBg()
    img_set.generate(mask_path, img_path, save_path, bg_path, scale, x, y)
    img_set.generate(mask_path, img_path, save_path)

    end = time.time()
    print(end - start)
