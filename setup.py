from setuptools import find_packages, setup

# Читаем README для описания
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Читаем требования из requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Версия проекта
version = "0.1.0"

setup(
    name="opnvpn_cli",
    version=version,
    author="Chekh",
    author_email="",
    description="Утилита для управления конфигурациями OpenVPN с автоматическим версионированием сертификатов и адресами",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/opnvpn_cli",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "opnvpn=opnvpn_cli.main:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Networking",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: Console",
    ],
    package_data={
        "opnvpn_cli": [
            "*.ovpn",
            "*.yaml",
            "*.env.example",
        ],
    },
    include_package_data=True,
)
