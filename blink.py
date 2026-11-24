#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blink.py - Pisca um LED ligado a um pino GPIO da Raspberry Pi
Prática 5 (SEL0337 - Projetos em Sistemas Embarcados) - Checkpoint 1

APLICAÇÃO
    Liga e desliga um LED a cada 0,1 s, indefinidamente. O programa foi feito
    para ser iniciado automaticamente no boot da Raspberry Pi como um serviço do
    systemd (unit file: systemd/blink-python.service), sem que ninguém precise
    fazer login e executá-lo manualmente.

    No unit file, o próprio interpretador Python é o programa chamado em
    ExecStart= (/usr/bin/python3 /home/sel/blink.py): o systemd inicia o Python,
    e o Python executa este script. Ao parar o serviço (systemctl stop), o
    systemd executa o programa de ExecStop= (blinkoff.sh), que apaga o LED e
    libera o GPIO.

FUNCIONAMENTO
    O acesso ao GPIO é feito pelo sistema de arquivos virtual sysfs
    (/sys/class/gpio), o mesmo mecanismo do script bash/blink.sh:
      1. unexport  -> libera o pino, caso tenha ficado exportado antes;
      2. export    -> cria a pasta /sys/class/gpio/gpioN que representa o pino;
      3. direction -> configura o pino como saída ("out");
      4. value     -> escreve 1 (LED aceso) ou 0 (LED apagado) em um laço infinito.

    O programa também trata o sinal SIGTERM (enviado pelo systemd ao parar o
    serviço) para encerrar de forma limpa, com código de saída 0.

USO MANUAL (teste): python3 blink.py   (Ctrl+C encerra)
Pino utilizado: GPIO 40
"""

import os
import signal
import sys
import time

GPIO_PIN = 40                        # número do pino no sysfs
SYSFS_GPIO = "/sys/class/gpio"       # raiz do GPIO no sistema de arquivos
GPIO_DIR = f"{SYSFS_GPIO}/gpio{GPIO_PIN}"  # pasta criada após o export
INTERVALO = 0.1                      # tempo aceso / apagado, em segundos


def escrever(caminho, valor):
    """Escreve um valor em um arquivo do sysfs (equivale a: echo valor > caminho)."""
    with open(caminho, "w") as arquivo:
        arquivo.write(str(valor))


def encerrar(signum, frame):
    """Chamada quando o systemd envia SIGTERM (systemctl stop): sai com sucesso."""
    sys.exit(0)


def configurar_gpio():
    """Exporta o pino e o configura como saída."""
    try:
        escrever(f"{SYSFS_GPIO}/unexport", GPIO_PIN)   # libera o pino, se já exportado
    except OSError:
        pass                                           # não estava exportado: normal
    escrever(f"{SYSFS_GPIO}/export", GPIO_PIN)         # cria /sys/class/gpio/gpio40
    time.sleep(0.1)                                    # dá tempo ao kernel de criar os arquivos
    escrever(f"{GPIO_DIR}/direction", "out")           # pino como saída


def piscar():
    """Laço infinito: acende o LED, espera, apaga o LED, espera."""
    while True:
        escrever(f"{GPIO_DIR}/value", 1)   # nível alto: LED aceso
        time.sleep(INTERVALO)
        escrever(f"{GPIO_DIR}/value", 0)   # nível baixo: LED apagado
        time.sleep(INTERVALO)


def main():
    signal.signal(signal.SIGTERM, encerrar)   # trata o "stop" do systemd
    configurar_gpio()
    print(f"blink.py iniciado: LED piscando no GPIO {GPIO_PIN}", flush=True)  # vai para o journalctl
    try:
        piscar()
    except KeyboardInterrupt:
        pass                                  # Ctrl+C em teste manual
    except OSError:
        # Se a pasta do GPIO sumiu, o ExecStop (blinkoff.sh) já liberou o pino
        # durante o "stop": é um encerramento normal. Caso contrário, é erro real.
        if os.path.exists(GPIO_DIR):
            raise
    finally:
        try:
            escrever(f"{GPIO_DIR}/value", 0)  # garante o LED apagado ao sair
        except OSError:
            pass                              # pino já liberado: nada a fazer
    return 0


if __name__ == "__main__":
    sys.exit(main())
