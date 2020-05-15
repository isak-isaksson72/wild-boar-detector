import os
import json
from tkinter import filedialog
from tkinter import *  
from PIL import ImageTk,Image  
import csv

class Object():
    def __init__(self):
        self.x_min = 0
        self.y_min = 0
        self.x_min = 0
        self.y_max = 0
        self.object_type = None

class Window():
    def __init__(self, root=None):
        self.root = root
        content = Frame(root)
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New Project", command=self.select_data_folder)
        filemenu.add_command(label="Open Project", command=self.open_project)
        filemenu.add_command(label="Save", command=self.save_project)
        filemenu.add_command(label="Export To CSV", command=self.export_to_csv)
        filemenu.add_command(label="Import From CSV", command=self.import_from_csv)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        root.config(menu=menubar)

        self.canvas = Canvas(content, width = 960, height = 720, borderwidth=2, relief="groove")
        self.root.bind("<Key>", self.key_press_handler)
        self.canvas.bind('<Button-3>', self.select_object)
        self.canvas.bind('<Button-1>', self.mouse_press_handler)
        self.canvas.bind('<B1-Motion>', self.mouse_move_handler)
        self.canvas.bind('<ButtonRelease-1>', self.mouse_release_handler) 

        class_group = Frame(content, borderwidth=2, relief="groove") 
        self.object_type = StringVar()
        self.object_type.set('Pig')
        Radiobutton(class_group, text="Pig", variable=self.object_type, value='Pig', command=self.select_label).pack(anchor = W )
        Radiobutton(class_group, text="Fox", variable=self.object_type, value='Fox', command=self.select_label).pack(anchor = W )
        Radiobutton(class_group, text="Deer", variable=self.object_type, value='Deer', command=self.select_label).pack(anchor = W )
        Radiobutton(class_group, text="Moose", variable=self.object_type, value='Moose', command=self.select_label).pack(anchor = W )
        
        self.image_names = Listbox(content, borderwidth=2, relief="groove")
        self.image_names.bind('<<ListboxSelect>>', self.select_image)

        self.objects = Listbox(content, borderwidth=2, relief="groove")
        self.objects.bind('<<ListboxSelect>>', self.select_object2)

        content.grid(column=0, row=0)
        content.grid_rowconfigure(1, weight=1)
        self.canvas.grid(column=1, row=0, rowspan=2)
        class_group.grid(column=2, row=0,sticky=(N))
        self.image_names.grid(column=0, row=0, rowspan=2, sticky=(N,S))
        self.objects.grid(column=2, row=1, sticky=(N,S))
        self.draw_started = False
        self.image_selected = False
        self.current_image = None
        self.current_object_selected = None      
        self.data = {}
        self.project_file = None

    def select_label(self,):
        if self.current_object_selected != None:
            self.data[self.current_image]['objects'][self.current_object_selected].object_type = self.object_type.get()

    def select_data_folder(self):
        folder_selected = filedialog.askdirectory()
        self.data_folder = folder_selected
        if folder_selected:
            images = os.listdir(folder_selected)
            self.data = {}
            i = 1
            self.image_names.delete(0, END)
            for image in images:
                self.data[image] = {'name': image, 'x_scale': 1.0, 'y_scale': 1.0, 'objects': [] }
                self.image_names.insert(i, image)
                i += 1

    def select_image(self,  event):
        image_name = self.image_names.get(ANCHOR)
        image_path = os.path.join(self.data_folder, image_name)
        self.current_object_selected = None
        exists = os.path.exists(image_path)
        if exists:
            self.canvas.delete('all')
            raw = Image.open(image_path)
            self.data[image_name]['x_scale'] = raw.size[0] / 960
            self.data[image_name]['y_scale'] = raw.size[1] / 720            
            raw = raw.resize((960,720), Image.ANTIALIAS)
            self.img = ImageTk.PhotoImage(raw)
            self.canvas.create_image(0, 0, anchor=NW, image=self.img)
            self.image_selected = True  
            self.current_image = image_name  
            self.draw_all_bounding_boxes()   
            self.fill_object_list() 

    def fill_object_list(self):
        self.objects.delete(0, END)
        for i in range(len(self.data[self.current_image]['objects'])):
            self.objects.insert(i, f'object_{i}')

    def open_project(self):
        f = filedialog.askopenfile(mode='r', filetypes =[('Project Files', '*.json')])
        self.data_folder = os.path.dirname(f.name)
        self.project_file = f.name
        if f is not None: 
            data = f.read() 
            data = json.loads(data)
            self.image_names.delete(0, END)
            self.canvas.delete('all')
            self.objects.delete(0, END)
            i = 1
            for image_name in data:
                self.data[image_name] = {'name': image_name, 'x_scale': data[image_name]['x_scale'], 'y_scale': data[image_name]['y_scale'], 'objects': [] }
                self.image_names.insert(i, image_name)
                i += 1
                for obj in data[image_name]['objects']:
                    o = Object()
                    o.x_min = obj['x_min']
                    o.x_max = obj['x_max']
                    o.y_min = obj['y_min']
                    o.y_max = obj['y_max']
                    o.object_type = obj['object_type']
                    self.data[image_name]['objects'].append(o)

    def export_to_csv(self):
        if self.project_file is None:
            return
        f = filedialog.asksaveasfile(mode='w', defaultextension=".csv")
        
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
                return
        csv_data = ''
        for image_name in self.data:            
            for o in self.data[image_name]['objects']:
                x_scale = self.data[image_name]['x_scale']
                y_scale = self.data[image_name]['y_scale']
                csv_data += f'{image_name},{int(o.x_min * x_scale)},{int(o.y_min * y_scale)},{int(o.x_max * x_scale)},{int(o.y_max * y_scale)},{o.object_type}\n'
        f.write(csv_data)
        f.close()

    def import_from_csv(self):        
        f = filedialog.askopenfile(mode='r', filetypes =[('Project Files', '*.csv')])
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        self.data_folder = os.path.dirname(f.name)
        csv_reader = csv.reader(f, delimiter=',')
        i = len(self.image_names.keys())
        for row in csv_reader:
            image_name = row[0]
            if image_name not in self.data:
                self.data[image_name] = {'name': image_name, 'objects': [] }
                self.image_names.insert(i, image_name)
                i += 1
                image_path = os.path.join(self.data_folder, image_name)
                raw = Image.open(image_path)
                self.data[image_name]['x_scale'] = raw.size[0] / 960
                self.data[image_name]['y_scale'] = raw.size[1] / 720  
            o = Object()
            o.x_min = int(row[1]) // self.data[image_name]['x_scale']           
            o.y_min = int(row[2]) // self.data[image_name]['y_scale']
            o.x_max = int(row[3]) // self.data[image_name]['x_scale']
            o.y_max = int(row[4]) // self.data[image_name]['y_scale']
            o.object_type = row[5]
            self.data[image_name]['objects'].append(o)
        f.close()

    def save_project(self):
        if self.project_file is None:
            f = filedialog.asksaveasfile(mode='w', defaultextension=".json")
            if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
                return
        else:
            f = open(self.project_file, 'w+')
        data = json.dumps(self.data, default=lambda x: x.__dict__)
        f.write(data)
        f.close()

    def select_object2(self, event):
        if self.objects.curselection() != ():
            object_index = int(self.objects.curselection()[0])
            self.current_object_selected = object_index
            self.draw_all_bounding_boxes(object_index)

    def select_object(self, event):
        i = 0
        for o in self.data[self.current_image]['objects']:
            if event.x > o.x_min and \
                event.x <  o.x_max and \
                event.y > o.y_min and \
                event.y < o.y_max:
                    self.current_object_selected = i
                    self.draw_all_bounding_boxes(i)
                    self.objects.selection_clear(0,END)
                    self.objects.selection_set(i,i)
                    self.objects.activate(i)
                    break
            i += 1

    def key_press_handler(self, event):        
        if event.keysym == 'Delete' and self.current_object_selected != None:
            del self.data[self.current_image]['objects'][self.current_object_selected]
            self.draw_all_bounding_boxes()
            self.current_object_selected = None
            self.fill_object_list() 
        elif event.state == 12 and event.keysym == 's':
            # 12 = left control
            self.save_project()

    def mouse_press_handler(self, event):
        if self.image_selected:
            self.draw_started = True
            self.x_start, self.y_start = event.x, event.y

    def mouse_move_handler(self, event):
        if self.draw_started:            
            self.draw_all_bounding_boxes()
            self.canvas.create_rectangle(self.x_start, self.y_start, event.x, event.y, outline="red", width=2)

    def mouse_release_handler(self, event):
        if self.draw_started:
            self.draw_started = False
            self.x_stop, self.y_stop = event.x, event.y
            if abs(self.x_stop -self.x_start) > 5 and abs(self.y_stop -self.y_start) > 5:
                self.add_new_class()

    def add_new_class(self):
        o = Object()
        o.x_min = self.x_start if self.x_start < self.x_stop else self.x_stop
        o.x_max = self.x_stop if self.x_stop > self.x_start else self.x_start
        o.y_min = self.y_start if self.y_start < self.y_stop else self.y_stop
        o.y_max = self.y_stop if self.y_stop > self.y_start else self.y_start
        o.object_type = self.object_type.get()
        self.data[self.current_image]['objects'].append(o)
        self.current_object_selected = len(self.data[self.current_image]['objects']) - 1
        self.objects.insert(self.current_object_selected, f'object_{self.current_object_selected}')

    def draw_all_bounding_boxes(self, selected_object = None):
        i = 0
        self.canvas.create_image(0, 0, anchor=NW, image=self.img)
        for o in self.data[self.current_image]['objects']:
            if selected_object == i:
                self.canvas.create_rectangle(o.x_min, o.y_min, o.x_max, o.y_max, outline="red", width=2)
                self.object_type.set(o.object_type)
            else:
                self.canvas.create_rectangle(o.x_min, o.y_min, o.x_max, o.y_max, outline="white", dash=(1, 1), width=2)
            i += 1
 
root = Tk() 
app = Window(root) 
root.mainloop() 