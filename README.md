# SEL0337 – Prática 5: systemd, Git e GitHub em Linux Embarcado

**Disciplina:** SEL0337 – Projetos em Sistemas Embarcados (USP)
**Plataforma:** Raspberry Pi com Raspberry Pi OS
**Integrantes:** Davi Andrade Laet - 15697361
Giovanne Tomaszewski Grecco - 16228852

## 1. Resumo

Esta prática coloca uma aplicação embarcada para rodar **automaticamente no boot** da Raspberry Pi, sem que ninguém precise fazer login e executá-la à mão. A aplicação é um *blink* de LED no GPIO 40, controlado diretamente pelo sistema de arquivos `/sys/class/gpio` e gerenciado pelo **systemd** por meio de um *unit file* (`.service`). O código e a documentação são versionados com **Git** e publicados no **GitHub**.

- **Checkpoint 1:** serviço no systemd, primeiro com um script Bash (`blink.sh`) e depois com um programa Python (`blink.py`) chamado pelo unit file, com um programa em `ExecStop=`.
- **Checkpoint 2:** controle de versão com Git/GitHub e esta documentação.

---

## 2. Conceitos envolvidos

### 2.1 Boot da Raspberry Pi (descrição para a Raspberry Pi 3B+)

Na Raspberry Pi quem assume o controle primeiro é a **GPU** (VideoCore), e não a CPU ARM.

| Estágio | O que acontece |
|---|---|
| ROM do SoC (*first-level bootloader*) | A GPU executa um código gravado na ROM do SoC Broadcom, inicializa alguns clocks e procura o cartão microSD (ou USB/Ethernet). Na partição `boot` (FAT32) busca o `bootcode.bin`. |
| `bootcode.bin` (*second-level*) | Inicializa a SDRAM e busca o `start.elf`. |
| `start.elf` (*third-level*) | Firmware da GPU. Lê o `config.txt`, carrega os *device trees* (`.dtb`) e a imagem do kernel na RAM e passa o controle à CPU ARM (parâmetros em `cmdline.txt`). |
| Kernel Linux | Inicializa os *device drivers* e monta o `rootfs` (partição ext4, a raiz `/`). |
| *Init system* (systemd) | Primeiro processo do espaço de usuário (PID 1). Inicia todos os serviços e os mantém até o desligamento. |

### 2.2 Init system e systemd

O *init system* é a etapa que inicializa o sistema operacional logo depois do kernel. O **systemd** é o init system moderno do Raspberry Pi OS, Debian, Ubuntu e outras distribuições. Comparado ao SysVinit (scripts shell em `/etc/init.d`), ele inicia serviços em paralelo, usa arquivos de configuração declarativos (`.service`), é mais rápido e organiza os processos em *cgroups* (um processo filho pertence ao grupo do pai).

### 2.3 Unit file

Um arquivo `.service` descreve como o systemd deve iniciar, parar e gerenciar um serviço. Tem três blocos:

| Seção | Função | Neste projeto |
|---|---|---|
| `[Unit]` | Descrição e dependências | `Description=` (texto mostrado no boot), `After=` |
| `[Service]` | Como executar o serviço | `Type=simple`, `ExecStart=` (o que roda ao iniciar), `ExecStop=` (o que roda ao parar) |
| `[Install]` | Quando o serviço é habilitado | `WantedBy=multi-user.target` |

### 2.4 systemctl

| Comando | Função |
|---|---|
| `sudo systemctl start blink-python` | Inicia o serviço agora |
| `sudo systemctl stop blink-python` | Para o serviço (executa o `ExecStop=`) |
| `sudo systemctl enable blink-python` | Habilita a inicialização automática no boot |
| `sudo systemctl disable blink-python` | Desabilita a inicialização no boot |
| `systemctl status blink-python` | Mostra estado e mensagens de erro |
| `sudo systemctl daemon-reload` | Recarrega os unit files após alterações |
| `journalctl -u blink-python -b` | Mostra os logs do serviço desde o último boot |

---

## 3. Montagem

