#!/usr/bin/python

from Tkinter import *
from tkFileDialog import askopenfilename


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
        self.possible_tags = ["Button 1","Button 2","Button 3","Button 4", "Joystick 1","Joystick 2","Joystick 3","Joystick 4","Hinge","Mainboard","Servo Mount","Servo Hold","Knob"]

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

    def openObj(self):
        self.obj = askopenfilename()
        self.e.delete(0,END)
        self.e.insert(0,self.obj)
        self.e.xview_moveto(1)


def main():
  
    root = Tk()
    root.geometry("400x350+100+100")
    app = Example(root)
    root.mainloop()  


if __name__ == '__main__':
    main()  
 