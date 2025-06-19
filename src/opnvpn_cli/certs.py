import yaml
from pathlib import Path
from datetime import datetime
import shutil
from typing import Dict

class CertManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.cert_dir = config_dir / "certs"
        self.cert_dir.mkdir(parents=True, exist_ok=True)

    def save_cert(self, cert_data: Dict[str, str], version: str = None) -> str:
        """Сохраняет сертификаты и ключи в новую версию"""
        version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        version_dir = self.cert_dir / version
        version_dir.mkdir(exist_ok=True)

        # Сохраняем каждый компонент сертификата
        for key, value in cert_data.items():
            if value:
                (version_dir / f"{key}.pem").write_text(value)

        # Сохраняем метаданные версии
        metadata = {
            "version": version,
            "created_at": datetime.now().isoformat(),
            "components": list(cert_data.keys())
        }
        (version_dir / "metadata.yaml").write_text(yaml.dump(metadata))

        return version

    def load_latest_cert(self) -> Dict[str, str]:
        """Загружает последнюю версию сертификатов"""
        versions = sorted([d for d in self.cert_dir.iterdir() if d.is_dir()])
        if not versions:
            return {}

        latest = versions[-1]
        cert_data = {}
        for file in latest.iterdir():
            if file.suffix == ".pem":
                cert_data[file.stem] = file.read_text()

        return cert_data

    def load_cert_version(self, version: str) -> Dict[str, str]:
        """Загружает конкретную версию сертификатов"""
        version_dir = self.cert_dir / version
        if not version_dir.exists():
            return {}

        cert_data = {}
        for file in version_dir.iterdir():
            if file.suffix == ".pem":
                cert_data[file.stem] = file.read_text()

        return cert_data

    def list_versions(self) -> list:
        """Возвращает список всех версий сертификатов"""
        versions = sorted([d for d in self.cert_dir.iterdir() if d.is_dir()], reverse=True)
        return [v.name for v in versions]

    def restore_version(self, version: str) -> bool:
        """Восстанавливает конкретную версию сертификатов"""
        version_dir = self.cert_dir / version
        if not version_dir.exists():
            return False

        # Создаем временную директорию для текущей версии
        temp_dir = self.cert_dir / "temp"
        temp_dir.mkdir(exist_ok=True)

        # Копируем все файлы из версии в временную директорию
        for file in version_dir.iterdir():
            if file.suffix == ".pem":
                shutil.copy(file, temp_dir / file.name)

        # Удаляем старые версии
        for d in self.cert_dir.iterdir():
            if d.is_dir() and d.name != version:
                shutil.rmtree(d)

        # Переименовываем временную директорию в текущую версию
        temp_dir.rename(self.cert_dir / "current")
        return True
