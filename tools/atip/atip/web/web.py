# Copyright (c) 2014 Intel Corporation.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of works must retain the original copyright notice, this list
#   of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the original copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of Intel Corporation nor the names of its contributors
#   may be used to endorse or promote products derived from this work without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY INTEL CORPORATION "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL INTEL CORPORATION BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors:
#         Fan, Yugang <yugang.fan@intel.com>

import time
import json
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    NoAlertPresentException,
    WebDriverException)
from atip.tizen import tizen
from atip.common import common
try:
    from urlparse import urljoin, urlparse
except ImportError:
    from urllib.parse import urljoin, urlparse


class WebAPP(common.APP):

    def __init__(self, app_config=None, app_name=None):
        self.__driver = None
        self.app_type = common.APP_TYPE_WEB
        self.app_name = app_name
        self.app_id = ""
        apk_activity_name = ""
        apk_pkg_name = ""
        if "platform" in app_config and "name" in app_config["platform"]:
            if app_config["platform"]["name"].upper().find('TIZEN') >= 0:
                app_id = tizen.get_appid_by_name(
                    self.app_name, app_config["platform"])
            if app_config["platform"]["name"].upper().find('ANDROID') >= 0:
                self.app_name = self.app_name.replace("-", "_")
                apk_name_update = "".join(
                    [i.capitalize() for i in self.app_name.split("_") if i])
                apk_activity_name = ".%sActivity" % apk_name_update
                apk_pkg_name = "org.xwalk.%s" % self.app_name
        app_config_str = json.dumps(app_config).replace(
            "TEST_APP_NAME", self.app_name).replace(
            "TEST_APP_ID", self.app_id).replace(
            "TEST_PKG_NAME", apk_pkg_name).replace(
            "TEST_ACTIVITY_NAME", apk_activity_name)
        self.app_config = json.loads(app_config_str)
        if "url-prefix" in app_config:
            self.url_prefix = app_config["url-prefix"]
        else:
            self.url_prefix = ""

    def __get_element_by_xpath(self, xpath, display=True):
        try:
            element = self.__driver.find_element_by_xpath(xpath)
            if display:
                try:
                    if element.is_displayed():
                        return element
                except StaleElementReferenceException:
                    pass
            else:
                return element
            print "Failed to get element"
        except Exception as e:
            print "Failed to get element: %s" % e
        return None

    def __get_element_by_tag(self, key, display=True):
        try:
            element = self.__driver.find_element_by_tag(key)
            return element
        except Exception as e:
            print "Failed to get element: %s" % e
            return None

    def __get_element_by_key(self, key, display=True):
        try:
            for i_element in self.__driver.find_elements_by_xpath(str(
                    "//*[@id='%(key)s']|"
                    "//*[@name='%(key)s']|"
                    "//*[@value='%(key)s']|"
                    "//*[contains(@class, '%(key)s')]|"
                    "//button[contains(text(), '%(key)s')]|"
                    "//input[contains(text(), '%(key)s')]|"
                    "//textarea[contains(text(), '%(key)s')]|"
                    "//a[contains(text(), '%(key)s')]") % {'key': key}):
                if display:
                    try:
                        if i_element.is_displayed():
                            return i_element
                    except StaleElementReferenceException:
                        pass
                else:
                    return i_element
            print "Failed to get element"
        except Exception as e:
            print "Failed to get element: %s" % e
        return None

    def __check_normal_text(self, text, display=True):
        try:
            for i_element in self.__driver.find_elements_by_xpath(str(
                    '//*[contains(normalize-space(.),"{text}") '
                    'and not(./*[contains(normalize-space(.),"{text}")])]'
                    .format(text=text))):
                if display:
                    try:
                        if i_element.is_displayed():
                            return i_element
                    except StaleElementReferenceException:
                        pass
                else:
                    return i_element
        except Exception as e:
            print "Failed to get element: %s" % e
        return None

    def __check_normal_text_element(self, text, key, display=True):
        element = self.__get_element_by_key(key, display)
        if element:
            try:
                for i_element in element.find_elements_by_xpath(str(
                        '//*[contains(normalize-space(.),"{text}") '
                        'and not(./*[contains(normalize-space(.),"{text}")])]'
                        .format(text=text))):
                    if display:
                        try:
                            if i_element.is_displayed():
                                return i_element
                        except StaleElementReferenceException:
                            pass
                    else:
                        return i_element
            except Exception as e:
                print "Failed to get element: %s" % e
        return None

    def launch_app(self):
        try:
            desired_capabilities = self.app_config["desired-capabilities"]
            self.__driver = WebDriver(
                str(self.app_config["driver-url"]), desired_capabilities)
        except Exception as e:
            print "Failed to launch %s: %s" % (self.app_name, e)
            return False
        return True

    def switch_url(self, url, with_prefix=True):
        if with_prefix:
            url = urljoin(self.url_prefix, url)
        try:
            self.__driver.get(url)
        except Exception as e:
            print "Failed to visit %s: %s" % (url, e)
            return False
        return True

    def title(self):
        try:
            return self.__driver.title
        except Exception as e:
            print "Failed to get title: %s" % e
            return None

    def current_url(self):
        try:
            return self.__driver.current_url
        except Exception as e:
            print "Failed to get current url: %s" % e
            return None

    def reload(self):
        self.__driver.refresh()
        return True

    def back(self):
        self.__driver.back()
        return True

    def forward(self):
        self.__driver.forward()
        return True

    def check_normal_text_timeout(self, text=None, display=True, timeout=2):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.__check_normal_text(text, display):
                return True
            time.sleep(0.2)
        return False

    def check_normal_text_element_timeout(
            self, text=None, key=None, display=True, timeout=2):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.__check_normal_text_element(text, key, display):
                return True
            time.sleep(0.2)
        return False

    def press_element_by_key(self, key, display=True):
        element = self.__get_element_by_key(key, display)
        if element:
            element.click()
            return True

        return False

    def click_element_by_key(self, key, display=True):
        element = self.__get_element_by_key(key, display)
        if element:
            ActionChains(self.__driver).click(element).perform()
            return True
        return False

    def click_element_coords(self, x, y, key, display=True):
        element = self.__get_element_by_key(key, display)
        if element:
            ActionChains(self.__driver).move_to_element_with_offset(
                element, x, y).click().perform()
            return True
        return False

    def fill_element_by_key(self, key, text, display=True):
        element = self.__get_element_by_key(key, display)
        if element:
            element.send_keys(text)
            return True
        return False

    def check_checkbox_by_key(self, key, display=True):
        element = self.__get_element_by_xpath(str(
            "//input[@id='%(key)s'][@type='checkbox']|"
            "//input[@name='%(key)s'][@type='checkbox']") % {'key': key}, display)
        if element:
            if not element.is_selected():
                element.click()
            return True
        return False

    def uncheck_checkbox_by_key(self, key, display=True):
        element = self.__get_element_by_xpath(str(
            "//input[@id='%(key)s'][@type='checkbox']|"
            "//input[@name='%(key)s'][@type='checkbox']") % {'key': key}, display)
        if element:
            if element.is_selected():
                element.click()
            return True
        return False

    def get_alert_text(self):
        try:
            alert_element = self.__driver.switch_to_alert()
            if alert_element:
                return alert_element.text
        except Exception as e:
            print "Failed to get alert text: %s" % e

        return None

    def check_alert_existing(self):
        try:
            self.__driver.switch_to_alert().text
        except NoAlertPresentException:
            return False
        return True

    def accept_alert(self):
        try:
            alert_element = self.__driver.switch_to_alert()
            alert_element.accept()
            return True
        except Exception as e:
            print "Failed to accept alert: %s" % e
            return False

    def quit(self):
        if self.__driver:
            self.__driver.quit()


def launch_webapp_by_name(context, app_name):
    if not context.web_config:
        assert False

    if app_name in context.apps:
        context.apps[app_name].quit()
    context.apps.update({app_name: WebAPP(context.web_config, app_name)})
    context.app = context.apps[app_name]
    if not context.app.launch_app():
        assert False
    assert True
