# import cv2
#
# img = cv2.imread('images/original_image.png', cv2.IMREAD_COLOR)
#
# rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
# gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
#
# cv2.imwrite("images/after_convert_to_rgb.png", rgb_img)
# cv2.imwrite("images/after_convert_to_gray.png", gray_img)
# cv2.imwrite("images/after_convert_back_to_bgr.png", bgr_img)