import io
import queue
import traceback

import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
import PySimpleGUI as sg
from PIL import Image

class Application:
    def __init__(self):
        self.myAWSIoTMQTTClient = None
        self.gui_queue = queue.Queue()

        middle_font = ('Helvetica', 14)
        context_font = ('Helvetica', 12)
        sg.theme('DarkGrey')

        col1 = [[sg.Column([
            [sg.Frame('', [[sg.Column([
                [sg.Text('Client Id:', font=middle_font)],
                [sg.Input('HR31', key='_CLIENTID_IN_', size=(19, 1), font=context_font),
                 sg.Button('Приєднати', key='_CONNECT_BTN_', size=(0, 1),font=context_font)],
                [sg.Text('Notes:', font=middle_font)],
                [sg.Multiline(key='_NOTES_', autoscroll=True, size=(26, 34), font=context_font, )],
            ], size=(300, 640), pad=(0, 0))]], font=middle_font)], ], pad=(0, 0), element_justification='c')]]

        col2 = [[sg.Column([[sg.Frame('CAM 1'.format((1)), [
            [sg.Image(key='_ESP32/PUB_'.format((1)), size=(640, 480))],  
        ], font=middle_font) ]], pad=(0, 0), element_justification='c')]]

        layout = [[
            sg.Column(col1), sg.Column(col2)
        ]]

        self.window = sg.Window('MQTT client', layout)

        while True:
 
            event, values = self.window.Read(timeout=5)
            if event is None or event == 'Exit':
                break

            if event == '_CONNECT_BTN_':
                if self.window[event].get_text() == 'Приєднати':

                    if len(self.window['_CLIENTID_IN_'].get()) == 0:
                        self.popup_dialog('Client Id is empty', 'Error', context_font)
                    else:
                        self.window['_CONNECT_BTN_'].update('Від\'єднати')
                        self.aws_connect(self.window['_CLIENTID_IN_'].get())
                        

                else:
                    self.window['_CONNECT_BTN_'].update('Приєднати')
                    self.aws_disconnect()
            try:
                message = self.gui_queue.get_nowait()
            except queue.Empty:
                message = None
            if message is not None:
                _target_ui = message.get("Target_UI")
                _image = message.get("Image")
                self.window[_target_ui].update(data=_image)

        self.window.Close()

    def aws_connect(self, client_id):
        ENDPOINT = "a39dh3uay4***************.amazonaws.com"
        PATH_TO_CERT = "certificate/DeviceCertificate.crt"
        PATH_TO_KEY = "certificate/Private.key"
        PATH_TO_ROOT = "certificate/RootCA.pem"

        self.myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(client_id)
        self.myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
        self.myAWSIoTMQTTClient.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)

        try:
            if self.myAWSIoTMQTTClient.connect():
                self.add_note('[MQTT] Connected')
                self.mqtt_subscribe('esp32/pub')

            else:
                self.add_note('[MQTT] Cannot Access AWS IOT')
        except Exception as e:
            tb = traceback.format_exc()
            sg.Print(f'An error happened.  Here is the info:', e, tb)

    def aws_disconnect(self):
        if self.myAWSIoTMQTTClient is not None:
            self.myAWSIoTMQTTClient.disconnect()
            self.add_note('[MQTT] Successfully Disconnected!')

    def mqtt_subscribe(self, topic):
        if self.myAWSIoTMQTTClient.subscribe(topic, 0, lambda client, userdata, message: {

            self.gui_queue.put({"Target_UI": "_{}_".format(str(message.topic).upper()),
                                "Image": self.byte_image_to_png(message)})
        }):
            self.add_note('\n[MQTT] Topic: {}\n-> Subscribed'.format(topic))
        else:
            self.add_note('[MQTT] Cannot subscribe\nthis Topic: {}'.format(topic))

    def add_note(self, note):
        note_history = self.window['_NOTES_'].get()
        self.window['_NOTES_'].update(note_history + note if len(note_history) > 1 else note)

    def byte_image_to_png(self, message):
        bytes_image = io.BytesIO(message.payload)
        picture = Image.open(bytes_image)

        im_bytes = io.BytesIO()
        picture.save(im_bytes, format="PNG")
        return im_bytes.getvalue()

    def popup_dialog(self, contents, title, font):
        sg.Popup(contents, title=title, keep_on_top=True, font=font)


if __name__ == '__main__':
    Application()
