from selenium import webdriver
import queue
import concurrent.futures
import os
import json
import time
import threading
from typing import Optional, List, Dict, Any




class MainApp:
    def __init__(self, driver_num: int = 4, headless: bool = True):
        """
        初始化MainApp
        :param driver_num: 要创建的driver数量
        :param headless: 是否使用无头模式（注：交互式获取cookie时会临时使用有头模式）
        """
        self.start_time = time.time()  # 记录开始时间，用于内部计时
        
        # 1. 创建必要的目录
        os.makedirs('data', exist_ok=True)  # 创建data目录，存在时不报错[citation:10]
        os.makedirs('test', exist_ok=True)  # 创建test目录，存在时不报错
        
        # 2. 检查并处理cookie文件
        self.cookie_file = 'data/cookie.json'
        self._check_and_load_cookie()
        
        # 3. 初始化实例变量
        self.driver_num = driver_num
        self.headless = headless
        self.driver_queue = queue.Queue()
        
        # 4. 异步启动线程池创建driver（不阻塞主线程）
        self._init_driver_async()
    
    def _check_and_load_cookie(self) -> None:
        """检查cookie文件，如果不存在则交互式获取并保存"""
        if not os.path.exists(self.cookie_file):
            print("未找到cookie文件，启动交互式浏览器获取cookie...")
            self._get_cookie_interactively()
        else:
            print(f"找到cookie文件: {self.cookie_file}")
            # 这里可以添加加载cookie的逻辑，后续在创建driver时使用
            self._load_cookie()
    
    def _get_cookie_interactively(self) -> None:
        """启动有头浏览器，让用户添加cookie后保存"""
        print("启动有头浏览器...")
        # 临时使用有头模式获取cookie
        options = webdriver.EdgeOptions()
        # 注意：这里强制使用有头模式，让用户能看到浏览器
        driver = webdriver.Edge(options=options)
        
        try:
            # 导航到目标网站，用户可以在此页面登录/添加cookie
            driver.get("https://chat.qwen.ai/")
            print("浏览器已打开，请添加必要的cookie")
            print("添加完成后，请在控制台按Enter键继续...")
            
            # 等待用户输入
            input('>')
            
            # 获取所有cookie
            cookies = driver.get_cookies()
            print(f"获取到 {len(cookies)} 个cookie")
            
            # 保存cookie到JSON文件
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"Cookie已保存到: {self.cookie_file}")
            
        finally:
            # 关闭交互式浏览器
            driver.quit()
            print("交互式浏览器已关闭")
    
    def _load_cookie(self) -> Optional[List[Dict[str, Any]]]:
        """从文件加载cookie"""
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            print(f"已从文件加载 {len(cookies)} 个cookie")
            return cookies
        except Exception as e:
            print(f"加载cookie文件失败: {e}")
            return None
    
    def _init_driver_async(self) -> None:
        """异步启动线程池在后台创建driver"""
        # 使用线程池创建指定数量的 driver
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.driver_num)
        
        # 提交所有driver创建任务
        self.driver_futures = []
        for i in range(self.driver_num):
            future = self.executor.submit(self._create_single_driver)
            self.driver_futures.append(future)
        
        print(f"已启动 {self.driver_num} 个driver的后台创建任务")
        
        # 启动后台线程处理driver创建完成后的队列放入
        self._process_driver_futures()
    
    def _process_driver_futures(self) -> None:
        """后台处理driver创建完成后的队列放入"""
        def process():
            for future in self.driver_futures:
                try:
                    driver = future.result()
                    self.driver_queue.put(driver)
                except Exception as e:
                    print(f"创建 driver 失败: {e}")
            print(f"所有driver创建完成，队列中有 {self.driver_queue.qsize()} 个driver")
        
        # 使用单独的线程处理，避免阻塞
        process_thread = threading.Thread(target=process, daemon=True)
        process_thread.start()
    
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
        driver.get("https://chat.qwen.ai/")

        with open('test/example.html', 'w+', encoding='utf-8') as f:
            f.write(driver.page_source)
        
    
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
    
    def _wait_for_drivers_ready(self, timeout: int = 30) -> bool:
        """等待driver创建完成"""
        print("等待driver创建完成...")
        start = time.time()
        while time.time() - start < timeout:
            if self.driver_queue.qsize() >= self.driver_num:
                print("所有driver已准备就绪")
                return True
            time.sleep(0.5)
        print(f"等待超时，只有 {self.driver_queue.qsize()}/{self.driver_num} 个driver就绪")
        return False


if __name__ == "__main__":
    # 创建应用实例，使用无头模式（但cookie获取时会临时使用有头模式）
    app = MainApp(driver_num=4, headless=True)
    
    # 等待driver创建完成
    if app._wait_for_drivers_ready():
        # 运行主程序
        app.run()
    
    # 清理资源
    app.del_app()
    
    # 计算并显示总用时
    end_time = time.time()
    print(f"总共用时: {round(end_time - app.start_time, 2)} 秒")
