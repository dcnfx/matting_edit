import cv2
import numpy as np
import time


class ChangeBg:
    def __init__(self):
        self.scale = scale
        self.coord = (x, y)  # upper-left corner
        self.mask = cv2.imread(mask_addr, 0)
        self.img = cv2.imread(img_addr)
        self.fg = None
        self.bg = None
        self.save_path = save_path

        if bg_addr:
            self.bg = cv2.imread(bg_addr)


    def generate_fg(self, mask_addr, img_addr, save_path, bg_addr=None, scale=1., x=0, y=0):
        img = img.astype(float)
        mask = np.expand_dims(self.mask.astype(float) / 255, 2)
        self.fg = np.multiply(mask, img).astype('uint8')

        if scale != 1.:
            self.fg = cv2.resize(self.fg, (int(self.img.shape[1] * self.scale), int(self.img.shape[0] * self.scale)))
            self.mask = cv2.resize(self.mask, (int(self.mask.shape[1] * self.scale), int(self.mask.shape[0] * self.scale)))

        if self.bg.any():
            result = self.move()
        else:
            result = self.fg
        self.save_alpha(result)

    def move(self):
        h_fg, w_fg, _ = self.fg.shape
        h_bg, w_bg, _ = self.bg.shape

        x1_global, y1_global = (max(self.coord[0], 0), max(self.coord[1], 0))
        x2_global, y2_global = (min(self.coord[0]+w_fg, w_bg), min(self.coord[1]+h_fg, h_bg))

        x1_fg, y1_fg = (max(-self.coord[0], 0), max(-self.coord[1], 0))
        x2_fg, y2_fg = (min(w_fg, w_bg-self.coord[0]), min(h_fg, h_bg-self.coord[1]))

        crop_bg = self.bg[y1_global:y2_global, x1_global:x2_global, :]
        crop_fg = self.fg[y1_fg:y2_fg, x1_fg:x2_fg, :]
        crop_mask = self.mask[y1_fg:y2_fg, x1_fg:x2_fg]

        patch = np.multiply(1. - np.expand_dims(crop_mask.astype(float) / 255, 2), crop_bg).astype('uint8')
        patch = np.add(patch, crop_fg)
        result = self.bg
        result[y1_global:y2_global, x1_global:x2_global, :] = patch
        return result

    def save_alpha(self, img):
        if not self.bg.any():
            result = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = self.mask
        else:
            result = img

        cv2.imwrite(self.save_path, result)


if __name__ == '__main__':
    img_path = "test_img.jpg"
    mask_path = "test_mask.jpg"
    bg_path = "bg.png"
    save_path = "save3.jpg"
    scale = 1
    x, y = (0, 0)  # x y

    start = time.time()

    img_set = ChangeBg(mask_addr=mask_path, img_addr=img_path, bg_addr=bg_path, save_path=save_path, scale=scale, x=x,
                         y=y)
    img_set.generate_fg()

    end = time.time()
    print(end - start)
