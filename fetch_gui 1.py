from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import RoundedRectangle, Rectangle, Color
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.utils import get_color_from_hex

import time
import socket
import threading
import cv2
from cv2 import aruco
from playsound import playsound

from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ColorProperty

PORT = 5077
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
# SERVER = "10.32.22.145"
# SERVER = "129.97.71.122" robo
SERVER = "10.0.0.101"  # room 5123
# SERVER = "192.168.10.162"
# SERVER = "192.168.0.49"  # 318 Far
# SERVER = "7192.168.2.90"
# SERVER = "192.168.1.6"  # laptop 5123
ADDR = (SERVER, PORT)


class Box(object):
    def __init__(self, workspace, box_number):
        self.workspace = workspace
        self.number = box_number
        self.previous_state = None
        self.current_state = 'Free'
        self.choosable = False
        self.previous_color = None
        self.color = ''


class MyApp(App):
    def build(self):
        return Userinterface()


class Userinterface(Widget):

    def __init__(self, **kwargs):
        super(Userinterface, self).__init__(**kwargs)
        self.__blue = '#1752A2'
        self.__green = '#009C86'
        self.__orange = '#FF8033'
        self.__pink = '#BE587D'
        self.dialog_box_color = (123 / 256, 143 / 256, 161 / 256, 1)
        self.__human_icon = 'human'
        self.__robot_icon = 'fetch'
        self.__return_icon = 'return'
        self.flashing_boxes = {}  # {'w1b1': self.__blue, 'w1b2': self.__green}
        self.selected_color = None
        self.selected_agent = None
        self.all_boxes = [[] for i in range(5)]
        self.generate_boxes()
        self.btn_workspace = None
        self.btn_box = None
        self.box_name = ''
        self.dummy_scan = False
        self.dummy_scan_done = False
        self.color_names = {
            self.__green: 'green',
            self.__blue: 'blue',
            self.__pink: 'pink',
            self.__orange: 'orange'
        }

        self.all_action_type = {'Human': 0, 'Assigned_to_Human': 1, 'Assigned_to_Robot': 2, 'Done': 3, 'Return': 4,
                                'Free': 5}

        self.color_list = {
            0: self.__green,
            1: self.__blue,
            2: self.__orange,
            3: self.__pink,
            4: 'white',
            self.__green: 0,
            self.__blue: 1,
            self.__orange: 2,
            self.__pink: 3,
            'white': 4
        }

        # Window.size = (self.width, self.height)
        Window.clearcolor = (1, 1, 1, 1)
        # Window.fullscreen = 'auto'
        Window.maximize()
        self.height = Window.size[1]
        self.width = Window.size[0]
        self.all_elements = {}
        self.gui_state = 'Free'
        self.create_workspaces()
        self.create_instruction()
        self.create_question_agent()
        self.create_question_yesno()
        self.create_msg_error()
        self.create_question_colors()
        self.create_finish_task()
        self.create_robot_decision()
        # self.assign_actions()
        self.initiate_camera()
        # self.update_camera()
        self.hide_question_colors()
        self.hide_question_agent()
        self.hide_question_yesno()
        self.hide_msg_error()
        self.hide_image_scan()

        # self.read_msg('0110')
        # time.sleep(10)
        # self.read_msg('2121')
        # time.sleep(3)
        # self.read_msg('1110')
        # self.v.present('sheet')
        #
        self.client = None
        self.start_socket()
        self.buttons_disabled = False
        time.sleep(1)
        col_chng = threading.Thread(target=self.color_flasher)
        col_chng.start()

    def create_workspaces(self):
        button = []
        btn_width = 70
        btn_height = 70
        buttons_gaps = 15
        view_padding = 15

        view_width = 2 * btn_width + 2 * view_padding + buttons_gaps
        view_height = 3 * btn_height + 2 * view_padding + 2 * buttons_gaps
        views_gaps = 25
        view1_x = (self.width - 4 * views_gaps - 3 * view_width)
        view1_y = 60
        btn_pos = [[btn_width + buttons_gaps, 0], [0, 0],
                   [0, btn_height + buttons_gaps],
                   [btn_width + buttons_gaps, btn_height + buttons_gaps],
                   [btn_width // 2 + buttons_gaps // 2, 2 * btn_height + 2 * buttons_gaps]]
        self.all_elements = {}
        for i in range(1, 5):
            with self.canvas:
                view_name = 'view_w' + str(i)

                Color(1., 1.0, 0, 0.3)
                view = Rectangle()
                view.pos = (view1_x - (i - 1) * view_width - (i - 1) * views_gaps, self.height - view1_y - view_height)
                view.size = (view_width, view_height)
                self.all_elements[view_name] = view
                # view.background_color = 'orange'
                # view.alpha = 0.3
                # self.v.add_subview(view)

                wlabel = Label()
                wlabel.width = 60
                wlabel.height = 34
                wlabel.font_size = 30.0
                wlabel.pos = (view.pos[0] + view.size[0] // 2 - wlabel.width // 2, view.pos[1] - wlabel.height)
                wlabel.text = 'W ' + str(i)
                wlabel.halign = 'center'
                wlabel.color = (0, 0, 0)
                self.add_widget(wlabel)

            for ii in range(1, 6):
                btn_name = 'w' + str(i) + 'b' + str(ii)
                label_name = 'label' + str(i) + str(ii)
                button = Button()
                button.pos = (
                    view.pos[0] + view_padding + btn_pos[ii - 1][0], view.pos[1] + view_padding + btn_pos[ii - 1][1])

                button.width = btn_width
                button.height = btn_height
                # button.texture = (1, 1, 1, 1)
                # button.border_width = 2
                # button.corner_radius = 5
                button.background_normal = ''
                button.background_disabled_normal = ''
                button.bind(on_press=self.btn_box_click)
                self.add_widget(button)
                self.all_elements[btn_name] = button

                label = Label()
                label.font_size = 30
                label.text = str(ii)
                label.pos = button.pos
                label.width = 34
                label.height = 34
                label.halign = 'center'
                label.color = (0, 0, 0, 1)
                self.add_widget(label)
                self.all_elements[label_name] = label

    def create_instruction(self):
        btn_name = 'instruct1'
        label_name = 'label_instruct1'
        btn_width = 55
        btn_height = 55
        button = Button()
        button.width = btn_width
        button.height = btn_height
        button.pos = (self.width - btn_width - 20, self.height - btn_height - 70)
        # button.pos = (self.width//2, self.height//2 - 30)
        button.background_normal = 'red'
        button.background_color = 'red'
        button.background_disabled_normal = ''
        self.add_widget(button)
        self.all_elements[btn_name] = button
        self.flashing_boxes[btn_name] = (self.__blue, self.__human_icon)

        label = Label()
        label.font_size = 20
        label.text = 'Assigned to you'
        label.pos = (button.pos[0] - 230, button.pos[1]-20)
        # label.width = 34
        # label.height = 34
        label.halign = 'right'
        label.color = (0, 0, 0, 1)
        label.text_size = (300, None)
        self.add_widget(label)
        self.all_elements[label_name] = label

        btn_name = 'instruct2'
        label_name = 'label_instruct2'
        button = Button()
        button.width = btn_width
        button.height = btn_height
        button.pos = (self.all_elements['instruct1'].pos[0], self.all_elements['instruct1'].pos[1] - btn_height - 10)
        button.background_normal = self.__robot_icon + '_blue' + '.jpg'
        button.border = (0, 0, 0, 0)
        # button.background_color = self.__blue
        button.background_disabled_normal = ''
        self.add_widget(button)
        self.all_elements[btn_name] = button


        label = Label()
        label.font_size = 20
        label.text = 'Assigned to Fetch'
        label.pos = (button.pos[0] - 230, button.pos[1]-20)
        # label.width = 34
        # label.height = 34
        label.halign = 'right'
        label.color = (0, 0, 0, 1)
        label.text_size = (300, None)
        self.add_widget(label)
        self.all_elements[label_name] = label

        btn_name = 'instruct3'
        label_name = 'label_instruct3'
        button = Button()
        button.width = btn_width
        button.height = btn_height
        button.pos = (self.all_elements['instruct2'].pos[0], self.all_elements['instruct2'].pos[1] - btn_height - 10)
        # button.pos = (self.width//2, self.height//2 - 30)
        button.background_normal = ''
        button.background_color = 'red'
        button.background_disabled_normal = ''
        self.add_widget(button)
        self.all_elements[btn_name] = button
        self.flashing_boxes[btn_name] = (self.__blue, self.__robot_icon)

        label = Label()
        label.font_size = 20
        label.text = 'Fetch\'s current task'
        label.pos = (button.pos[0] - 230, button.pos[1]-20)
        # label.width = 34
        # label.height = 34
        label.halign = 'right'
        label.color = (0, 0, 0, 1)
        label.text_size = (300, None)
        self.add_widget(label)
        self.all_elements[label_name] = label

        btn_name = 'instruct4'
        label_name = 'label_instruct4'
        button = Button()
        button.width = btn_width
        button.height = btn_height
        button.pos = (self.all_elements['instruct3'].pos[0], self.all_elements['instruct3'].pos[1] - btn_height - 10)
        # button.pos = (self.width//2, self.height//2 - 30)
        button.background_normal = ''
        button.background_color = 'red'
        button.background_disabled_normal = ''
        self.add_widget(button)
        self.all_elements[btn_name] = button
        self.flashing_boxes[btn_name] = (self.__blue, self.__return_icon)

        label = Label()
        label.font_size = 20
        label.text = 'Fetch is returning a block'
        label.pos = (button.pos[0] - 230, button.pos[1]-20)
        # label.width = 34
        # label.height = 34
        label.text_size = (300, None)
        label.halign = 'right'
        label.color = (0, 0, 0, 1)
        self.add_widget(label)
        self.all_elements[label_name] = label

    def create_question_agent(self):
        btn_w = 80
        btn_h = 80
        with self.canvas:
            self.all_elements['view_agent_color'] = Color(1, 0, 0, 1)
            view_agent = RoundedRectangle(radius=[(20, 20), (20, 20), (20, 20), (20, 20)])
            view_agent.size = (500, 250)
            view_agent.pos = (self.width // 2 - view_agent.size[0] // 2,
                              self.all_elements['view_w1'].pos[1] - self.all_elements['view_w1'].size[
                                  1] // 2 - 285 // 2 - 35)
        #
        label_agent = Label()
        label_agent.text = 'Who do you want to assign this task to?'
        label_agent.pos = (view_agent.pos[0] + 15, view_agent.pos[1] + view_agent.size[1] - 50)
        label_agent.width = view_agent.size[0] - 30
        label_agent.height = 35
        label_agent.font_size = 25
        # self.add_widget(label_agent)
        self.all_elements['label_agent'] = label_agent

        btn_agent_human = ToggleButton(text='Me', group='agents')
        btn_agent_robot = ToggleButton(text='Fetch', group='agents')
        btn_agent_select = RelativeLayout()
        btn_agent_select.width = 160
        btn_agent_select.height = 80

        btn_agent_human.pos = (view_agent.pos[0] + view_agent.size[0] // 2 - btn_agent_select.width - 30,
                               label_agent.pos[1] - label_agent.height - btn_h)
        btn_agent_robot.pos = (
            view_agent.pos[0] + view_agent.size[0] // 2 - btn_agent_select.width + 2 * btn_agent_human.width,
            label_agent.pos[1] - label_agent.height - btn_h)
        btn_agent_human.width = btn_w
        btn_agent_human.height = btn_h
        btn_agent_human.background_normal = ''
        btn_agent_human.background_color = '#B59C76'
        btn_agent_human.font_size = 25
        btn_agent_human.color = 'white'
        btn_agent_human.bind(on_press=self.btn_agent_human_click)

        btn_agent_robot.background_normal = ''
        btn_agent_robot.background_color = '#B59C76'
        btn_agent_robot.font_size = 25
        btn_agent_robot.color = 'white'
        btn_agent_robot.bind(on_press=self.btn_agent_robot_click)

        btn_agent_select.add_widget(btn_agent_human)
        btn_agent_select.add_widget(btn_agent_robot)
        self.all_elements['btn_agent_human'] = btn_agent_human
        self.all_elements['btn_agent_robot'] = btn_agent_robot

        # self.add_widget(btn_agent_select)
        self.all_elements['btn_agent_select'] = btn_agent_select

        btn_agent_select.border_width = 4

        #
        btn_agent_ok = Button()
        btn_agent_ok.text = 'OK'
        btn_agent_ok.width = 80
        btn_agent_ok.height = 60
        btn_agent_ok.pos = (view_agent.pos[0] + view_agent.size[0] // 2 - btn_agent_ok.width - 20,
                            view_agent.pos[1] + 10)
        btn_agent_ok.background_color = 'white'
        btn_agent_ok.background_normal = ''
        btn_agent_ok.color = 'black'
        btn_agent_ok.font_size = 20
        btn_agent_ok.bind(on_press=self.btn_agent_ok_click)
        # self.add_widget(btn_agent_ok)
        self.all_elements['btn_agent_ok'] = btn_agent_ok

        btn_agent_cancel = Button()
        btn_agent_cancel.text = 'Cancel'
        btn_agent_cancel.width = 80
        btn_agent_cancel.height = 60
        btn_agent_cancel.pos = (btn_agent_ok.pos[0] + btn_agent_ok.width + 20,
                                view_agent.pos[1] + 10)
        btn_agent_cancel.background_color = 'white'
        btn_agent_cancel.background_normal = ''
        btn_agent_cancel.color = 'black'
        btn_agent_cancel.font_size = 20
        btn_agent_cancel.bind(on_press=self.btn_agent_cancel_click)
        # self.add_widget(btn_agent_cancel)
        self.all_elements['btn_agent_cancel'] = btn_agent_cancel

    def create_question_colors(self):
        btn_color_gap = 20
        btn_y = 85
        btn_w = 80
        btn_h = 80
        with self.canvas:
            view_color_color = Color(0, 103, 103, 1)
            view_color = RoundedRectangle(radius=[(20, 20), (20, 20), (20, 20), (20, 20)])
            view_color.size = (750, 285)
            view_color.pos = (
                self.width // 2 - view_color.size[0] // 2,
                self.all_elements['view_w1'].pos[1] - self.all_elements['view_w1'].size[1] // 2 - 285 // 2 - 35)
        # view_color. = '#a8a8a8'
        self.all_elements['view_color'] = view_color
        self.all_elements['view_color_color'] = view_color_color

        btn_color_select = RelativeLayout()
        btn_color_select.width = 160
        btn_color_select.height = 80

        btn_green = ToggleButton(text='Green', group='colors')
        btn_green.width = btn_w
        btn_green.height = btn_h
        btn_green.pos = (view_color.pos[0] + btn_color_gap, view_color.pos[1] + btn_y + 30)
        btn_green.background_color = self.__green
        btn_green.background_normal = ''
        btn_green.background_down = ''

        btn_green.opacity = 1
        btn_green.font_size = 20
        btn_green.color = 'white'
        btn_green.bind(on_press=self.btn_green_click)
        btn_color_select.add_widget(btn_green)
        self.all_elements['btn_green'] = btn_green




        btn_blue = ToggleButton(text='Blue', group='colors')
        btn_blue.width = btn_w
        btn_blue.height = btn_h
        btn_blue.pos = (btn_green.pos[0] + 2 * btn_w + btn_color_gap, view_color.pos[1] + btn_y + 30)
        btn_blue.background_color = self.__blue
        btn_blue.background_normal = ''
        btn_blue.background_down = ''
        btn_blue.font_size = 20
        btn_blue.color = 'white'
        btn_blue.bind(on_press=self.btn_blue_click)
        btn_color_select.add_widget(btn_blue)
        self.all_elements['btn_blue'] = btn_blue

        btn_orange = ToggleButton(text='Orange', group='colors')
        btn_orange.width = btn_w
        btn_orange.height = btn_h
        btn_orange.pos = (btn_blue.pos[0] + 2 * btn_w + btn_color_gap, view_color.pos[1] + btn_y + 30)
        btn_orange.background_color = self.__orange
        btn_orange.background_normal = ''
        btn_orange.background_down = ''
        btn_orange.font_size = 20
        btn_orange.color = 'white'
        btn_orange.bind(on_press=self.btn_orange_click)
        btn_color_select.add_widget(btn_orange)
        self.all_elements['btn_orange'] = btn_orange

        btn_pink = ToggleButton(text='Pink', group='colors')
        btn_pink.width = btn_w
        btn_pink.height = btn_h
        btn_pink.pos = (btn_orange.pos[0] + 2 * btn_w + btn_color_gap, view_color.pos[1] + btn_y + 30)
        btn_pink.background_color = self.__pink
        btn_pink.background_normal = ''
        btn_pink.background_down = ''

        btn_pink.font_size = 20
        btn_pink.color = 'white'
        btn_pink.bind(on_press=self.btn_pink_click)
        btn_color_select.add_widget(btn_pink)
        # self.add_widget(btn_color_select)
        self.all_elements['btn_pink'] = btn_pink
        self.all_elements['btn_color_select'] = btn_color_select

        btn_color_ok = Button()
        btn_color_ok.text = 'OK'
        btn_color_ok.width = 80
        btn_color_ok.height = 60
        btn_color_ok.pos = (view_color.pos[0] + view_color.size[0] // 2 - btn_color_ok.size[0] - 20,
                            btn_blue.pos[1] - btn_blue.size[1] - 10)
        btn_color_ok.background_color = 'white'
        btn_color_ok.background_normal = ''
        btn_color_ok.color = 'black'
        btn_color_ok.font_size = 20
        btn_color_ok.bind(on_press=self.btn_color_ok_click)
        # self.add_widget(btn_color_ok)
        self.all_elements['btn_color_ok'] = btn_color_ok

        btn_color_cancel = Button()
        btn_color_cancel.text = 'Cancel'
        btn_color_cancel.width = 80
        btn_color_cancel.height = 60
        btn_color_cancel.pos = (
            view_color.pos[0] + view_color.size[0] // 2 + 20, btn_blue.pos[1] - btn_blue.size[1] - 10)
        btn_color_cancel.background_color = 'white'
        btn_color_cancel.background_normal = ''
        btn_color_cancel.color = 'black'
        btn_color_cancel.font_size = 20
        btn_color_cancel.bind(on_press=self.btn_color_cancel_click)
        # self.add_widget(btn_color_cancel)
        self.all_elements['btn_color_cancel'] = btn_color_cancel

        label_color = Label()
        label_color.text = 'Select the color for this spot.'
        label_color.pos = (
            view_color.pos[0] + 15 - view_color.size[0] // 4, view_color.pos[1] + view_color.size[1] - 50)
        label_color.size = (view_color.size[0] - 30, 35)
        label_color.font_size = 25
        # self.add_widget(label_color)
        self.all_elements['label_color'] = label_color

    def create_question_yesno(self):
        with self.canvas:
            self.all_elements['view_yesno_color'] = Color(1, 0, 0, 1)
            view_yesno = RoundedRectangle(radius=[(20, 20), (20, 20), (20, 20), (20, 20)])
            view_yesno.size = (480, 200)
            view_yesno.pos = (
                self.width // 2 - view_yesno.size[0] // 2,
                self.all_elements['view_w1'].pos[1] - self.all_elements['view_w1'].size[1])
            self.all_elements['view_yesno'] = view_yesno

        label_yesno = Label()
        label_yesno.text = 'tjkku'
        label_yesno.height = 70
        label_yesno.pos = (view_yesno.pos[0] + 30, view_yesno.pos[1] + view_yesno.size[1] - label_yesno.height)
        label_yesno.width = view_yesno.size[0] - 30

        # # label_yesno.number_of_lines = 2
        label_yesno.max_lines = 2
        label_yesno.font_size = 20
        label_yesno.halign = 'center'
        # self.add_widget(label_yesno)
        self.all_elements['label_yesno'] = label_yesno

        btn_dialog_yes = Button()
        btn_dialog_yes.text = 'Yes'
        btn_dialog_yes.width = 80
        btn_dialog_yes.height = 60
        btn_dialog_yes.pos = (view_yesno.pos[0] + view_yesno.size[0] // 2 - btn_dialog_yes.width - 30,
                              label_yesno.pos[1] - label_yesno.height)
        btn_dialog_yes.background_color = 'white'
        btn_dialog_yes.background_normal = ''
        btn_dialog_yes.color = 'black'
        btn_dialog_yes.font_size = 20
        btn_dialog_yes.bind(on_press=self.btn_yesno_yes)
        # self.add_widget(btn_dialog_yes)
        self.all_elements['btn_dialog_yes'] = btn_dialog_yes

        btn_dialog_no = Button()
        btn_dialog_no.text = 'No'
        btn_dialog_no.width = 80
        btn_dialog_no.height = 60
        btn_dialog_no.pos = (btn_dialog_yes.x + btn_dialog_yes.width + 40, label_yesno.pos[1] - label_yesno.height)
        btn_dialog_no.background_color = 'white'
        btn_dialog_no.background_normal = ''
        btn_dialog_no.color = 'black'
        btn_dialog_no.font_size = 20
        btn_dialog_no.bind(on_press=self.btn_yesno_no)
        # self.add_widget(btn_dialog_no)
        self.all_elements['btn_dialog_no'] = btn_dialog_no

    def create_msg_error(self):
        with self.canvas:
            self.all_elements['view_error_color'] = Color(1, 0, 0, 1)
            view_error = RoundedRectangle()
            view_error.size = (425, 150)
            view_error.pos = (
                self.width // 2 - view_error.size[0] // 2,
                self.all_elements['view_w1'].pos[1] - self.all_elements['view_w1'].size[1])
            self.all_elements['view_error'] = view_error
        #
        label_error = Label()
        label_error.text = 'jl;k;l'
        label_error.pos = (view_error.pos[0] + 30, view_error.pos[1] + view_error.size[1] - 50)
        label_error.width = view_error.size[0] - 40
        label_error.height = 35
        label_error.font_size = 20
        label_error.text_size = (400, None)
        label_error.halign = 'center'
        label_error.max_lines = 2
        # self.add_widget(label_error)
        self.all_elements['label_error'] = label_error
        #
        btn_error = Button()
        btn_error.text = 'Ok'
        btn_error.width = 80
        btn_error.height = 60
        btn_error.pos = (
            view_error.pos[0] + view_error.size[0] // 2 + btn_error.width // 2 - btn_error.width,
            label_error.pos[1] - label_error.height - btn_error.height)
        btn_error.background_color = 'white'
        btn_error.background_normal = ''
        btn_error.color = 'black'
        btn_error.font_size = 20
        btn_error.bind(on_press=self.btn_error_ok)
        # self.add_widget(btn_error)
        self.all_elements['btn_error'] = btn_error

    def create_finish_task(self):
        with self.canvas:
            self.all_elements['view_finish_cancel_color'] = Color(0, 0, 0, 0)
            view_finish_cancel = RoundedRectangle(radius=[(20, 20), (20, 20), (20, 20), (20, 20)])
            view_finish_cancel.size = (425, 200)
            view_finish_cancel.pos = (
                10,
                self.all_elements['view_w1'].pos[1] - self.all_elements['view_w1'].size[1] - 10)
            self.all_elements['view_finish_cancel'] = view_finish_cancel

        btn_finish = Button()
        btn_finish.text = 'Finished'
        btn_finish.width = 100
        btn_finish.height = 60
        btn_finish.pos = (view_finish_cancel.pos[0] + view_finish_cancel.size[0] // 2 - btn_finish.width - 10,
                          50 + view_finish_cancel.pos[1])
        btn_finish.background_color = 'white'
        btn_finish.background_normal = ''
        # 	btn_finish.border_width = 2
        # 	btn_finish.corner_radius = 5
        # 	btn_finish.border_color = 'black'
        btn_finish.color = 'black'
        btn_finish.font_size = 25
        # 	btn_finish.enabled = False
        # 	btn_finish.hidden = True
        btn_finish.bind(on_press=self.btn_finish)
        # self.add_widget(btn_finish)
        self.all_elements['btn_finish'] = btn_finish
        btn_cancel_action = Button()
        btn_cancel_action.text = 'Cancel'
        btn_cancel_action.width = 100
        btn_cancel_action.height = 60
        btn_cancel_action.pos = (
            view_finish_cancel.pos[0] + view_finish_cancel.size[0] // 2 + 10, 50 + view_finish_cancel.pos[1])
        btn_cancel_action.background_color = 'white'
        btn_cancel_action.background_normal = ''
        btn_cancel_action.color = 'black'
        btn_cancel_action.font_size = 25
        btn_cancel_action.bind(on_press=self.btn_cancel_action)
        self.all_elements['btn_cancel_action'] = btn_cancel_action
        #
        label_finish = Label()
        label_finish.text = 'gfgfgf'
        label_finish.width = 30
        label_finish.height = 35
        label_finish.text_size = (view_finish_cancel.size[0] - 30, None)
        label_finish.pos = (view_finish_cancel.pos[0] + view_finish_cancel.size[0] // 2,
                            btn_finish.pos[1] + btn_finish.height + label_finish.height + 10)
        label_finish.halign = 'center'
        label_finish.font_size = 20
        label_finish.color = 'black'
        label_finish.max_lines = 2
        # self.add_widget(label_finish)
        self.all_elements['label_finish'] = label_finish

    def create_robot_decision(self):
        image = Image()
        image.size = (640, 480)
        image.allow_stretch = True
        image.center_x = self.width // 2
        image.center_y = self.height // 2
        image.source = 'fetch2.png'
        self.all_elements['image_robot'] = image

    def initiate_camera(self):

        image = Image()
        image.size = (640, 480)
        image.center_x = self.width // 2
        image.center_y = 30 + image.size[1] // 2
        self.all_elements['image'] = image

        with self.canvas:
            image_box_color = Color(1, 1, 1, 0)
            image_box = RoundedRectangle()
            image_box.pos = (image.pos[0] - 20, image.pos[1] - 20)
            image_box.size = (680, 460)

        self.all_elements['image_box'] = image_box
        self.all_elements['image_box_color'] = image_box_color
        self.add_widget(image)

        img_cancel_button = Button()
        img_cancel_button.color = 'black'
        img_cancel_button.background_normal = ''
        img_cancel_button.size = (80, 40)
        img_cancel_button.background_color = self.dialog_box_color
        img_cancel_button.center_x = image.center_x
        img_cancel_button.center_y = image.center_y - image.size[1] // 2 + 20
        img_cancel_button.text = 'Cancel'
        img_cancel_button.font_size = 20
        img_cancel_button.bind(on_press=self.btn_cancel_image)
        self.all_elements['img_cancel_button'] = img_cancel_button
        self.add_widget(img_cancel_button)

        # opencv2 stuffs
        self.capture = cv2.VideoCapture(0)
        # cv2.namedWindow("CV2 Image")
        Clock.schedule_interval(self.update_camera, 1.0 / 33.0)
        # return layout
        self.dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
        self.parameters = aruco.DetectorParameters()
        self.id_counter = 0
        self.cur_id = -1
        self.prev_id = -1
        self.counter_add = 0
        # detector = aruco.ArucoDetector(dictionary, parameters)

    def update_camera(self, dt):
        # display image from cam in opencv window
        ret, frame = self.capture.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, self.dictionary, parameters=self.parameters)
        frame_markers = aruco.drawDetectedMarkers(frame.copy(), corners, ids)
        if ids is not None:
            ids = [i[0] for i in ids]
        if ids:
            if len(ids) == 1:

                self.cur_id = ids[0]
                if self.cur_id == self.prev_id:
                    self.id_counter += self.counter_add
                else:
                    self.id_counter = 1
                self.prev_id = self.cur_id
            else:
                self.id_counter = 0
        else:
            self.id_counter = 0
        # cv2.imshow("CV2 Image", frame_markers)
        # convert it to texture
        buf1 = cv2.flip(frame_markers, 0)
        buf = buf1.tostring()
        texture1 = Texture.create(size=(frame_markers.shape[1], frame_markers.shape[0]), colorfmt='bgr')
        # if working on RASPBERRY PI, use colorfmt='rgba' here instead, but stick with "bgr" in blit_buffer.
        texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        # display image from the texture
        self.all_elements['image'].texture = texture1
        if self.id_counter > 10 and self.id_counter < 15:
            if self.cur_id in list(range(61, 79)):
                border_col = self.__blue
            elif self.cur_id in list(range(43, 61)):
                border_col = self.__orange
            elif self.cur_id in list(range(25, 43)):
                border_col = self.__pink
            elif self.cur_id in list(range(79, 97)):
                border_col = self.__green
            self.all_elements['image_box_color'].rgba = get_color_from_hex(border_col)#(0, 1, 0, 1)
        elif self.id_counter >= 15:
            if self.dummy_scan:
                self.dummy_scan_done = True
                self.hide_image_scan()
                self.show_finish_cancel()
            else:
                self.send(str(self.cur_id))
                self.hide_image_scan()
                self.show_finish_cancel()
           # ''' while True:
           #      try:
           #          playsound('C:\\Users\\SIRRL\\Desktop\\pythonProject\\gui\\ding.wav')
           #          break
           #      except:
           #          pass'''
            time.sleep(0.1)


        else:
            self.all_elements['image_box_color'].rgba = (1, 1, 1, 0)

    def start_socket(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(100000)
        self.client.connect(ADDR)
        # self.client.settimeout(None)
        socket_thread = threading.Thread(target=self.receive)
        socket_thread.start()

    def receive(self):
        # client.settimeout(10000)
        connected = True
        while connected:
            msg_length = self.client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = self.client.recv(msg_length).decode(FORMAT)
                print(msg)
                if msg == DISCONNECT_MESSAGE:
                    connected = False
                else:
                    self.read_msg(msg)
        # self.send(DISCONNECT_MESSAGE)
        self.client.settimeout(1)
        self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()
        time.sleep(2)
        return False

    def generate_message(self, previous_action=None, action=None, workspace=None, box_number=None, color=None):
        if previous_action is None:
            previous_action = self.all_action_type[
                self.all_boxes[self.btn_workspace - 1][self.btn_box - 1].previous_state]
        if action is None:
            action = self.all_action_type[self.all_boxes[self.btn_workspace - 1][self.btn_box - 1].current_state]
        if workspace is None:
            workspace = self.btn_workspace
        if box_number is None:
            box_number = self.btn_box
        if color is None:
            clr = self.all_boxes[self.btn_workspace - 1][self.btn_box - 1].color
            color = self.color_list[clr]

        msg = str(previous_action) + str(action) + str(workspace) + str(box_number) + str(color)
        return msg

    def state_update(self, state, workspace=None, box=None, color=None):
        if workspace and box:
            ws = workspace - 1
            bx = box - 1
        else:
            ws = self.btn_workspace - 1
            bx = self.btn_box - 1

        tmp_curstate = self.all_boxes[ws][bx].current_state
        tmp_color = self.all_boxes[ws][bx].color

        if color:
            col = color
        else:
            col = tmp_color

        self.all_boxes[ws][bx].previous_state = tmp_curstate
        self.all_boxes[ws][bx].current_state = state
        self.all_boxes[ws][bx].color = col
        self.all_boxes[ws][bx].previous_color = tmp_color

    def send(self, msg=None):
        if msg is None:
            msg = self.generate_message()
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)

    def read_msg(self, msg):
        # message: action_type + workspace + box + color
        robot_action_list = {0: 'Robot', 1: 'Done', 2: 'Assigned_to_Human', 3: 'Assigned_to_Robot', 4: 'Reject',
                             5: 'Return', 6: 'Human_by_Robot', 8: 'Disable', 9: 'Enable'}
        action_type = robot_action_list[int(msg[0])]
        ws = int(msg[1])
        box = int(msg[2])
        msg_box_name = 'w' + str(ws) + 'b' + str(box)
        color = self.color_list[int(msg[3])]
        # tmp_curstate = self.all_boxes[ws - 1][box - 1].current_state
        if action_type == 'Disable':
            self.buttons_disabled = True
            if self.gui_state == 'Color':
                Clock.schedule_once(self.btn_color_cancel_click)
            elif self.gui_state == 'Agent':
                Clock.schedule_once(self.btn_agent_cancel_click)
            elif self.gui_state == 'YesNo':
                Clock.schedule_once(self.btn_yesno_no)
            elif self.gui_state == 'Error':
                Clock.schedule_once(self.btn_error_ok)
            elif self.gui_state == 'Finish':
                Clock.schedule_once(self.stop_finish_button)
            elif self.gui_state == 'Image':
                Clock.schedule_once(self.stop_image)
            Clock.schedule_once(self.show_robot)

        if action_type == 'Enable':
            # self.all_elements['image_robot'].source = 'return.jpg'
            Clock.schedule_once(self.remove_robot)
            if self.gui_state == 'Image':
                Clock.schedule_once(self.restart_image)
            elif self.gui_state == 'Finish':
                Clock.schedule_once(self.restart_finish_button)
            else:
                self.buttons_disabled = False

        elif action_type in ['Robot', 'Human_by_Robot', 'Assigned_to_Robot']:
            self.state_update(state='Robot', workspace=ws, box=box, color=color)
            # self.all_boxes[ws - 1][box - 1].current_state = 'Robot'
            # self.color_changer(msg_box_name, color, ws, box)
            self.flashing_boxes[msg_box_name] = (color, self.__robot_icon)
            # self.icon_changer(msg_box_name, 'fetch.png')

        elif action_type == 'Done':
            if self.all_boxes[ws - 1][box - 1].previous_state == 'Done':
                self.state_update(state='Free', workspace=ws, box=box, color=color)
                # self.color_changer(msg_box_name, color, ws, box)
                # self.icon_changer(msg_box_name)

            else:
                self.state_update(state='Done', workspace=ws, box=box, color=color)
            self.flashing_boxes.pop(msg_box_name)
            time.sleep(1)
            self.icon_changer(msg_box_name)
            self.color_changer(msg_box_name, color, ws, box)



        elif action_type == 'Assigned_to_Human':
            self.state_update(state='Assigned_to_Human', workspace=ws, box=box, color=color)
            # self.color_changer(msg_box_name, color, ws, box)
            self.flashing_boxes[msg_box_name] = (color, self.__human_icon)
            print('assigned')
            # self.icon_changer(msg_box_name, self.__human_icon)

        elif action_type == 'Reject':
            self.state_update(state='Free', workspace=ws, box=box, color=color)
            self.icon_changer(msg_box_name)
            self.color_changer(msg_box_name, color, ws, box)

        elif action_type == 'Return':
            self.state_update(state='Return', workspace=ws, box=box, color=color)
            self.flashing_boxes[msg_box_name] = (self.all_boxes[ws - 1][box - 1].previous_color, self.__return_icon)
            # self.icon_changer(box_name=msg_box_name, icon=self.__return_icon, color=color)
            # self.color_changer(msg_box_name, color, ws, box)

    def generate_boxes(self):
        for i in range(0, 4):
            for j in range(0, 5):
                self.all_boxes[i].append(Box(workspace=i + 1, box_number=j + 1))

    def disable_enable_buttons(self, action='disable', excepted_buttons=[]):
        if action == 'disable':
            tf = True
        else:
            tf = False

        for i in range(1, 5):
            for ii in range(1, 6):
                btn_name = 'w' + str(i) + 'b' + str(ii)
                if btn_name not in excepted_buttons:
                    self.all_elements[btn_name].disabled = tf
                    self.all_elements[btn_name].background_disabled_normal = self.all_elements[
                        btn_name].background_normal

    def show_question_colors(self):
        self.all_elements['view_color_color'].rgba = self.dialog_box_color
        # self.all_elements['label_color'].opacity = 1
        # self.all_elements['btn_color_select'].opacity = 1
        # self.all_elements['btn_green'].opacity = 1
        # self.all_elements['btn_orange'].opacity = 1
        # self.all_elements['btn_blue'].opacity = 1
        # self.all_elements['btn_pink'].opacity = 1
        # self.all_elements['btn_color_ok'].opacity = 1
        # self.all_elements['btn_color_cancel'].opacity = 1

        # self.all_elements['label_color'].disabled = False
        # self.all_elements['btn_color_select'].disabled = False
        # self.all_elements['btn_green'].disabled = False
        # self.all_elements['btn_orange'].disabled = False
        # self.all_elements['btn_blue'].disabled = False
        # self.all_elements['btn_pink'].disabled = False
        self.all_elements['btn_color_ok'].disabled = True
        self.all_elements['btn_green'].state = 'normal'
        self.all_elements['btn_orange'].state = 'normal'
        self.all_elements['btn_pink'].state = 'normal'
        self.all_elements['btn_blue'].state = 'normal'

        self.all_elements['btn_green'].background_color = self.__green
        self.all_elements['btn_orange'].background_color = self.__orange
        self.all_elements['btn_pink'].background_color = self.__pink
        self.all_elements['btn_blue'].background_color = self.__blue
        # self.all_elements['btn_color_cancel'].disabled = False

        self.add_widget(self.all_elements['label_color'])
        self.add_widget(self.all_elements['btn_color_select'])
        # self.add_widget(self.all_elements['btn_green'])
        # self.add_widget(self.all_elements['btn_orange'])
        # self.add_widget(self.all_elements['btn_blue'])
        # self.add_widget(self.all_elements['btn_pink'])
        self.add_widget(self.all_elements['btn_color_ok'])
        self.add_widget(self.all_elements['btn_color_cancel'])
        self.buttons_disabled = True
        self.gui_state = 'Color'

    def hide_question_colors(self):
        self.all_elements['view_color_color'].rgba = (0, 0, 0, 0)
        # self.all_elements['label_color'].opacity = 0
        # self.all_elements['btn_color_select'].opacity = 0
        # self.all_elements['btn_green'].opacity = 0
        # self.all_elements['btn_orange'].opacity = 0
        # self.all_elements['btn_blue'].opacity = 0
        # self.all_elements['btn_pink'].opacity = 0
        # self.all_elements['btn_color_ok'].opacity = 0
        # self.all_elements['btn_color_cancel'].opacity = 0

        # self.all_elements['label_color'].disabled = True
        # self.all_elements['btn_color_select'].disabled = True
        # self.all_elements['btn_green'].disabled = True
        # self.all_elements['btn_orange'].disabled = True
        # self.all_elements['btn_blue'].disabled = True
        # self.all_elements['btn_pink'].disabled = True
        # self.all_elements['btn_color_ok'].disabled = True
        # self.all_elements['btn_color_cancel'].disabled = True

        self.remove_widget(self.all_elements['label_color'])
        self.remove_widget(self.all_elements['btn_color_select'])
        # self.remove_widget(self.all_elements['btn_green'])
        # self.remove_widget(self.all_elements['btn_orange'])
        # self.remove_widget(self.all_elements['btn_blue'])
        # self.remove_widget(self.all_elements['btn_pink'])
        self.remove_widget(self.all_elements['btn_color_ok'])
        self.remove_widget(self.all_elements['btn_color_cancel'])
        self.buttons_disabled = False
        self.gui_state = 'Free'

    def show_question_agent(self):
        self.all_elements['view_agent_color'].rgba = self.dialog_box_color
        # self.all_elements['label_agent'].opacity = 1
        # self.all_elements['btn_agent_select'].opacity = 1
        # self.all_elements['btn_agent_human'].opacity = 1
        # self.all_elements['btn_agent_robot'].opacity = 1
        # self.all_elements['btn_agent_ok'].opacity = 1
        # self.all_elements['btn_agent_cancel'].opacity = 1
        #
        # self.all_elements['label_agent'].disabled = False
        # self.all_elements['btn_agent_select'].disabled = False
        # self.all_elements['btn_agent_human'].disabled = False
        # self.all_elements['btn_agent_robot'].disabled = False
        # self.all_elements['btn_agent_ok'].disabled = True
        # self.all_elements['btn_agent_cancel'].disabled = False
        self.all_elements['btn_agent_human'].state = 'normal'
        self.all_elements['btn_agent_robot'].state = 'normal'
        self.add_widget(self.all_elements['label_agent'])
        self.add_widget(self.all_elements['btn_agent_select'])
        # self.add_widget(self.all_elements['btn_agent_human'])
        # self.add_widget(self.all_elements['btn_agent_robot'])
        self.add_widget(self.all_elements['btn_agent_ok'])
        self.add_widget(self.all_elements['btn_agent_cancel'])
        self.buttons_disabled = True
        self.gui_state = 'Agent'

    def hide_question_agent(self):
        self.all_elements['view_agent_color'].rgba = (0, 0, 0, 0)
        # self.all_elements['label_agent'].opacity = 0
        # self.all_elements['btn_agent_select'].opacity = 0
        # self.all_elements['btn_agent_human'].opacity = 0
        # self.all_elements['btn_agent_robot'].opacity = 0
        # self.all_elements['btn_agent_ok'].opacity = 0
        # self.all_elements['btn_agent_cancel'].opacity = 0

        # self.all_elements['label_agent'].disabled = True
        # self.all_elements['btn_agent_select'].disabled = True
        # self.all_elements['btn_agent_human'].disabled = True
        # self.all_elements['btn_agent_robot'].disabled = True
        self.all_elements['btn_agent_ok'].disabled = True
        # self.all_elements['btn_agent_cancel'].disabled = True

        self.remove_widget(self.all_elements['label_agent'])
        self.remove_widget(self.all_elements['btn_agent_select'])
        # self.remove_widget(self.all_elements['btn_agent_human'])
        # self.remove_widget(self.all_elements['btn_agent_robot'])
        self.remove_widget(self.all_elements['btn_agent_ok'])
        self.remove_widget(self.all_elements['btn_agent_cancel'])
        self.buttons_disabled = False
        self.gui_state = 'Free'

    def show_question_yesno(self, btn_state):
        if btn_state == 'Assigned_to_Robot':
            self.all_elements['label_yesno'].text = 'Do you want to cancel this assignment?'
        elif btn_state == 'Assigned_to_Human':
            self.all_elements[
                'label_yesno'].text = 'Do you want to do this task assigned by Fetch?'
        elif btn_state == 'Human':
            self.all_elements['label_yesno'].text = 'Do you want to select another box?'
        elif btn_state == 'Done':
            self.all_elements['label_yesno'].text = 'Do you want to return this block?'
        #
        self.all_elements['view_yesno_color'].rgba = self.dialog_box_color
        # self.all_elements['btn_dialog_yes'].opacity = 1
        # self.all_elements['btn_dialog_no'].opacity = 1
        # self.all_elements['label_yesno'].opacity = 1
        #
        # self.all_elements['btn_dialog_yes'].disabled = False
        # self.all_elements['btn_dialog_no'].disabled = False
        # self.all_elements['label_yesno'].disabled = False

        self.add_widget(self.all_elements['btn_dialog_yes'])
        self.add_widget(self.all_elements['btn_dialog_no'])
        self.add_widget(self.all_elements['label_yesno'])
        self.buttons_disabled = True
        self.gui_state = 'YesNo'

    def hide_question_yesno(self):
        self.all_elements['view_yesno_color'].rgba = (0, 0, 0, 0)
        # self.all_elements['btn_dialog_yes'].opacity = 0
        # self.all_elements['btn_dialog_no'].opacity = 0
        # self.all_elements['label_yesno'].opacity = 0

        # self.all_elements['btn_dialog_yes'].disabled = True
        # self.all_elements['btn_dialog_no'].disabled = True
        # self.all_elements['label_yesno'].disabled = True

        self.remove_widget(self.all_elements['btn_dialog_yes'])
        self.remove_widget(self.all_elements['btn_dialog_no'])
        self.remove_widget(self.all_elements['label_yesno'])
        self.buttons_disabled = False
        self.gui_state = 'Free'

    def hide_msg_error(self):
        self.all_elements['view_error_color'].rgba = (0, 0, 0, 0)
        # self.all_elements['btn_error'].opacity = 0
        # self.all_elements['label_error'].opacity = 0
        #
        # self.all_elements['btn_error'].disabled = True
        # self.all_elements['label_error'].disabled = True

        self.remove_widget(self.all_elements['btn_error'])
        self.remove_widget(self.all_elements['label_error'])
        self.buttons_disabled = False
        self.gui_state = 'Free'

    def show_msg_error(self, error_type, precedence=None):
        if error_type == 'precedence':
            lb_txt = ''
            for i in precedence:
                lb_txt += str(i) + ', '
            if len(precedence) > 1:
                self.all_elements['label_error'].text = 'Tasks' + lb_txt[0:-2] + ' need to be completed first.'
            else:
                self.all_elements['label_error'].text = 'Task ' + lb_txt[0:-2] + ' needs to be completed first.'
        else:
            self.all_elements['label_error'].text = 'Fetch is currently doing this action. Please select another spot.'

        # self.all_elements['btn_error'].disabled = False
        # self.all_elements['label_error'].disabled = False

        self.all_elements['view_error_color'].rgba = self.dialog_box_color
        # self.all_elements['btn_error'].opacity = 1
        # self.all_elements['label_error'].opacity = 1

        self.add_widget(self.all_elements['btn_error'])
        self.add_widget(self.all_elements['label_error'])
        self.buttons_disabled = True
        self.gui_state = 'Error'

    def show_finish_cancel(self):
        self.all_elements['view_finish_cancel_color'].rgba = self.dialog_box_color
        # self.all_elements['btn_finish'].disabled = False
        # self.all_elements['btn_finish'].opacity = 1
        # self.all_elements['btn_cancel_action'].disabled = False
        # self.all_elements['btn_cancel_action'].opacity = 1
        # self.all_elements['label_finish'].disabled = False
        # self.all_elements['label_finish'].opacity = 1
        # self.all_elements['label_finish'].text = text

        self.add_widget(self.all_elements['btn_finish'])
        self.add_widget(self.all_elements['btn_cancel_action'])
        self.add_widget(self.all_elements['label_finish'])
        self.buttons_disabled = True
        self.gui_state = 'Finish'

    def hide_finish_cancel(self):
        self.all_elements['view_finish_cancel_color'].rgba = (0, 0, 0, 0)
        # self.all_elements['btn_finish'].disabled = True
        # self.all_elements['btn_finish'].opacity = 1
        # self.all_elements['btn_cancel_action'].disabled = True
        # self.all_elements['btn_cancel_action'].opacity = 1
        self.all_elements['label_finish'].text = ''
        # self.all_elements['label_finish'].disabled = True
        # self.all_elements['label_finish'].opacity = 1

        self.remove_widget(self.all_elements['btn_finish'])
        self.remove_widget(self.all_elements['btn_cancel_action'])
        self.remove_widget(self.all_elements['label_finish'])
        self.buttons_disabled = False
        self.gui_state = 'Free'

    def hide_image_scan(self):
        self.remove_widget(self.all_elements['img_cancel_button'])
        self.remove_widget(self.all_elements['image'])
        self.all_elements['image_box_color'].rgba = (0, 0, 0, 0)
        self.id_counter = 0
        self.cur_id = -1
        self.prev_id = -1
        self.counter_add = 0
        self.buttons_disabled = False
        self.gui_state = 'Free'

    def show_image_scan(self):
        self.add_widget(self.all_elements['img_cancel_button'])
        self.add_widget(self.all_elements['image'])
        self.counter_add = 1
        self.buttons_disabled = True
        self.gui_state = 'Image'

    def stop_finish_button(self, sender):
        self.all_elements['btn_finish'].disabled = True
        self.all_elements['btn_cancel_action'].disabled = True
        time.sleep(1)

    def stop_image(self, sender):
        self.counter_add = 0
        self.all_elements['image'].disabled = True
        time.sleep(1)

    def restart_finish_button(self, sender):
        self.all_elements['btn_finish'].disabled = False
        self.all_elements['btn_cancel_action'].disabled = False
        time.sleep(1)

    def restart_image(self, sender):
        self.counter_add = 1
        self.all_elements['image'].disabled = False
        time.sleep(1)

    def show_robot(self, sender):
        self.add_widget(self.all_elements['image_robot'])

    def remove_robot(self, sender):
        self.remove_widget(self.all_elements['image_robot'])

    def is_precedence_constraint(self, box):
        ws = box.workspace
        bn = box.number
        done = True
        precedence = []

        if bn > 1:
            for i in range(0, bn - 1):
                done = done and (self.all_boxes[ws - 1][i].current_state == 'Done' or
                                 self.all_boxes[ws - 1][i].current_state == 'Robot')
                if self.all_boxes[ws - 1][i].current_state != 'Done' and self.all_boxes[ws - 1][
                    i].current_state != 'Robot':
                    precedence.append(i + 1)
        return done, precedence

    def btn_box_click(self, sender):
        if not self.buttons_disabled:
            sender_name = list(self.all_elements.keys())[list(self.all_elements.values()).index(sender)]
            self.btn_workspace = int(sender_name[1])
            self.btn_box = int(sender_name[3])
            ww = self.btn_workspace - 1
            bb = self.btn_box - 1
            self.box_name = 'w' + str(self.btn_workspace) + 'b' + str(self.btn_box)
            self.buttons_disabled = True
            cr_state = self.all_boxes[ww][bb].current_state
            if cr_state == 'Free':
                done, precedence = self.is_precedence_constraint(self.all_boxes[ww][bb])
                if done:
                    self.show_question_colors()
                else:
                    self.show_msg_error(error_type='precedence', precedence=precedence)
            elif cr_state == 'Assigned_to_Robot':
                self.show_question_yesno('Assigned_to_Robot')
            elif cr_state == 'Assigned_to_Human':
                self.show_question_yesno('Assigned_to_Human')
            elif cr_state == 'Human':
                self.show_question_yesno('Human')
            elif cr_state == 'Done':
                self.show_question_yesno('Done')
            elif cr_state == 'Robot':
                self.show_msg_error(error_type='robot')

    def btn_green_click(self, sender):
        if self.all_elements['btn_green'].state == 'down':
            self.selected_color = self.__green
            self.all_elements['btn_color_ok'].disabled = False
            self.all_elements['btn_green'].background_color = '#026a5b'
            self.all_elements['btn_blue'].background_color = self.__blue
            self.all_elements['btn_pink'].background_color = self.__pink
            self.all_elements['btn_orange'].background_color = self.__orange
            # self.all_elements['btn_green'].opacity = 0.5
            # self.all_elements['btn_blue'].opacity = 1
            # self.all_elements['btn_pink'].opacity = 1
            # self.all_elements['btn_orange'].opacity = 1
        else:
            self.selected_color = None
            self.all_elements['btn_color_ok'].disabled = True
            self.all_elements['btn_green'].background_color = self.__green
            # self.all_elements['btn_green'].opacity = 1
        # self.all_elements['btn_green'].disabled = True
        # print(self.all_elements['btn_green'].background_disabled_normal)
        # self.all_elements['btn_green'].background_color = self.__green
        # # self.all_elements['btn_green'].opacity= 0
        # self.all_elements['btn_orange'].disabled = False
        # self.all_elements['btn_blue'].disabled = False
        # self.all_elements['btn_pink'].disabled = False

    def btn_blue_click(self, sender):
        if self.all_elements['btn_blue'].state == 'down':
            self.selected_color = self.__blue
            self.all_elements['btn_color_ok'].disabled = False
            self.all_elements['btn_blue'].background_color = '#092448'
            self.all_elements['btn_green'].background_color = self.__green
            self.all_elements['btn_pink'].background_color = self.__pink
            self.all_elements['btn_orange'].background_color = self.__orange
            # self.all_elements['btn_green'].opacity = 1
            # self.all_elements['btn_blue'].opacity = 0.5
            # self.all_elements['btn_pink'].opacity = 1
            # self.all_elements['btn_orange'].opacity = 1
        else:
            self.selected_color = None
            self.all_elements['btn_color_ok'].disabled = True
            self.all_elements['btn_blue'].background_color = self.__blue
            # self.all_elements['btn_blue'].opacity = 1
        # self.selected_color = self.__blue
        # self.all_elements['btn_color_ok'].disabled = False
        # self.all_elements['btn_green'].disabled = False
        # self.all_elements['btn_orange'].disabled = False
        # self.all_elements['btn_blue'].disabled = True
        # self.all_elements['btn_pink'].disabled = False

    def btn_pink_click(self, sender):
        if self.all_elements['btn_pink'].state == 'down':
            self.selected_color = self.__pink
            self.all_elements['btn_color_ok'].disabled = False
            self.all_elements['btn_pink'].background_color = '#75324b'
            self.all_elements['btn_blue'].background_color = self.__blue
            self.all_elements['btn_green'].background_color = self.__green
            self.all_elements['btn_orange'].background_color = self.__orange
            # self.all_elements['btn_green'].opacity = 1
            # self.all_elements['btn_blue'].opacity = 1
            # self.all_elements['btn_pink'].opacity = 0.5
            # self.all_elements['btn_orange'].opacity = 1
        else:
            self.selected_color = None
            self.all_elements['btn_color_ok'].disabled = True
            self.all_elements['btn_pink'].background_color = self.__pink
            # self.all_elements['btn_pink'].opacity = 1
        # self.selected_color = self.__pink
        # self.all_elements['btn_color_ok'].disabled = False
        # self.all_elements['btn_green'].disabled = False
        # self.all_elements['btn_orange'].disabled = False
        # self.all_elements['btn_blue'].disabled = False
        # self.all_elements['btn_pink'].disabled = True

    def btn_orange_click(self, sender):
        if self.all_elements['btn_orange'].state == 'down':
            self.selected_color = self.__orange
            self.all_elements['btn_color_ok'].disabled = False
            self.all_elements['btn_orange'].background_color = '#be5f25'
            self.all_elements['btn_blue'].background_color = self.__blue
            self.all_elements['btn_green'].background_color = self.__green
            self.all_elements['btn_pink'].background_color = self.__pink
            # self.all_elements['btn_green'].opacity = 1
            # self.all_elements['btn_blue'].opacity = 1
            # self.all_elements['btn_pink'].opacity = 1
            # self.all_elements['btn_orange'].opacity = 0.5
        else:
            self.selected_color = None
            self.all_elements['btn_color_ok'].disabled = True
            self.all_elements['btn_orange'].background_color = self.__orange
            # self.all_elements['btn_orange'].opacity = 1
        # self.selected_color = self.__orange
        # self.all_elements['btn_color_ok'].disabled = False
        # self.all_elements['btn_green'].disabled = False
        # self.all_elements['btn_orange'].disabled = True
        # self.all_elements['btn_blue'].disabled = False
        # self.all_elements['btn_pink'].disabled = False

    def btn_color_ok_click(self, sender):
        self.hide_question_colors()
        self.show_question_agent()

    def btn_color_cancel_click(self, sender):
        self.hide_question_colors()
        self.disable_enable_buttons(action='enable')
        self.selected_color = None

    def btn_agent_ok_click(self, sender):
        # agent_ind = self.all_elements['btn_agent_select'].selected_index
        tb = next((t for t in ToggleButton.get_widgets('agents') if t.state == 'down'), None)
        agent_ind = tb.text if tb else None
        ww = self.btn_workspace - 1
        bb = self.btn_box - 1
        if agent_ind == 'Me':
            self.selected_agent = 'Human'
            self.state_update(state='Human', color=self.selected_color)
            self.color_changer(self.box_name, self.selected_color)
            block_color = self.color_names[self.selected_color]
            label_text = 'Placing a ' + block_color + ' block on workspace #' + str(
                self.btn_workspace) + ' and spot #' + str(self.btn_box)
            self.all_elements['label_finish'].text = label_text
            # self.show_finish_cancel(label_text)
            self.send()
            self.hide_question_agent()
            self.dummy_scan = False
            self.show_image_scan()

        else:
            self.selected_agent = 'Fetch'
            self.state_update(state='Assigned_to_Robot', color=self.selected_color)
            # self.color_changer(self.box_name, self.selected_color)
            self.icon_changer(self.box_name, self.__robot_icon, self.selected_color)
            self.disable_enable_buttons(action='enable')
            self.send()
            self.hide_question_agent()



    def btn_agent_cancel_click(self, sender):
        self.selected_color = None
        self.selected_agent = None
        self.hide_question_agent()
        self.disable_enable_buttons(action='enable')

    def btn_agent_robot_click(self, sender):
        if self.all_elements['btn_agent_robot'].state == 'down':
            self.all_elements['btn_agent_ok'].disabled = False
        else:
            self.all_elements['btn_agent_ok'].disabled = True

    def btn_agent_human_click(self, sender):
        if self.all_elements['btn_agent_human'].state == 'down':
            self.all_elements['btn_agent_ok'].disabled = False
        else:
            self.all_elements['btn_agent_ok'].disabled = True

    def btn_yesno_yes(self, sender):
        ww = self.btn_workspace - 1
        bb = self.btn_box - 1
        cr_state = self.all_boxes[ww][bb].current_state
        pr_state = self.all_boxes[ww][bb].previous_state
        if cr_state == 'Assigned_to_Robot':
            self.state_update(state='Free', color='white')
            # self.all_boxes[ww][bb].current_state = 'Free'
            self.color_changer(self.box_name, 'white')
            self.icon_changer(self.box_name)
            self.disable_enable_buttons(action='enable')
        elif cr_state == 'Assigned_to_Human':
            block_color = self.color_names[self.all_boxes[ww][bb].color]
            self.dummy_scan = True
            self.dummy_scan_done = False
            self.state_update(state='Human')
            # self.all_boxes[ww][bb].current_state = 'Human'
            self.flashing_boxes.pop(self.box_name)
            self.icon_changer(self.box_name, '')
            label_text = 'Placing a ' + block_color + ' block on workspace #' + str(
                self.btn_workspace) + ' and spot #' + str(self.btn_box)
            self.all_elements['label_finish'].text = label_text
            self.show_image_scan()
            # self.show_finish_cancel()

        elif cr_state == 'Human':
            if pr_state == 'Assigned_to_Human':
                self.state_update(state='Assigned_to_Human')
                self.flashing_boxes[self.box_name] = (self.all_boxes[ww][bb].color, self.__human_icon)
            else:
                self.state_update(state='Free', color='white')
                self.color_changer(self.box_name, 'white')
            self.disable_enable_buttons(action='enable')
            self.hide_finish_cancel()

        elif cr_state == 'Done':
            self.state_update(state='Return')
            block_color = self.color_names[self.all_boxes[ww][bb].color]
            label_text = 'Returning the ' + block_color + ' block on workspace #' + str(
                self.btn_workspace) + ' and spot #' + str(self.btn_box)
            # self.all_boxes[ww][bb].previous_color = self.all_boxes[ww][bb].color
            self.all_elements['label_finish'].text = label_text
            self.show_finish_cancel()
            self.color_changer(self.box_name, 'white')

        # self.all_boxes[ww][bb].previous_state = cr_state
        self.send()
        self.hide_question_yesno()

    def btn_yesno_no(self, sender):
        self.hide_question_yesno()
        self.disable_enable_buttons(action='enable')

    def btn_error_ok(self, sender):
        self.hide_msg_error()
        self.disable_enable_buttons(action='enable')

    def btn_finish(self, sender):
        cr_state = self.all_boxes[self.btn_workspace - 1][self.btn_box - 1].current_state
        if cr_state == 'Return':
            self.state_update(state='Free', color='white')
        elif cr_state == 'Human':
            self.state_update(state='Done')

        self.color_changer(box_name=self.box_name, color=self.all_boxes[self.btn_workspace - 1][self.btn_box - 1].color)

        self.send()
        self.hide_finish_cancel()
        self.disable_enable_buttons(action='enable')

    def btn_cancel_action(self, sender):
        ww = self.btn_workspace - 1
        bb = self.btn_box - 1
        cr_state = self.all_boxes[ww][bb].current_state
        pr_state = self.all_boxes[ww][bb].previous_state
        if cr_state == 'Human':
            if pr_state == 'Assigned_to_Human':
                self.state_update(state='Assigned_to_Human')
                self.flashing_boxes[self.box_name] = (self.all_boxes[ww][bb].color, self.__human_icon)
            else:
                self.state_update(state='Free', color='white')
                self.color_changer(self.box_name, 'white')
        elif cr_state == 'Return':
            self.state_update(state=pr_state)
            self.color_changer(self.box_name, self.all_boxes[ww][bb].previous_color)

        self.send()
        self.hide_finish_cancel()
        self.disable_enable_buttons(action='enable')

    def btn_cancel_image(self, sender):
        ww = self.btn_workspace - 1
        bb = self.btn_box - 1
        cr_state = self.all_boxes[ww][bb].current_state
        pr_state = self.all_boxes[ww][bb].previous_state
        if cr_state == 'Human':
            if pr_state == 'Assigned_to_Human':
                self.state_update(state='Assigned_to_Human')
                self.flashing_boxes[self.box_name] = (self.all_boxes[ww][bb].color, self.__human_icon)
            else:
                self.state_update(state='Free', color='white')
                self.color_changer(self.box_name, 'white')

        self.send()
        self.hide_image_scan()
        # self.disable_enable_buttons(action='enable')

    def color_flasher(self):
        while True:
            if self.flashing_boxes:
                fl_bx = dict(self.flashing_boxes)
                for box in fl_bx:
                    self.all_elements[box].background_normal = fl_bx[box][1] + '_' + self.color_names[
                        fl_bx[box][0]] + '.jpg'
                    self.all_elements[box].border = (0, 0, 0, 0)
                time.sleep(0.8)
                fl_bx = dict(self.flashing_boxes)
                for box in fl_bx:
                    self.all_elements[box].background_normal = fl_bx[box][1] + '.jpg'
                    self.all_elements[box].background_color = 'white'
                    self.all_elements[box].border = (0, 0, 0, 0)
                    self.all_elements[box].color = 'black'
                time.sleep(0.8)
                for box in fl_bx:
                    self.all_elements[box].background_normal = fl_bx[box][1] + '_' + fl_bx[box][0] + '.jpg'
                    self.all_elements[box].border = (0, 0, 0, 0)
                    self.all_elements[box].color = 'ffffff'

    def icon_changer(self, box_name, icon=None, color=None, workspace=None, box=None):
        if icon:
            if color:
                self.all_elements[box_name].background_normal = icon + '_' + self.color_names[color] + '.jpg'
                if workspace is None:
                    self.all_boxes[self.btn_workspace - 1][self.btn_box - 1].color = color
                else:
                    self.all_boxes[workspace - 1][box - 1].color = color
            else:
                self.all_elements[box_name].background_normal = icon + '.jpg'
            self.all_elements[box_name].border = (0, 0, 0, 0)
        else:
            self.all_elements[box_name].background_normal = ''
            # self.all_elements[box_name].background_normal = ''

    def color_changer(self, box_name, color, workspace=None, box=None):
        self.all_elements[box_name].background_color = color
        self.all_elements[box_name].background_normal = ''
        # if workspace is None:
        #     self.all_boxes[self.btn_workspace - 1][self.btn_box - 1].color = color
        # else:
        #     self.all_boxes[workspace - 1][box - 1].color = color


#


myapp = MyApp().run()
cv2.destroyAllWindows()
