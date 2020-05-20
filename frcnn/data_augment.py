import cv2
import numpy as np
import copy

def overlay_image_alpha(img, img_overlay, pos, alpha_mask):
    """Overlay img_overlay on top of img at the position specified by
    pos and blend using alpha_mask.

    Alpha mask must contain values within the range [0, 1] and be the
    same size as img_overlay.
    """

    x, y = pos

    # Image ranges
    y1, y2 = max(0, y), min(img.shape[0], y + img_overlay.shape[0])
    x1, x2 = max(0, x), min(img.shape[1], x + img_overlay.shape[1])

    # Overlay ranges
    y1o, y2o = max(0, -y), min(img_overlay.shape[0], img.shape[0] - y)
    x1o, x2o = max(0, -x), min(img_overlay.shape[1], img.shape[1] - x)

    # Exit if nothing to do
    if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
        return

    alpha = alpha_mask[y1o:y2o, x1o:x2o]
    alpha_inv = 1 - alpha
    
    fg = alpha * img_overlay[y1o:y2o, x1o:x2o ]
    bg = alpha_inv * img[y1:y2, x1:x2,]
    img[y1:y2, x1:x2] = (fg + bg)
    img = np.array(img, dtype=np.uint8)
    return img

def augment_generated_training_set(img_data, config):
	assert 'filepath' in img_data	

	img_data_aug = copy.deepcopy(img_data)

	img = cv2.imread(img_data_aug['filepath'], cv2.IMREAD_UNCHANGED)
	rows, cols = img.shape[:2]
	alpha = img[:,:,3]
	img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	img_aug = np.zeros((rows, cols, 2), dtype=np.uint8)
	img_aug[:,:,0] = img_gray
	img_aug[:,:,1] = alpha

	#adjust size
	if np.random.randint(0, 2) == 0:
		scale_percent = np.random.randint(50, 101)
		height = int(img_aug.shape[0] * scale_percent / 100)
		width = int(img_aug.shape[1] * scale_percent / 100)		
		dim = (width, height)
		img_aug = cv2.resize(img_aug, dim, interpolation = cv2.INTER_AREA)
		rows, cols = height, width

	# crop image
	if np.random.randint(0, 4) == 0:
		x_crop_w = np.random.randint(cols * 1.5 // 2, cols + 1)
		y_crop_h = np.random.randint(rows * 1.5 // 2, rows + 1)
		x_start = 0 if np.random.randint(0, 2) == 0 else cols - x_crop_w
		y_start = 0 if np.random.randint(0, 2) == 0 else  rows - y_crop_h
		img_aug = img_aug[ y_start:y_start + y_crop_h, x_start:x_start + x_crop_w]		
		rows, cols = y_crop_h, x_crop_w
	
	# Mirror image
	if np.random.randint(0, 2) == 0:
		img_aug = cv2.flip(img_aug, 1)


	# Adjust brightness
	if np.random.randint(0, 2) == 0:
		level = np.random.randint(-50, 10)
		fg = img_aug[:,:,0]
		fg = cv2.add(fg,level)
		img_aug[:,:,0] = fg
	# Add background noise
	bg = np.random.randint(0, 256, (rows * 2, cols * 2, 1)) 
	pos = (np.random.randint(0, bg.shape[1] - cols), np.random.randint(0, bg.shape[0] - rows))
	
	img_aug = overlay_image_alpha(bg, img_aug[:,:,:1], pos, img_aug[:,:,1:2] // 255)

	
	img_data_aug['height'] = bg.shape[0]
	img_data_aug['width'] = bg.shape[1]	
	img_data_aug['bboxes'][0]['x1'] = pos[0]
	img_data_aug['bboxes'][0]['y1'] = pos[1]
	img_data_aug['bboxes'][0]['x2'] = pos[0] + cols
	img_data_aug['bboxes'][0]['y2'] = pos[1] + rows	
	img_aug = np.repeat(img_aug, 3, 2)	
	return img_data_aug, img_aug

def augment_validation_set(img_data, config):
	assert 'filepath' in img_data
	assert 'bboxes' in img_data
	#assert 'width' in img_data
	#assert 'height' in img_data
	img_data_aug = copy.deepcopy(img_data)

	img = cv2.imread(img_data_aug['filepath'], cv2.IMREAD_UNCHANGED)
	rows, cols = img.shape[:2]
	img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	img_aug = cv2.medianBlur(img_gray, 1)
	
	# Mirror image
	if np.random.randint(0, 2) == 3:
		img_aug = cv2.flip(img_aug, 1)
		for bbox in img_data_aug['bboxes']:
				x1 = bbox['x1']
				x2 = bbox['x2']
				bbox['x2'] = cols - x1
				bbox['x1'] = cols - x2
	img_aug = np.expand_dims(img_aug, -1)
	img_aug = np.repeat(img_aug, 3, 2)
	return img_data_aug, img_aug

'''
c = None
import glob
files = glob.glob('C:/Scania/wild-boar-detector/data/generated_training/*.png')
i = 0
while(c != 27):
	files_path = files[np.random.randint(0,len(files))]
	img_data = {'filepath':files_path, 'bboxes':[{}] }
	img_data_aug, img_aug = augment_generated_training_set(img_data, None)
	print(f'Shape: {img_aug.shape}')
	#start_point = (img_data_aug['bboxes'][0]['x1'], img_data_aug['bboxes'][0]['y1'])
	#end_point = (img_data_aug['bboxes'][0]['x2'], img_data_aug['bboxes'][0]['y2'])
	#img_aug = cv2.rectangle(img_aug,start_point, end_point, 255, 2) 
	try:
		cv2.imshow('Window', img_aug)
		print(img_data_aug)
		c = cv2.waitKey()	
	except Exception as e:
		print(e)
		pass
cv2.destroyAllWindows()
'''