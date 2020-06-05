from getpass import getpass
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main():
    stream_link = input('Вставь ссылку на стрим: ')
    twitch_viewer = TwitchViewer(stream_link)
    twitch_viewer.twitch_authorization()
    twitch_viewer.watch_stream()


class TwitchViewer:
    def __init__(self, stream_link):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_experimental_option("excludeSwitches",
                                               ["enable-logging"])

        self.driver = webdriver.Chrome(options=chrome_options,
                                       executable_path="./chromedriver.exe")
        self.stream_link = stream_link

    def twitch_authorization(self):
        login_page = 'https://twitch.tv/login'
        self.driver.get(login_page)

        if self.driver.title != 'Войти - Twitch':
            print('Непредвидимая страница')
            self.driver.quit()
            return

        self.driver.find_element_by_id('login-username').send_keys(
            input('Введи имя пользователя: '))
        self.driver.find_element_by_id('password-input').send_keys(
            getpass('Введи пароль: '))
        self.driver.find_element_by_xpath(
            "//button[@data-a-target='passport-login-button']").click()
        self.enter_auth_code()

    def enter_auth_code(self):
        auth_code = input('Введи код авторизации: ')
        auth_code_area = self.driver.find_element_by_xpath(
            "//div[@aria-label='Ввести код подтверждения']")
        auth_code_area.find_element_by_xpath("//input[@type='text']") \
            .send_keys(auth_code)
        try:
            element_title = EC.title_is('Twitch')
            WebDriverWait(self.driver, 10).until(element_title)
            print('Успешно вошли')
        except TimeoutException:
            print('Не перешли на главную')
            if not self.check_authorization():
                print('Пробуем заново зайти')
                self.twitch_authorization()

    def check_authorization(self):
        profile_page = 'https://twitch.tv/login'
        self.driver.get(profile_page)
        error = self.driver.\
            find_element_by_class_name('core-error__message-container').text
        return bool(error == 'Чтобы просмотреть страницу, войдите в систему')

    def watch_stream(self):
        print('Начинаем смотреть')
        self.driver.get(self.stream_link)
        sleep(5)

        start_balance = self.get_points_balance()
        print(f'На момент старта баланс: {start_balance}')

        num_execut = 0
        while True:
            if num_execut >= 2:
                self.driver.get(self.stream_link)
                num_execut = 0
                print('Перезагрузили страницу')
                sleep(5)

            end_balance = self.get_points_balance()
            print(f'С начала стрима заработали '
                  f'+{end_balance - start_balance} поинтов')

            self.check_stream()
            self.find_bonus_points()

            num_execut += 1

    def get_points_balance(self):
        balance_xpath = "//div[@data-test-selector='balance-string']"
        balance = self.driver.find_element_by_xpath(balance_xpath)
        balance = balance.text.replace(' ', '')
        return int(balance)

    def find_bonus_points(self):
        try:
            print('Смотрим и ищем points gift')
            points_gift_xpath = "//button[@class='tw-button tw-button--success tw-interactive']"

            points_gift_button = WebDriverWait(self.driver, 900).until(
                EC.visibility_of_element_located((By.XPATH, points_gift_xpath)))
            points_gift_button.click()
            sleep(1)

            print('Получили points gift')
        except TimeoutException:
            print('Не нашли points gift за 15 мин.')

    def check_stream(self):
        class AnyEc:
            def __init__(self, *args):
                self.ecs = args

            def __call__(self, driver):
                for fn in self.ecs:
                    try:
                        if fn(driver):
                            return True
                    except:
                        pass

        print('Проверяем стрим')
        old_live_indicator_xpath = "//div[@class='channel-header-user-tab__user-content tw-align-items-center tw-flex tw-full-height']/div[3]"
        new_live_indicator_xpath = "//div[@class='tw-border-radius-medium tw-c-background-inherit tw-channel-status-text-indicator--mask tw-inline-block']"

        live_indicator_xpath = ''
        for xpath in [old_live_indicator_xpath, new_live_indicator_xpath]:
            if self.driver.find_elements_by_xpath(xpath):
                live_indicator_xpath = xpath

        if not live_indicator_xpath:
            print('Стрим офлайн')
            try:
                WebDriverWait(self.driver, 600).until(AnyEc(
                    EC.visibility_of_element_located((By.XPATH,
                                                      old_live_indicator_xpath)),
                    EC.visibility_of_element_located((By.XPATH,
                                                      new_live_indicator_xpath))
                ))
            except TimeoutException:
                print('За 10 минут стрим не восстановился, завершаем работу')
                self.driver.quit()
        print('Стрим работает, продолжаем смотреть')


if __name__ == '__main__':
    main()
