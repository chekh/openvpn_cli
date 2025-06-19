# Создание продвинутого скрипта с использованием Typer
# Функции:
# - База адресов (в JSON)
# - Добавление доменов или IP
# - Просмотр списка
# - Резолвинг
# - Генерация OpenVPN-конфига с версией

import logging
import os
import socket
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Optional

import typer
import yaml
from dotenv import load_dotenv

from .certs import CertManager

app = typer.Typer()

# Загрузка настроек из .env
load_dotenv()

# README
README_PATH = 'README.md'

# Настройка логирования
LOG_FILE = Path(os.getenv('LOG_FILE_PATH', 'app.log'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация менеджера сертификатов
CONFIGS_DIR = Path(os.getenv('CONFIGS_DIR', 'configs'))
cert_manager = CertManager(CONFIGS_DIR)

# Пути к конфигам
BASE_CONFIG_PATH = CONFIGS_DIR / 'base' / 'base_config.ovpn'
ADDRESS_DB_PATH = CONFIGS_DIR / 'addresses.yaml'
OVPN_OUTPUT_PATH = CONFIGS_DIR / 'new_configs' / 'custom.ovpn'

# Загрузка базового конфига из файла
def load_base_config():
    """Загрузка базового конфига с вложенными сертификатами"""
    if not BASE_CONFIG_PATH.exists():
        logger.error("Файл базового конфига не найден!")
        return ""
    
    try:
        base_config = BASE_CONFIG_PATH.read_text()
        
        # Загружаем сертификаты
        cert_data = cert_manager.load_latest_cert()
        
        # Вставляем сертификаты в конфиг
        if cert_data:
            for tag, content in cert_data.items():
                if content:
                    base_config = base_config.replace(
                        f"<{tag}>\n</{tag}>",
                        f"<{tag}>\n{content}\n</{tag}>"
                    )
        
        return base_config
    except Exception as e:
        logger.error(f"Ошибка при чтении базового конфига: {e}")
        return ""

# Загрузка адресов из YAML файла
def load_addresses():
    """Загрузка адресов из YAML файла"""
    if not ADDRESS_DB_PATH.exists():
        logger.info("Файл адресов не найден, создание нового")
        return {"addresses": []}
    try:
        with ADDRESS_DB_PATH.open("r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке адресов: {e}")
        return {"addresses": []}

@app.command()
def setup_configs(base_config: str, configs_dir: str):
    """
    Настроить структуру конфигураций и извлечь сертификаты из исходного конфига
    
    Args:
        base_config: Путь к базовому конфигу
        configs_dir: Путь к директории для хранения конфигов
    """
    try:
        # Создаем директории
        base_dir = Path(configs_dir) / "base"
        new_configs_dir = Path(configs_dir) / "new_configs"
        
        base_dir.mkdir(parents=True, exist_ok=True)
        new_configs_dir.mkdir(parents=True, exist_ok=True)
        
        # Копируем базовый конфиг
        base_config_path = Path(base_config)
        if not base_config_path.exists():
            raise FileNotFoundError(f"Базовый конфиг не найден: {base_config}")
        
        # Читаем содержимое конфига
        config_content = base_config_path.read_text()
        
        # Извлекаем сертификаты и важные теги
        cert_data = {}
        important_tags = ["ca", "cert", "key", "tls-auth", "tls-crypt"]
        
        for tag in important_tags:
            start_tag = f"<{tag}>"
            end_tag = f"</{tag}>"
            start_idx = config_content.find(start_tag)
            end_idx = config_content.find(end_tag)
            
            if start_idx != -1 and end_idx != -1:
                start_idx += len(start_tag)
                content = config_content[start_idx:end_idx].strip()
                if content:
                    cert_data[tag] = content
                    # Удаляем из конфига, оставляя только теги
                    config_content = config_content.replace(
                        f"{start_tag}\n{content}\n{end_tag}",
                        f"{start_tag}\n{end_tag}"
                    )
        
        # Сохраняем конфиг без сертификатов
        (base_dir / "base_config.ovpn").write_text(config_content)
        
        # Сохраняем сертификаты
        if cert_data:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
            cert_manager.save_cert(cert_data, version)
            typer.echo(f"✅ Сертификаты сохранены в версию: {version}")
        
        # Создаем файл базы адресов, если его нет
        address_db_path = Path(configs_dir) / "addresses.yaml"
        if not address_db_path.exists():
            address_db_path.write_text("addresses: []\n", encoding='utf-8')
        
        typer.echo("✅ Структура конфигов настроена:")
        typer.echo(f"  - Базовый конфиг: {base_dir / 'base_config.ovpn'}")
        typer.echo(f"  - База адресов: {address_db_path}")
        typer.echo(f"  - Директория новых конфигов: {new_configs_dir}")
        
    except Exception as e:
        logger.error(f"Ошибка при настройке конфигов: {e}")
        raise typer.Exit(code=1)


def save_addresses(data):
    """Сохранение адресов в YAML файл"""
    try:
        with ADDRESS_DB_PATH.open("w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        logger.info("Адреса успешно сохранены")
    except Exception as e:
        logger.error(f"Ошибка при сохранении адресов: {e}")
        raise


def resolve_address(addr: str) -> List[str]:
    try:
        socket.inet_aton(addr)
        return [addr]
    except OSError:
        pass

    try:
        return socket.gethostbyname_ex(addr)[2]
    except socket.gaierror:
        return []


@app.command()
def add(addr: str, name: Optional[str] = None):
    """
    Добавить домен или IP в базу
    """
    addresses = load_addresses()
    
    # Проверка на существование
    if any(a.get('name') == name for a in addresses['addresses']):
        typer.echo(f"⚠️ Адрес с именем {name} уже существует")
        return
    
    # Получение типа адреса
    try:
        socket.inet_aton(addr)
        address_type = "ip"
    except OSError:
        address_type = "domain"
    
    new_address = {
        "name": name or addr,
        "type": address_type,
        "address": addr,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resolved_ips": []
    }
    
    addresses['addresses'].append(new_address)
    save_addresses(addresses)
    typer.echo(f"✅ Добавлено: {new_address['name']} ({addr})")


@app.command()
def list():
    """
    Показать список доменов/IP в базе
    """
    addresses = load_addresses()
    if not addresses['addresses']:
        typer.echo("📭 База пуста.")
    else:
        typer.echo("📚 Адреса в базе:")
        for i, addr in enumerate(addresses['addresses'], 1):
            typer.echo(f"{i:>2}. {addr['name']} ({addr['address']})")
            if addr['resolved_ips']:
                typer.echo(f"    Решенные IP: {', '.join(addr['resolved_ips'])}")
            typer.echo(f"    Тип: {addr['type']}")
            typer.echo(f"    Добавлен: {addr['added_at']}")
            typer.echo()


@app.command()
def generate(version: Optional[str] = None):
    """
    Сгенерировать OpenVPN-конфиг с маршрутами
    """
    addresses = load_addresses()
    seen_ips = set()
    base_config = load_base_config()
    route_lines = []

    for addr in addresses['addresses']:
        if addr['type'] == 'domain':
            resolved_ips = resolve_address(addr['address'])
            addr['resolved_ips'] = resolved_ips
        else:
            resolved_ips = [addr['address']]

        for ip in resolved_ips:
            if ip not in seen_ips:
                seen_ips.add(ip)
                route_lines.append(f"route {ip} 255.255.255.255")

    # Сохраняем обновленные адреса с разрешенными IP
    save_addresses(addresses)

    version_tag = version or datetime.utcnow().strftime("%Y%m%d%H%M%S")
    header = f"# Autogenerated OpenVPN config\n# Version: {version_tag}"

    # Создаем уникальное имя файла на основе версии
    output_path = CONFIGS_DIR / "new_configs" / f"custom_{version_tag}.ovpn"
    
    # Формируем конфиг
    config = f"{header}\n\n{base_config.strip()}\n\n" + "\n".join(route_lines) + "\n"
    output_path.write_text(config)

    typer.echo(f"✅ Конфиг сгенерирован: {output_path} (версия: {version_tag})")


@app.command()
def cert_list():
    """
    Показать список версий сертификатов
    """
    versions = cert_manager.list_versions()
    if not versions:
        typer.echo("⚠️ Нет версий сертификатов")
        return

    typer.echo("📚 Версии сертификатов:")
    for i, version in enumerate(versions, 1):
        typer.echo(f"{i:>2}. {version}")


@app.command()
def cert_restore(version: str):
    """
    Восстановить конкретную версию сертификатов
    """
    if cert_manager.restore_version(version):
        typer.echo(f"✅ Версия {version} успешно восстановлена")
    else:
        typer.echo(f"❌ Версия {version} не найдена")


if __name__ == "__main__":
    try:
        # Если нет аргументов, выводим README
        if len(sys.argv) == 1:
            with open(README_PATH, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            app()
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
        raise
