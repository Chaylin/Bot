import pyautogui
import pyperclip
import time


class Discord:

    @staticmethod
    def send_message(message):
        pyautogui.press('win')
        time.sleep(1)
        pyautogui.typewrite('Apps: Discord')
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(10)
        pyperclip.copy("@")
        pyautogui.hotkey("ctrl", "v")
        pyautogui.typewrite('everyone ')
        pyautogui.typewrite(message)
        pyautogui.press('enter')

