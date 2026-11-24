#!/bin/bash
# =============================================================================
# blink.sh - Pisca um LED ligado a um pino GPIO da Raspberry Pi
# Prática 5 (SEL0337 - Projetos em Sistemas Embarcados) - Checkpoint 1
#
# APLICAÇÃO
#   Liga e desliga um LED a cada 0,1 s, indefinidamente. Este script é o
#   "serviço" que o systemd pode iniciar automaticamente no boot
#   (ver systemd/blink.service).
#
# FUNCIONAMENTO
#   O acesso ao GPIO é feito direto pelo sistema de arquivos virtual sysfs
#   (/sys/class/gpio): escrever em um "arquivo" altera o hardware.
#     export    -> torna o pino disponível para uso (cria a pasta gpioN)
#     unexport  -> libera o pino (remove a pasta gpioN)
#     direction -> define se o pino é entrada ("in") ou saída ("out")
#     value     -> 1 = nível alto (LED aceso) | 0 = nível baixo (LED apagado)
#
# USO MANUAL (teste): chmod +x blink.sh && ./blink.sh   (Ctrl+C encerra)
# Pino utilizado: GPIO 40
# =============================================================================

# Libera o pino 40 caso ele já tenha sido exportado em uma execução anterior
# (evita o erro "Device or resource busy" no export). Se o pino ainda não
# estiver exportado, este comando mostra um erro, que pode ser ignorado.
echo 40 > /sys/class/gpio/unexport

# Exporta o pino 40: cria a pasta /sys/class/gpio/gpio40 para controlá-lo
echo 40 > /sys/class/gpio/export

# Configura o pino 40 como saída (out), pois ele vai alimentar o LED
echo out > /sys/class/gpio/gpio40/direction

# Laço infinito: o teste [ 1 ] é sempre verdadeiro
while [ 1 ]
do
    echo 1 > /sys/class/gpio/gpio40/value   # nível alto: LED aceso
    sleep 0.1s                              # espera 100 ms
    echo 0 > /sys/class/gpio/gpio40/value   # nível baixo: LED apagado
    sleep 0.1s                              # espera 100 ms
done
# Fim do laço: volta ao "do" e repete (período de 0,2 s = pisca a 5 Hz)
