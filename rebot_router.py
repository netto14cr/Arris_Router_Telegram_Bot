import os
from io import BytesIO
import qrcode
from dotenv import load_dotenv
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import speedtest
import subprocess

class RouterBot:
    def __init__(self, telegram_token, router_url, router_username, router_password):
        self.telegram_token = telegram_token
        self.router_url = router_url
        self.router_username = router_username
        self.router_password = router_password
        self.application = Application.builder().token(telegram_token).build()
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('restart', self.reboot_router))
        self.application.add_handler(CommandHandler('speedtest', self.check_speed))
        self.application.add_handler(CommandHandler('checkconnection', self.check_connection))
        self.application.add_handler(CommandHandler('wifipassword', self.generate_wifi_pin))
        

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Welcome to the Router Bot!\n"
            "You can use the following commands:\n"
            "/restart - Restart the router\n"
            "/speedtest - Check the Internet speed\n"
            "/checkconnection - Check Internet connection\n"
            "/wifipassword - Get the WiFi password\n"
            "/start - Show this message again"
        )

    async def reboot_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('Starting the router reboot process...')

        driver = None
        try:
            # Initialize the Selenium driver
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Optional: For running the browser in the background
            driver = webdriver.Chrome(options=options)  # Or specify the path to the chromedriver executable

            # Enter the router login page
            driver.get(self.router_url)

            # Wait until the username field is visible
            username_field = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.NAME, 'loginUsername'))
            )
            # Enter the username
            username_field.send_keys(self.router_username)

            # Wait until the password field is visible
            password_field = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.NAME, 'loginPassword'))
            )
            # Enter the password
            password_field.send_keys(self.router_password)

            # Submit the login form
            password_field.send_keys(Keys.RETURN)

            # Wait for the page to load completely
            WebDriverWait(driver, 15).until(
                EC.url_to_be(f'{self.router_url}/home.asp')
            )

            # If the URL after login is not as expected, print an error message and close the browser
            if driver.current_url != f'{self.router_url}/home.asp':
                await update.message.reply_text('Error: Could not access correct page after login')
                return

            # Access the configuration page
            driver.get(f'{self.router_url}/RgConfiguration.asp')

            # Wait for the SaveChanges button to be visible
            save_changes_button = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="submit"][name="SaveChanges"][reboot=""]'))
            )
            await update.message.reply_text('Rebooting the router...')
            time.sleep(2)  # Wait 2 seconds before clicking the button 
            save_changes_button.click()
            time.sleep(5)
            
            # Maximum number of updates
            max_updates = 2
            # Maximum total wait time in seconds
            max_wait_time = 130
            # Time between page updates in seconds
            refresh_interval = 60

            # Start counting time
            start_time = time.time()
            # Update counter
            update_count = 0

            # Wait until the page has loaded completely
            while time.time() - start_time < max_wait_time and update_count < max_updates:
                try:
                    url2 = f'{self.router_url}/login.asp'
                    WebDriverWait(driver, 20).until(EC.url_to_be(url2))
                    await update.message.reply_text('The router has been restarted successfully!')
                    time.sleep(2)
                    break  # Exit the loop if the page has loaded successfully
                except TimeoutException:
                    # If the page has not loaded yet after 20 seconds, try to refresh it
                    if time.time() - start_time > refresh_interval:
                        driver.refresh()
                        start_time = time.time()  # Restart the timer
                        update_count += 1  # Increase the update count
                    time.sleep(1)  # Wait 1 second before trying again

            # Verify if the maximum time has passed without the page loading completely
            if time.time() - start_time >= max_wait_time or update_count >= max_updates:
                await update.message.reply_text('Error: Could not verify router status after restart!')

        except TimeoutException:
            await update.message.reply_text('Error: Timeout. Could not reboot the router.')

        except Exception as e:
            await update.message.reply_text(f'Error rebooting the router: {e}')

        finally:
            if driver:
                await update.message.reply_text('Process finished successfully! Closing the browser...')
                time.sleep(2)
                driver.quit()

        await update.message.reply_text('Iniciando proceso de reiniciar el router...')

        driver = None
        try:
            # Initialize the Selenium driver
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Opcional: For running the browser in the background
            driver = webdriver.Chrome(options=options)  # Or specify the path to the chromedriver executable

            # Enter the router login page
            driver.get(self.router_url)

            # Wait until the username field is visible
            username_field = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.NAME, 'loginUsername'))
            )
            # Enter the username
            username_field.send_keys(self.router_username)

            # Wait until the password field is visible
            password_field = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.NAME, 'loginPassword'))
            )
            # Ingresar la contraseña
            password_field.send_keys(self.router_password)

            # Enviar el formulario de login
            password_field.send_keys(Keys.RETURN)

            # Esperar a que la página se cargue completamente
            WebDriverWait(driver, 15).until(
                EC.url_to_be(f'{self.router_url}/home.asp')
            )

            # Si la URL después del login no es la esperada, imprimir un mensaje de error y cerrar el navegador
            if driver.current_url != f'{self.router_url}/home.asp':
                await update.message.reply_text('Error: No se pudo acceder a la página correcta después del login')
                return

            # Acceder a la página de configuración
            driver.get(f'{self.router_url}/RgConfiguration.asp')

            # Esperar a que el botón SaveChanges sea visible
            save_changes_button = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="submit"][name="SaveChanges"][reboot=""]'))
            )
            await update.message.reply_text('Reiniciando el router...')
            time.sleep(2)  # Esperar 2 segundos antes de hacer clic en el botón 
            save_changes_button.click()
            time.sleep(5)
            
            # Número máximo de actualizaciones
            max_updates = 2
            # Tiempo máximo total de espera en segundos
            max_wait_time = 130
            # Tiempo entre actualizaciones de página en segundos
            refresh_interval = 60

            # Start counting time
            start_time = time.time()
            #counter of updates
            update_count = 0

            # Wait until the page has loaded completely
            while time.time() - start_time < max_wait_time and update_count < max_updates:
                try:
                    url2 = f'{self.router_url}/login.asp'
                    WebDriverWait(driver, 20).until(EC.url_to_be(url2))
                    await update.message.reply_text('The router has been restarted successfully!')
                    time.sleep(2)
                    break  # Exit the loop if the page has loaded successfully
                except TimeoutException:
                    # If the page has not loaded yet after 20 seconds, try to refresh it
                    if time.time() - start_time > refresh_interval:
                        driver.refresh()
                        start_time = time.time()  # Restart the timer
                        update_count += 1  # Increase the update count
                    time.sleep(1)  # Wait 1 second before trying again

            # Verify if the maximum time has passed without the page loading completely
            if time.time() - start_time >= max_wait_time or update_count >= max_updates:
                await update.message.reply_text('Error: It no posibble verify the router status after restart!')

        except TimeoutException:
            await update.message.reply_text('Error: The time to load the page has expired!')

        except Exception as e:
            await update.message.reply_text(f'Error to restart the router: {e}')

        finally:
            if driver:
                await update.message.reply_text('Process finished, closing the browser...')
                time.sleep(2)
                driver.quit()

    async def check_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('Checking internet speed, please wait...')
        try:
            st = speedtest.Speedtest()
            st.get_best_server()  # Find the best server for accurate results
            st.download()
            st.upload()
            res = st.results.dict()
            await update.message.reply_text(f"Download speed: {res['download'] / 1_000_000:.2f} Mbps\n"
                                            f"Upload speed: {res['upload'] / 1_000_000:.2f} Mbps\n"
                                            f"Ping: {res['ping']} ms")
        except Exception as e:
            await update.message.reply_text(f"Error checking internet speed: {e}")

    async def check_connection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('Checking internet connection, please wait...')
        try:
            response = requests.get('http://www.google.com', timeout=10)
            if response.status_code == 200:
                await update.message.reply_text('Internet connection is up.')
            else:
                await update.message.reply_text('No internet connection.')
        except requests.ConnectionError:
            await update.message.reply_text('No internet connection.')
            
    async def generate_wifi_pin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('Starting the process to generate a new WiFi PIN...')

        driver = None
        try:
            # Initialize the Selenium driver
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Optional: For running the browser in the background
            driver = webdriver.Chrome(options=options)  # Or specify the path to the chromedriver executable

            # Enter the router login page
            driver.get(self.router_url)

            # Wait until the username field is visible
            username_field = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.NAME, 'loginUsername'))
            )
            # Enter the username
            username_field.send_keys(self.router_username)

            # Wait until the password field is visible
            password_field = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.NAME, 'loginPassword'))
            )
            # Enter the password
            password_field.send_keys(self.router_password)

            # Submit the login form
            password_field.send_keys(Keys.RETURN)

            # Wait for the page to load completely
            WebDriverWait(driver, 15).until(
                EC.url_to_be(f'{self.router_url}/home.asp')
            )

            # If the URL after login is not as expected, print an error message and close the browser
            if driver.current_url != f'{self.router_url}/home.asp':
                await update.message.reply_text('Error: Could not access correct page after login')
                return

            # Access the primary network page
            driver.get(f'{self.router_url}/wlanPrimaryNetwork.asp')
            
            # wait for the SSID
            ssid_field = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.ID, '_ServiceSetIdentifier'))
            )
            router_ssid = ssid_field.get_attribute('value')
            print("SSID....", router_ssid)
            
            # wiat for the password 
            password_field = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.ID, '_WpaPreSharedKey'))
            )
            
            router_password = password_field.get_attribute('value')
            print("Password....", router_password)
            

            # Wait for the Generate PIN button to be visible
            generate_pin_button = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="submit"][value="Generate PIN"]'))
            )
            await update.message.reply_text('Generating a new WiFi PIN...')
            time.sleep(3)  # Wait 2 seconds before clicking the button
            generate_pin_button.click()
            time.sleep(5)  # Wait 5 seconds for the page to update

            # Refresh the page to get the new PIN
            driver.refresh()
            time.sleep(5)  # Wait 2 seconds after refreshing

            # Get the new PIN value
            new_pin_field = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, '_CfgDevPin'))
            )
            
            new_pin = new_pin_field.get_attribute('value')
            
            # Generate QR code for the new PIN
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f'WIFI:T:WPA;S:{router_ssid};P:{router_password};;')
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')

            # Save QR code image to a BytesIO object
            qr_bytes = BytesIO()
            img.save(qr_bytes)
            qr_bytes.seek(0)

            # Send the new PIN and QR code via Telegram
            await update.message.reply_text(f'New WiFi PIN: {new_pin}')
            await update.message.reply_photo(photo=qr_bytes)

        except TimeoutException:
            await update.message.reply_text('Error: The time to load the page has expired!')

        except Exception as e:
            await update.message.reply_text(f'Error generating WiFi PIN: {e}')

        finally:
            if driver:
                await update.message.reply_text('Process finished, closing the browser...')
                time.sleep(2)
                driver.quit()


    def run(self):
        self.application.run_polling()
        
    

if __name__ == '__main__':
    load_dotenv()  # Load environment variables from .env file
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    ROUTER_URL = os.getenv('ROUTER_URL')
    ROUTER_USERNAME = os.getenv('ROUTER_USERNAME')
    ROUTER_PASSWORD = os.getenv('ROUTER_PASSWORD')
    bot = RouterBot(TELEGRAM_TOKEN, ROUTER_URL, ROUTER_USERNAME, ROUTER_PASSWORD)
    bot.run()