LED em série com um resistor limitador de corrente (valor: <!-- PREENCHER: valor do resistor -->), ligado entre o pino GPIO 40 (número usado em `/sys/class/gpio`) e o GND da Raspberry Pi.

---

## 4. Estrutura do repositório

```
SEL0337-Pratica5/
├── README.md
├── .gitignore
├── bash/
│   ├── blink.sh                  # blink do LED em Bash (código do roteiro)
│   └── blinkoff.sh               # programa do ExecStop: apaga o LED e libera o GPIO
├── python/
│   └── blink.py                  # blink do LED em Python (chamado pelo unit file)
├── systemd/
│   ├── blink.service             # unit file do serviço em Bash
│   └── blink-python.service      # unit file do serviço em Python
└── imagens/                      # fotos da montagem e do funcionamento
```

---

## 5. Checkpoint 1 – Serviço no systemd

### 5.1 Script Bash (`bash/blink.sh`)

O acesso ao GPIO é feito pelo sysfs: escrever em um arquivo altera o hardware.

| Comando | O que faz |
|---|---|
| `echo 40 > /sys/class/gpio/unexport` | Libera o pino, caso já esteja exportado de uma execução anterior |
| `echo 40 > /sys/class/gpio/export` | Exporta o pino, criando `/sys/class/gpio/gpio40` |
| `echo out > /sys/class/gpio/gpio40/direction` | Configura o pino como saída |
| `echo 1 > .../gpio40/value` | Nível alto: LED aceso |
| `echo 0 > .../gpio40/value` | Nível baixo: LED apagado |
| `while [ 1 ] ... done` | Repete indefinidamente, com `sleep 0.1s` entre as mudanças |

### 5.2 Programa Python (`python/blink.py`)

Faz o mesmo que o script Bash, escrevendo nos mesmos arquivos do sysfs. Além disso: trata o sinal `SIGTERM` (enviado pelo systemd no `stop`) para encerrar de forma limpa, apaga o LED ao sair e imprime uma mensagem que aparece no `journalctl`. Todo o funcionamento está comentado no próprio código.

### 5.3 Unit file do serviço em Python (`systemd/blink-python.service`)

```ini
# =============================================================================
# blink-python.service - unit file do serviço em Python (python/blink.py)
# Instalação: sudo cp blink-python.service /lib/systemd/system/
# Ajuste /home/sel/ se os arquivos estiverem em outra pasta.
# Habilite apenas UM dos serviços (blink ou blink-python), pois ambos
# controlam o mesmo pino.
# =============================================================================

[Unit]
# Texto exibido na tela de boot: "[ OK ] Started Blink LED (Python)."
Description=Blink LED (Python)
# Inicia depois do sistema básico no ar (inclui o sysfs do GPIO).
# Obs.: o roteiro usa After=multi-user.target, mas junto com
# WantedBy=multi-user.target isso pode gerar um ciclo de ordenação no systemd.
After=basic.target

[Service]
# simple: o processo de ExecStart é o próprio serviço
Type=simple
# O Python também é chamado no unit file: o systemd inicia o interpretador,
# que executa o script (e depende dele para importar as bibliotecas).
ExecStart=/usr/bin/python3 /home/sel/blink.py
# Programa executado ao parar o serviço (systemctl stop blink-python):
# apaga o LED e libera o GPIO 40.
ExecStop=/home/sel/blinkoff.sh
# Sem User=, o serviço roda como root (necessário para escrever em /sys/class/gpio).

[Install]
# Habilita o serviço no boot (systemctl enable) dentro do grupo multi-user
WantedBy=multi-user.target
```

O próprio Python é chamado no unit file (`/usr/bin/python3 /home/sel/blink.py`): o systemd inicia o interpretador, que executa o script. No `ExecStop=` roda o `blinkoff.sh`, que apaga o LED e faz o `unexport` do GPIO.

### 5.4 Instalação e teste

