import cv2
import numpy as np
import copy
import glob

def overlay_image_alpha(img, img_overlay, pos, alpha_mask):
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

def load_image(file_path):
	img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
	rows, cols = img.shape[:2]
	alpha = img[:,:,3]
	img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	img_orig = np.zeros((rows, cols, 2), dtype=np.uint8)
	img_orig[:,:,0] = img_gray
	img_orig[:,:,1] = alpha
	return img_orig

def augment_image(img_orig, scale):

	img_aug = img_orig
	
	#adjust size
	height = int(img_aug.shape[0] * scale)
	width = int(img_aug.shape[1] * scale)		
	dim = (width, height)
	img_aug = cv2.resize(img_aug, dim, interpolation = cv2.INTER_AREA)
	
	# Mirror image
	if np.random.randint(0, 2) == 0:
		img_aug = cv2.flip(img_aug, 1)

	size = 4
	# generating the kernel
	kernel_motion_blur = np.zeros((size, size))
	kernel_motion_blur[int((size-1)/2), :] = np.ones(size)
	kernel_motion_blur = kernel_motion_blur / size

	# applying the kernel to the input image
	img_aug = cv2.filter2D(img_aug, -1, kernel_motion_blur)

	return img_aug



def augment_generated_training_set(img_data, config):
	assert 'filepath' in img_data	

	img_data_aug = copy.deepcopy(img_data)
	
	bg = cv2.imread('data/bg.jpg', cv2.IMREAD_UNCHANGED)
	bg = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
	bg = cv2.medianBlur(bg, 1)
	bg = np.expand_dims(bg, -1)	

	feeder = load_image('data/feeder.png')
	tree = load_image('data/tree.png')
	files = glob.glob('data/generated_training/*.png')
	files = [name for name in files if 'attack' not in name]
	obj_count = np.random.randint(1, 6)
	objects = []
	for obj in range(obj_count):
		file_path = files[np.random.randint(0, len(files))]		
		img_orig = load_image(file_path)
		pos = (
			np.random.randint(0 - img_orig.shape[1] // 2, bg.shape[1] - img_orig.shape[1] // 2), 
			np.random.randint(bg.shape[0] // 4, bg.shape[0] - img_orig.shape[0] // 2)
		)
		y_min = bg.shape[0] // 4
		y_max = bg.shape[0] - img_orig.shape[0] // 2
		scale = ( pos[1] - y_min + 3 * y_max) / (4 * y_max - y_min)		
		img_aug = augment_image(img_orig, scale)
		objects.append({
			'image': img_aug,
			'pos': pos,
			'ground': pos[1] + img_aug.shape[0],
			'object': True
		})

	objects.append({
		'image': feeder,
		'pos': (447, 0),
		'ground': feeder.shape[0],
		'object': False
	})
	objects.append({
		'image': tree,
		'pos': (0, 313),
		'ground': 313 + tree.shape[0],
		'object': False
	})
	objects = sorted(objects, key=lambda obj: obj['ground'])
	img_data_aug['height'] = bg.shape[0]
	img_data_aug['width'] = bg.shape[1]	
	img_data_aug['bboxes'] = []
	for obj in objects:			
		img_aug = overlay_image_alpha(bg, obj['image'][:,:,:1], obj['pos'], obj['image'][:,:,1:2] / 255.0)
		if obj['object']:
			bbox = {
				'x1': obj['pos'][0] if obj['pos'][0] > 0 else 0,
				'y1': obj['pos'][1] if obj['pos'][1] > 0 else 0,
				'x2': obj['pos'][0] + obj['image'].shape[1] if obj['pos'][0] + obj['image'].shape[1] < bg.shape[1] else bg.shape[1] - 1,
				'y2': obj['pos'][1] + obj['image'].shape[0] if obj['pos'][1] + obj['image'].shape[0] < bg.shape[0] else bg.shape[0] - 1
			}
			tmp = bbox['x1']
			if bbox['x1'] > bbox['x2']:
				bbox['x1'] = bbox['x2']
				bbox['x2'] = tmp
			tmp = bbox['y1']
			if bbox['y1'] > bbox['y2']:
				bbox['y1'] = bbox['y2']
				bbox['y2'] = tmp
			img_data_aug['bboxes'].append(bbox)
		bg = img_aug
	vinget = cv2.imread('data/vinget.png', cv2.IMREAD_UNCHANGED)
		
	img_aug = overlay_image_alpha(img_aug, vinget[:,:,:1], (0,0), (np.random.randint(65,80) / 100.0) * vinget[:,:,3:4] / 255.0)
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


if __name__ == "__main__":
	c = None
	import glob
	files = glob.glob('data/generated_training/*.png')
	objects = []
	i = 0
	while(c != 27 and i < 2000):
		files_path = files[np.random.randint(0,len(files))]
		img_data = {'filepath':files_path, 'bboxes':[{}], 'img_files': files }
		img_data_aug, img_aug = augment_generated_training_set(img_data, None)
		img_file_name = f'data/pre_gen/{i}.jpg'
		#print(f'Shape: {img_aug.shape}')
		for bbox in img_data_aug['bboxes']:
			start_point = (bbox['x1'], bbox['y1'])
			end_point = (bbox['x2'], bbox['y2'])
			objects.append(f"{img_file_name},{bbox['x1']},{bbox['y1']},{bbox['x2']},{bbox['y2']},Pig")
			#color = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))
			#img_aug = cv2.rectangle(img_aug,start_point, end_point, color, 2)
		try:
			#cv2.imshow('Window', img_aug)
			#print(img_data_aug)
			#c = cv2.waitKey()	
			cv2.imwrite(img_file_name,img_aug)
			i += 1
		except Exception as e:
			print(e)
			pass
	with open('generated.txt','w') as f:
  		f.write('\n'.join(objects))
	cv2.destroyAllWindows()
