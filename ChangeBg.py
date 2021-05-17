import cv2
import numpy as np
import time
import sentry_sdk


class ChangeBg:
    def __init__(self):
        self.blur_scale = 1.2

    def generate(self, mask_addr, img_addr, save_path, blur_coeff=None, bg_addr=None, bg_color=None, scale=1., x=0, y=0):
        mask = cv2.imread(mask_addr, 0)
        img = cv2.imread(img_addr)

        try:
            _, _ = mask.shape, img.shape
        except AttributeError:
            print("mask/img cannot be read")

        if scale != 1.:
            img = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))
            mask = cv2.resize(mask, (int(mask.shape[1] * scale), int(mask.shape[0] * scale)))

        img_alpha = img.astype(float)
        mask_alpha = np.expand_dims(mask.astype(float) / 255, 2)
        fg = np.multiply(mask_alpha, img_alpha).astype('uint8')

        if bg_addr:
            bg = cv2.imread(bg_addr)
            try:
                _ = bg.shape
            except AttributeError:
                print("bg cannot be read")

            if blur_coeff is not None:
                bg = self.blur(bg, blur_coeff)

            result = self.move(fg, bg, mask, x, y)
            self.save(result, save_path)
        elif bg_color:
            bg = self.change_color(bg_color, mask)
            result = np.add(bg, fg)
            self.save(result, save_path)
        else:
            self.save(fg, save_path, mask=mask)

    def blur(self, bg, blur_coeff):
        blur_coeff = (blur_coeff, blur_coeff)
        return cv2.blur(bg, blur_coeff)

    def change_color(self, bg_color, mask):
        r, g, b = self.hex_to_rgb(bg_color)
        r = np.zeros(mask.shape) + r
        g = np.zeros(mask.shape) + g
        b = np.zeros(mask.shape) + b

        bg = cv2.merge((b, g, r))
        return self.bg_blending(mask, bg)


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

        patch = self.bg_blending(crop_mask, crop_bg)
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
        write_status = cv2.imwrite(save_path, result)
        if write_status is not True:
            print("img save error")
            raise OSError

    def bg_blending(self, mask, bg):
        return np.multiply(1. - np.expand_dims(mask.astype(float) / 255, 2), bg).astype('uint8')

    def hex_to_rgb(self, value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


if __name__ == '__main__':
    img_path = "test_img.jpg"
    mask_path = "test_mask.jpg"
    bg_path = "wallhaven-rd3xvm.jpg"
    save_path = "save4.jpg"
    scale = 0.3
    x, y = (22, -6)  # x y
    bg_color = "#ffaaff"
    blur_coeff = 50

    sentry_sdk.init("http://3a06f4e9985c453f83c448479309c91b@192.168.50.13:9900/3")

    start = time.time()

    img_set = ChangeBg()
    # img_set.generate(mask_path, img_path, save_path, bg_path, scale=scale, x=x, y=y)
    # img_set.generate(mask_path, img_path, save_path)
    # img_set.generate(mask_path, img_path, save_path, bg_color=bg_color)
    img_set.generate(mask_path, img_path, save_path, bg_addr=bg_path, scale=scale, x=x, y=y, blur_coeff=blur_coeff)


    end = time.time()
    print(end - start)
