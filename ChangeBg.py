import cv2
import numpy as np
import time
import sentry_sdk


class ChangeBg:
    def __init__(self):
        self.threshold = 12000000

    # generate image and save
    def generate(self, mask_addr, img_addr, save_path, blur_coeff=None, bg_addr=None, bg_color=None, scale=1., x=0, y=0):
        mask = cv2.imread(mask_addr, 0)
        img = cv2.imread(img_addr)

        try:
            (h_org, w_org), _ = mask.shape, img.shape
        except AttributeError:
            print("mask/img cannot be read")
            raise AttributeError("mask/img cannot be read")

        # integrate with background image
        if bg_addr:
            bg = cv2.imread(bg_addr)
            try:
                h_bg, w_bg, _ = bg.shape
            except AttributeError:
                print("bg cannot be read")
                raise AttributeError("bg cannot be read")

            if blur_coeff is not None:
                bg = self.blur(bg, blur_coeff)

            if scale != 1.:
                if scale - 0.01 <= 0.:
                    scale = 0.01

            result = self.move(img, bg, mask, x, y, scale)
            self.save(result, save_path)

        # integrate with background color
        elif bg_color:
            # Scale down image if image is overly large.
            if h_org * w_org > self.threshold:
                print("fg downsample")
                downsample_scale = self.threshold / (h_org * w_org)
                h_new, w_new = self.down_sample(h_org, w_org, scale=downsample_scale)
                mask = cv2.resize(mask, (w_new, h_new))
                img = cv2.resize(img, (w_new, h_new))
                bg = self.change_color(bg_color, mask)
                fg = self.fg_blending(mask, img)
                result = np.add(bg, fg)
                result = cv2.resize(result, (w_new, h_new))
            else:
                bg = self.change_color(bg_color, mask)
                fg = self.fg_blending(mask, img)
                result = np.add(bg, fg)

            self.save(result, save_path)

        # no bg settings, save rgba fg
        else:
            fg = self.fg_blending(mask, img)
            self.save(fg, save_path, mask=mask)

    # scale down overly large image with given org h, w, and wanted scale.
    # return down scaled h, w
    def down_sample(self, h, w, scale):
        return int(h * scale), int(w * scale)

    # foreground alpha blending with given mask and image
    # return integrated foreground
    def fg_blending(self, mask, img):
        h_org, w_org = mask.shape
        if h_org * w_org > self.threshold:
            print("fg downsample")
            downsample_scale = self.threshold / (h_org * w_org)
            h_new, w_new = self.down_sample(h_org, w_org, scale=downsample_scale)
            mask = cv2.resize(mask, (w_new, h_new))
            img = cv2.resize(img, (w_new, h_new))
            result = np.multiply(np.expand_dims(mask.astype(float) / 255, 2), img).astype('uint8')
            return cv2.resize(result, (w_org, h_org))
        else:
            return np.multiply(np.expand_dims(mask.astype(float) / 255, 2), img).astype('uint8')

    # gaussian blur background with given window size in pixel
    # return blurred image
    def blur(self, bg, blur_coeff):
        # h_new, w_new = (int(bg.shape[0] * self.blur_scale), int(bg.shape[1] * self.blur_scale))
        # h_extra, w_extra = (h_new - bg.shape[0]) // 2, (w_new - bg.shape[1]) // 2
        # bg = cv2.resize(bg, (w_new, h_new))
        # bg = bg[h_extra:bg.shape[0]+h_extra, w_extra:bg.shape[1]+w_extra, :]

        blur_coeff = (blur_coeff, blur_coeff)
        return cv2.blur(bg, blur_coeff)

    # generate background with given bg_color (HEX format, e.g. "#ffffff") and mask
    # return alpha blended background with given color
    def change_color(self, bg_color, mask):
        r, g, b = self.hex_to_rgb(bg_color)
        r = np.zeros(mask.shape) + r
        g = np.zeros(mask.shape) + g
        b = np.zeros(mask.shape) + b

        bg = cv2.merge((b, g, r))
        return self.bg_blending(mask, bg)

    # Move fg position on bg with given x, y coordinates and scale. (bg is always in original size. x, y indicate upper
    # left corner of fg from upper left corner of bg as the original (0, 0).)
    # Return moved result in bg size.
    def move(self, img, bg, mask, x, y, scale):
        h_org, w_org, _ = img.shape

        h_fg, w_fg = int(h_org * scale), int(w_org * scale)
        h_bg, w_bg, _ = bg.shape
        coord = (x, y)

        x1_global, y1_global = (max(coord[0], 0), max(coord[1], 0))
        x2_global, y2_global = (min(coord[0]+w_fg, w_bg), min(coord[1]+h_fg, h_bg))

        # coords in fg
        x1_fg, y1_fg = (int(max(-coord[0], 0)/scale), int(max(-coord[1], 0)/scale))
        x2_fg, y2_fg = (int(min(w_fg, w_bg-coord[0])/scale), int(min(h_fg, h_bg-coord[1])/scale))

        crop_bg = bg[y1_global:y2_global, x1_global:x2_global, :]
        h_crop, w_crop = crop_bg.shape[0], crop_bg.shape[1]

        crop_fg = img[y1_fg:y2_fg, x1_fg:x2_fg, :]
        crop_mask = mask[y1_fg:y2_fg, x1_fg:x2_fg]

        fg_patch = self.fg_blending(crop_mask, crop_fg)

        crop_mask = cv2.resize(crop_mask, (w_crop, h_crop))
        patch = self.bg_blending(crop_mask, crop_bg)
        fg_patch = cv2.resize(fg_patch, (w_crop, h_crop))
        patch = np.add(patch, fg_patch)
        result = bg
        result[y1_global:y2_global, x1_global:x2_global, :] = patch
        return result

    # Save image with given img and save_path. If mask is specified, save in rgba; otherwise, save in rgb. Raise error
    # if save failure.
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

    # Alpha blend bg with given mask and org bg image.
    # Returns original sized blended mask.
    def bg_blending(self, mask, bg):
        h_org, w_org = mask.shape

        # scale down if bg is overly large
        if h_org * w_org > self.threshold:
            print("bg downsample")
            downsample_scale = self.threshold / (h_org * w_org)
            h_new, w_new = self.down_sample(h_org, w_org, scale=downsample_scale)
            mask = cv2.resize(mask, (w_new, h_new))
            bg = cv2.resize(bg, (w_new, h_new))
            result = np.multiply(1. - np.expand_dims(mask.astype(float) / 255, 2), bg).astype('uint8')
            return cv2.resize(result, (w_org, h_org))
        else:
            return np.multiply(1. - np.expand_dims(mask.astype(float) / 255, 2), bg).astype('uint8')

    # Convert HEX format color to RGB format.
    # Returns (r, g, b) values.
    def hex_to_rgb(self, value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def main():
    img_path = "demo1_rotoscope(1).jpg"
    mask_path = "demo1_rotoscope.png"
    bg_path = "demo1_rotoscope(1).jpg"
    save_path = "save5.png"
    scale = 0.9
    x, y = (0,0)  # x y
    bg_color = "#ffaaff"
    blur_coeff = 20

    # sentry_sdk.init("http://3a06f4e9985c453f83c448479309c91b@192.168.50.13:9900/3")

    start = time.time()

    img_set = ChangeBg()
    # img_set.generate(mask_path, img_path, save_path, bg_path, scale=scale, x=x, y=y)
    # img_set.generate(mask_path, img_path, save_path)
    # img_set.generate(mask_path, img_path, save_path, bg_color=bg_color)
    img_set.generate(mask_path, img_path, save_path, bg_addr=bg_path, scale=scale, x=x, y=y, blur_coeff=blur_coeff)


    end = time.time()
    print(end - start)

if __name__ == '__main__':
    main()