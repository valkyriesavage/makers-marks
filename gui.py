#!/usr/bin/python

from Tkinter import *
from tkFileDialog import askopenfilename
import os


class Example(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)   
         
        self.parent = parent        
        self.initUI()
        
    def initUI(self):

        self.obj = ''
        self.chosen_tags = []
        self.tag_to_add = StringVar()
        self.tag_to_add.set("test")
        self.possible_tags = ["Button 1","Button 2","Button 3","Button 4", "Joystick 1",
                              "Joystick 2","Mainboard","Camera", "Raspberry Pi",
                              "Servo Mount","Servo Move", "Distance Sensor", "Hinge",
                              "Gyroscope", "Speaker", "Right Parting Line",
                              "Left Parting Line", "Hole 1","Hole 2","Hole 3","Hole 4"]

        self.parent.title("Makers\' Marks")

        self.pack(fill=BOTH, expand=1)
        
        self.boss = IntVar()
        self.lip = IntVar()

        self.boss_s = False
        self.lip_s = False

        self.bosc = Checkbutton(self, text="Bosses?",
            variable=self.boss, command=self.onClickB)
        self.bosc.grid(row=3,column=0,padx=5, pady=5)

        self.lipc = Checkbutton(self, text="Lip?",
            variable=self.lip, command=self.onClickL)
        self.lipc.grid(row=3,column=1,padx=5, pady=5)

        o = Button(self, text="Browse", command=self.openObj, padx=4, pady=2, anchor=W)
        o.grid(row=1,column=2, pady=5)

        title = Label(self, text="Makers\' Marks", font=("Helvetica", 32), anchor=W, justify=LEFT)
        title.grid(row=0, column=1, columnspan=3,sticky=W)

        l1 = Label(self, text="Obj: ")
        l1.grid(row=1,column=0,padx=5, pady=5, sticky=E)

        self.e = Entry(self)
        self.e.grid(row=1,column=1, pady=5, sticky=W)

        b = Button(self, text="Go!", command=self.execute, height=2, width=6, anchor=CENTER)
        b.grid(row=3,column=2,padx=5, pady=5)

        l2 = Label(self, text="Tags: ")
        l2.grid(row=2,column=0,padx=5, pady=5, sticky=E)

        # tags = OptionMenu(self, self.tag_to_add, "what", "help", "ok")
        # tags.grid(row=2, column=2)

        scrollbar = Scrollbar(self)
        scrollbar.grid(row=2,column=1, sticky=E)
        self.listbox = Listbox(self, selectmode=MULTIPLE)
        self.listbox.grid(row=2,column=1, columnspan=2, sticky=W)
        for item in self.possible_tags:
            self.listbox.insert(END,item)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        

    def onClickB(self): 
        if self.boss.get() == 1:
            self.boss_s = True 
        else:
            self.boss_s = False 

    def onClickL(self):
        if self.lip.get() == 1:
            self.lip_s = True
        else:
            self.lip_s = False

    def execute(self):
        items = self.listbox.curselection()
        self.chosen_tags = [self.possible_tags[item] for item in items]
        print "starting with obj at ", self.obj, " tags ", self.chosen_tags
        print "bosses: ", self.boss_s, " lip: ", self.lip_s
        sort_tags(self.chosen_tags)
        os.system("python process.py {0} {1} {2}".format(self.obj, self.boss_s, self.lip_s))
        print "all done! look for the .stl in the current directory."
        sys.exit()

    def openObj(self):
        self.obj = askopenfilename()
        self.e.delete(0,END)
        self.e.insert(0,self.obj)
        self.e.xview_moveto(1)

def sort_tags(tags):
        tags = renametags(tags)
        os.system("rm -r tags; mkdir tags")
        for tag in tags:
            os.system("cp alltags/{0} tags/{0}".format(tag))

def renametags(tags):
    new_tags = []
    for tag in tags:
        if tag == "Button 1":
            new_tags.append("b1.jpg")
        if tag == "Button 2":
            new_tags.append("b2.jpg")
        if tag == "Button 3":
            new_tags.append("b3.jpg")
        if tag == "Button 4":
            new_tags.append("b4.jpg")
        if tag == "Joystick 1":
            new_tags.append("j1.jpg")
        if tag == "Joystick 2":
            new_tags.append("j2.jpg")
        if tag == "Mainboard":
            new_tags.append("m.jpg")
        if tag == "Hole 1":
            new_tags.append("hole.jpg")
        if tag == "Hole 2":
            new_tags.append("hole2.jpg")
        if tag == "Hole 3":
            new_tags.append("hole3.jpg")
        if tag == "Hole 4":
            new_tags.append("hole4.jpg")
        if tag == "Right Parting Line":
            new_tags.append("r.jpg")
        if tag == "Left Parting Line":
            new_tags.append("l.jpg")
        if tag == "Hinge":
            new_tags.append("h.jpg")
        if tag == "Servo Mount":
            new_tags.append("smount.jpg")
        if tag == "Servo Move":
            new_tags.append("smove.jpg")
        if tag == "Camera":
            new_tags.append("cam.jpg")
        if tag == "Raspberry Pi":
            new_tags.append("rpi.jpg")
        if tag == "Gyroscope":
            new_tags.append("gyro.jpg")
        if tag == "Speaker":
            new_tags.append("s.jpg")
        if tag == "Distance Sensor":
            new_tags.append("d.jpg")
    return new_tags


    
def main():
  
    root = Tk()
    root.geometry("400x350+100+100")
    app = Example(root)
    root.mainloop()



if __name__ == '__main__':
    main()  
 