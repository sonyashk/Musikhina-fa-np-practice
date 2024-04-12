import logging
def new_client_request(self):
        """"Обработка запроса клиента"""
        cli_request, ip_addr = self.socket.listen()
        path = cli_request.path
        # Получаем результат существования файла от роутера
        body, status_code, mime = self.router(path)
        header = self.get_header(status_code, body, mime)
        self.socket.send(header.encode() + body)
        logger.info(
            f"{utils.get_date()} -> {ip_addr}, {path} {status_code} - {cli_request.method} {cli_request.user_agent}")

def read_config() -> dict:
    """Чтение настроек из файла yaml"""
    with open("settings.yml", "r") as file:
        return yaml.safe_load(file)

LOGGER_FILE = "./logs/server.log"
# Настройки логирования
logging.basicConfig(
    format="%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s",
    handlers=[logging.FileHandler(LOGGER_FILE)],
    level=logging.INFO,
)

def router(self, path: str) -> Tuple[bytes, int, str]:
        """Роутер для ассоциации между путями и файлами"""

        allowed_extensions = ["js", "html", "css", "png", "jpg"]