```bash
# 1) Copiar os arquivos para /home/sel (ajuste se for outra pasta)
cp bash/blink.sh bash/blinkoff.sh python/blink.py /home/sel/
chmod +x /home/sel/blink.sh /home/sel/blinkoff.sh /home/sel/blink.py

# 2) Teste manual (Ctrl+C encerra)
/home/sel/blink.sh
python3 /home/sel/blink.py

# 3) Instalar o unit file
sudo cp systemd/blink-python.service /lib/systemd/system/
sudo systemctl daemon-reload

# 4) Testar o serviço
sudo systemctl start blink-python
systemctl status blink-python
sudo systemctl stop blink-python        # executa o ExecStop (blinkoff.sh)

# 5) Habilitar no boot e reiniciar
sudo systemctl enable blink-python
sudo reboot
```

Para o serviço em Bash, use `blink.service` e o nome `blink` nos comandos. **Habilite apenas um dos dois serviços**, pois ambos controlam o mesmo pino.

Após o reboot, o LED deve piscar sem nenhum login. Para ver a mensagem `[ OK ] Started Blink LED (Python).` no boot, desabilite a *splash screen* (`sudo raspi-config` → System → Splash Screen).

---

## 6. Checkpoint 2 – Git e GitHub

Fluxo usado: o repositório local fica na Raspberry Pi (**trabalho local**) e o GitHub é o repositório remoto (**origin**).

| Comando | Para que serve |
|---|---|
| `git init` | Cria o repositório local |
| `git config --global user.name "usuario"` / `user.email "email"` | Identifica o autor dos commits |
| `git clone https://...` | Copia um repositório remoto para a máquina |
| `git add <arquivos>` | Seleciona mudanças para o próximo commit |
| `git commit -m "mensagem"` | Registra uma versão com mensagem descritiva |
| `git push` | Envia os commits locais ao GitHub |
| `git pull` | Traz do GitHub as atualizações |
| `git log` | Mostra o histórico de commits |
| `git rm <arquivo>` | Remove um arquivo do repositório |
| `git checkout <arquivo>` | Descarta alterações locais ainda não commitadas |
| `git reset` | Desfaz `git add` ou move o ramo para um commit anterior |
| `.gitignore` | Lista arquivos que o Git deve ignorar |

O `git push` pede usuário e senha. No lugar da senha informa-se o **token de acesso pessoal** gerado em *Settings → Developer settings → Personal access tokens*. O `.gitignore` deste repositório ignora qualquer arquivo com `token` no nome, para que a chave não seja enviada ao GitHub por engano.

O histórico completo de versões está no próprio GitHub (aba *Commits*) e foi exportado com `git log > historico_git.txt`.

---

## 7. Resultados

**Montagem prática:**

![Montagem prática](imagens/montagem.jpg)

**Funcionamento (LED piscando após o boot / status do serviço):**

![Funcionamento do serviço](imagens/funcionamento.jpg)

---

## 8. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Serviço não inicia | `systemctl status blink-python` e `journalctl -u blink-python -b --no-pager` |
| `Permission denied` | O serviço roda como root. No teste manual use `sudo`. |
| `Device or resource busy` no export | Pino já exportado: `echo 40 \| sudo tee /sys/class/gpio/unexport` |
| LED não pisca | O número do pino no sysfs depende do `gpiochip`: confira com `cat /sys/class/gpio/gpiochip*/base` e `ls /sys/class/gpio` |
| Alterou o unit file e nada mudou | Copie-o de novo para `/lib/systemd/system/` e rode `sudo systemctl daemon-reload` |
| `No such file` no `ExecStart` | Confira os caminhos em `/home/sel/` e a permissão de execução (`chmod +x`) |

---

## 9. Referências

- `man systemd.service`, `man systemd.unit`, `man systemctl`
- Documentação do Git: https://git-scm.com/doc
- Documentação da Raspberry Pi: https://www.raspberrypi.com/documentation/
- Roteiro da Prática 5 – SEL0337 (USP)


Vídeo do funcionamento do projeto:

https://github.com/user-attachments/assets/bf46b5b2-4649-4c0a-b4f7-f2b05d50ebfd
