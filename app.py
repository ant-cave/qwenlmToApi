import time
from selenium import webdriver
import queue
import concurrent.futures
import os
from rich import print
import json

class MainApp:
    def __init__(self, driver_num=4, headless=True):
        
        if not os.path.exists('test'):
            os.makedirs('test')



        self.driver_num = driver_num
        self.headless = headless
        self.driver_queue = queue.Queue()

        self.account_queue = queue.Queue()# 账号队列
        with open('data/config.json', 'r', encoding='utf-8') as f:
            config_data = json.loads(f.read())
        for account in config_data['accounts']:
            self.account_queue.put(account)

        self.__init_driver()
    
    def __init_driver(self):
        # 使用线程池创建指定数量的 driver
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.driver_num) as executor:
            # 创建多个 driver 任务
            futures = []
            for i in range(self.driver_num):
                future = executor.submit(self._create_single_driver)
                futures.append(future)
            
            # 等待所有 driver 创建完成并放入队列
            for future in concurrent.futures.as_completed(futures):
                try:
                    driver = future.result()
                    self.driver_queue.put(driver)
                except Exception as e:
                    print(f"创建 driver 失败: {e}")
    
    def _create_single_driver(self):
        # 创建单个 driver 的辅助方法
        options = webdriver.EdgeOptions()
        if self.headless:
            options.add_argument('--headless')
        driver = webdriver.Edge(options=options)
        return driver
    
    def run(self):
        driver=self.driver_queue.get()
        driver:webdriver.Edge
        driver.get("https://chat.qwen.ai")

        account=self.account_queue.get()

        with open('test/example.html', 'w+', encoding='utf-8') as f:
            f.write(driver.page_source)
        

        time.sleep(0.5)

        login_button=driver.find_element("xpath",'//*[@id="root"]/div/div/div/header/div/div[2]/div/a[1]/button')
        login_button.click()

        login_input=driver.find_element("xpath",'//*[@id="root"]/div/div/div/div[2]/div/div[1]/form/div/div[1]/span[2]/input')
        login_input.send_keys(account['username'])
        
        print('开始输入密码')
        password_input=driver.find_element("xpath",'//*[@id="root"]/div/div/div/div[2]/div/div[1]/form/div/div[2]/span[2]/input')
        password_input.send_keys(account['password'])

        login_button_submit=driver.find_element("xpath",'//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[3]/button')
        login_button_submit.click()

        input('>')
    
    def del_app(self):
        self.__del__()

    def __del__(self):
        # 使用线程池关闭所有 driver
        drivers_to_close = []
        while not self.driver_queue.empty():
            drivers_to_close.append(self.driver_queue.get())
        
        if drivers_to_close:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.driver_num) as executor:
                # 提交所有关闭任务
                futures = []
                for driver in drivers_to_close:
                    future = executor.submit(self._close_single_driver, driver)
                    futures.append(future)
                
                # 等待所有关闭任务完成
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"关闭 driver 失败: {e}")
    
    def _close_single_driver(self, driver:webdriver.Edge):
        # 关闭单个 driver 的辅助方法
        driver.quit()

app = MainApp(driver_num=1, headless=False)
app.run()
app.del_app()
