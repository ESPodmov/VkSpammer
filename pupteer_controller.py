import random
import subprocess
import requests
import DolphinController
import json
from pyppeteer import connect, element_handle
import asyncio
import nest_asyncio

nest_asyncio.apply()


creative = """jjj"""


async def mouseover(name: str, data: str, page):
    elem = await page.waitForSelector(f'input[name="{name}"]', {"visible": True})
    await elem.type(data)
    await page.keyboard.press("Enter")


async def open_chat_and_join(page, link: str, creative: str):
    await page.goto(link, timeout=500000)
    invite_str = link.split("//")[1]
    if "join/" in invite_str:
        invite_str = invite_str.split("join/")[1]
    else:
        invite_str = invite_str.split("&")[1]
        invite_str = invite_str.split("=")[1]
    try:
        elem = await page.waitForSelector(f'button[data-chat-link="{invite_str}"]', {"timeout": 20000, "visible": True})
        await elem.click()
        text_field = await page.waitForSelector('div[role="textbox"]', {"timeout": 10000, "visible": True})
        await text_field.focus()
        await page.keyboard.down("ControlLeft")
        await page.keyboard.press("A")
        await page.keyboard.up("ControlLeft")
        await page.keyboard.press("Backspace")
        await page.keyboard.down("ControlLeft")
        await page.keyboard.press("V")
        await page.keyboard.up("ControlLeft")
        # x_btn = await page.waitForSelector('div[class="page_media_x_wrap inl_bl"]', {"visible": True})
        # await x_btn.click()
        await text_field.click()
        print(link + " worked")
        with open("./consumables/used/worked_links.txt", "a") as my_file:
            my_file.write(link + "\n")
        return True
    # пометить чат как отработанный
    except Exception as e:
        # вывести чат из рабочих
        print(e)
        print(link + " is not working")
        await page.close()
        return False


async def press_send(page, xpath):
    try:
        textbox = await page.waitForSelector('div[role="textbox"]', {"timeout": 20000, "visible": True})
        await textbox.focus()
        await textbox.press("Enter")
        my_msg = await page.waitForXPath(
            xpath, {"visible": True})
        function_string = f'document.evaluate("{xpath}", document, null, 9, null)'
        my_func = f'{function_string}.singleNodeValue.parentNode.lastChild.previousSibling.clientWidth == 0'
        await page.waitForFunction(my_func)
        print("Message sent")
        await asyncio.sleep(random.random() * 0.75 + 0.5)
    except Exception as e:
        print(e.args)


with open("./config/auth_data.json", "r", encoding="utf-8") as file:
    auth_data = json.load(file)
# authentication in dolphin
auth_token = DolphinController.authentication(auth_data["username"], auth_data["password"])
headers = {
    "Authorization": f"Bearer {auth_token}",
    "Content-Type": "application/json"
}
# starting session with headers
session = requests.session()
session.headers = headers
accounts = {}
with open("./consumables/current/accounts.txt", "r") as file:
    for line in file:
        split_line = line.split(":")
        accounts[split_line[0]] = split_line[1]
with open("./consumables/current/chat_links.txt", "r") as file:
    chat_links = file.read().splitlines()
accounts_counter = 0
# getting settings file
with open("./config/settings.json", "r") as file:
    settings = json.load(file)
xpath_to_find = f"(//*[@class='im-mess--text wall_module _im_log_body'"
creative_array = creative.split("\n")
for line in creative_array:
    xpath_to_find = xpath_to_find + f" and contains(., '{line}')"
xpath_to_find = xpath_to_find + "])[last()]"


async def main():
    all_chat_counter = 0
    for login in accounts:
        chat_pages = []
        current_profile_id = DolphinController.create_profile_and_send_id(session)
        automation_json = DolphinController.start_automation(session, profile_id=current_profile_id)
        dolphin_port = automation_json["automation"]["port"]
        print(dolphin_port)
        dolphin_ws_endpoint = automation_json["automation"]["wsEndpoint"]
        print(dolphin_ws_endpoint)
        browser = await connect({"browserWSEndpoint": f'ws://127.0.0.1:{dolphin_port}{dolphin_ws_endpoint}'})
        page = await browser.newPage()
        await page.setViewport({"width": 1380, "height": 635})
        await page.goto("https://vk.com/")
        await mouseover("login", login, page=page)
        await mouseover("password", accounts[login], page)
        chat_counter = 0
        subprocess.run("clip", text=True, input=creative, encoding="utf-16")
        await asyncio.sleep(3.0)
        # opening num of chats (set from settings)
        await page.close()
        while chat_counter < settings["chats_num"] and all_chat_counter < len(chat_links):
            current_page = await browser.newPage()
            await current_page.setViewport({"width": 1380, "height": 635})
            response = await open_chat_and_join(current_page, chat_links[all_chat_counter],
                                                creative=creative)
            if response:
                chat_pages.append(current_page)
                chat_counter += 1
            all_chat_counter += 1
        # loop = asyncio.get_event_loop()
        # tasks = []
        for elem in chat_pages:  # may cause error because of parameter body
            await press_send(elem, xpath_to_find)
        with open("./consumables/used/worked_accounts.txt", "a") as my_file:
            my_file.write(str(login) + ":" + str(accounts[login]) + "\n")
        try:
            await browser.close()
        except Exception:
            pass
        await browser.close()
        try:
            DolphinController.stop_profile(session=session, profile_id=current_profile_id)
            DolphinController.delete_browser_profile(session=session, profile_id=current_profile_id)
        except Exception:
            pass


asyncio.run(main())
